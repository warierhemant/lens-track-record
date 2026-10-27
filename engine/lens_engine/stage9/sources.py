"""Stage 9 data sources: blind items for prediction, outcomes only after the predictions seal.

Every source has three parts:
  items()             blind pairs: pred_id, dataset, use_case, test_id, arm ids and the two
                      texts, plus the arm order within the test (order_a, order_b; not an
                      outcome, used only by the position and always-newer baselines and never
                      shown to a predictor). No outcome, winner, click or class field.
  arms()              blind arms for best-of-k: arm_ref, dataset, test_id, arm_id, text.
  release(ledger)     {"pairs": {pred_id: outcome}, "arms": {arm_ref: {"is_best": bool}}}.
                      Refused unless the ledger verifies and holds the predictions manifest
                      (MANIFEST_REF), i.e. every prediction of the run was sealed first. Each
                      source releases once.

Test ids are prefixed with the dataset id, so clusters never collide across datasets.
Pair outcome status is decided, null, identical or undecided; undecided pairs are never joined
(stage9_analysis reads the first three only). A test whose top arm is tied gets no arm outcome
(as data.pairs.best_of_k drops it), decided after the seal, so the predicted set never depends
on an outcome. Slot order (which arm is B) comes from a seeded hash of the pair id.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from lens_engine.harness.ledger import Ledger, verify

FROZEN_REF = "stage9:FROZEN"
MANIFEST_REF = "stage9:PREDICTIONS"   # equal to stage9_analysis.MANIFEST_REF (tested)
BLIND_KEYS = ("pred_id", "dataset", "use_case", "test_id", "arm_a", "arm_b", "text_a", "text_b")
META_KEYS = ("order_a", "order_b")
ARM_KEYS = ("arm_ref", "dataset", "test_id", "arm_id", "text")
STATUSES = ("decided", "null", "identical", "undecided")
JOINED = ("decided", "null", "identical")


class SourceError(RuntimeError):
    pass


def _unit(*parts) -> float:
    h = hashlib.sha256("\x1f".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


def arm_ref(dataset: str, arm_id: str) -> str:
    return f"{dataset}:arm:{arm_id}"


def _ledger_ref(ledger: Ledger, ref: str):
    row = ledger.con.execute(
        "SELECT seq, ts, payload FROM ledger WHERE kind='prediction' AND ref=?", (ref,)).fetchone()
    return None if row is None else (row[0], row[1], json.loads(row[2]))


def best_arms(ctr: dict[str, tuple[str, float]]) -> dict[str, bool]:
    """{arm_id: (test_id, ctr)} -> {arm_id: is_best} for tests with one top arm only."""
    by: dict[str, list[tuple[str, float]]] = {}
    for a, (t, c) in ctr.items():
        by.setdefault(t, []).append((a, c))
    out = {}
    for arms in by.values():
        top = max(c for _, c in arms)
        if sum(c == top for _, c in arms) == 1 and len(arms) >= 2:
            out.update({a: c == top for a, c in arms})
    return out


class _Source:
    dataset: str
    use_case: str

    def __init__(self):
        self._released = False

    def items(self) -> list[dict]:
        raise NotImplementedError

    def arms(self) -> list[dict]:
        """Every arm that appears in a pair, once."""
        seen: dict[str, dict] = {}
        for it in self.items():
            for side in ("a", "b"):
                aid = it[f"arm_{side}"]
                if aid not in seen:
                    seen[aid] = {"arm_ref": arm_ref(self.dataset, aid), "dataset": self.dataset,
                                 "test_id": it["test_id"], "arm_id": aid,
                                 "text": it[f"text_{side}"]}
        return list(seen.values())

    def _check_gate(self, ledger: Ledger) -> dict:
        if self._released:
            raise SourceError(f"{self.dataset}: outcomes already released once")
        v = verify(ledger)
        if not v.ok:
            raise SourceError(f"{self.dataset}: ledger does not verify: {v.problems[:3]}")
        man = _ledger_ref(ledger, MANIFEST_REF)
        if man is None:
            raise SourceError(f"{self.dataset}: predictions are not sealed yet; outcomes refused")
        if self.dataset not in man[2].get("datasets", {}):
            raise SourceError(f"{self.dataset}: not in the sealed predictions manifest")
        self._released = True
        return {"manifest_seq": man[0], "frozen_ts": _ledger_ref(ledger, FROZEN_REF)[1]}

    def release(self, ledger: Ledger) -> dict:
        raise NotImplementedError


# ------------------------------------------------------------------ synthetic (tests, dry runs)
class SyntheticSource(_Source):
    """Generated tests of 2-4 arms with hidden strength s; P(B wins) = sigmoid(k (s_B - s_A)).
    The text carries a noisy copy of s so a mock stack can be informative without seeing y.
    Some tests get a duplicate of arm 0 (same text): that pair is an identical pair. The best
    arm is the argmax of s plus noise; ties never occur."""

    def __init__(self, dataset: str, use_case: str, n_tests: int = 120, seed: int = 0,
                 k: float = 2.5, decided_share: float = 0.8, undecided_share: float = 0.05,
                 dup_share: float = 0.25, arms: tuple[int, int] = (2, 4)):
        super().__init__()
        self.dataset, self.use_case = dataset, use_case
        rng = np.random.default_rng(seed)
        self._items, self._out, self._best = [], {}, {}
        for t in range(n_tests):
            tid = f"{dataset}:t{t}"
            n = int(rng.integers(arms[0], arms[1] + 1))
            s = list(rng.normal(0, 1, n))
            text = [f"synthetic headline {t}-{i} {'very ' * int(rng.integers(0, 4))}"
                    f"strength {s[i] + rng.normal(0, .3):.3f}" for i in range(n)]
            if rng.random() < dup_share:
                s.append(s[0])
                text.append(text[0])
            q = np.array(s) + rng.normal(0, 0.5, len(s))
            for i in range(len(s)):
                self._best[f"t{t}a{i}"] = bool(i == int(np.argmax(q)))
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    pid = f"{dataset}:t{t}:a{i}|a{j}"
                    a, b = (i, j) if _unit(seed, pid) < 0.5 else (j, i)
                    self._items.append({
                        "pred_id": pid, "dataset": dataset, "use_case": use_case,
                        "test_id": tid, "arm_a": f"t{t}a{a}", "arm_b": f"t{t}a{b}",
                        "text_a": text[a], "text_b": text[b], "order_a": a, "order_b": b})
                    u = rng.random()
                    if text[a] == text[b]:
                        self._out[pid] = {"status": "identical"}
                    elif u < decided_share:
                        pb = 1 / (1 + np.exp(-k * (s[b] - s[a])))
                        self._out[pid] = {"status": "decided", "y": int(rng.random() < pb)}
                    elif u < decided_share + undecided_share:
                        self._out[pid] = {"status": "undecided"}
                    else:
                        self._out[pid] = {"status": "null"}

    def items(self) -> list[dict]:
        return [dict(x) for x in self._items]

    def release(self, ledger: Ledger) -> dict:
        self._check_gate(ledger)
        return {"pairs": {k: dict(v) for k, v in self._out.items()},
                "arms": {arm_ref(self.dataset, a): {"is_best": b} for a, b in self._best.items()}}


# ------------------------------------------------------------------ other public outcome sets
class PairFileSource(_Source):
    """Two JSONL files. items: {pair_id, test_id, arm_a, arm_b, text_a, text_b, order_a,
    order_b}. outcomes: pair rows {pair_id, status, y (decided only, 1 if B won), closed_at}
    and optional best-arm rows {test_id, best_arm, closed_at}. The outcomes file is opened only
    in release(); it is prospective, so every closed_at must be later than the config's seal."""

    ITEM_FIELDS = {"pair_id", "test_id", "arm_a", "arm_b", "text_a", "text_b", "order_a",
                   "order_b"}

    def __init__(self, dataset: str, use_case: str, items_path: Path, items_sha256: str,
                 outcomes_path: Path):
        super().__init__()
        self.dataset, self.use_case = dataset, use_case
        self.items_path, self.items_sha256 = Path(items_path), items_sha256
        self.outcomes_path = Path(outcomes_path)

    def items(self) -> list[dict]:
        raw = self.items_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.items_sha256:
            raise SourceError(f"{self.dataset}: items file differs from the config's sha256")
        out = []
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if set(r) != self.ITEM_FIELDS:
                raise SourceError(f"{self.dataset}: items rows need exactly "
                                  f"{sorted(self.ITEM_FIELDS)}; got {sorted(r)}")
            out.append({"pred_id": f"{self.dataset}:{r['pair_id']}", "dataset": self.dataset,
                        "use_case": self.use_case, "test_id": f"{self.dataset}:{r['test_id']}",
                        "arm_a": str(r["arm_a"]), "arm_b": str(r["arm_b"]),
                        "text_a": r["text_a"], "text_b": r["text_b"],
                        "order_a": int(r["order_a"]), "order_b": int(r["order_b"])})
        return out

    def release(self, ledger: Ledger) -> dict:
        gate = self._check_gate(ledger)
        arms_of: dict[str, list[str]] = {}
        for a in self.arms():
            arms_of.setdefault(a["test_id"], []).append(a["arm_id"])
        pairs, arms = {}, {}
        for line in self.outcomes_path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not str(r.get("closed_at", "")) > gate["frozen_ts"]:
                raise SourceError(f"{self.dataset}: outcome {r.get('pair_id', r.get('test_id'))} "
                                  "closed at or before the config was sealed (not prospective)")
            if "best_arm" in r:
                tid = f"{self.dataset}:{r['test_id']}"
                for a in arms_of.get(tid, []):
                    arms[arm_ref(self.dataset, a)] = {"is_best": a == str(r["best_arm"])}
                continue
            o = {"status": r["status"]}
            if r["status"] == "decided":
                o["y"] = int(r["y"])
            pairs[f"{self.dataset}:{r['pair_id']}"] = o
        return {"pairs": pairs, "arms": arms}


