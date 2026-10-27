"""Stage 9 runner: seal the frozen config, predict and seal, join, evaluate. Stops at the first
refusal. It writes exactly the ledger engine/scripts/stage9_analysis.py reads, and evaluate
calls that script; no endpoint is computed here.

Phases, each against one hash-chained ledger (lens_engine.harness.ledger), named in the config:

  1. seal_config  the config's SHA-256 is sealed as `stage9:FROZEN`, the first entry of a fresh
                  ledger, with the code hash. Publish the printed hash outside the ledger
                  (spec 4.1) before phase 2 touches real data.
  2. predict      the ledger must verify and hold only that entry. Real sources (the sealed
                  holdout, any pair_files set) open only with the published config hash and an
                  explicit Stage 9 confirmation. Every blind pair gets one sealed record
                      {"record": "pair", "test_id", "p", "p_text",
                       "baselines": {position, length, always_newer, familiarity,
                                     recognition},
                       "familiarity": standardised familiarity gap, chosen arm minus other,
                       "b_is_later": slot B holds the later arm (the analysis's control side)}
                  and every arm one {"record": "arm", "test_id", "score"} (best-of-k). The
                  prediction-side null tests run, then the manifest `stage9:PREDICTIONS`
                  closes the phase with their results. Publish the printed head.
  3. join         the ledger must verify against that published head, and every rebuilt pair
                  and arm must match its sealed text hash. Only then do the sources release
                  outcomes: {"status": decided|null|identical, "y"} per pair and {"is_best"}
                  per arm. Undecided pairs and tied tests get no outcome. The day is closed
                  and the final head printed. The sealed holdout is read once per run, so it
                  is joined only in the process that predicted it (cli `sealed-run`).
  4. evaluate     the ledger is verified against the published final head and the outcome-side
                  null tests run first (inside stage9_analysis.run, its step 3b, so the gate is
                  the same standalone). Only if every spec 4.7 null test passed does
                  stage9_analysis.run (prereg gate, config hash, ledger, endpoints P, S1-S6 in
                  order) compute any accuracy number; otherwise none is computed or written.
"""
from __future__ import annotations

import hashlib
import json
import math
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from lens_engine.harness.ledger import Ledger, verify
from lens_engine.stage9 import config as C
from lens_engine.stage9 import nulls
from lens_engine.stage9 import sources as S
from lens_engine.stage9.analysis import S9
from lens_engine.stage9.models import blind, blind_arms

FROZEN_REF, MANIFEST_REF = S.FROZEN_REF, S.MANIFEST_REF
RESULTS_SCHEMA = "lens.stage9.results/2"


class Refused(RuntimeError):
    """The phase must not run."""


def _sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def _text_sha(it: dict) -> str:
    return _sha(it["text_a"], it["text_b"])


def _sig(x: float) -> float:
    x = max(-50.0, min(50.0, x))
    return 1 / (1 + math.exp(-x))


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _load(config_path, root):
    cfg, sha = C.load(config_path, strict=True)
    return cfg, sha, C.resolve(root, cfg["ledger"]["path"])


def _open(path: Path, clock=None) -> Ledger:
    path.parent.mkdir(parents=True, exist_ok=True)
    return Ledger(str(path), **({"clock": clock} if clock else {}))


@contextmanager
def _atomic(led: Ledger):
    led.con.execute("BEGIN")
    try:
        yield
    except BaseException:
        led.con.execute("ROLLBACK")
        raise
    led.con.execute("COMMIT")


def _preds(led: Ledger) -> dict:
    return {r[3]: (r[0], r[1], json.loads(r[4])) for r in led.rows() if r[2] == "prediction"}


