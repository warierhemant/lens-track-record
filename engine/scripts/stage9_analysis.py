"""Stage 9 analysis (step 8.13, phase 6 "evaluate"): every pre-registered endpoint, once.

Run on the Mac, from the repo root, only after the Stage 9 package is sealed:

    python engine/scripts/stage9_analysis.py --config engine/experiments/stage9/FROZEN_CONFIG.json \
        --expected-head <published ledger head> --out engine/experiments/stage9/results.json

What it does, in order, and it stops at the first refusal:

  1. prereg gate   engine/scripts/prereg_check.py --strict must report 0 FAIL and 0 SKIP.
  2. config        loads the frozen config JSON, checks every required field and hashes its
                   bytes. The hash must equal `config_sha256` in the ledger's single
                   `stage9:FROZEN` entry, which must be sealed before every prediction.
  3. ledger        opened read-only, verified with lens_engine.harness.ledger.verify, anchored on
                   the head published after phase 5 (--expected-head; it cannot live in the
                   config, whose hash the ledger seals first). Every number comes from the
                   joined predictions and outcomes.
  3b. null tests   spec 4.7, the same gate the runner's `evaluate` applies (it calls this
                   function): the prediction-side rows come from the sealed manifest
                   `stage9:PREDICTIONS`, the outcome-side rows are run here
                   (lens_engine.stage9.nulls.outcome_side). If any row in NULL_TESTS fails or is
                   missing, no endpoint is computed: the output holds the null tests and
                   "withheld", and main() exits 3. Run standalone or through the runner, the
                   script never prints an endpoint unless every null test passed.
  4. endpoints     section 5 of research/accuracy/PREREG_PACKAGE_DRAFT.md in its fixed order
                   (P, S1, S2, S3, S4, C98, S5, S6), then the report-only familiarity rows. A
                   secondary is gated only while every earlier one passed; after the first
                   failure later rows are still computed but marked "not gated (hierarchy
                   stopped at X)". Every CI is a cluster bootstrap by test id with the frozen
                   n_boot and seed (2,000 and 9000 in the draft).

It never opens data/ or the sealed holdout: predictions and outcomes are read from the ledger only.

Ledger payloads (sealed by run_stage9.py phases 4 and 5; this is the contract it must follow):

  prediction, record "pair" (ref = pair id):
      {"record": "pair", "test_id", "p": P(B wins) from the frozen stack (text + describe),
       "p_text": text-only stack, "baselines": {name: P(B wins)} (position, length,
       always_newer, familiarity, recognition, running_base_rate),
       "familiarity": float (optional),
       "b_is_later": true if slot B holds the later (newer) arm of the test (required when
       the slots are randomised: it says which slot is the control)}
  prediction, record "arm" (ref = arm id): {"record": "arm", "test_id", "score": float}
  outcome for a pair: {"status": "decided" | "null" | "identical", "y": 1 if B won else 0
                       (decided only)}
  outcome for an arm: {"is_best": bool}
  prediction, ref "stage9:FROZEN": {"config_sha256", ...}; never gets an outcome.
  prediction, ref "stage9:PREDICTIONS" (the manifest): {"null_tests": {prediction-side rows}, ...};
  required (step 3b); never gets an outcome.
  every prediction without an outcome (the manifest, undecided pairs, tied tests) is skipped
  for the endpoints and counted in n_predictions_without_outcome.

"Always-control" (S5, S6) is the earlier arm of the test, as in 8.6: with b_is_later sealed on
every decided pair the control won when y != b_is_later. Only if b_is_later is missing on some
pair is slot A taken as the control (the legacy layout), and the row says so.

The "98% when confident" endpoint (C98) is the product's headline promise (RESUME.md 2026-10-15,
R-0 v2 plan dbadebd0, rule 4b, quoted by the owner on PR #9):

  (4b) per split, on the fit set's out-of-fold decided predictions, t98_s = the smallest t on
  the grid 0.00-0.49 such that at t and every larger grid t with at least 50 calls, selective
  accuracy >= 0.98 (0.5 = never call if none). Report realised coverage and selective accuracy
  (cluster CI) on home decided pairs, and null/identical call rates, for base and full.

`fit_t98` implements that rule. For Stage 9 one t98 per arm is fitted on the non-holdout
out-of-fold decided predictions named in the config (`c98.fit`: path, sha256 and the fitted
`threshold_full` / `threshold_base`); the analysis re-hashes that file, refits, and refuses if
either differs. A qualifying t must itself have at least `min_calls` calls (otherwise a tiny
fit set would qualify every t vacuously). C98 then reports, for full (`p`) and base (`p_text`):
selective accuracy and coverage on decided pairs with cluster-bootstrap CIs, null and
identical call rates (Wilson CIs), and the share of calls on nulls at the decided base rate.
Rule 4b itself is report-only; the gating pass rule of C98 (full arm only: `point` or
`ci_lower` >= target) comes from the config, fixed before sealing. t = 0.5 means never call.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ENGINE = Path(__file__).resolve().parents[1]
ROOT = ENGINE.parent
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from lens_engine.harness import metrics  # noqa: E402
from lens_engine.harness.ledger import verify  # noqa: E402
from lens_engine.r0 import decision  # noqa: E402

FROZEN_REF = "stage9:FROZEN"
MANIFEST_REF = "stage9:PREDICTIONS"
ORDER = ["P", "S1", "S2", "S3", "S4", "C98", "S5", "S6"]
# spec 4.7: every row must pass before any endpoint exists (lens_engine.stage9.nulls)
NULL_TESTS = ("mock_harness", "label_shuffle", "identical_pairs", "paraphrase_pairs",
              "null_pairs", "scrambled_instruction", "baselines_full_system", "stability",
              "ledger_tamper")
PREDICTION_SIDE_NULLS = ("identical_pairs", "paraphrase_pairs", "scrambled_instruction",
                         "stability")
EXIT_WITHHELD = 3
# S1 leakage / heuristic baselines. recognition (does the base model recognise the text as seen
# before) was added 2026-10-18 (PREREG_PACKAGE_DRAFT.md section 5, draft change 5.1). The
# web_presence baseline added with it was DROPPED 2026-10-20 (draft change 5.2, open item O13):
# no free, licensed, pre-cutoff exact-phrase web index was found. The drop is disclosed in the
# package and in the Stage 9 report.
S1_BASELINES = ["position", "length", "always_newer", "familiarity", "recognition"]
REQUIRED = {
    "config_id": str,
    "ledger": {"path": str},
    "bootstrap": {"n_boot": int, "seed": int},
    "primary": {"L_bar": float, "parity_bar": float, "pass_rule": str},
    "s2": {"margin_nats": float},
    "s3": {"slope_lo": float, "slope_hi": float, "ece_min_n": int},
    "s4": {"threshold": float, "null_call_max": float, "identical_ahead_max": float,
           "decided_base_rate": float},
    "c98": {"target_accuracy": float, "pass_rule": str, "source": str, "min_calls": int,
            "fit": {"path": str, "sha256": str, "threshold_full": float,
                    "threshold_base": float}},
    "s5": {"target_accuracy": float},
    "s6": {"plan_id": str, "checkpoints": list, "alpha_per_look": list},
    # extra metrics (PREREG_PACKAGE_DRAFT.md section 5.5, Emily's decision 5, 2026-10-20): reported
    # after the hierarchy, never part of it; each has a pre-set rule or the label "descriptive"
    "extra": {"kappa_matched": {"coverage": float, "external_kappa": float},
              "reliability": {"n_bins": int}},
    "null_tests": {k: {} for k in NULL_TESTS},
}
PASS_RULES = ("point", "ci_lower")


class Refused(RuntimeError):
    """The analysis must not run (gate failed, config or ledger not as sealed)."""


# ---------------------------------------------------------------- 1. prereg gate
def _load_prereg_check():
    spec = importlib.util.spec_from_file_location(
        "prereg_check", ENGINE / "scripts" / "prereg_check.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["prereg_check"] = mod  # dataclasses look the module up by name
    spec.loader.exec_module(mod)
    return mod


def prereg_gate(root: Path = ROOT, package: Path | None = None) -> dict:
    """Run prereg_check in strict mode. Any FAIL or SKIP refuses the analysis."""
    pc = _load_prereg_check()
    checks = pc.run(root, package or pc.PACKAGE, strict=True)
    bad = [c for c in checks if c.status != "PASS"]
    if not checks:
        raise Refused("prereg_check found nothing to check")
    if bad:
        lines = "; ".join(f"{c.status} {c.id}: {c.detail}" for c in bad[:5])
        raise Refused(f"prereg_check --strict did not pass ({len(bad)} not PASS): {lines}")
    return {"n_pass": len(checks)}


# ---------------------------------------------------------------- 2. config
def _check_shape(obj, shape, where="config"):
    for key, want in shape.items():
        if key not in obj or obj[key] is None:
            raise Refused(f"{where}.{key} missing or null (not frozen)")
        if isinstance(want, dict):
            if not isinstance(obj[key], dict):
                raise Refused(f"{where}.{key} must be an object")
            _check_shape(obj[key], want, f"{where}.{key}")
        elif want is float:
            if isinstance(obj[key], bool) or not isinstance(obj[key], (int, float)):
                raise Refused(f"{where}.{key} must be a number")
        elif not isinstance(obj[key], want) or isinstance(obj[key], bool):
            raise Refused(f"{where}.{key} must be {want.__name__}")


def load_config(path: Path) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    cfg = json.loads(raw)
    _check_shape(cfg, REQUIRED)
    for sec in ("primary", "c98"):
        if cfg[sec]["pass_rule"] not in PASS_RULES:
            raise Refused(f"config.{sec}.pass_rule must be one of {PASS_RULES}")
    s6 = cfg["s6"]
    if len(s6["checkpoints"]) != len(s6["alpha_per_look"]) or s6["checkpoints"] != sorted(
            s6["checkpoints"]):
        raise Refused("config.s6 checkpoints must be increasing and match alpha_per_look")
    ts = [("s4.threshold", cfg["s4"]["threshold"]),
          ("c98.fit.threshold_full", cfg["c98"]["fit"]["threshold_full"]),
          ("c98.fit.threshold_base", cfg["c98"]["fit"]["threshold_base"])]
    for name, t in ts:
        if not 0 <= t <= 0.5:
            raise Refused(f"config.{name} must be in [0, 0.5]")
    return cfg, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------- 3. ledger
@dataclass
class Data:
    pairs: list[dict]   # {"ref", "seq", "test_id", "p", "p_text", "baselines", "familiarity",
                        #  "status", "y"}
    arms: list[dict]    # {"ref", "test_id", "score", "is_best"}
    n_unjoined: int
    head: str
    manifest: dict | None = None   # payload of the sealed stage9:PREDICTIONS entry


def read_ledger(path: Path, expected_head: str, config_sha: str) -> Data:
    p = Path(path)
    if not p.exists():
        raise Refused(f"ledger not found: {p}")
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        v = verify(con, expected_head=expected_head)
        if not v.ok:
            raise Refused("ledger verify failed: " + "; ".join(v.problems[:5]))
        rows = con.execute(
            "SELECT seq, kind, ref, payload, hash FROM ledger ORDER BY seq").fetchall()
    finally:
        con.close()
    frozen = [(s, json.loads(pl)) for s, k, r, pl, _ in rows
              if k == "prediction" and r == FROZEN_REF]
    if len(frozen) != 1:
        raise Refused(f"expected exactly one {FROZEN_REF} entry, found {len(frozen)}")
    f_seq, f_pl = frozen[0]
    if f_pl.get("config_sha256") != config_sha:
        raise Refused(f"config sha256 {config_sha} differs from the sealed "
                      f"{f_pl.get('config_sha256')}")
    preds, outs = {}, {}
    for seq, kind, ref, payload, _ in rows:
        if kind == "prediction" and ref != FROZEN_REF:
            if seq < f_seq:
                raise Refused(f"prediction {ref} sealed before {FROZEN_REF}")
            preds[ref] = (seq, json.loads(payload))
        elif kind == "outcome":
            if ref == FROZEN_REF:
                raise Refused(f"{FROZEN_REF} must not have an outcome")
            outs[ref] = json.loads(payload)
    pairs, arms = [], []
    for ref, (seq, pr) in preds.items():
        if ref not in outs:
            continue
        o = outs[ref]
        if pr.get("record") == "pair":
            if o.get("status") not in ("decided", "null", "identical"):
                raise Refused(f"pair {ref}: outcome status {o.get('status')!r}")
            if o["status"] == "decided" and o.get("y") not in (0, 1):
                raise Refused(f"pair {ref}: decided outcome needs y in (0, 1)")
            pairs.append({"ref": ref, "seq": seq, "test_id": str(pr["test_id"]),
                          "p": float(pr["p"]), "p_text": float(pr["p_text"]),
                          "baselines": pr.get("baselines", {}),
                          "familiarity": pr.get("familiarity"),
                          "b_is_later": pr.get("b_is_later"),
                          "status": o["status"], "y": o.get("y")})
        elif pr.get("record") == "arm":
            arms.append({"ref": ref, "test_id": str(pr["test_id"]), "score": float(pr["score"]),
                         "is_best": bool(o["is_best"]), "frontier": pr.get("frontier") or {},
                         "frontier_probe": pr.get("frontier_probe") or {}})
        else:
            raise Refused(f"prediction {ref}: unknown record {pr.get('record')!r}")
    man = preds.get(MANIFEST_REF)
    return Data(pairs, arms, n_unjoined=len(set(preds) - set(outs)),
                head=rows[-1][4], manifest=man[1] if man else None)


# ---------------------------------------------------------------- 3b. null tests
def outcome_side(cfg: dict, pairs: list[dict], ledger_path: Path, head: str) -> dict:
    """The outcome-side spec 4.7 rows (seeded mock runs, label shuffle, null pairs, baselines,
    ledger tamper), run by lens_engine.stage9.nulls on synthetic data and this ledger only."""
    from lens_engine.stage9 import nulls
    return nulls.outcome_side(cfg, pairs, ledger_path, head)


def null_gate(cfg: dict, d: Data, ledger_path: Path, head: str) -> dict:
    """Spec 4.7. Prediction-side rows from the sealed manifest (only those names), outcome-side
    rows run now on the verified ledger. Returns {"null_tests", "failed"}; a missing row fails."""
    if d.manifest is None:
        raise Refused(f"no sealed predictions manifest ({MANIFEST_REF})")
    pre = d.manifest.get("null_tests")
    if not isinstance(pre, dict):
        raise Refused("the manifest holds no prediction-side null tests")
    got = {k: pre[k] for k in PREDICTION_SIDE_NULLS if k in pre}
    got.update(outcome_side(cfg, d.pairs, Path(ledger_path), head))
    nt = {k: got.get(k, {"pass": False, "why": "not run"}) for k in NULL_TESTS}
    return {"null_tests": nt, "failed": [k for k, v in nt.items() if v.get("pass") is not True]}


# ---------------------------------------------------------------- statistics
def _ci(d):
    return [d["ci95"][0], d["ci95"][1]]


def _passes(rule: str, point: float, ci_lo: float, bar: float) -> bool:
    return bool((point if rule == "point" else ci_lo) >= bar)


def normalised_lift(hits, chance) -> float:
    c = float(np.mean(chance))
    return float((np.mean(hits) - c) / (1 - c))


TOL = 1e-9  # grid thresholds such as 0.49 are not decided by float error at the boundary
T98_GRID = np.round(np.arange(0.0, 0.495, 0.01), 2)  # 0.00 .. 0.49


def called(p, t: float) -> np.ndarray:
    """The can't-tell rule: call when |p - 0.5| >= t (with tolerance). t >= 0.5 never calls."""
    p = np.asarray(p, float)
    if t >= 0.5:
        return np.zeros(p.shape, bool)
    return np.abs(p - 0.5) >= t - TOL


