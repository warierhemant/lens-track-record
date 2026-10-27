"""Decision rules and calibration summaries for 8.6 / 8.8 (spec 4.4, 4.5, 4.6, 4.8)."""
from __future__ import annotations

import numpy as np
from scipy import stats

from lens_engine.harness import metrics

R0_MARGIN = 0.0075   # nats per pair, spec 4.4


def r0_verdict(ci_lo: float, ci_hi: float, margin: float = R0_MARGIN) -> str:
    """Spec 4.4: KEEP if the CI lower bound > 0; DROP if the upper bound < margin;
    otherwise UNDETERMINED. KEEP is checked first (a CI inside (0, margin) is KEEP)."""
    if ci_lo > 0:
        return "KEEP"
    if ci_hi < margin:
        return "DROP"
    return "UNDETERMINED"


def tost_equivalent(ci90_lo: float, ci90_hi: float, margin: float) -> bool:
    """Two one-sided tests at 5% each: the 90% CI lies inside (-margin, +margin)."""
    return bool(ci90_lo > -margin and ci90_hi < margin)


def per_pair_logloss(y, p) -> np.ndarray:
    y = np.asarray(y, float)
    p = np.clip(np.asarray(p, float), metrics.EPS, 1 - metrics.EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ltt_threshold(conf_null, alpha: float = 0.05, delta: float = 0.10,
                  grid=None) -> dict:
    """Learn-then-Test, fixed sequence from the most conservative threshold down.
    H0_t: the null-pair call rate at threshold t exceeds alpha. Reject when the exact
    binomial P(X <= k | n, alpha) <= delta. The chosen t is the smallest rejected t
    before the first non-rejection; if even the largest t is not rejected, never call (t=0.5).
    A pair is called when |p - 0.5| >= t."""
    c = np.asarray(conf_null, float)
    n = len(c)
    grid = np.round(np.arange(0.49, -0.0001, -0.01), 2) if grid is None else np.asarray(grid)
    chosen, path = 0.5, []
    for t in grid:
        k = int((c >= t).sum())
        pv = float(stats.binom.cdf(k, n, alpha)) if n else 1.0
        path.append((float(t), k, pv))
        if pv <= delta:
            chosen = float(t)
        else:
            break
    return {"threshold": chosen, "n_null": n, "alpha": alpha, "delta": delta,
            "null_call_rate_at_threshold": float((c >= chosen).mean()) if n else float("nan"),
            "path_tail": path[-3:]}


def match_coverage(conf, eligible, n_calls: int) -> np.ndarray:
    """Call the n_calls most confident pairs among `eligible` (ties broken by order).
    Used to compare a panel-filtered rule with the |p - 0.5| rule at matched coverage."""
    conf = np.asarray(conf, float)
    eligible = np.asarray(eligible, bool)
    idx = np.where(eligible)[0]
    idx = idx[np.argsort(-conf[idx], kind="mergesort")][:n_calls]
    called = np.zeros(len(conf), bool)
    called[idx] = True
    return called


def reliability_table(y, p, n_bins: int = 10) -> list[dict]:
    y, p = np.asarray(y, float), np.asarray(p, float)
    edges = np.linspace(0, 1, n_bins + 1)
    b = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    out = []
    for i in range(n_bins):
        m = b == i
        if not m.any():
            continue
        lo, hi = metrics.wilson(y[m].sum(), int(m.sum()))
        out.append({"bin": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "n": int(m.sum()),
                    "mean_predicted": float(p[m].mean()), "observed": float(y[m].mean()),
                    "observed_ci95": (lo, hi)})
    return out


def debiased_ece(y, p, n_bins: int = 15) -> float:
    """Debiased L2 calibration error (Kumar, Liang, Ma 2019), equal-mass bins:
    sqrt(max(0, sum_b w_b [(ybar_b - pbar_b)^2 - ybar_b (1 - ybar_b) / (n_b - 1)]))."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    order = np.argsort(p, kind="mergesort")
    tot = 0.0
    for chunk in np.array_split(order, n_bins):
        nb = len(chunk)
        if nb < 2:
            continue
        yb, pb = y[chunk].mean(), p[chunk].mean()
        tot += nb / len(y) * ((yb - pb) ** 2 - yb * (1 - yb) / (nb - 1))
    return float(np.sqrt(max(tot, 0.0)))


def calibration_gate(slope_ci, intercept_ci, spiegel_p, n: int) -> dict:
    """Spec 4.5 / 4.2 row 8.8: slope 95% CI inside [0.8, 1.25] on >= 3,000 pairs (primary),
    then intercept CI contains 0, then Spiegelhalter not rejected at 0.05 (fixed order)."""
    prim = bool(n >= 3000 and slope_ci[0] >= 0.8 and slope_ci[1] <= 1.25)
    s1 = bool(intercept_ci[0] <= 0 <= intercept_ci[1])
    s2 = bool(spiegel_p >= 0.05)
    return {"n": n, "primary_slope_inside_0.8_1.25": prim, "secondary1_intercept_contains_0": s1,
            "secondary2_spiegelhalter_not_rejected": s2}