def _check_frozen(led: Ledger, sha: str, expected_head: str | None = None) -> dict:
    v = verify(led, expected_head=expected_head)
    if not v.ok:
        raise Refused("ledger does not verify: " + "; ".join(v.problems[:5]))
    rows = led.rows()
    if not rows or rows[0][2] != "prediction" or rows[0][3] != FROZEN_REF:
        raise Refused(f"the first ledger entry must be {FROZEN_REF}: run seal-config first")
    pr = _preds(led)
    if pr[FROZEN_REF][2]["config_sha256"] != sha:
        raise Refused(f"config file sha256 {sha} differs from the sealed "
                      f"{pr[FROZEN_REF][2]['config_sha256']}")
    _check_code(pr[FROZEN_REF][2])
    return pr


def _check_code(frozen: dict) -> None:
    """Package 2.9 and 4 step 7: the run uses exactly the code sealed with stage9:FROZEN. A code
    change after seal-config is refused here; it needs a new config_id and a new ledger."""
    now = C.code_sha256()
    if frozen.get("code_sha256") != now:
        raise Refused(f"the Stage 9 code changed since seal-config (sealed "
                      f"{frozen.get('code_sha256')}, now {now}): a new config and ledger are needed")


# ------------------------------------------------------------------ 1. seal the config
def _is_holdout(cfg: dict) -> bool:
    return any(d["source"] == "upworthy_sealed_holdout" for d in cfg["datasets"])


def seal_config(config_path, root=C.ROOT, clock=None, package=None) -> dict:
    """Seal the config as stage9:FROZEN. Runbook G8: the signed package's SHA-256 is recorded in the
    same entry (`package_sha256`). A real (non-synthetic) holdout config refuses unless `package` is
    a signed PREREG_PACKAGE_v<N>.md and its hash is already a `package` line in
    docs/track-record/README.md (publication.require_published); other configs record it if given."""
    from lens_engine.stage9 import publication as P
    cfg, sha, lp = _load(config_path, root)
    pkg = None
    try:
        if _is_holdout(cfg) and not C.is_synthetic(cfg):
            if package is None:
                raise Refused("the Stage 9 holdout config seals only with --package "
                              "research/accuracy/PREREG_PACKAGE_v<N>.md (the signed copy: v1, or v2 "
                              "after the 2026-10-23 re-seal), whose hash is published as a "
                              "`package` line in docs/track-record/README.md first (runbook G8)")
            pkg = P.require_published(root, package)
        elif package is not None:
            pkg = P.package_record(root, package)
    except P.PublicationError as e:
        raise Refused(str(e)) from None
    led = _open(lp, clock)
    if led.rows():
        raise Refused("ledger is not empty: a Stage 9 run starts on a fresh ledger")
    payload = {"config_sha256": sha, "config_id": cfg["config_id"], "code_sha256": C.code_sha256(),
               "synthetic": C.is_synthetic(cfg), "internal_benchmark": cfg["internal_benchmark"]}
    if pkg:
        payload.update(pkg)
    led.seal_prediction(FROZEN_REF, payload)
    out = {"config_id": cfg["config_id"], "config_sha256": sha, "ledger": str(lp),
           "head": led.head_hash(), "synthetic": C.is_synthetic(cfg)}
    if pkg:
        out["package_sha256"] = pkg["package_sha256"]
    return out


def _sources(cfg: dict, published: bool, given: dict | None):
    if given is not None:
        if set(given) != {d["id"] for d in cfg["datasets"]}:
            raise Refused("injected sources must match the config's datasets exactly")
        return given
    return {d["id"]: S.build(d, published=published) for d in cfg["datasets"]}


def _gate_credit(cfg: dict, credit_usd) -> float:
    """PREREG_PACKAGE_DRAFT.md section 2.7 (Emily's decision 4): a real run that makes paid calls
    never starts with less credit in hand than its reserve (>= its worst-case cost): if the credit
    ran out halfway, the run would be lost after the holdout was read."""
    cr = cfg.get("credit")
    if not cr:   # config.validate requires the section; never skip the check on a real run
        raise Refused("the config has no credit section (package 2.7): real data stays closed")
    if isinstance(credit_usd, bool) or not isinstance(credit_usd, (int, float)):
        raise Refused("real Stage 9 data needs --credit-in-hand-usd (the API credit read from the "
                      f"console just before the run; reserve {cr['reserve_usd']} USD)")
    if credit_usd < cr["reserve_usd"]:
        raise Refused(f"credit in hand {credit_usd} USD is below the Stage 9 reserve "
                      f"{cr['reserve_usd']} USD (worst case {cr['worst_case_usd']} USD): top up first")
    return float(credit_usd)


