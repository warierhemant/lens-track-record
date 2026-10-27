"""Plain-English Stage 9 report (Markdown) from runner.evaluate's results.

The null tests come first. If any failed, no accuracy number exists at all (spec 4.7: the
runner does not compute the endpoints); the report says which failed and stops. Otherwise each pre-registered endpoint of
stage9_analysis.py follows in its fixed order (P, S1, S2, S3, S4, C98, S5, S6), pass or fail,
every number with its 95% interval, then the report-only familiarity rows, the frontier arms (F1:
each arm's L, chance line and recognition-probe hit rate) and what the result does NOT show. A synthetic run and an internal benchmark are labelled at the top.
"""
from __future__ import annotations

import math

NULL_NAMES = {
    "mock_harness": "A mock that knows nothing scores like chance",
    "label_shuffle": "Shuffled outcomes give no signal",
    "identical_pairs": "Two identical texts are never called",
    "paraphrase_pairs": "Trivial rewordings are almost never called",
    "null_pairs": "False-winner rate on tests with no real difference",
    "scrambled_instruction": "Harness check: the probe follows a plain instruction (which has more "
                             "words?)",
    "baselines_full_system": "The full system beats the position, length, newer-arm, "
                             "familiarity and recognition guesses",
    "stability": "A re-run with new seeds makes the same pick",
    "ledger_tamper": "Every edited, deleted or back-dated ledger entry is caught",
}
ENDPOINT_NAMES = {
    "P": "Lens finds the best headline of a test more often than chance (best-of-k lift)",
    "S1": "The text learner beats the position, length, newer-arm, familiarity and "
          "recognition guesses",
    "S2": "The panel describe call adds to the text learner (log-loss)",
    "S3": "Lens's probabilities mean what they say (calibration)",
    "S4": "The can't-tell rule stays quiet on tests with no real difference",
    "C98": "When Lens is confident, it is right at least 98% of the time",
    "S5": "Lens picks the winner of decided pairs often enough",
    "S6": "Letter-style claim: Lens beats the strongest naive guess (customer-v1 looks)",
}
ORDER = list(ENDPOINT_NAMES)
# The 98% display rule. Emily's ruling of 2026-10-21 (display ruling, after the runbook's dry run
# printed the phrase while C98 had failed): "about 98% when confident" may appear only when C98
# PASSES IN THE ENDPOINT HIERARCHY (its own bar, pass_rule at c98.target_accuracy, and gated: every
# earlier endpoint passed). Ruling 5's thresholds (accuracy >= 0.975, 95% CI lower bound >= 0.96)
# stay as extra conditions on top. Every use of the phrase carries its coverage and its null-pair
# call rate beside it (ruling 5). When C98 fails or is not gated, the report shows the measured
# accuracy with its CI lower bound, its coverage and its null-call rate, and never the phrase.
DISPLAY_98 = {"min_accuracy": 0.975, "min_ci_lower": 0.96}
PHRASE_98 = "About 98% when confident"


def _arm_set_lines(res: dict) -> list[str]:
    """The arm-set rule's counts (precollect.ARM_SET_RULE), sealed in the predictions manifest."""
    out = []
    for ds, n in sorted((res.get("arm_set") or {}).items()):
        out.append(f"- Arm-set rule ({ds}): the text-only pre-collection held {n['n_pre_arms']} arms in "
                   f"{n['n_pre_tests']} tests; the outcome read kept {n['n_outcome_arms']} arms in "
                   f"{n['n_outcome_tests']} tests. {n['n_excluded_arms']} arms "
                   f"({n['n_excluded_arms_in_kept_tests']} inside kept tests) and {n['n_excluded_tests']} "
                   "whole tests are excluded by the rule fixed before the read (an arm whose packages all "
                   "had zero impressions; a test left with fewer than 2 arms); every n above counts the "
                   "kept arms only.")
    return out


def display_98_allowed(c98: dict) -> bool:
    """True only if C98 passed in the hierarchy (pass and gated) AND ruling 5's thresholds hold."""
    if not (c98 and c98.get("pass") is True and c98.get("gated") is True):
        return False
    full = c98.get("full") or {}
    acc = full.get("selective_accuracy")
    lo = (full.get("selective_accuracy_ci95") or [None])[0]
    return bool(_ok(acc) and _ok(lo) and acc >= DISPLAY_98["min_accuracy"]
                and lo >= DISPLAY_98["min_ci_lower"])


