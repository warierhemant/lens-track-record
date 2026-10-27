"""Spec 4.7 null tests. All must pass before any accuracy number is shown.

Prediction side (run in `predict`, before any outcome exists; results sealed in the manifest):
  identical_pairs        n constructed pairs with the same text on both sides: "ahead" (called
                         by the can't-tell rule at s4.threshold) on <= 5%
  paraphrase_pairs       n constructed trivial paraphrases (punctuation, spacing, case): <= 10%
  scrambled_instruction  n pairs with different word counts, the probe asked "which has more
                         words?": answers follow word count on >= 80%
  stability              n pairs re-predicted after reseed: same pick on >= 90%
Outcome side (run in `evaluate`, from the verified ledger):
  mock_harness           n_runs seeded runs of n_pairs through this same runner (seal, predict,
                         join, stage9_analysis.read_ledger) with a mock whose p ignores
                         everything: kappa 95% cluster CI covers 0 on >= min_covering runs
  label_shuffle          n_shuffles shuffles of the decided labels; the one-sided rank test
                         p-values must be uniform (KS p > ks_p_min)
  null_pairs             false-winner rate on null pairs with its Wilson CI; needs >= min_n
  baselines_full_system  the full system (p) beats each S1 baseline, paired cluster CI > 0
                         (S1 of the analysis checks the learner, p_text). The baselines include
                         the recognition leakage guess (2026-10-18): if "pick the arm the
                         model recognises" does as well, the accuracy may be memory, not
                         reading. (The web_presence guess was dropped 2026-10-20, package
                         draft change 5.2.)
  ledger_tamper          an edited, a deleted and a back-dated entry of every kind, each
                         re-chained, are all detected against the published head
"""
from __future__ import annotations

import json
import math
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
from scipy import stats

from lens_engine.harness import metrics
from lens_engine.harness.ledger import canonical_json, entry_hash, verify
from lens_engine.stage9.analysis import S9


def _row(passed: bool, **kw) -> dict:
    return {"pass": bool(passed), **kw}


def _short(n_have: int, n_need: int) -> dict:
    return _row(False, n=n_have, why=f"only {n_have} available, {n_need} needed")


def _pick(p) -> np.ndarray:
    return np.sign(np.asarray(p, float) - 0.5)


def _sample(rng, seq, n):
    idx = rng.choice(len(seq), size=min(n, len(seq)), replace=False) if len(seq) else []
    return [seq[i] for i in sorted(idx)]


# ------------------------------------------------------------------ prediction side
_EDITS = (lambda t: t[:-1] if t.endswith(".") else t + ".",
          lambda t: "  ".join(t.split()),
          lambda t: (t[0].swapcase() + t[1:]) if t else t,
          lambda t: t + " ")


def null_arm_ids(kind: str, i: int) -> tuple[str, str]:
    """The arm ids of constructed null pair i (runbook gap G5): unique per pair, so a table-backed
    stack (ensemble.TableComponents, keyed by arm id) holds each pair's own readout and embedding
    rows (tables.assemble), and never a 'x'/'y' shared by every pair."""
    return f"null:{kind}:{i}:a", f"null:{kind}:{i}:b"


def constructed_texts(texts, n: int, seed: int, kind: str) -> list[tuple[str, str]]:
    """(text_a, text_b) of the n constructed pairs drawn from a set of distinct texts: identical
    (A == B) or a trivial paraphrase (punctuation, spacing, case). Depends only on the SET of texts
    and the seed, so the text-only staging (e2e_gpu_pass holdout set, holdout_emb) builds exactly
    the pairs constructed_pairs builds from the same texts at predict time."""
    keys = sorted(set(texts))
    rng = np.random.default_rng(seed)
    out = []
    for i, t in enumerate(_sample(rng, keys, n)):
        other = t
        for j in range(len(_EDITS) if kind == "paraphrase" else 0):
            other = _EDITS[(i + j) % len(_EDITS)](t)
            if other != t:  # an edit that changes nothing would be an identical pair
                break
        out.append((t, other))
    return out