def _gate_paid(cfg: dict, credit_usd, frontier: dict | None) -> float:
    """Which credit check a real predict runs (B4, Emily's ruling 4, 2026-10-21).

    A config holding the sealed Upworthy holdout makes every paid call in the text-only
    pre-collection (phase 2b), whose credit check runs before its holdout text read
    (precollect.gate_credit). predict then makes no paid call, so it checks the pre-collection
    instead of the credit: the sealed results must be passed, with the credit recorded at build at
    or above the reserve. Any other real config (prospective pair_files sets, no pre-collection)
    keeps the credit check here, before its rows are read."""
    if not any(d["source"] == "upworthy_sealed_holdout" for d in cfg["datasets"]):
        return _gate_credit(cfg, credit_usd)
    if not frontier or not frontier.get("head"):
        raise Refused("real Stage 9 holdout data needs the sealed text-only pre-collection first "
                      "(its credit check runs before its holdout text read, package section 4 "
                      "step 2): pass --precollect-head")
    try:
        return _gate_credit(cfg, frontier.get("credit_in_hand_usd"))
    except Refused as e:
        raise Refused(f"the pre-collection's sealed credit check does not hold: {e}") from None


def _gate_real(cfg: dict, sha: str, published_sha: str | None, confirm: bool) -> bool:
    """True when real data may open. Synthetic configs never need it."""
    if C.is_synthetic(cfg):
        return False
    if published_sha != sha:
        raise Refused("real Stage 9 data opens only after the config hash is published: pass "
                      "--published-config-sha256 equal to the sealed config hash")
    if not confirm:
        raise Refused("real Stage 9 data needs --confirm-stage9 (the owner's yes; spec 4.1, R11)")
    return True


# ------------------------------------------------------------------ 2. predict and seal
def _check_p(ref: str, k: str, v) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or not 0 <= v <= 1:
        raise Refused(f"{ref}: {k}={v!r} is not a probability")
    return float(v)


def baselines(cfg: dict, it: dict, scored: dict[str, dict[str, float]]) -> dict:
    """The S1 baselines as P(B wins) = sigmoid(scale * (s_B - s_A)). `scored` holds the per-text
    scores of familiarity and recognition."""
    b = cfg["baselines"]
    gap = {"length": len(it["text_b"]) - len(it["text_a"]),
           "position": it["order_b"] - it["order_a"],
           "always_newer": float(np.sign(it["order_b"] - it["order_a"])),
           **{k: v[it["text_b"]] - v[it["text_a"]] for k, v in scored.items()}}
    return {k: _sig(float(b[k]["scale"]) * gap[k]) for k in C.S1_BASELINES}


TEXT_SCORED = ("familiarity", "recognition")  # web_presence dropped 2026-10-20 (draft change 5.2)


def _score_texts(name: str, scorer, texts: list[str]) -> dict[str, float]:
    if scorer is None:
        raise Refused(f"no {name} scorer: S1 and the baselines null test need the {name} "
                      "baseline on every pair (models.TextScorer)")
    v = scorer.score_texts(texts)
    if len(v) != len(texts) or not all(isinstance(x, (int, float)) and math.isfinite(x)
                                       for x in v):
        raise Refused(f"the {name} scorer must return one finite number per text")
    return dict(zip(texts, map(float, v)))


def _arm_scores_from_pairs(arms: list[dict], items: list[dict], p: dict) -> list[float]:
    """Mean logit of the arm beating each other arm of its test, from the sealed pair p."""
    acc: dict[str, list[float]] = {}
    for it in items:
        lg = _logit(p[it["pred_id"]])
        acc.setdefault(it["arm_b"], []).append(lg)
        acc.setdefault(it["arm_a"], []).append(-lg)
    return [float(np.mean(acc[a["arm_id"]])) for a in arms]


