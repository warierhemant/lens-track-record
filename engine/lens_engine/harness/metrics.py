"""Evaluation metrics with cluster-bootstrap CIs by test id (spec 4.1, 4.5, 4.6, 4.7, 7.2).

Pairwise convention: y = 1 if arm B won, p = predicted P(B wins). Pairs are position
balanced upstream, so chance is 50% and kappa = 2 * accuracy - 1 in expectation.
A prediction at exactly p = 0.5 is a tie and counts as half a hit (no coin needed).
"""
from __future__ import annotations

import numpy as np
from scipy import stats

EPS = 1e-6
N_BOOT = 2000


# ------------------------------------------------------------------ point metrics
def _clip(p):
    return np.clip(np.asarray(p, float), EPS, 1 - EPS)


def hit_rate(y, p) -> float:
    y, p = np.asarray(y), np.asarray(p, float)
    pred = np.where(p > 0.5, 1.0, np.where(p < 0.5, 0.0, 0.5))
    return float(np.mean(np.where(pred == 0.5, 0.5, pred == y)))


def cohen_kappa(y, p) -> float:
    """Kappa between the predicted label (p > 0.5) and the real winner; ties are split."""
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    pred = np.where(p > 0.5, 1.0, np.where(p < 0.5, 0.0, 0.5))
    po = np.mean(np.where(pred == 0.5, 0.5, pred == y))
    py1, pp1 = y.mean(), pred.mean()
    pe = py1 * pp1 + (1 - py1) * (1 - pp1)
    return float((po - pe) / (1 - pe)) if pe < 1 else 0.0


def log_loss(y, p) -> float:
    y, p = np.asarray(y, float), _clip(p)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.mean((p - y) ** 2))


def _logistic_fit(x, y, offset=None, fit_slope=True, iters=50):
    """Tiny IRLS. Returns (intercept, slope). With fit_slope=False, slope is fixed at 1
    via the offset (calibration-in-the-large)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    off = np.zeros_like(x) if offset is None else np.asarray(offset, float)
    X = np.column_stack([np.ones_like(x), x]) if fit_slope else np.ones((len(x), 1))
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ beta + off
        mu = 1 / (1 + np.exp(-eta))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        grad = X.T @ (y - mu)
        hess = X.T @ (X * w[:, None])
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return (np.nan, np.nan)
        beta += step
        if np.max(np.abs(step)) < 1e-10:
            break
    return (float(beta[0]), float(beta[1])) if fit_slope else (float(beta[0]), 1.0)


def calibration_slope_intercept(y, p) -> tuple[float, float]:
    """Slope: logistic regression of y on logit(p). Intercept: calibration-in-the-large,
    the intercept with logit(p) as an offset (slope fixed at 1). Perfect: slope 1, int 0."""
    lp = np.log(_clip(p) / (1 - _clip(p)))
    _, slope = _logistic_fit(lp, y)
    intercept, _ = _logistic_fit(lp, y, offset=lp, fit_slope=False)
    return slope, intercept


def spiegelhalter_z(y, p) -> tuple[float, float]:
    """Spiegelhalter (1986) Z for calibration; returns (Z, two-sided p)."""
    y, p = np.asarray(y, float), _clip(p)
    num = np.sum((y - p) * (1 - 2 * p))
    den = np.sqrt(np.sum((1 - 2 * p) ** 2 * p * (1 - p)))
    z = float(num / den) if den > 0 else 0.0
    return z, float(2 * stats.norm.sf(abs(z)))


def coverage_accuracy(y, p, thresholds=None) -> list[dict]:
    """Abstain when |p - 0.5| < t. Returns coverage and selective accuracy per threshold."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    conf = np.abs(p - 0.5)
    if thresholds is None:
        thresholds = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
    out = []
    for t in thresholds:
        m = conf >= t if t > 0 else np.ones_like(conf, bool)
        out.append({"threshold": t, "coverage": float(m.mean()),
                    "n_called": int(m.sum()),
                    "selective_accuracy": hit_rate(y[m], p[m]) if m.any() else float("nan")})
    return out