def constructed_pairs(items: list[dict], n: int, seed: int, kind: str) -> list[dict]:
    """Blind items built from distinct arm texts: identical (A == B) or trivial paraphrase."""
    texts: dict[str, dict] = {}
    for it in items:
        for side in ("a", "b"):
            texts.setdefault(it[f"text_{side}"], it)
    out = []
    for i, (t, other) in enumerate(constructed_texts(texts, n, seed, kind)):
        src = texts[t]
        a, b = null_arm_ids(kind, i)
        out.append({"pred_id": f"null:{kind}:{i}", "dataset": src["dataset"],
                    "use_case": src["use_case"], "test_id": f"null:{kind}:{i}",
                    "arm_a": a, "arm_b": b, "text_a": t, "text_b": other})
    return out


def null_specs(texts, cfg: dict) -> list[dict]:
    """Every constructed null pair the prediction-side null tests will score, from the distinct
    holdout texts and the config (null_tests n, bootstrap seed): {pred_id, kind, arm_a, arm_b,
    text_a, text_b}. The text-only staging writes these (texts only to the GPU and Voyage routes,
    sha256 only to the tables)."""
    nt, seed = cfg["null_tests"], cfg["bootstrap"]["seed"]
    out = []
    for kind, key in (("identical", "identical_pairs"), ("paraphrase", "paraphrase_pairs")):
        for i, (t, o) in enumerate(constructed_texts(texts, nt[key]["n"], seed, kind)):
            a, b = null_arm_ids(kind, i)
            out.append({"pred_id": f"null:{kind}:{i}", "kind": kind, "arm_a": a, "arm_b": b,
                        "text_a": t, "text_b": o})
    return out


def _ahead(stack, built: list[dict], n: int, t: float, bar: float) -> dict:
    if len(built) < n:
        return _short(len(built), n)
    p = [r["p"] for r in stack.predict_pairs(built)]
    k = int(S9.called(p, t).sum())
    return _row(k / len(built) <= bar, n=len(built), ahead=k, rate=k / len(built),
                wilson95=list(metrics.wilson(k, len(built))), threshold=t, bar=bar)


def scrambled(probe, items: list[dict], n: int, bar: float, seed: int) -> dict:
    if probe is None:
        return _row(False, n=0, why="no probe given (--probe): not run")
    wc = lambda s: len(s.split())  # noqa: E731
    cand = [it for it in items if wc(it["text_a"]) != wc(it["text_b"])]
    if len(cand) < n:
        return _short(len(cand), n)
    sub = _sample(np.random.default_rng(seed), cand, n)
    ans = probe.more_words(sub)
    follow = sum(a is not None and (a > 0.5) == (wc(it["text_b"]) > wc(it["text_a"]))
                 for a, it in zip(ans, sub))
    return _row(follow / n >= bar, n=n, follow=follow, rate=follow / n, bar=bar,
                probe=getattr(probe, "name", None))


def stability(stack, items: list[dict], p_by_id: dict, n: int, bar: float, seed: int) -> dict:
    if len(items) < n:
        return _short(len(items), n)
    sub = _sample(np.random.default_rng(seed), items, n)
    if callable(getattr(stack, "reseed", None)):
        stack.reseed(seed + 1)
    p2 = [r["p"] for r in stack.predict_pairs(sub)]
    p1 = [p_by_id[it["pred_id"]] for it in sub]
    same = int((_pick(p1) == _pick(p2)).sum())
    return _row(same / n >= bar, n=n, same_pick=same, rate=same / n, bar=bar,
                reseeded=callable(getattr(stack, "reseed", None)))


def prediction_side(cfg: dict, stack, probe, items: list[dict], p_by_id: dict,
                    null_items: list[dict] | None = None) -> dict:
    """null_items: the constructed null pairs staged before the holdout read (the arm-set rule:
    drawn from the pre-collection text set, which can hold texts the outcome read dropped), as
    frozen_models.FrozenStack.null_items returns them; None constructs them from the items."""
    nt, seed, t = cfg["null_tests"], cfg["bootstrap"]["seed"], cfg["s4"]["threshold"]
    idn, par = nt["identical_pairs"], nt["paraphrase_pairs"]

    def built(kind, n):
        if null_items is None:
            return constructed_pairs(items, n, seed, kind)
        return [dict(r) for r in null_items if r["kind"] == kind]
    return {
        "identical_pairs": _ahead(stack, built("identical", idn["n"]), idn["n"], t, idn["ahead_max"]),
        "paraphrase_pairs": _ahead(stack, built("paraphrase", par["n"]), par["n"], t, par["ahead_max"]),
        "scrambled_instruction": scrambled(probe, items, nt["scrambled_instruction"]["n"],
                                           nt["scrambled_instruction"]["follow_min"], seed),
        "stability": stability(stack, items, p_by_id, nt["stability"]["n"],
                               nt["stability"]["same_pick_min"], seed),
    }