def selective(y, p, t: float) -> tuple[float, float]:
    """(selective accuracy, coverage) of the rule 'call when |p - 0.5| >= t' on decided pairs."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = called(p, t)
    acc = metrics.hit_rate(y[m], p[m]) if m.any() else float("nan")
    return acc, float(m.mean()) if len(m) else float("nan")


def fit_t98(y, p, grid=T98_GRID, min_calls: int = 50, target: float = 0.98) -> dict:
    """Rule 4b: the smallest grid t such that at t and at every larger grid t with at least
    `min_calls` calls, selective accuracy >= target. t itself must have >= min_calls calls.
    Returns threshold 0.5 (never call) if no grid t qualifies."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    grid = np.sort(np.asarray(grid, float))
    rows = []
    for t in grid:
        m = called(p, t)
        n = int(m.sum())
        rows.append((float(t), n, metrics.hit_rate(y[m], p[m]) if n else float("nan")))
    chosen = 0.5
    ok_above = True  # every larger grid t with >= min_calls calls meets the target
    for t, n, acc in reversed(rows):
        if n >= min_calls:
            ok_above = ok_above and acc >= target
            if ok_above:
                chosen = t
        if not ok_above:
            break
    return {"threshold": chosen, "min_calls": min_calls, "target": target,
            "path": [{"t": t, "n_called": n, "selective_accuracy": a} for t, n, a in rows]}