# ------------------------------------------------------------------ Upworthy sealed holdout
_CLASS = {"decided": "decided", "null_identical": "identical", "null_nonsig": "null",
          "undecided": "undecided"}


class UpworthyHoldoutSource(_Source):
    """The 8.0 sealed holdout through the sealed join path (lens_engine.stage9.access).

    Stage 9 only, on the Mac, after the config hash is published: the runner refuses to build
    this source before then. The holdout is read ONCE per object (spec 9 R11: touched more than
    once voids it): the first items() call reads it, later calls return the cached blind items,
    and the outcome columns (winner, class, click rates) are split off at once and released only
    after the predictions manifest is sealed. So predict and join must run in one process (cli
    `sealed-run`). Arms and their best-of-k target come from the same single read: each arm's
    click rate is on every pair it is in.

    The arm-set rule (precollect.ARM_SET_RULE). runner.predict binds the pre-collection's
    {(test id, text sha256): arm id} index BEFORE items() reads anything (bind_precollection). The
    read then re-keys every load_packages arm to its pre-collection arm id (precollect.reconcile),
    so arm ids, pair ids and arm refs are the pre-collection's and every table built from the
    text-only rebuild covers them. Pre-collection arms the read lacks (zero-impression arms, tests
    left with one arm) are excluded by rule and counted in `arm_set`; an outcome arm with no
    pre-collection arm refuses. Unbound (synthetic tests only) the load_packages ids are kept."""

    def __init__(self, dataset: str, use_case: str, holdout_sha256: str, slot_seed: int,
                 load_fn=None, hash_fn=None):
        super().__init__()
        self.dataset, self.use_case = dataset, use_case
        self.holdout_sha256, self.slot_seed = holdout_sha256, slot_seed
        self._load_fn, self._hash_fn = load_fn, hash_fn
        self._out: dict | None = None
        self._items: list[dict] | None = None
        self._index: dict | None = None
        self.arm_set: dict | None = None

    @property
    def loaded(self) -> bool:
        return self._items is not None

    def bind_precollection(self, index: dict) -> None:
        """Set the pre-collection arm index (precollect.load_results()["arm_index"]) before the read."""
        if self._items is not None:
            raise SourceError("bind the pre-collection before the holdout read, never after it")
        if not index:
            raise SourceError("the pre-collection arm index is empty: refused before the read")
        self._index = dict(index)

    def items(self) -> list[dict]:
        if self._items is not None:
            return [dict(x) for x in self._items]
        if self._load_fn is None:
            from lens_engine.data import guard
            from lens_engine.stage9 import access
            self._load_fn, self._hash_fn = access.holdout_pairs, guard.holdout_hash_on_file
        if self._hash_fn() != self.holdout_sha256:
            raise SourceError("holdout hash on file differs from the config: the seal is broken")
        df = self._load_fn()
        recs = df.to_dict("records")
        key = {}                                    # outcome arm id -> the id every table uses
        if self._index is not None:
            from lens_engine.stage9 import precollect
            seen = {(str(r["test_id"]), str(r[f"arm_id_{s}"]), r[f"headline_{s}"])
                    for r in recs for s in (1, 2)}
            try:
                key, self.arm_set = precollect.reconcile(self._index, sorted(seen))
            except precollect.PrecollectError as e:
                raise SourceError(f"arm-set rule: {e}") from None
        items, pairs, ctr = [], {}, {}
        for r in recs:
            arm = {s: key.get(str(r[f"arm_id_{s}"]), str(r[f"arm_id_{s}"])) for s in (1, 2)}
            # bound: the pair id (and so the A/B slot coin) uses the sorted pre-collection ids only
            pid = f"{self.dataset}:{'|'.join(sorted((arm[1], arm[2])))}" if key \
                else f"{self.dataset}:{r['pair_id']}"
            tid = f"{self.dataset}:{r['test_id']}"
            one_is_b = _unit(self.slot_seed, pid) < 0.5
            a, b = (2, 1) if one_is_b else (1, 2)
            items.append({"pred_id": pid, "dataset": self.dataset, "use_case": self.use_case,
                          "test_id": tid, "arm_a": arm[a], "arm_b": arm[b],
                          "text_a": r[f"headline_{a}"], "text_b": r[f"headline_{b}"],
                          "order_a": int(r[f"arm_idx_{a}"]), "order_b": int(r[f"arm_idx_{b}"])})
            o = {"status": _CLASS[r["pair_class"]]}
            if o["status"] == "decided":
                o["y"] = int(int(r["winner"]) == b)
            pairs[pid] = o
            for s in (1, 2):
                ctr[arm[s]] = (tid, float(r[f"ctr_{s}"]))
        arms = {arm_ref(self.dataset, a): {"is_best": v} for a, v in best_arms(ctr).items()}
        self._out, self._items = {"pairs": pairs, "arms": arms}, items
        return [dict(x) for x in items]

    def release(self, ledger: Ledger) -> dict:
        self._check_gate(ledger)
        if self._out is None:
            raise SourceError("items() was never called")
        out, self._out = self._out, None
        return out


def build(spec: dict, published: bool) -> _Source:
    """A source from one config dataset entry. The holdout needs published=True."""
    src = spec["source"]
    if src == "synthetic":
        return SyntheticSource(spec["id"], spec["use_case"], n_tests=spec.get("n_tests", 120),
                               seed=spec.get("seed", 0),
                               decided_share=spec.get("decided_share", 0.8),
                               dup_share=spec.get("dup_share", 0.25),
                               arms=tuple(spec.get("arms", (2, 4))))
    if src == "pair_files":
        return PairFileSource(spec["id"], spec["use_case"], spec["items"]["path"],
                              spec["items"]["sha256"], spec["outcomes"]["path"])
    if src == "upworthy_sealed_holdout":
        if not published:
            raise SourceError("the sealed holdout opens only after the config hash is published "
                              "(pass --published-config-sha256 and --confirm-stage9)")
        return UpworthyHoldoutSource(spec["id"], spec["use_case"], spec["holdout_sha256"],
                                     spec.get("slot_seed", 9001))
    raise SourceError(f"unknown source {src!r}")