def predict(config_path, stack, familiarity, probe=None, published_sha: str | None = None,
            confirm: bool = False, sources: dict | None = None, root=C.ROOT, clock=None,
            batch: int = 256, run_null_tests: bool = True, recognition=None,
            credit_usd=None, frontier: dict | None = None) -> dict:
    """frontier: the text-only pre-collection's results (precollect.load_results), or None. A real
    run with config frontier_arms must pass it: every arm then carries each frontier arm's score
    and the analysis computes F1 from them (package 5.4); a missing score fails closed."""
    cfg, sha, lp = _load(config_path, root)
    led = _open(lp, clock)
    pr = _check_frozen(led, sha)
    if len(pr) > 1 or len(led.rows()) > 1:
        raise Refused("predictions already exist in this ledger; a run predicts once")
    published = _gate_real(cfg, sha, published_sha, confirm)
    credit = _gate_paid(cfg, credit_usd, frontier) if published else None
    tables = _preflight(cfg, stack, frontier, published)
    null_items = _null_items(stack) if run_null_tests else None
    srcs = _sources(cfg, published, sources)
    _bind_precollection(cfg, srcs, frontier, published)
    items, arms = [], []
    for d in cfg["datasets"]:
        src = srcs[d["id"]]
        got = src.items()
        for it in got:
            if it["dataset"] != d["id"] or it["use_case"] != d["use_case"]:
                raise Refused(f"item {it['pred_id']} does not belong to dataset {d['id']}")
        items += got
        arms += src.arms()
    refs = [it["pred_id"] for it in items] + [a["arm_ref"] for a in arms]
    if len(set(refs)) != len(refs) or {FROZEN_REF, MANIFEST_REF} & set(refs):
        raise Refused("pair and arm refs must be unique and never a reserved ref")
    if not items:
        raise Refused("no items to predict")

    b = blind(items)
    lens = []
    for i in range(0, len(b), batch):
        lens += stack.predict_pairs(b[i:i + batch])
    if len(lens) != len(items):
        raise Refused("the stack returned the wrong number of predictions")
    p = {it["pred_id"]: _check_p(it["pred_id"], "p", lp_["p"]) for it, lp_ in zip(items, lens)}
    pt = {it["pred_id"]: _check_p(it["pred_id"], "p_text", lp_["p_text"])
          for it, lp_ in zip(items, lens)}

    texts = sorted({it[f"text_{s}"] for it in items for s in ("a", "b")})
    scorers = dict(zip(TEXT_SCORED, (familiarity, recognition)))
    scored = {k: _score_texts(k, sc, texts) for k, sc in scorers.items()}
    fam = scored["familiarity"]
    gaps = np.array([fam[it["text_b"]] - fam[it["text_a"]] for it in items])
    sd = float(gaps.std()) or 1.0

    if callable(getattr(stack, "score_arms", None)):
        ab = blind_arms(arms)
        scores = []
        for i in range(0, len(ab), batch):
            scores += stack.score_arms(ab[i:i + batch])
        method = "stack.score_arms"
    else:
        scores = _arm_scores_from_pairs(arms, items, p)
        method = "mean pair logit within the test"
    if len(scores) != len(arms) or not all(math.isfinite(float(s)) for s in scores):
        raise Refused("arm scores must be one finite number per arm")

    fr = _frontier_fields(cfg, frontier, arms, items, published)
    model = {"name": stack.name, "version": stack.version}
    counts: dict[str, dict] = {}
    pre = nulls.prediction_side(cfg, stack, probe, b, p, null_items=null_items) if run_null_tests else None
    arm_set = {d: getattr(srcs[d], "arm_set") for d in srcs if getattr(srcs[d], "arm_set", None)}
    with _atomic(led):  # every record and the manifest seal together, or none does
        for it, g in zip(items, gaps):
            ref = it["pred_id"]
            pp = p[ref]
            f = None if pp == 0.5 else float((g if pp > 0.5 else -g) / sd)
            led.seal_prediction(ref, {
                "record": "pair", "test_id": it["test_id"], "p": pp, "p_text": pt[ref],
                "baselines": baselines(cfg, it, scored), "familiarity": f,
                "b_is_later": bool(it["order_b"] > it["order_a"]),
                "dataset": it["dataset"], "use_case": it["use_case"], "arm_a": it["arm_a"],
                "arm_b": it["arm_b"], "text_sha256": _text_sha(it), "model": model})
            counts.setdefault(it["dataset"], {"pairs": 0, "arms": 0})["pairs"] += 1
        for a, s in zip(arms, scores):
            led.seal_prediction(a["arm_ref"], {
                "record": "arm", "test_id": a["test_id"], "score": float(s),
                "dataset": a["dataset"], "arm_id": a["arm_id"], "text_sha256": _sha(a["text"]),
                "model": model, **fr.get(a["arm_ref"], {})})
            counts[a["dataset"]]["arms"] += 1

        led.seal_prediction(MANIFEST_REF, {
            "config_sha256": sha, "n_pairs": len(items), "n_arms": len(arms), "datasets": counts,
            "arm_score_method": method, "familiarity_model": familiarity.name,
            "recognition_model": recognition.name, "credit_in_hand_usd": credit,
            "familiarity_gap_sd": sd, "model": model, "null_tests": pre,
            "precollect_head": (frontier or {}).get("head"),
            "precollect_coverage": (frontier or {}).get("coverage"),
            "gpu_pass_head": (tables or {}).get("gpu_pass_head"),
            "tables_manifest_sha256": (tables or {}).get("tables_manifest_sha256"),
            "tables": tables, "arm_set": arm_set or None})
    return {"n_pairs": len(items), "n_arms": len(arms), "datasets": counts, "arm_set": arm_set or None,
            "null_tests": pre, "head": led.head_hash(), "sources": srcs}


