"""Which per-split Gemma adapters Stage 9 scores with (Emily's ruling 1, 2026-10-21; package 2.1).

The gated 10-split ensemble needs the 10 per-split LoRA adapters to read out holdout pairs. The
8.1c NF4 adapters were never saved (the Modal runs had no Volume; only readouts came back), so the
learner is decided by this tree, fixed before any holdout read:

  1. The bf16 8.1c gate (PR #99, E2E job g81c; amendment
     engine/experiments/8_1c/AMEND_gemma_bf16_gate_e2e.json) runs and saves all 10 adapters to the
     Mac. Its sealed gate_adoption_rule gives adoption_gemma_4_31b_base_bf16.json verdict:
       ADOPT_BF16                -> the Stage 9 learner is the bf16 10-split ensemble from those
                                    adapters (route "bf16")
       NF4_STAYS or NO_ADOPTION  -> step 2
  2. NF4 retrain on E2E: the 10 per-split adapters retrained with the sealed 8.1c recipe and seeds
     (8_1c/PLAN.json + AMEND_gemma_4_31b_base.json, NF4, SEED_LORA = 81200 + split). Accepted
     (route "nf4_retrain") only if EVERY split's tune log-loss (the selected checkpoint, after the
     fitted pair scale, as sealed in results_gemma_4_31b_base.json selection.<s>.LEARNER_selected.
     tune.logloss) replays the sealed NF4 value within the pre-stated tolerance
         |LL_retrain,s - LL_sealed,s| <= 0.011088638914821092   for s = 0 .. 9
     = the sealed noise margin, 2 x pooled seed SD (scaling/amend_gemma_4_31b_base.json
     measured_seed_spread.two_x; per-model seed SD 0.0017-0.0087). Any split outside it: no
     admissible learner, Stage 9 cannot be sealed on this draft (a new draft is written).

Either way the stack is re-fit only as the sealed stack gate procedure specifies (stack_gate/
PLAN.json `stacker`, the same code, on the new readouts) and the frozen config pins the adapter
sha256 list (model.adapters.sha256, 10 entries in split order).
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

N_SPLITS = 10
SEED_LORA = 81200
NOISE_MARGIN = 0.011088638914821092
# results_gemma_4_31b_base.json (sha256 5b864276...b332a) selection.<s>.LEARNER_selected.tune.logloss
NF4_SEALED_TUNE_LL = (0.2243362531676933, 0.2064756540311527, 0.22838976161580388,
                      0.2307657355974872, 0.24863472794010957, 0.20828817951757767,
                      0.24317801603556236, 0.21295950892117105, 0.2130896013504211,
                      0.2223345365545513)
NF4_RESULTS_SHA256 = "5b86427602fee3ebd1f52443e1c4d8679d1c67ef1797c6507bf482a4795b332a"
BF16_VERDICTS = ("ADOPT_BF16", "NF4_STAYS", "NO_ADOPTION")
ROUTES = ("bf16", "nf4_retrain")
_HEX = re.compile(r"[0-9a-f]{64}")


class LearnerError(RuntimeError):
    pass


def _check_shas(shas, what: str) -> list[str]:
    shas = list(shas or [])
    if len(shas) != N_SPLITS or not all(isinstance(s, str) and _HEX.fullmatch(s) for s in shas):
        raise LearnerError(f"{what}: need {N_SPLITS} adapter sha256 values in split order")
    if len(set(shas)) != N_SPLITS:
        raise LearnerError(f"{what}: adapter sha256 values must be distinct")
    return shas


def replay_check(tune_ll, sealed=NF4_SEALED_TUNE_LL, tol: float = NOISE_MARGIN) -> dict:
    """Per-split |LL_retrain - LL_sealed| <= tol on all 10 splits."""
    ll = [float(x) for x in tune_ll]
    if len(ll) != N_SPLITS or not all(math.isfinite(x) for x in ll):
        raise LearnerError(f"need {N_SPLITS} finite per-split tune log-losses")
    diffs = [a - b for a, b in zip(ll, sealed)]
    bad = [s for s, d in enumerate(diffs) if abs(d) > tol]
    return {"pass": not bad, "tolerance": tol, "diffs": diffs, "max_abs_diff": max(map(abs, diffs)),
            "splits_outside": bad}


def decide(bf16_verdict: str | None, bf16_adapters=None, nf4_retrain: dict | None = None) -> dict:
    """The ruling-1 tree. nf4_retrain: {"tune_logloss": [10], "adapters": [10 sha256],
    "seeds": [81200 + s]}. Returns {"route": "bf16" | "nf4_retrain" | None, "status", ...}."""
    if bf16_verdict is None:
        return {"route": None, "status": "PENDING: the bf16 8.1c gate has not given a verdict"}
    if bf16_verdict not in BF16_VERDICTS:
        raise LearnerError(f"unknown bf16 verdict {bf16_verdict!r}")
    if bf16_verdict == "ADOPT_BF16":
        return {"route": "bf16", "status": "ADOPTED", "adapters": _check_shas(bf16_adapters, "bf16")}
    if nf4_retrain is None:
        return {"route": None, "status": f"PENDING: bf16 verdict {bf16_verdict}; the NF4 retrain "
                                         "(sealed 8.1c recipe and seeds, E2E) has not run"}
    seeds = list(nf4_retrain.get("seeds") or [])
    if seeds != [SEED_LORA + s for s in range(N_SPLITS)]:
        raise LearnerError("the NF4 retrain must use the sealed seeds 81200 + split")
    rc = replay_check(nf4_retrain["tune_logloss"])
    if not rc["pass"]:
        return {"route": None, "status": "NO ADMISSIBLE LEARNER: the NF4 retrain does not replay the "
                                         f"sealed tune log-loss on splits {rc['splits_outside']}",
                "replay": rc}
    return {"route": "nf4_retrain", "status": "ACCEPTED", "replay": rc,
            "adapters": _check_shas(nf4_retrain.get("adapters"), "nf4_retrain")}


def adapter_sha256(path: Path) -> str:
    """sha256 of one saved adapter: a single file, or a directory hashed as the sorted
    (relative path, file sha256) list so the pin does not depend on the file system."""
    p = Path(path)
    if p.is_file():
        return hashlib.sha256(p.read_bytes()).hexdigest()
    if not p.is_dir():
        raise LearnerError(f"adapter {p.name} does not exist")
    h = hashlib.sha256()
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        h.update(f.relative_to(p).as_posix().encode() + b"\x1f"
                 + hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"\x1e")
    return h.hexdigest()


def check_adapters(paths, pinned) -> None:
    """Every adapter on disk must equal its pin in model.adapters.sha256 (split order)."""
    pinned = _check_shas(pinned, "model.adapters.sha256")
    got = [adapter_sha256(p) for p in paths]
    bad = [s for s, (a, b) in enumerate(zip(got, pinned)) if a != b]
    if len(got) != N_SPLITS or bad:
        raise LearnerError(f"adapters differ from the frozen config's pins on splits {bad}")