def check_t98(cfg: dict, root: Path) -> dict:
    """Re-hash the frozen fit file (non-holdout out-of-fold decided predictions) and refit t98
    for full (p) and base (p_text). Refuses if the hash or either fitted value differs."""
    c = cfg["c98"]
    fp = Path(c["fit"]["path"])
    fp = fp if fp.is_absolute() else root / fp
    if not fp.exists():
        raise Refused(f"c98 fit file not found: {fp}")
    raw = fp.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != c["fit"]["sha256"]:
        raise Refused(f"c98 fit file sha256 {got} differs from the frozen {c['fit']['sha256']}")
    fit = json.loads(raw)
    y = np.asarray(fit["y"], float)
    if not len(y) or not np.isin(y, (0, 1)).all():
        raise Refused("c98 fit file: y must be non-empty and in (0, 1) (decided pairs only)")
    out = {}
    for arm, key in (("full", "p"), ("base", "p_text")):
        r = fit_t98(y, fit[key], min_calls=c["min_calls"], target=c["target_accuracy"])
        frozen = c["fit"][f"threshold_{arm}"]
        if abs(r["threshold"] - frozen) > TOL:
            raise Refused(f"c98 t98 for {arm}: refit gives {r['threshold']}, config says {frozen}")
        out[arm] = r["threshold"]
    return {"fit_sha256": got, "n_fit": int(len(y)), **{f"t98_{k}": v for k, v in out.items()}}