def _null_items(stack) -> list[dict] | None:
    """The constructed null pairs a table-backed stack was built for (frozen_models.FrozenStack:
    the staged null_pairs.jsonl, drawn from the pre-collection text set), loaded BEFORE the holdout
    read; None for a stack without them (the pairs are then constructed from the items)."""
    if not callable(getattr(stack, "null_items", None)):
        return None
    try:
        return stack.null_items()
    except Exception as e:  # noqa: BLE001  (before the read: any failure refuses cleanly)
        raise Refused(f"the stack's null pairs failed to load before the holdout read: {e}") from None


def _bind_precollection(cfg: dict, srcs: dict, frontier: dict | None, published: bool) -> None:
    """The arm-set rule (precollect.ARM_SET_RULE), BEFORE the holdout read: every sealed-holdout
    source gets the pre-collection's {(test id, text sha256): arm id} index, so its single read
    re-keys the load_packages arms to the ids every table uses. A real holdout run without the index
    refuses here."""
    for d in cfg["datasets"]:
        src = srcs[d["id"]]
        if not isinstance(src, S.UpworthyHoldoutSource):
            continue
        idx = (frontier or {}).get("arm_index")
        if idx:
            try:
                src.bind_precollection(idx)
            except S.SourceError as e:
                raise Refused(str(e)) from None
        elif published:
            raise Refused("the sealed holdout needs the pre-collection's arm index (the arm-set rule, "
                          "precollect.ARM_SET_RULE) before its read: pass --precollect-head")