# ------------------------------------------------------------------ outcome side
def label_shuffle(y, p, n_shuffles: int, ks_min: float, seed: int) -> dict:
    """One-sided Mann-Whitney (normal approximation, tie-corrected) of p on shuffled labels."""
    y, p = np.asarray(y, int), np.asarray(p, float)
    n1, n = int(y.sum()), len(y)
    n0 = n - n1
    if n1 == 0 or n0 == 0:
        return _row(False, n=n, why="decided labels are all one class")
    r = stats.rankdata(p)
    _, ties = np.unique(p, return_counts=True)
    var = n1 * n0 / 12 * ((n + 1) - (ties ** 3 - ties).sum() / (n * (n - 1)))
    if var <= 0:
        return _row(False, n=n, why="every p is the same")
    rng = np.random.default_rng(seed)
    pv = np.empty(n_shuffles)
    for i in range(n_shuffles):
        u = r[rng.permutation(y) == 1].sum() - n1 * (n1 + 1) / 2
        pv[i] = stats.norm.sf((u - n1 * n0 / 2) / math.sqrt(var))
    ks = float(stats.kstest(pv, "uniform").pvalue)
    return _row(ks > ks_min, n=n, n_shuffles=n_shuffles, ks_p=ks, bar=ks_min,
                share_p_below_05=float((pv < 0.05).mean()))


def null_pairs(p_null, t: float, min_n: int) -> dict:
    n = len(p_null)
    k = int(S9.called(p_null, t).sum()) if n else 0
    out = {"n": n, "called": k, "rate": k / n if n else None,
           "wilson95": list(metrics.wilson(k, n)), "threshold": t, "min_n": min_n}
    return _row(n >= min_n, **out, **({} if n >= min_n else {"why": f"only {n} null pairs"}))


def baselines_full(dec: list[dict], n_boot: int, seed: int) -> dict:
    cl = np.array([r["test_id"] for r in dec])
    y = np.array([r["y"] for r in dec], float)
    p = np.array([r["p"] for r in dec])
    rows = {}
    for name in S9.S1_BASELINES:
        if not all(name in r["baselines"] for r in dec):
            rows[name] = _row(False, why=f"baseline {name} missing on some decided pairs")
            continue
        pb = np.array([r["baselines"][name] for r in dec], float)
        d = metrics.cluster_bootstrap(
            lambda a, b, c: metrics.hit_rate(a, b) - metrics.hit_rate(a, c), cl, y, p, pb,
            n_boot=n_boot, seed=seed)
        rows[name] = _row(d["ci95"][0] > 0, hit_rate_diff=d["point"], ci95=list(d["ci95"]))
    return _row(all(v["pass"] for v in rows.values()), baselines=rows)


def _rechain(con, from_seq: int) -> None:
    rows = con.execute("SELECT seq, ts, kind, payload FROM ledger WHERE seq >= ? ORDER BY seq",
                       (from_seq,)).fetchall()
    prev = con.execute("SELECT hash FROM ledger WHERE seq < ? ORDER BY seq DESC LIMIT 1",
                       (from_seq,)).fetchone()
    prev = prev[0] if prev else "0" * 64
    for seq, ts, kind, payload in rows:
        h = entry_hash(prev, seq, ts, kind, json.loads(payload))
        con.execute("UPDATE ledger SET prev_hash=?, hash=? WHERE seq=?", (prev, h, seq))
        prev = h