def share_of_calls_on_nulls(coverage: float, null_call_rate: float, base_rate: float) -> float:
    """Of all calls on a decided+null mixture with `base_rate` decided, the share on nulls."""
    on_null = (1 - base_rate) * null_call_rate
    den = on_null + base_rate * coverage
    return float(on_null / den) if den > 0 else float("nan")


def mcnemar_one_sided(lens_hit, base_hit) -> dict:
    """Exact one-sided McNemar: H1 Lens right more often than the baseline on discordant pairs."""
    from scipy import stats
    lens_hit, base_hit = np.asarray(lens_hit, bool), np.asarray(base_hit, bool)
    b = int((lens_hit & ~base_hit).sum())
    c = int((~lens_hit & base_hit).sum())
    pv = float(stats.binom.sf(b - 1, b + c, 0.5)) if b + c else 1.0
    return {"b": b, "c": c, "p": pv}


def later_won(rows: list[dict]):
    """Per decided row, did the later (challenger) arm win? None unless every row carries a
    sealed bool b_is_later (then slot A is taken as the control)."""
    if not rows or not all(isinstance(r.get("b_is_later"), bool) for r in rows):
        return None
    return np.array([(r["y"] == 1) == r["b_is_later"] for r in rows], bool)


def running_base_rate_hits(lw) -> np.ndarray:
    """Usual-winner rule 3 (ruling 2026-10-14, as run_8_6.running_base_rate_hits), in the given
    order: pick the side (earlier or later arm) that won more of the EARLIER pairs; the earlier
    arm when tied or with no history."""
    hits = np.zeros(len(lw), bool)
    nl = ne = 0
    for j, w in enumerate(lw):
        hits[j] = (nl > ne) == bool(w)
        nl += int(w)
        ne += 1 - int(w)
    return hits


NAIVE_ORDER = ("running_base_rate", "always_control", "always_challenger")  # grade.py tie order