def _preflight(cfg: dict, stack, frontier: dict | None, published: bool) -> dict | None:
    """Runbook gaps G2 and G7, BEFORE the holdout read: a stack backed by assembled tables
    (frozen_models.FrozenStack) checks that every pair, arm and text the run will score has its
    rows and that its describes come from the given pre-collection; its provenance (the GPU pass
    head, package 4 step 2b, and the table manifest sha256) is sealed in the manifest. A real
    holdout run refuses a stack without that provenance."""
    if callable(getattr(stack, "preflight", None)):
        try:
            return stack.preflight(frontier)
        except Exception as e:  # noqa: BLE001  (before the read: any failure refuses cleanly)
            raise Refused(f"the stack's preflight failed before the holdout read: {e}") from None
    if published and any(d["source"] == "upworthy_sealed_holdout" for d in cfg["datasets"]):
        raise Refused("a real holdout run needs a table-backed stack with provenance (the GPU pass "
                      "head, package 4 step 2b): use lens_engine.stage9.frozen_models:stack")
    return None


def _frontier_fields(cfg: dict, frontier: dict | None, arms: list[dict], items: list[dict],
                     published: bool) -> dict:
    """{arm_ref: {"frontier": {arm: score}, "frontier_probe": {arm: named?}}} from the sealed
    pre-collection. Fails closed on a real holdout run that lacks it or lacks any arm's score
    (the frontier arms run on the sealed holdout only; prospective sets have none)."""
    names = sorted((cfg.get("frontier_arms") or {}).keys() & {"opus_5_5_zero_shot", "sonnet_5_5_zero_shot"})
    if frontier is None:
        holdout = any(d["source"] == "upworthy_sealed_holdout" for d in cfg["datasets"])
        if published and names and holdout:
            raise Refused("real Stage 9 data needs the sealed text-only pre-collection (frontier "
                          "arms, package section 4 step 2b): pass its results")
        return {}
    from lens_engine.stage9 import precollect
    precollect.check_items(frontier, items)
    out: dict[str, dict] = {}
    kept: dict[str, set] = {}
    for a in arms:
        kept.setdefault(a["test_id"], set()).add(a["arm_id"])
    for name in names:
        f = frontier["frontier"][name]
        # precollect.PARTIAL_RULE: a pre-collection STOPPED by the spend rule covers some tests only;
        # arms of tests it never sent carry no frontier score (F1 runs on the covered tests). An arm
        # of a covered test without a score, or any missing score in a complete run, fails closed.
        partial = frontier.get("complete", True) is False
        covered = set(f.get("covered_tests") or ()) if partial else None
        miss = [a for a in arms if a["arm_id"] not in f["scores"]
                and not (partial and a["test_id"].split(":", 1)[-1] not in covered)]
        if miss:
            raise Refused(f"{len(miss)} arms have no {name} score in the pre-collection: fail closed")
        for a in arms:
            o = out.setdefault(a["arm_ref"], {"frontier": {}, "frontier_probe": {}})
            if a["arm_id"] not in f["scores"]:
                continue                                  # not covered (partial run, by rule)
            o["frontier"][name] = float(f["scores"][a["arm_id"]])
            t = a["test_id"].split(":", 1)[-1]
            named = f["probe"].get(t, "absent")
            # arm-set rule: a probe answer naming an arm the outcome read excluded leaves the test out
            # of the probe rows (never counted as 'not recognised', which is the answer N)
            if named != "absent" and (named is None or named in kept[a["test_id"]]):
                o["frontier_probe"][name] = named == a["arm_id"]
    return out


