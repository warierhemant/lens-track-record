"""The Stage 9 frozen config: template, validation, hashing.

One JSON file is both the pre-registration the runner follows and the config that
engine/scripts/stage9_analysis.py reads. Its exact bytes are hashed; the hash is sealed as the
single `stage9:FROZEN` entry, the first entry of a fresh ledger, before any prediction
(runner.seal_config). A sealed config is never edited; an amendment is a new file with a new
config_id and a new ledger.

The analysis sections (`ledger`, `bootstrap`, `primary`, `s2` ... `s6`) are exactly the shape
stage9_analysis.REQUIRED checks, carrying the bars of PREREG_PACKAGE_DRAFT.md section 5. The
runner sections add what the analysis does not need: the datasets, the frozen model, the four
S1 baseline scales (position, length, always_newer, familiarity, recognition; web_presence was
dropped 2026-10-20, package draft change 5.2), and
the spec 4.7 null tests.

Datasets (every dataset in one config is pooled by the analysis, which has no notion of a
dataset, so a config holds only sets that may be pooled):
  upworthy_sealed_holdout  the 2,110-test holdout drawn in 8.0, read once through
                           lens_engine.stage9.access.holdout_pairs. The Stage 9 headline.
  pair_files               another public outcome set. Prospective: every outcome must close
                           after the config is sealed. A TEST-ONLY set runs only in its own
                           config with `internal_benchmark: true` and is never a public claim.
  synthetic                tests and dry runs only; such a config can never be published.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from lens_engine import paths
from lens_engine.stage9.analysis import S9

SCHEMA = "lens.stage9.config/1"
FROZEN_REF = S9.FROZEN_REF
SOURCES = ("upworthy_sealed_holdout", "pair_files", "synthetic")
LICENCES = ("TRAIN-OK", "TEST-ONLY", "SYNTHETIC")
S1_BASELINES = tuple(S9.S1_BASELINES)
ROOT = paths.PROJECT_ROOT
TODO = "TODO"

# spec 4.7, every row (all must pass before any accuracy number is shown)
NULL_TESTS = {
    "mock_harness": {"n_runs": 5, "n_pairs": 1000, "min_covering": 4},
    "label_shuffle": {"n_shuffles": 1000, "ks_p_min": 0.01},
    "identical_pairs": {"n": 200, "ahead_max": 0.05},
    "paraphrase_pairs": {"n": 200, "ahead_max": 0.10},
    "null_pairs": {"min_n": 600},
    "scrambled_instruction": {"n": 200, "follow_min": 0.80},
    "baselines_full_system": {},
    "stability": {"n": 300, "same_pick_min": 0.90},
    "ledger_tamper": {},
}


class ConfigError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(root: Path, p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else Path(root) / p


# The arm-set rule (precollect.ARM_SET_RULE, package 2.1b), recorded in the holdout dataset entry.
ARM_SET_RULE_NOTE = ("lens.stage9.arm_set/1 (precollect.ARM_SET_RULE): arms keyed by (test id, text "
                     "sha256); load_packages arms re-keyed to the text-only pre-collection ids at the "
                     "read; pre-collection arms and tests the read lacks are excluded by rule and "
                     "counted in stage9:PREDICTIONS arm_set; an unknown outcome arm refuses")


def code_sha256() -> str:
    """Hash of the code that turns the config into numbers: this package and the analysis."""
    here = Path(__file__).resolve().parent
    files = sorted(here.glob("*.py")) + [Path(S9.__file__)]
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode() + b"\x1f" + f.read_bytes() + b"\x1e")
    return h.hexdigest()


# ------------------------------------------------------------------ registry candidates
_STATUS = re.compile(r"\b(TRAIN[- ]OK|TEST[- ]ONLY)\b", re.IGNORECASE)


def registry_candidates(path: Path) -> list[dict]:
    """Rows of data/REGISTRY.md (a markdown table) marked TRAIN-OK or TEST-ONLY.

    Only the dataset name (first cell) and the licence verdict are taken; nothing is opened.
    A missing registry gives no candidates (cloud sessions have no data/)."""
    p = Path(path)
    if not p.exists():
        return []
    out, seen = [], set()
    for line in p.read_text().splitlines():
        if not line.lstrip().startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        m = _STATUS.search(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        name = next((c for c in cells if c and not c.isdigit()), "")
        if not name or name.lower() in ("dataset", "name") or name in seen:
            continue
        seen.add(name)
        lic = "TEST-ONLY" if m.group(1).upper().startswith("TEST") else "TRAIN-OK"
        out.append({"name": name, "licence": lic})
    return out


# ------------------------------------------------------------------ template
def template(registry: Path | None = None, today: str | None = None) -> dict:
    """A draft config. Every TODO must be replaced before validate(strict=True) accepts it."""
    today = today or dt.date.today().isoformat()
    cands = registry_candidates(registry) if registry else []
    return {
        "schema": SCHEMA,
        "config_id": "stage9-holdout-v1",
        "written": today,
        "status": "DRAFT: replace every TODO, then `seal-config`. A sealed config is never edited.",
        "internal_benchmark": False,
        "ledger": {"path": "engine/experiments/stage9/ledger.sqlite"},
        "bootstrap": {"n_boot": 2000, "seed": 9000},
        # PREREG_PACKAGE_DRAFT.md section 5, in its order
        "primary": {"L_bar": 0.171, "parity_bar": 0.198, "pass_rule": TODO},
        "s2": {"margin_nats": 0.0075},
        "s3": {"slope_lo": 0.8, "slope_hi": 1.25, "ece_min_n": 1500},
        "s4": {"threshold": TODO, "null_call_max": 0.05, "identical_ahead_max": 0.05,
               "decided_base_rate": 0.248},
        "c98": {"target_accuracy": 0.98, "pass_rule": TODO, "min_calls": 50,
                "source": "R-0 v2 plan dbadebd0 rule 4b (RESUME.md 2026-10-15)",
                "fit": {"path": TODO, "sha256": TODO, "threshold_full": TODO,
                        "threshold_base": TODO}},
        "s5": {"target_accuracy": TODO},
        "s6": {"plan_id": "customer-v1", "checkpoints": [40, 80, 160, 320, 640],
               "alpha_per_look": [0.01] * 5,
               # canonical-JSON SHA-256 of the plan (PREREG_PACKAGE_DRAFT.md 2.4, O7): sealing the
               # config seals customer-v1
               "plan_sha256": "d0884d21345afa5cd11c86044e316c62dc42a0aef2622afe21dcd4ebdce9ffae"},
        # PREREG_PACKAGE_DRAFT.md section 5.5 (Emily's decision 5, 2026-10-20)
        "extra": {"kappa_matched": {"coverage": 0.49, "external_kappa": 0.31,
                                    "source": "Squoosh, arXiv 2608.07517: kappa 0.31 on the 49% "
                                              "its vote gate answers"},
                  "reliability": {"n_bins": 10},
                  "confidence_auroc": {"label": "descriptive"},
                  "ece": {"label": "descriptive", "min_n": "s3.ece_min_n"}},
        # PREREG_PACKAGE_DRAFT.md section 2.3 (Emily's decision 2): head-to-head frontier arms on
        # every holdout test, sealed with the Lens predictions. Runner support is not built yet:
        # `implementation_sha256` stays TODO until it is, so a config cannot seal without it.
        "frontier_arms": {
            "opus_5_5_zero_shot": {
                "model": "claude-opus-5-5", "task": "best-of-k letter pick, both orders (fwd, "
                "rev) per test, scores = mean of the two picks; plus the 300-test recognition probe",
                "prompt_source": "engine/experiments/8_1/frontier_arm.py PROMPT and RECOG",
                "prompt_sha256": "1a50b6346ee8012ab83dcd6a33345d4336f60c060c5af5327132128d5e8fcdbe",
                "recog_sha256": "9a63cc3d5d17996e520b5fd04b447820ba2a45bd669e6a741a3f5ab96058b7d3",
                "max_tokens": 512, "effort": "low", "api": "Batch",
                "expected_usd": 5, "worst_usd": 9},
            "sonnet_5_5_zero_shot": {
                "model": "claude-sonnet-5-5", "task": "as the Opus arm (the 8.1 B7 design, for "
                "continuity with dev G3)",
                "prompt_source": "engine/experiments/8_1/frontier_arm.py PROMPT and RECOG",
                "prompt_sha256": "1a50b6346ee8012ab83dcd6a33345d4336f60c060c5af5327132128d5e8fcdbe",
                "recog_sha256": "9a63cc3d5d17996e520b5fd04b447820ba2a45bd669e6a741a3f5ab96058b7d3",
                "max_tokens": 512, "effort": "low", "api": "Batch",
                "expected_usd": 1, "worst_usd": 5},
            "endpoint": "F1 per arm: paired best-of-k accuracy, Lens minus arm, cluster bootstrap "
                        "by test id (n_boot, seed 9000). 'Lens beats <arm>' only if the 95% CI "
                        "lower bound > 0. Reported after the hierarchy, labelled provisional",
            "dropped": {"sonnet_8x2_panel": "adds nothing to any endpoint (S2 tests describe "
                                            "only); about 90 USD (Emily's decision 2)"},
            "implementation_sha256": TODO},
        # PREREG_PACKAGE_DRAFT.md section 2.7 (Emily's decision 4): never start below the reserve
        "credit": {"reserve_usd": 70, "worst_case_usd": 68,
                   "basis": "READINESS_2026-10-20 section 2: worst case of A (Opus describe, Batch) "
                            "+ B (Opus 5.5 zero-shot) + C (Sonnet 5.5 zero-shot) = 54 + 9 + 5"},
        "label": {"rule": "provisional while the post-Opus-cutoff (June 2026) set has fewer than "
                          "100 decided pairs", "min_post_cutoff_decided_pairs": 100,
                  "post_cutoff_decided_pairs_at_sealing": TODO},
        "model": {"stack_id": TODO, "stack_sha256": TODO, "text_only_stack_id": TODO,
                  "interface": "lens_engine.stage9.models.StackedModel",
                  # Emily's ruling 1 (2026-10-21, learner.py): the per-split adapters Stage 9
                  # reads out with, route bf16 or nf4_retrain, sha256 pinned in split order
                  "adapters": {"route": TODO, "sha256": [TODO] * 10}},
        "baselines": {
            "rule": "P(B wins) = sigmoid(scale * (s_B - s_A)) on a per-arm score; scale fitted "
                    "on non-holdout decided pairs before sealing (as 8.1b H.fit_pair_scale)",
            "length": {"score": "characters of the text", "scale": TODO},
            "position": {"score": "arm order within the test", "scale": TODO},
            "always_newer": {"score": "sign of the arm order gap (newer arm)", "scale": TODO},
            "familiarity": {"score": "mean token log-probability under the open base model",
                            "model": TODO, "scale": TODO,
                            # the real scorer lives outside this repo: pinned here, not by
                            # code_sha256 (review 2026-10-20)
                            "implementation_sha256": TODO},
            # added 2026-10-18 (PREREG_PACKAGE_DRAFT.md section 5 draft change)
            "recognition": {"score": "recognition / membership score of the exact text under "
                                     "the frozen model (models.Recognition)",
                            "model": TODO, "scale": TODO, "implementation_sha256": TODO},
            # web_presence: DROPPED 2026-10-20 (package draft change 5.2, O13): no free licensed
            # pre-cutoff exact-phrase web index. Disclosed in the report; never re-added after
            # sealing.
            "dropped": {"web_presence": "no free, licensed, pre-cutoff exact-phrase web index "
                                        "(PREREG_PACKAGE_DRAFT.md draft change 5.2)"},
        },
        "datasets": [{
            "id": "upworthy_holdout",
            "source": "upworthy_sealed_holdout",
            "licence": "TRAIN-OK",
            "use_case": "headline",
            "sealed_set": "retrospective: the 8.0 sealed holdout, read once through stage9.access",
            "holdout_sha256": TODO,
            "slot_seed": 9001,
            "arm_set_rule": ARM_SET_RULE_NOTE,
        }],
        "null_tests": json.loads(json.dumps(NULL_TESTS)),
        "registry_candidates": [
            {**c, "note": "not in this config: a prospective set runs in its own config and "
                          "ledger" + (" with internal_benchmark true (TEST-ONLY licence)"
                                      if c["licence"] == "TEST-ONLY" else "")}
            for c in cands],
    }


def synthetic(n_tests: int = 300, n_boot: int = 2000, fit: dict | None = None,
              ledger: str = "ledger.sqlite", seed: int = 1, decided_share: float = 0.8,
              null_tests: dict | None = None) -> dict:
    """A complete config over one synthetic dataset (dry runs and tests)."""
    c = template(today="2026-10-18")
    c["config_id"] = "stage9-synthetic-dry-run"
    c["status"] = "SYNTHETIC DRY RUN: never publish"
    c["ledger"]["path"] = ledger
    c["bootstrap"]["n_boot"] = n_boot
    c["primary"]["pass_rule"] = "point"
    c["s4"]["threshold"] = 0.3
    c["c98"]["pass_rule"] = "ci_lower"
    c["c98"]["fit"] = fit or {"path": "c98_fit.json", "sha256": "0" * 64,
                              "threshold_full": 0.5, "threshold_base": 0.5}
    c["s5"]["target_accuracy"] = 0.6
    c["label"]["post_cutoff_decided_pairs_at_sealing"] = 0
    c["frontier_arms"]["implementation_sha256"] = "0" * 64
    c["model"].update(stack_id="mock-stack", stack_sha256="0" * 64,
                      text_only_stack_id="mock-stack-text",
                      adapters={"route": "bf16", "sha256": [f"{i:064x}" for i in range(1, 11)]})
    for name, k in (("length", 0.01), ("position", 0.1), ("always_newer", 0.2),
                    ("familiarity", 1.0), ("recognition", 1.0)):
        c["baselines"][name]["scale"] = k
    for name in ("familiarity", "recognition"):
        c["baselines"][name]["implementation_sha256"] = "0" * 64
    c["baselines"]["familiarity"]["model"] = "mock-familiarity"
    c["baselines"]["recognition"]["model"] = "mock-recognition"
    c["datasets"] = [{"id": "synthetic_headlines", "source": "synthetic", "licence": "SYNTHETIC",
                      "use_case": "headline", "n_tests": n_tests, "seed": seed,
                      "decided_share": decided_share}]
    if null_tests:
        for k, v in null_tests.items():
            c["null_tests"][k].update(v)
    return c


# ------------------------------------------------------------------ validation
def _todos(obj, where="config") -> list[str]:
    if isinstance(obj, dict):
        return [x for k, v in obj.items() for x in _todos(v, f"{where}.{k}")]
    if isinstance(obj, list):
        return [x for i, v in enumerate(obj) for x in _todos(v, f"{where}[{i}]")]
    return [where] if obj == TODO else []


def _num(x, where, lo=None, hi=None):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ConfigError(f"{where} must be a number")
    if (lo is not None and x < lo) or (hi is not None and x > hi):
        raise ConfigError(f"{where} must be in [{lo}, {hi}]")


def validate(cfg: dict, strict: bool = True) -> dict:
    """The runner's sections. strict=True (sealing) also refuses any TODO left; the analysis
    sections are checked by stage9_analysis.load_config in load()."""
    if cfg.get("schema") != SCHEMA:
        raise ConfigError(f"schema must be {SCHEMA}")
    if not isinstance(cfg.get("config_id"), str) or not cfg["config_id"]:
        raise ConfigError("config_id is required")
    if strict:
        left = _todos(cfg)
        if left:
            raise ConfigError("config still has TODO values: " + ", ".join(left[:8]))
    if not isinstance(cfg.get("internal_benchmark"), bool):
        raise ConfigError("internal_benchmark must be true or false")
    ds = cfg.get("datasets")
    if not isinstance(ds, list) or not ds:
        raise ConfigError("datasets must list at least one dataset")
    ids = [d.get("id") for d in ds]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise ConfigError("dataset ids must be unique non-empty strings")
    for d in ds:
        w = f"datasets.{d['id']}"
        if d.get("source") not in SOURCES:
            raise ConfigError(f"{w}.source must be one of {SOURCES}")
        if d.get("licence") not in LICENCES:
            raise ConfigError(f"{w}.licence must be one of {LICENCES}")
        if d["licence"] == "TEST-ONLY" and not cfg["internal_benchmark"]:
            raise ConfigError(f"{w}: a TEST-ONLY dataset runs only in a config with "
                              "internal_benchmark true (it is never a public claim)")
        if (d["source"] == "synthetic") != (d["licence"] == "SYNTHETIC"):
            raise ConfigError(f"{w}: the synthetic source goes with licence SYNTHETIC, and only it")
    if len({d["source"] == "synthetic" for d in ds}) > 1:
        raise ConfigError("a config cannot mix synthetic and real datasets")
    b = cfg.get("baselines", {})
    for name in S1_BASELINES:
        if not isinstance(b.get(name), dict):
            raise ConfigError(f"baselines.{name} is required (S1)")
        if strict:
            _num(b[name].get("scale"), f"baselines.{name}.scale")
    ad = (cfg.get("model") or {}).get("adapters")
    if strict:
        _check_adapters(ad)
    # PREREG_PACKAGE_DRAFT.md 2.7 (Emily's decision 4): every config carries the credit reserve,
    # so the runner's reserve check can never be skipped by leaving the section out
    cr = cfg.get("credit")
    if not isinstance(cr, dict):
        raise ConfigError("credit is required (reserve_usd, worst_case_usd; package 2.7)")
    _num(cr.get("reserve_usd"), "credit.reserve_usd", 0)
    _num(cr.get("worst_case_usd"), "credit.worst_case_usd", 0)
    if cr["reserve_usd"] < cr["worst_case_usd"]:
        raise ConfigError("credit.reserve_usd must be at least credit.worst_case_usd")
    nt = cfg.get("null_tests")
    if not isinstance(nt, dict) or set(nt) != set(NULL_TESTS):
        raise ConfigError(f"null_tests must hold exactly the spec 4.7 rows {sorted(NULL_TESTS)}")
    for name, want in NULL_TESTS.items():
        for k in want:
            _num(nt[name].get(k), f"null_tests.{name}.{k}", 0)
    return cfg


def _check_adapters(ad) -> None:
    """Emily's ruling 1 (2026-10-21): a real config pins the 10 per-split adapters it reads out
    with (learner.py decides the route) before it can be sealed."""
    from lens_engine.stage9 import learner
    if not isinstance(ad, dict) or ad.get("route") not in learner.ROUTES:
        raise ConfigError(f"model.adapters.route must be one of {learner.ROUTES} (learner.decide)")
    try:
        learner._check_shas(ad.get("sha256"), "model.adapters.sha256")
    except learner.LearnerError as e:
        raise ConfigError(str(e)) from None


def is_synthetic(cfg: dict) -> bool:
    return any(d["source"] == "synthetic" for d in cfg["datasets"])


def load(path: Path, strict: bool = True) -> tuple[dict, str]:
    """(config, sha256 of the file's bytes). strict also runs the analysis's own config check,
    so a config the analysis would refuse is never sealed."""
    raw = Path(path).read_bytes()
    try:
        cfg = json.loads(raw)
    except ValueError as e:
        raise ConfigError(f"config is not JSON: {e}") from None
    validate(cfg, strict=strict)
    if strict:
        try:
            S9.load_config(path)
        except S9.Refused as e:
            raise ConfigError(f"stage9_analysis refuses this config: {e}") from None
    return cfg, hashlib.sha256(raw).hexdigest()