def ledger_tamper(ledger_path: Path, head: str) -> dict:
    """On in-memory copies only: the published ledger is opened read-only and never written."""
    src = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True)
    try:
        rows = src.execute("SELECT seq, kind FROM ledger ORDER BY seq").fetchall()
        first = {}
        for seq, kind in rows:
            first.setdefault(kind, seq)
        cases = []
        for kind, seq in sorted(first.items()):
            for attack in ("edit", "delete", "backdate"):
                con = sqlite3.connect(":memory:", isolation_level=None)
                src.backup(con)
                con.execute("DROP TRIGGER IF EXISTS ledger_no_update")
                con.execute("DROP TRIGGER IF EXISTS ledger_no_delete")
                con.execute("BEGIN")
                if attack == "edit":
                    pl = json.loads(con.execute("SELECT payload FROM ledger WHERE seq=?",
                                                (seq,)).fetchone()[0])
                    pl["tampered"] = True
                    con.execute("UPDATE ledger SET payload=? WHERE seq=?",
                                (canonical_json(pl), seq))
                elif attack == "delete":
                    con.execute("DELETE FROM ledger WHERE seq=?", (seq,))
                else:
                    con.execute("UPDATE ledger SET ts=? WHERE seq=?",
                                ("2000-01-01T00:00:00.000000+00:00", seq))
                _rechain(con, seq)
                cases.append({"kind": kind, "attack": attack,
                              "detected": not verify(con, expected_head=head).ok})
                con.close()
    finally:
        src.close()
    return _row(bool(cases) and all(c["detected"] for c in cases), cases=cases,
                n_detected=sum(c["detected"] for c in cases), n=len(cases))


def mock_harness(n_runs: int, n_pairs: int, min_covering: int, n_boot: int, seed: int) -> dict:
    """Seeded mock runs through this runner and the analysis's own ledger reader."""
    from lens_engine.stage9 import config as C
    from lens_engine.stage9 import mocks, runner
    runs = []
    for i in range(n_runs):
        with tempfile.TemporaryDirectory() as d:
            c = C.synthetic(n_tests=n_pairs, n_boot=n_boot, seed=seed + i, decided_share=1.0)
            c["config_id"] = f"stage9-null-mock-{i}"
            c["datasets"][0].update(arms=[2, 2], dup_share=0.0)
            cp = Path(d) / "config.json"
            cp.write_text(json.dumps(c, indent=1))
            runner.seal_config(cp, root=d)
            pr = runner.predict(cp, mocks.RandomStack(seed + i), mocks.MockFamiliarity(),
                                root=d, run_null_tests=False,
                                recognition=mocks.MockRecognition())
            jn = runner.join(cp, pr["head"], sources=pr["sources"], root=d)
            data = S9.read_ledger(Path(d) / c["ledger"]["path"], jn["head"],
                                  C.sha256_file(cp))
            dec = [r for r in data.pairs if r["status"] == "decided"]
            k = metrics.cluster_bootstrap(metrics.cohen_kappa, [r["test_id"] for r in dec],
                                          np.array([r["y"] for r in dec], float),
                                          np.array([r["p"] for r in dec]),
                                          n_boot=n_boot, seed=seed + i)
            runs.append({"seed": seed + i, "n": len(dec), "kappa": k["point"],
                         "ci95": list(k["ci95"]), "covers_0": k["ci95"][0] <= 0 <= k["ci95"][1]})
    cov = sum(r["covers_0"] for r in runs)
    return _row(cov >= min_covering, runs=runs, n_covering=cov, bar=min_covering)


def outcome_side(cfg: dict, pairs: list[dict], ledger_path: Path, head: str) -> dict:
    nt, B = cfg["null_tests"], cfg["bootstrap"]
    dec = [r for r in pairs if r["status"] == "decided"]
    mh, ls = nt["mock_harness"], nt["label_shuffle"]
    return {
        "mock_harness": mock_harness(mh["n_runs"], mh["n_pairs"], mh["min_covering"],
                                     B["n_boot"], B["seed"]),
        "label_shuffle": label_shuffle([r["y"] for r in dec], [r["p"] for r in dec],
                                       ls["n_shuffles"], ls["ks_p_min"], B["seed"]),
        "null_pairs": null_pairs([r["p"] for r in pairs if r["status"] == "null"],
                                 cfg["s4"]["threshold"], nt["null_pairs"]["min_n"]),
        "baselines_full_system": baselines_full(dec, B["n_boot"], B["seed"]),
        "ledger_tamper": ledger_tamper(ledger_path, head),
    }