# ------------------------------------------------------------------ 3. join
def join(config_path, expected_head: str, published_sha: str | None = None,
         confirm: bool = False, sources: dict | None = None, root=C.ROOT, clock=None) -> dict:
    cfg, sha, lp = _load(config_path, root)
    led = _open(lp, clock)
    pr = _check_frozen(led, sha, expected_head=expected_head)
    if MANIFEST_REF not in pr:
        raise Refused("predictions are not sealed (no manifest): nothing to join")
    if any(r[2] == "outcome" for r in led.rows()):
        raise Refused("outcomes already joined in this ledger")
    published = _gate_real(cfg, sha, published_sha, confirm)
    srcs = _sources(cfg, published, sources)
    sealed = {k: v[2] for k, v in pr.items() if v[2].get("record") in ("pair", "arm")}
    with _atomic(led):  # all outcomes join together, or none does
        n = {"pairs_joined": 0, "arms_joined": 0, "pairs_without_outcome": 0,
             "arms_without_outcome": 0, "undecided": 0}
        for d in cfg["datasets"]:
            src = srcs[d["id"]]
            if isinstance(src, S.UpworthyHoldoutSource) and not src.loaded:
                raise Refused("the sealed holdout is read once per run: join it in the same "
                              "process that predicted it (cli `sealed-run`), never by re-reading "
                              "it")
            # rebuild the blind pairs and arms (the holdout from its single read) and check they
            # are exactly what was sealed
            rebuilt = {it["pred_id"]: _text_sha(it) for it in src.items()}
            rebuilt.update({a["arm_ref"]: _sha(a["text"]) for a in src.arms()})
            mine = {k: v for k, v in sealed.items() if v["dataset"] == d["id"]}
            if set(rebuilt) != set(mine):
                raise Refused(f"{d['id']}: rebuilt items differ from the sealed predictions")
            bad = [k for k, h in rebuilt.items() if mine[k]["text_sha256"] != h]
            if bad:
                raise Refused(f"{d['id']}: {len(bad)} item texts differ from what was sealed")
            rel = src.release(led)
            outs = {**rel["pairs"], **rel["arms"]}
            extra = set(outs) - set(mine)
            if extra:
                raise Refused(f"{d['id']}: {len(extra)} outcomes have no sealed prediction")
            for ref in sorted(mine):
                kind = mine[ref]["record"]
                o = outs.get(ref)
                if kind == "pair":
                    if o is not None and o.get("status") not in S.STATUSES:
                        raise Refused(f"{ref}: outcome status {o.get('status')!r}")
                    if o is None or o["status"] not in S.JOINED:
                        n["undecided" if o else "pairs_without_outcome"] += 1
                        continue
                    if o["status"] == "decided" and o.get("y") not in (0, 1):
                        raise Refused(f"{ref}: a decided outcome needs y in (0, 1)")
                    led.join_outcome(ref, o)
                    n["pairs_joined"] += 1
                else:
                    if o is None:
                        n["arms_without_outcome"] += 1
                        continue
                    if not isinstance(o.get("is_best"), bool):
                        raise Refused(f"{ref}: an arm outcome needs is_best true or false")
                    led.join_outcome(ref, {"is_best": o["is_best"]})
                    n["arms_joined"] += 1
        led.close_day()
    return {**n, "head": led.head_hash()}


# ------------------------------------------------------------------ 4. evaluate
def evaluate(config_path, expected_head: str, root=C.ROOT, package: Path | None = None) -> dict:
    """stage9_analysis.run does it all, null-test gate included (spec 4.7: it computes no
    endpoint unless every null test passes), so the gate is the same here and standalone."""
    cfg, sha, lp = _load(config_path, root)
    led = _open(lp)
    try:
        frozen = _preds(led).get(FROZEN_REF)
        if frozen is not None:          # no FROZEN entry: stage9_analysis refuses below
            _check_code(frozen[2])
    finally:
        led.con.close()
    try:
        res = S9.run(Path(config_path), expected_head, Path(root), package)
    except S9.Refused as e:
        raise Refused(f"stage9_analysis refused: {e}") from None
    led = _open(lp)
    try:
        man = _preds(led)[MANIFEST_REF]
    finally:
        led.con.close()
    nt, failed = res.pop("null_tests"), res.pop("null_tests_failed")
    return {"schema": RESULTS_SCHEMA, "config_id": cfg["config_id"], "config_sha256": sha,
            "ledger_head": expected_head, "synthetic": C.is_synthetic(cfg),
            "internal_benchmark": cfg["internal_benchmark"],
            "model": man[2].get("model"), "arm_score_method": man[2].get("arm_score_method"),
            "arm_set": man[2].get("arm_set"),
            "null_tests": nt, "null_tests_failed": failed, "accuracy_shown": not failed,
            "analysis": res}