def _hits(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return np.where(p == 0.5, False, (p > 0.5) == (y == 1))


# ---------------------------------------------------------------- 4. endpoints
def endpoints(d: Data, cfg: dict) -> dict:
    B = cfg["bootstrap"]
    nb, seed = B["n_boot"], B["seed"]
    out: dict[str, dict] = {}
    dec = [r for r in d.pairs if r["status"] == "decided"]
    if not dec:
        raise Refused("no decided pairs joined")
    cl = np.array([r["test_id"] for r in dec])
    y = np.array([r["y"] for r in dec], float)
    p = np.array([r["p"] for r in dec])
    pt = np.array([r["p_text"] for r in dec])

    # P: best-of-k normalised lift
    if not d.arms:
        raise Refused("no arm records joined: primary endpoint cannot be computed")
    tid, hits, chance = metrics.best_of_k_hits([a["test_id"] for a in d.arms],
                                               [a["score"] for a in d.arms],
                                               [a["is_best"] for a in d.arms])
    L = metrics.cluster_bootstrap(normalised_lift, tid, hits, chance, n_boot=nb, seed=seed)
    pc = cfg["primary"]
    out["P"] = {"name": "best-of-k normalised lift L", "point": L["point"], "ci95": _ci(L),
                "n_tests": int(len(tid)), "chance": float(chance.mean()),
                "accuracy": float(hits.mean()), "bar": pc["L_bar"], "pass_rule": pc["pass_rule"],
                "pass": _passes(pc["pass_rule"], L["point"], L["ci95"][0], pc["L_bar"]),
                "parity_with_lola": _passes(pc["pass_rule"], L["point"], L["ci95"][0],
                                            pc["parity_bar"])}

    # S1: learner beats each leakage / heuristic baseline (paired hit-rate difference)
    s1 = {}
    for name in S1_BASELINES:
        if not all(name in r["baselines"] for r in dec):
            s1[name] = {"pass": False, "why": f"baseline {name} missing on some decided pairs"}
            continue
        pb = np.array([r["baselines"][name] for r in dec], float)
        diff = metrics.cluster_bootstrap(
            lambda a, b, c: metrics.hit_rate(a, b) - metrics.hit_rate(a, c),
            cl, y, pt, pb, n_boot=nb, seed=seed)
        s1[name] = {"hit_rate_diff": diff["point"], "ci95": _ci(diff), "pass": diff["ci95"][0] > 0}
    out["S1"] = {"name": "learner beats baselines", "baselines": s1,
                 "pass": all(v["pass"] for v in s1.values())}

    # S2: panel gain in nats per decided pair
    gain = metrics.cluster_bootstrap(
        lambda a, b, c: metrics.log_loss(a, b) - metrics.log_loss(a, c), cl, y, pt, p,
        n_boot=nb, seed=seed)
    verdict = decision.r0_verdict(gain["ci95"][0], gain["ci95"][1], cfg["s2"]["margin_nats"])
    if (cfg.get("model") or {}).get("frozen_design") == "STACK_no_describe":
        # the stack gate dropped describe (package 2.2): p is p_text, so there is no panel gain to
        # test. S2 is skipped and does not stop the hierarchy.
        out["S2"] = {"name": "panel gain log-loss(text) - log-loss(text+describe)",
                     "verdict": "not tested: describe dropped by the stack gate",
                     "skipped": True, "pass": None}
        verdict = None
    if verdict is not None:
        out["S2"] = {"name": "panel gain log-loss(text) - log-loss(text+describe)",
                 "point": gain["point"], "ci95": _ci(gain), "verdict": verdict,
                 "pass": verdict == "KEEP", "label": "provisional until 8.7 has 100+ post-cutoff "
                 "decided pairs"}

    # S3: calibration gate in fixed order
    s3c = cfg["s3"]
    sl = metrics.cluster_bootstrap(lambda a, b: metrics.calibration_slope_intercept(a, b)[0],
                                   cl, y, p, n_boot=nb, seed=seed)
    it = metrics.cluster_bootstrap(lambda a, b: metrics.calibration_slope_intercept(a, b)[1],
                                   cl, y, p, n_boot=nb, seed=seed)
    _, sp = metrics.spiegelhalter_z(y, p)
    # spec 4.5: the debiased ECE with its bootstrap CI and n, never below ece_min_n
    ece = (metrics.cluster_bootstrap(decision.debiased_ece, cl, y, p, n_boot=nb, seed=seed)
           if len(y) >= s3c["ece_min_n"] else None)
    g1 = bool(s3c["slope_lo"] <= sl["ci95"][0] and sl["ci95"][1] <= s3c["slope_hi"])
    g2 = bool(it["ci95"][0] <= 0 <= it["ci95"][1])
    g3 = bool(sp >= 0.05)
    out["S3"] = {"name": "calibration", "slope": sl["point"], "slope_ci95": _ci(sl),
                 "intercept": it["point"], "intercept_ci95": _ci(it), "spiegelhalter_p": sp,
                 "slope_inside": g1, "intercept_contains_0": g2, "spiegelhalter_ok": g3,
                 "debiased_ece": ece["point"] if ece else None,
                 "debiased_ece_ci95": _ci(ece) if ece else None, "n": int(len(y)),
                 "pass": g1 and g2 and g3}

    # S4 and C98 share the null / identical pairs
    base_rate = cfg["s4"]["decided_base_rate"]

    def can_tell(t: float, key: str = "p") -> dict:
        pp = p if key == "p" else pt
        nulls = np.array([r[key] for r in d.pairs if r["status"] == "null"])
        ident = np.array([r[key] for r in d.pairs if r["status"] == "identical"])
        acc = metrics.cluster_bootstrap(lambda a, b: selective(a, b, t)[0], cl, y, pp,
                                        n_boot=nb, seed=seed)
        cov = metrics.cluster_bootstrap(lambda a, b: selective(a, b, t)[1], cl, y, pp,
                                        n_boot=nb, seed=seed)
        k_null = int(called(nulls, t).sum())
        null_rate = k_null / len(nulls) if len(nulls) else float("nan")
        k_id = int(called(ident, t).sum())
        return {"threshold": t,
                "selective_accuracy": acc["point"], "selective_accuracy_ci95": _ci(acc),
                "coverage": cov["point"], "coverage_ci95": _ci(cov),
                "n_decided": int(len(y)), "n_called": int(called(pp, t).sum()),
                "null_call_rate": null_rate,
                "null_call_ci95": list(metrics.wilson(k_null, len(nulls))),
                "n_null": int(len(nulls)),
                "identical_ahead_rate": k_id / len(ident) if len(ident) else float("nan"),
                "identical_ahead_ci95": list(metrics.wilson(k_id, len(ident))),
                "n_identical": int(len(ident)),
                "share_of_calls_on_nulls_at_base_rate": share_of_calls_on_nulls(
                    cov["point"], null_rate, base_rate)}

    s4c = cfg["s4"]
    s4 = can_tell(s4c["threshold"])
    # "under 5%" (Emily's decision 5, 2026-10-20): strictly below null_call_max
    s4_ok = bool(s4["n_null"] and s4["null_call_rate"] < s4c["null_call_max"]
                 and s4["n_identical"]
                 and s4["identical_ahead_rate"] <= s4c["identical_ahead_max"])
    out["S4"] = {"name": "can't-tell rule", **s4, "pass": s4_ok}

    c = cfg["c98"]
    full = can_tell(c["fit"]["threshold_full"], "p")
    base = can_tell(c["fit"]["threshold_base"], "p_text")
    c98_ok = (np.isfinite(full["selective_accuracy"]) and _passes(
        c["pass_rule"], full["selective_accuracy"], full["selective_accuracy_ci95"][0],
        c["target_accuracy"]))
    out["C98"] = {"name": "accuracy when confident (98% rule, 4b)", "full": full, "base": base,
                  "target_accuracy": c["target_accuracy"], "pass_rule": c["pass_rule"],
                  "gated_on": "full", "source": c["source"], "pass": bool(c98_ok)}

    # S5: decided-pair accuracy vs always-control (the earlier arm)
    acc = metrics.cluster_bootstrap(metrics.hit_rate, cl, y, p, n_boot=nb, seed=seed)
    kap = metrics.cluster_bootstrap(metrics.cohen_kappa, cl, y, p, n_boot=nb, seed=seed)
    lw = later_won(dec)
    out["S5"] = {"name": "decided-pair accuracy", "accuracy": acc["point"],
                 "accuracy_ci95": _ci(acc),
                 "always_control": float(np.mean(~lw) if lw is not None else np.mean(y == 0)),
                 "always_control_rule": ("earlier arm of the test" if lw is not None
                                         else "slot A (b_is_later not sealed)"),
                 "kappa": kap["point"], "kappa_ci95": _ci(kap),
                 "target": cfg["s5"]["target_accuracy"],
                 "pass": acc["point"] >= cfg["s5"]["target_accuracy"]}

    # S6: letter-style claim, customer-v1 looks only, on called decided pairs in seal order
    out["S6"] = edge_test(dec, cfg)

    # extra metrics (section 5.5): after the hierarchy, never gated
    out["extra"] = extra_metrics(cl, y, p, cfg)

    # Report only: familiarity
    fam = [(r["familiarity"], r) for r in dec if r["familiarity"] is not None]
    if fam:
        f = np.array([v for v, _ in fam], float)
        h = _hits([r["y"] for _, r in fam], [r["p"] for _, r in fam]).astype(float)
        slope = float(np.polyfit(f, h, 1)[0]) if np.ptp(f) > 0 else float("nan")
        below = f < np.median(f)
        out["familiarity"] = {"slope_hit_on_familiarity": slope, "n": int(len(f)),
                              "accuracy_below_median": float(h[below].mean()) if below.any()
                              else float("nan"), "gated": False}
    return out


def frontier_endpoint(arms: list[dict], cfg: dict) -> dict:
    """F1 (package 5.4, Emily's decision 2): per frontier arm, paired best-of-k accuracy Lens minus
    the arm on the same holdout tests (tests where every arm carries that arm's score), cluster
    bootstrap by test id with the frozen n_boot and seed. 'Lens beats <arm>' only if the 95% CI
    lower bound is above 0. Each arm's accuracy, L and chance line, and its recognition-probe
    rates (share of probe tests it claimed to recognise; share where the arm it named won) are
    printed beside it. After the hierarchy; provisional like every Upworthy number."""
    B = cfg["bootstrap"]
    names = sorted((cfg.get("frontier_arms") or {}).keys() & {k for a in arms for k in a["frontier"]})
    out = {"label": "provisional; after the hierarchy, never gated", "arms": {}}
    for name in names:
        by: dict[str, list[dict]] = {}
        for a in arms:
            by.setdefault(a["test_id"], []).append(a)
        tests = sorted(t for t, g in by.items() if all(name in a["frontier"] for a in g))
        if not tests:
            continue
        rows = [a for t in tests for a in by[t]]
        tid = [a["test_id"] for a in rows]
        best = [a["is_best"] for a in rows]
        t1, h_lens, chance = metrics.best_of_k_hits(tid, [a["score"] for a in rows], best)
        t2, h_arm, _ = metrics.best_of_k_hits(tid, [a["frontier"][name] for a in rows], best)
        assert list(t1) == list(t2)
        d = metrics.cluster_bootstrap(lambda a, b: float(np.mean(a - b)), t1, h_lens, h_arm,
                                      n_boot=B["n_boot"], seed=B["seed"])
        probe = {}
        for t, g in by.items():
            named = [a for a in g if name in a["frontier_probe"]]
            if named:
                pick = [a for a in named if a["frontier_probe"][name]]
                probe[t] = None if not pick else bool(pick[0]["is_best"])
        rec = [v for v in probe.values() if v is not None]
        out["arms"][name] = {
            "n_tests": len(tests), "lens_accuracy": float(h_lens.mean()),
            "arm_accuracy": float(h_arm.mean()), "chance": float(chance.mean()),
            "arm_L": normalised_lift(h_arm, chance), "lens_minus_arm": d["point"], "ci95": _ci(d),
            "lens_beats_arm": bool(d["ci95"][0] > 0),
            "recognition_probe": {"n_probe_tests": len(probe),
                                  "recognised_share": (len(rec) / len(probe)) if probe else None,
                                  "named_arm_won_share": (sum(rec) / len(rec)) if rec else None}}
    return out


def top_coverage(y, p, coverage: float):
    """The ceil(coverage x n) most confident decided pairs (|p - 0.5|, stable order)."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    n = int(np.ceil(coverage * len(p)))
    idx = np.argsort(-np.abs(p - 0.5), kind="mergesort")[:n]
    return y[idx], p[idx]


def kendall_tau_b(x, h) -> float:
    """Kendall tau-b between confidence x and the 0/1 hit h (ties handled), O(n log n) via scipy."""
    from scipy import stats
    if np.ptp(x) == 0 or np.ptp(h) == 0:
        return float("nan")
    return float(stats.kendalltau(x, h).statistic)


def auroc(score, label) -> float:
    """P(score of a correct call > score of a wrong call), ties half (Mann-Whitney)."""
    from scipy import stats
    s, lab = np.asarray(score, float), np.asarray(label, bool)
    n1, n0 = int(lab.sum()), int((~lab).sum())
    if not n1 or not n0:
        return float("nan")
    r = stats.rankdata(s)
    return float((r[lab].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def extra_metrics(cl, y, p, cfg: dict) -> dict:
    """Section 5.5 of the package: kappa at matched coverage, reliability curve + monotonicity
    test, confidence AUROC and ECE. All on decided pairs, cluster bootstrap by test id with the
    frozen n_boot and seed. Never gated, never part of the hierarchy."""
    B, ex = cfg["bootstrap"], cfg["extra"]
    nb, seed = B["n_boot"], B["seed"]
    km = ex["kappa_matched"]
    kap = metrics.cluster_bootstrap(lambda a, b: metrics.cohen_kappa(*top_coverage(a, b, km["coverage"])),
                                    cl, y, p, n_boot=nb, seed=seed)
    out = {"kappa_matched_coverage": {
        "coverage": km["coverage"], "kappa": kap["point"], "ci95": _ci(kap),
        "n_called": int(np.ceil(km["coverage"] * len(p))), "external_kappa": km["external_kappa"],
        "above_external": bool(kap["ci95"][0] > km["external_kappa"]),
        "rule": "Lens kappa is said to exceed the external figure only if its 95% CI lower bound "
                "is above it; the external figure is another vendor's data set, never placed in "
                "the same row as an Upworthy number"}}
    conf = np.abs(p - 0.5)
    side = p != 0.5
    hit = _hits(y, p).astype(float)
    nbins = ex["reliability"]["n_bins"]
    order = np.argsort(conf[side], kind="mergesort")
    bins = []
    for chunk in np.array_split(order, nbins):
        if len(chunk):
            c = 0.5 + conf[side][chunk]
            bins.append({"n": int(len(chunk)), "mean_confidence": float(c.mean()),
                         "accuracy": float(hit[side][chunk].mean())})
    tau = metrics.cluster_bootstrap(kendall_tau_b, cl[side], conf[side], hit[side], n_boot=nb, seed=seed)
    out["reliability"] = {"bins": bins, "monotonicity_kendall_tau": tau["point"],
                          "monotonicity_ci95": _ci(tau), "monotone": bool(tau["ci95"][0] > 0),
                          "rule": "monotone if the cluster-bootstrap 95% CI of Kendall tau-b between "
                                  "|p - 0.5| and the hit is above 0"}
    au = metrics.cluster_bootstrap(lambda a, b: auroc(a, b), cl[side], conf[side], hit[side].astype(bool),
                                   n_boot=nb, seed=seed)
    out["confidence_auroc"] = {"auroc": au["point"], "ci95": _ci(au), "label": "descriptive"}
    min_n = cfg["s3"]["ece_min_n"]
    if len(y) >= min_n:
        e = metrics.cluster_bootstrap(decision.debiased_ece, cl, y, p, n_boot=nb, seed=seed)
        out["ece"] = {"debiased_ece": e["point"], "ci95": _ci(e), "n": int(len(y)), "label": "descriptive"}
    else:
        out["ece"] = {"withheld": f"n = {len(y)} decided pairs < {min_n}", "label": "descriptive"}
    return out


def edge_test(dec: list[dict], cfg: dict) -> dict:
    s6 = cfg["s6"]
    t = cfg["s4"]["threshold"]
    calls = sorted((r for r in dec if called([r["p"]], t)[0]), key=lambda r: r["seq"])
    lw_all = later_won(calls)
    rbr_all = running_base_rate_hits(lw_all) if lw_all is not None else None
    looks, claim = [], None
    for n, alpha in zip(s6["checkpoints"], s6["alpha_per_look"]):
        if len(calls) < n:
            looks.append({"n": n, "reached": False})
            continue
        sub = calls[:n]
        y = np.array([r["y"] for r in sub], float)
        lens = _hits(y, [r["p"] for r in sub])
        if lw_all is not None:
            lw = lw_all[:n]
            naive = {"always_control": ~lw, "always_challenger": lw}
        else:
            naive = {"always_control": y == 0, "always_challenger": y == 1}
        if all("running_base_rate" in r["baselines"] for r in sub):
            naive["running_base_rate"] = _hits(
                y, [r["baselines"]["running_base_rate"] for r in sub])
        elif lw_all is not None:
            naive["running_base_rate"] = rbr_all[:n]
        best = max(naive, key=lambda k: (naive[k].mean(), -NAIVE_ORDER.index(k)))
        m = mcnemar_one_sided(lens, naive[best])
        ok = m["p"] <= alpha
        looks.append({"n": n, "reached": True, "strongest_naive": best, **m, "alpha": alpha,
                      "edge_shown": ok})
        if ok and claim is None:
            claim = n
            break  # the first passing look ends the sequential test
    return {"name": "letter-style edge test", "plan_id": s6["plan_id"], "n_called": len(calls),
            "looks": looks, "claimed_at": claim, "pass": claim is not None}


def apply_hierarchy(res: dict) -> dict:
    """Fixed order: a row is gated only if every earlier row passed."""
    stopped = None
    for key in ORDER:
        row = res[key]
        if row.get("skipped"):
            row["gated"] = False
            continue
        if stopped is None:
            row["gated"] = True
            if not row["pass"]:
                stopped = key
        else:
            row["gated"] = False
            row["note"] = f"not gated (hierarchy stopped at {stopped})"
    res["hierarchy_stopped_at"] = stopped
    return res


# ---------------------------------------------------------------- driver
def run(config_path: Path, expected_head: str, root: Path = ROOT,
        package: Path | None = None) -> dict:
    gate = prereg_gate(root, package)
    cfg, sha = load_config(config_path)
    lp = Path(cfg["ledger"]["path"])
    lp = lp if lp.is_absolute() else root / lp
    data = read_ledger(lp, expected_head, sha)
    ng = null_gate(cfg, data, lp, expected_head)
    meta = {"config_id": cfg["config_id"], "config_sha256": sha, "ledger_head": data.head,
            "prereg_checks_passed": gate["n_pass"], "n_pairs": len(data.pairs),
            "n_arms": len(data.arms), "n_predictions_without_outcome": data.n_unjoined,
            "n_boot": cfg["bootstrap"]["n_boot"], "seed": cfg["bootstrap"]["seed"]}
    if ng["failed"]:  # spec 4.7: no endpoint exists until the machinery passes
        return {"withheld": "spec 4.7 null tests failed: " + ", ".join(ng["failed"]),
                "hierarchy_stopped_at": None, "null_tests": ng["null_tests"],
                "null_tests_failed": ng["failed"], "meta": meta}
    t98 = check_t98(cfg, root)
    res = apply_hierarchy(endpoints(data, cfg))
    if any(a["frontier"] for a in data.arms):
        res["F1"] = frontier_endpoint(data.arms, cfg)
    res["null_tests"], res["null_tests_failed"] = ng["null_tests"], []
    res["meta"] = {**meta, "c98_fit": t98}
    lab = cfg.get("label") or {}
    res["label"] = {"label": "provisional", "rule": lab.get("rule", "provisional while the "
                    "post-Opus-cutoff (June 2026) set has fewer than 100 decided pairs"),
                    "post_cutoff_decided_pairs_at_sealing": lab.get("post_cutoff_decided_pairs_at_sealing"),
                    "note": "lifted only by a separate report from the prospective ledger, never by "
                            "editing these results"}
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", type=Path, required=True, help="frozen Stage 9 config JSON")
    ap.add_argument("--expected-head", required=True,
                    help="ledger head hash published after the outcome join")
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this checkout)")
    ap.add_argument("--package", type=Path, default=None, help="prereg package markdown")
    ap.add_argument("--out", type=Path, default=None, help="write results JSON here")
    a = ap.parse_args(argv)
    try:
        res = run(a.config, a.expected_head, a.root, a.package)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=1, allow_nan=True)
    if a.out:
        a.out.write_text(text + "\n")
    print(text)
    if res.get("withheld"):
        print(f"WITHHELD: {res['withheld']}; no endpoint computed", file=sys.stderr)
        return EXIT_WITHHELD
    return 0


if __name__ == "__main__":
    sys.exit(main())