def _ok(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def _pct(x, d=1) -> str:
    return f"{100 * x:.{d}f}%" if _ok(x) else "n/a"


def _ci(ci, f=_pct) -> str:
    return f"95% CI {f(ci[0])} to {f(ci[1])}" if ci and all(_ok(v) for v in ci) else "no CI"


def _pts(x) -> str:
    return f"{100 * x:+.1f} pts" if _ok(x) else "n/a"


def _num(x, d=3) -> str:
    return f"{x:.{d}f}" if _ok(x) else "n/a"


def _rule(rule: str) -> str:
    return "the point estimate" if rule == "point" else "the lower end of the 95% CI"


def _null_line(name: str, r: dict) -> str:
    head = f"- **{NULL_NAMES[name]}**: {'PASS' if r['pass'] else 'FAIL'}."
    if "why" in r:
        return head + f" {r['why']}."
    if name == "mock_harness":
        return head + (f" Kappa's 95% CI covered 0 on {r['n_covering']} of {len(r['runs'])} "
                       f"runs (needs {r['bar']}).")
    if name == "label_shuffle":
        return head + (f" {r['n_shuffles']} shuffles of {r['n']} outcomes; uniformity test "
                       f"p = {_num(r['ks_p'])} (needs above {r['bar']}).")
    if name in ("identical_pairs", "paraphrase_pairs"):
        return head + (f" Called {r['ahead']} of {r['n']} ({_pct(r['rate'])}, "
                       f"{_ci(r['wilson95'])}); the bar is {_pct(r['bar'], 0)} or fewer.")
    if name == "null_pairs":
        return head + (f" Called {r['called']} of {r['n']} null pairs ({_pct(r['rate'])}, "
                       f"{_ci(r['wilson95'])}); reported, needs at least {r['min_n']} pairs.")
    if name == "scrambled_instruction":
        # Emily's ruling 2 (2026-10-22): the probe is the deterministic str.split word count of spec
        # 4.7, so this row checks that the sampled pairs reach the probe intact, not a model.
        return head + (f" Followed word count on {r['follow']} of {r['n']} "
                       f"({_pct(r['rate'])}); the bar is {_pct(r['bar'], 0)}. A harness check (probe "
                       f"{r.get('probe') or 'unnamed'}): the Stage 9 probe counts words with str.split "
                       "(spec 4.7), so the row tests that the sampled pairs reach it intact, not a "
                       "model's instruction following.")
    if name == "stability":
        return head + (f" Same pick on {r['same_pick']} of {r['n']} ({_pct(r['rate'])}); "
                       f"the bar is {_pct(r['bar'], 0)}.")
    if name == "ledger_tamper":
        return head + f" {r['n_detected']} of {r['n']} tampered copies caught."
    if name == "baselines_full_system":
        parts = [f"{k} {_pts(v.get('hit_rate_diff'))} ({_ci(v.get('ci95'), _pts)})"
                 if "why" not in v else f"{k}: {v['why']}" for k, v in r["baselines"].items()]
        return head + " Gain over each: " + "; ".join(parts) + "."
    return head


def _verdict(r: dict) -> str:
    v = "PASS" if r["pass"] else "FAIL"
    if not r.get("gated", True):
        v += f" ({r.get('note', 'not gated')}; proves nothing)"
    return v


def _ct(r: dict) -> str:
    return (f"called {r['n_called']} of {r['n_decided']} decided pairs (coverage "
            f"{_pct(r['coverage'])}, {_ci(r['coverage_ci95'])}), right on "
            f"{_pct(r['selective_accuracy'])} ({_ci(r['selective_accuracy_ci95'])}); "
            f"called {_pct(r['null_call_rate'])} of {r['n_null']} null pairs "
            f"({_ci(r['null_call_ci95'])}) and {_pct(r['identical_ahead_rate'])} of "
            f"{r['n_identical']} identical pairs; at the decided base rate "
            f"{_pct(r['share_of_calls_on_nulls_at_base_rate'])} of calls would be on nulls")


def confident_claim(c98: dict) -> str:
    """The one sentence that may carry "about 98% when confident", from the C98 endpoint row
    (stage9_analysis: `full`, `pass`, and `gated` from apply_hierarchy). The phrase appears only
    when display_98_allowed(c98); otherwise the sentence gives the measured accuracy with its 95% CI
    lower bound, the coverage and the null-pair call rate, without the phrase. Never without the
    coverage and the null-pair call rate at the same threshold."""
    c98 = c98 or {}
    full = c98.get("full") or {}
    acc, cov, nul = (full.get(k) for k in ("selective_accuracy", "coverage", "null_call_rate"))
    lo = (full.get("selective_accuracy_ci95") or [None])[0]
    if not all(_ok(x) for x in (acc, lo, cov, nul)):
        return ("No confident-call figure: accuracy when confident, its CI lower bound, coverage or "
                "the null-pair call rate is missing.")
    tail = (f"it calls {_pct(cov)} of decided pairs (coverage) and {_pct(nul)} of null pairs, tests "
            "whose arms truly tie (null-pair call rate).")
    if display_98_allowed(c98):
        return (f"{PHRASE_98}: right on {_pct(acc)} of its calls "
                f"({_ci(full['selective_accuracy_ci95'])}); " + tail)
    why = ("C98 did not pass" if c98.get("pass") is not True else
           "C98 was not gated (the hierarchy stopped earlier)" if c98.get("gated") is not True else
           "accuracy or its CI lower bound is under the display thresholds")
    return (f"Accuracy when confident: right on {_pct(acc)} of its calls, CI lower bound "
            f"{_pct(lo)}; " + tail + f" ({why}, so no rounded claim is made.)")


def _endpoint_line(k: str, r: dict) -> str:
    if r.get("skipped"):
        return f"- **{k}. {ENDPOINT_NAMES[k]}**: {r['verdict']}."
    head = f"- **{k}. {ENDPOINT_NAMES[k]}**: {_verdict(r)}."
    if k == "P":
        return head + (f" Lift L = {_num(r['point'])} ({_ci(r['ci95'], _num)}) on "
                       f"{r['n_tests']} tests; picked the best arm {_pct(r['accuracy'])} of the "
                       f"time where chance is {_pct(r['chance'])}. The bar is L of at least "
                       f"{r['bar']} at "
                       f"{_rule(r['pass_rule'])}; parity with LOLA "
                       f"{'is' if r['parity_with_lola'] else 'is not'} claimed.")
    if k == "S1":
        parts = [f"{n} {_pts(v.get('hit_rate_diff'))} ({_ci(v.get('ci95'), _pts)})"
                 if "why" not in v else f"{n}: {v['why']}" for n, v in r["baselines"].items()]
        return head + " Gain over each: " + "; ".join(parts) + "."
    if k == "S2":
        return head + (f" Gain {_num(r['point'], 4)} nats per pair "
                       f"({_ci(r['ci95'], lambda v: _num(v, 4))}): {r['verdict']}. "
                       f"{r['label'].capitalize()}.")
    if k == "S3":
        ece = (f"Debiased calibration error {_pct(r['debiased_ece'])} "
               f"({_ci(r.get('debiased_ece_ci95'))}, n = {r.get('n')})."
               if r.get("debiased_ece") is not None else
               "No calibration error figure is shown below 1,500 decided pairs.")
        n2 = lambda v: _num(v, 2)  # noqa: E731
        return head + (f" Slope {n2(r['slope'])} ({_ci(r['slope_ci95'], n2)}),"
                       f" inside the bar: {'yes' if r['slope_inside'] else 'no'}; intercept "
                       f"{n2(r['intercept'])} ({_ci(r['intercept_ci95'], n2)}),"
                       f" contains 0: {'yes' if r['intercept_contains_0'] else 'no'}; "
                       f"Spiegelhalter p = {_num(r['spiegelhalter_p'])}. {ece}")
    if k == "S4":
        return head + f" At threshold {_num(r['threshold'], 2)}: {_ct(r)}."
    if k == "C98":
        f, b = r["full"], r["base"]
        return head + (f" Full system at threshold {_num(f['threshold'], 2)}: {_ct(f)}. "
                       f"Text-only at {_num(b['threshold'], 2)}: {_ct(b)}. A pass needs "
                       f"{_rule(r['pass_rule'])} of the full system at "
                       f"{_pct(r['target_accuracy'], 0)} or more.")
    if k == "S5":
        return head + (f" Right on {_pct(r['accuracy'])} of decided pairs "
                       f"({_ci(r['accuracy_ci95'])}); always keeping the control "
                       f"({r.get('always_control_rule', 'slot A')}) gets "
                       f"{_pct(r['always_control'])}; kappa {_num(r['kappa'], 2)} "
                       f"({_ci(r['kappa_ci95'], lambda v: _num(v, 2))}). Target "
                       f"{_pct(r['target'])}.")
    if k == "S6":
        reached = [lk for lk in r["looks"] if lk["reached"]]
        if not reached:
            return head + f" {r['n_called']} calls: no checkpoint of {r['plan_id']} reached."
        last = reached[-1]
        return head + (f" {r['n_called']} calls; last look at {last['n']} against "
                       f"{last['strongest_naive']}: one-sided p = {last['p']:.3g} (needs "
                       f"{last['alpha']} or less)" + (f"; edge shown at {r['claimed_at']}."
                                                     if r["claimed_at"] else "."))
    return head


def frontier_lines(f1: dict) -> list[str]:
    """F1 (package 5.4; runbook step K): one line per frontier arm with its L, its chance line and
    its recognition-probe hit rate beside it, then Lens minus the arm with its 95% CI. After the
    hierarchy, never gated, provisional like every Upworthy number. Empty when F1 is absent."""
    arms = (f1 or {}).get("arms") or {}
    if not arms:
        return []
    out = ["## Frontier arms (F1, after the hierarchy, never gated)", "",
           f"Label: {f1.get('label', 'provisional; after the hierarchy, never gated')}. Each arm "
           "ran zero-shot on the same holdout tests as Lens; \"Lens beats\" an arm only if the "
           "95% CI lower bound of Lens minus the arm is above 0.", ""]
    for name, r in sorted(arms.items()):
        rp = r.get("recognition_probe") or {}
        if rp.get("n_probe_tests"):
            n, share, won = (rp["n_probe_tests"], rp.get("recognised_share"),
                             rp.get("named_arm_won_share"))
            k = round(share * n) if _ok(share) else None
            probe = (f"recognition probe: it claimed to recognise {_pct(share)} of the {n} probe "
                     f"tests ({k} of {n})" if k is not None else
                     f"recognition probe: recognised share missing on {n} probe tests")
            if _ok(won) and k:
                probe += f", and the arm it named won {_pct(won)} of those ({round(won * k)} of {k})"
        else:
            probe = "recognition probe: not run"
        out.append(
            f"- **{name}**: L = {_num(r.get('arm_L'))}; it picked the best arm "
            f"{_pct(r.get('arm_accuracy'))} of the time where chance is {_pct(r.get('chance'))}; "
            f"{probe}. On {r.get('n_tests')} tests Lens picked the best arm "
            f"{_pct(r.get('lens_accuracy'))} of the time: Lens minus the arm "
            f"{_pts(r.get('lens_minus_arm'))} ({_ci(r.get('ci95'), _pts)}). Lens beats this arm: "
            f"{'yes' if r.get('lens_beats_arm') else 'no'}.")
    return out


def render(res: dict) -> str:
    a = res["analysis"]
    L = []
    if res["synthetic"]:
        L += ["> **SYNTHETIC DRY RUN. These numbers come from generated data and a mock model. "
              "They are not evidence about Lens and must never be quoted.**", ""]
    if res["internal_benchmark"]:
        L += ["> **Internal benchmark only. This set's licence does not allow a public claim.**",
              ""]
    L += [f"# Stage 9 accuracy proof: {res['config_id']}", "",
          "## What we tested", "",
          "The frozen config was written and sealed (its hash is the first entry of a "
          "tamper-evident ledger, and is published) before any prediction. Every prediction "
          "was sealed before any outcome was joined. Nothing here was tuned on these results.",
          "",
          f"- Config SHA-256: `{res['config_sha256']}`",
          f"- Ledger head after the join: `{res['ledger_head']}`",
          f"- Model: {res['model']['name']} {res['model']['version']}" if res.get("model")
          else "- Model: n/a",
          f"- {a['meta']['n_pairs']} pairs and {a['meta']['n_arms']} arms joined; "
          f"{a['meta']['n_predictions_without_outcome']} sealed entries have no outcome "
          "(undecided pairs, tied tests and the manifest).", *_arm_set_lines(res), "",
          "## Null tests (spec 4.7)", "",
          "These check the machinery, not Lens. All must pass before any accuracy number is "
          "shown.", ""]
    L += [_null_line(k, v) for k, v in res["null_tests"].items()]
    if not res["accuracy_shown"]:
        L += ["", "**No accuracy number is shown**, because these null tests failed: "
              + ", ".join(NULL_NAMES[k].lower() for k in res["null_tests_failed"]) + ". "
              "The endpoints were not computed: they would prove nothing until the machinery "
              "passes.", ""]
        return "\n".join(L + _not_shown())
    stop = a["hierarchy_stopped_at"]
    L += ["", "## The answer, endpoint by endpoint", "",
          "Endpoints are checked in a fixed order; once one fails, later ones are shown but "
          "not claimed.", "",
          "**Every pre-registered endpoint passed.**" if stop is None else
          f"**Not every endpoint passed.** The hierarchy stopped at {stop}.", ""]
    L += [_endpoint_line(k, a[k]) for k in ORDER]
    if a.get("C98", {}).get("full"):
        L += ["", "## The confident-call claim", "", confident_claim(a["C98"])]
    fam = a.get("familiarity")
    if fam:
        L += ["", "## Reported, never gated", "",
              f"- Familiarity: the hit rate changes by {_num(fam['slope_hit_on_familiarity'])} "
              f"per standard deviation of familiarity gap (n = {fam['n']}); accuracy on pairs "
              f"below the median familiarity gap {_pct(fam['accuracy_below_median'])}."]
    ex = a.get("extra")
    if ex:
        km, rel = ex["kappa_matched_coverage"], ex["reliability"]
        n2 = lambda v: _num(v, 2)  # noqa: E731
        au, ece = ex["confidence_auroc"], ex["ece"]
        L += ["", "## Extra metrics (fixed before sealing, never gated)", "",
              f"- Kappa on the {_pct(km['coverage'], 0)} most confident decided pairs: "
              f"{n2(km['kappa'])} ({_ci(km['ci95'], n2)}). Above the external "
              f"{n2(km['external_kappa'])} by the pre-set rule (CI lower bound above it): "
              f"{'yes' if km['above_external'] else 'no'}. The external figure comes from "
              "another vendor's data set.",
              f"- Reliability: accuracy rises with confidence (Kendall tau "
              f"{n2(rel['monotonicity_kendall_tau'])}, {_ci(rel['monotonicity_ci95'], n2)}): "
              f"{'yes' if rel['monotone'] else 'no'}. Bins (confidence -> accuracy): "
              + "; ".join(f"{_pct(b['mean_confidence'])} -> {_pct(b['accuracy'])}"
                          for b in rel["bins"]) + ".",
              f"- Confidence AUROC for a correct call (descriptive): {n2(au['auroc'])} "
              f"({_ci(au['ci95'], n2)}).",
              (f"- Debiased ECE (descriptive): {_num(ece['debiased_ece'])} ({_ci(ece['ci95'])}, "
               f"n = {ece['n']})." if "debiased_ece" in ece else f"- ECE withheld: {ece['withheld']}.")]
    f1 = frontier_lines(a.get("F1"))
    if f1:
        L += [""] + f1
    lab = a.get("label")
    if lab:
        L += ["", f"**Label: {lab['label']}.** {lab['rule']}."]
    return "\n".join(L + [""] + _not_shown())


def _not_shown() -> list[str]:
    return ["## What this does not show", "",
            "- It covers only the datasets in the frozen config. It says nothing about other "
            "channels, audiences or a customer's own tests.",
            "- Every Upworthy result stays provisional until 100 or more decided pairs from "
            "tests that ended after the Opus 5.5 training cutoff (June 2026) exist (spec 3.3).",
            "- It says nothing about B2B buyers: B2B evidence is a separately sealed set and "
            "stays pending until it reaches its pre-registered size.",
            "- No web-presence baseline: it was dropped before sealing because no free, "
            "licensed, pre-cutoff exact-phrase web index was found.",
            "- \"Confident\" means the frozen threshold; coverage is how often Lens is willing "
            "to call at all. Most pairs may be \"can't tell\".",
            "- An interval that crosses the bar is not a pass, even when the point estimate is "
            "above it.", ""]