def aurc(y, p) -> float:
    """Area under the risk-coverage curve (lower is better), ranking by |p - 0.5|."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    order = np.argsort(-np.abs(p - 0.5), kind="mergesort")
    pred = np.where(p > 0.5, 1.0, np.where(p < 0.5, 0.0, 0.5))[order]
    err = np.where(pred == 0.5, 0.5, (pred != y[order]).astype(float))
    return float(np.mean(np.cumsum(err) / np.arange(1, len(err) + 1)))


def wilson(k: float, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return float(c - h), float(c + h)


def false_separation_rate(p_null, margin: float = 0.0) -> dict:
    """Share of NULL pairs the predictor calls 'ahead' (|p - 0.5| > margin), Wilson CI."""
    p = np.asarray(p_null, float)
    called = np.abs(p - 0.5) > margin
    lo, hi = wilson(called.sum(), len(p))
    return {"rate": float(called.mean()) if len(p) else float("nan"), "n": int(len(p)),
            "ci95": (lo, hi)}


# ------------------------------------------------------------------ best-of-k
def best_of_k_hits(test_ids, scores, is_best) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per test: hit (argmax score is the best arm; ties in score split credit),
    chance 1/k. Returns (unique test ids, hit, chance)."""
    test_ids = np.asarray(test_ids)
    scores = np.asarray(scores, float)
    is_best = np.asarray(is_best, bool)
    order = np.argsort(test_ids, kind="mergesort")
    t, s, b = test_ids[order], scores[order], is_best[order]
    uniq, start = np.unique(t, return_index=True)
    end = np.append(start[1:], len(t))
    hits = np.empty(len(uniq))
    chance = np.empty(len(uniq))
    for i, (a, e) in enumerate(zip(start, end)):
        ss, bb = s[a:e], b[a:e]
        top = ss == ss.max()
        hits[i] = (top & bb).sum() / top.sum()
        chance[i] = 1.0 / (e - a)
    return uniq, hits, chance


# ------------------------------------------------------------------ cluster bootstrap
def cluster_bootstrap(stat, clusters, *arrays, n_boot: int = N_BOOT, seed: int = 0,
                      alpha: float = 0.05) -> dict:
    """Percentile CI for stat(*arrays) resampling whole clusters with replacement."""
    clusters = np.asarray(clusters)
    arrays = [np.asarray(a) for a in arrays]
    point = stat(*arrays)
    uniq, inv = np.unique(clusters, return_inverse=True)
    order = np.argsort(inv, kind="mergesort")
    counts = np.bincount(inv)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    rng = np.random.default_rng(seed)
    G = len(uniq)
    reps = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, G, G)
        c = counts[pick]
        offs = np.repeat(np.cumsum(c) - c, c)
        idx = order[np.repeat(starts[pick], c) + (np.arange(c.sum()) - offs)]
        reps[b] = stat(*(a[idx] for a in arrays))
    reps = reps[np.isfinite(reps)]
    lo, hi = np.quantile(reps, [alpha / 2, 1 - alpha / 2])
    return {"point": float(point), "ci95": (float(lo), float(hi)), "n_clusters": int(G),
            "n": int(len(clusters)), "n_boot": int(n_boot), "seed": seed}


def pairwise_report(y, p, clusters, seed: int = 0, n_boot: int = N_BOOT) -> dict:
    """All pairwise metrics, each with a cluster-bootstrap CI by test id."""
    y = np.asarray(y, float)
    p = np.asarray(p, float)

    def cb(f):
        return cluster_bootstrap(f, clusters, y, p, n_boot=n_boot, seed=seed)

    rep = {
        "n": int(len(y)),
        "hit_rate": cb(hit_rate),
        "kappa": cb(cohen_kappa),
        "log_loss": cb(log_loss),
        "brier": cb(brier),
        "calibration_slope": cb(lambda a, b: calibration_slope_intercept(a, b)[0]),
        "calibration_intercept": cb(lambda a, b: calibration_slope_intercept(a, b)[1]),
        "aurc": cb(aurc),
    }
    z, pz = spiegelhalter_z(y, p)
    rep["spiegelhalter"] = {"z": z, "p": pz, "rejected_at_0.05": pz < 0.05}
    rep["coverage_accuracy"] = coverage_accuracy(y, p)
    rep["chance"] = {"hit_rate": 0.5, "kappa": 0.0, "log_loss": float(np.log(2)), "brier": 0.25}
    return rep


def best_of_k_report(test_ids, scores, is_best, seed: int = 0, n_boot: int = N_BOOT) -> dict:
    uniq, hits, chance = best_of_k_hits(test_ids, scores, is_best)
    acc = cluster_bootstrap(np.mean, uniq, hits, n_boot=n_boot, seed=seed)
    diff = cluster_bootstrap(lambda h, c: np.mean(h - c), uniq, hits, chance,
                             n_boot=n_boot, seed=seed)
    return {"n_tests": int(len(uniq)), "accuracy": acc, "chance": float(chance.mean()),
            "accuracy_minus_chance": diff}


def across_split_interval(split_values, n_boot: int = N_BOOT, seed: int = 0) -> dict:
    """Spec 4.2: the across-split 95% interval is the 2.5th-97.5th percentile of a
    bootstrap (2,000 resamples, seeded) over the per-split means."""
    v = np.asarray(split_values, float)
    rng = np.random.default_rng(seed)
    reps = v[rng.integers(0, len(v), (n_boot, len(v)))].mean(axis=1)
    lo, hi = np.quantile(reps, [0.025, 0.975])
    return {"mean": float(v.mean()), "ci95": (float(lo), float(hi)), "n_splits": int(len(v))}
