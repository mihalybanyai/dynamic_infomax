"""Jeffreys' posterior pull in exp-decay, read as motives with breaking points (spec 002 §0).

Model (A&M Eq. 6; spec 002 §1.2, §4.1): y_t = sum_mu (1/D) exp(-k_mu t), k_mu = exp(-theta_mu),
m = 26 stakes t in [1, 5], sigma = 0.1, one encounter (N = 1). Since exp(-k t) = G(theta - log t)
with G(z) = exp(-exp(-z)), theta_mu is the log stake at which motive mu gives way and y_t is the
share of motives still holding at stake t ("fairness").

Each character is a fairness curve x generated with D_TRUE = 12 motives and observed without
noise. Observers model D in {4, 8, 12} motives. For each, the script fits the maximum-likelihood
curve, samples the posterior under Jeffreys (sqrt det g) and under A&M's log-normal prior
(theta_mu ~ N(0, 1)) with an affine-invariant ensemble sampler, and reports the posterior mean
fairness against what was seen, and A&M's posterior deviation Delta (eq. 9: distance from the
maximum-likelihood curve to the posterior mean curve, in units of sigma). It also reports where
the Jeffreys prior alone puts its mass, and two checks (broad initialisation, SVD conditioning).

Run:    uv run python notes/spec-002-motives-example/jeffreys_pull.py
Output: notes/spec-002-motives-example/jeffreys_pull.out (stdout; takes a few minutes)
"""

import sys
from datetime import date

import numpy as np
from scipy.optimize import least_squares

M = 26
T = np.linspace(1.0, 5.0, M)
SIGMA = 0.1
LO, HI = -8.0, 15.0  # breaking points outside e^-8 .. e^15: negligible mass under both priors
D_TRUE = 12
D_OBS = (4, 8, 12)
SEEDS = (0, 1)
LOW, HIGH = T < 2, T > 4  # "small stakes" 1-2, "large stakes" 4-5
NEVER, ALWAYS = 6.0, -3.0  # breaking points far above / below every stake seen


def curves(th: np.ndarray) -> np.ndarray:
    """th (W, D) -> fairness curves (W, m)."""
    k = np.exp(-th)
    return np.exp(-k[:, None, :] * T[None, :, None]).mean(axis=2)


def log_sqrt_det_g(th: np.ndarray) -> np.ndarray:
    """log sqrt det g up to a constant: sum of log singular values of the Jacobian."""
    d = th.shape[1]
    kt = np.exp(-th)[:, None, :] * T[None, :, None]
    s = np.linalg.svd(kt * np.exp(-kt) / d, compute_uv=False)
    with np.errstate(divide="ignore"):
        out = np.log(s).sum(axis=1)
    out[~np.isfinite(out)] = -np.inf
    return out


def log_target(th: np.ndarray, x: np.ndarray | None, kind: str) -> np.ndarray:
    out = np.full(th.shape[0], -np.inf)
    inside = np.all((th > LO) & (th < HI), axis=1)
    if not inside.any():
        return out
    t = th[inside]
    lp = log_sqrt_det_g(t) if kind == "jeffreys" else -0.5 * (t**2).sum(axis=1)
    if x is not None:
        lp = lp - ((curves(t) - x[None, :]) ** 2).sum(axis=1) / (2 * SIGMA**2)
    out[inside] = lp
    return out


def ensemble(x, kind, start, rng, walkers=96, steps=6000, burn=2000, spread=0.05, a=2.0):
    """Goodman-Weare stretch moves; returns sampled curves and breaking points, acceptance."""
    d = start.size
    pos = start[None, :] + spread * rng.standard_normal((walkers, d))
    lp = log_target(pos, x, kind)
    half = walkers // 2
    ys, ths, acc = [], [], 0
    for it in range(steps):
        for s in (0, 1):
            idx = np.arange(s * half, (s + 1) * half)
            other = np.arange((1 - s) * half, (2 - s) * half)
            z = ((a - 1) * rng.random(half) + 1) ** 2 / a
            partner = pos[rng.choice(other, half)]
            prop = partner + z[:, None] * (pos[idx] - partner)
            lpp = log_target(prop, x, kind)
            ok = np.log(rng.random(half)) < (d - 1) * np.log(z) + lpp - lp[idx]
            pos[idx[ok]] = prop[ok]
            lp[idx[ok]] = lpp[ok]
            acc += ok.sum()
        if it >= burn and it % 10 == 0:
            ys.append(curves(pos))
            ths.append(pos.copy())
    return np.concatenate(ys), np.concatenate(ths), acc / (steps * walkers)


def characters() -> dict[str, np.ndarray]:
    """Everyday characters as breaking points of D_TRUE motives (log stakes)."""
    q = D_TRUE // 4
    return {
        "mostly honest: 9 motives hold at every stake seen, 3 give way at stakes 1.2-3.3":
            np.r_[np.full(D_TRUE - q, NEVER), np.linspace(0.2, 1.2, q)],
        "honest up to one price: every motive gives way at stake 2.5":
            np.full(D_TRUE, np.log(2.5)),
        "steady: half the motives hold at every stake seen, half at none":
            np.r_[np.full(D_TRUE // 2, NEVER), np.full(D_TRUE // 2, ALWAYS)],
        "eroding: prices spread from stake 0.4 to 20":
            np.linspace(-1.0, 3.0, D_TRUE),
    }


def ml_fit(x: np.ndarray, d: int, rng) -> np.ndarray:
    """Least-squares breaking points for d motives, best of many starts."""
    best, best_cost = None, np.inf
    starts = [np.sort(rng.uniform(-2.0, 5.0, d)) for _ in range(40)]
    starts += [np.full(d, v) for v in (-1.0, 0.5, 1.0, 3.0)]
    for s in starts:
        r = least_squares(lambda th: curves(th[None, :])[0] - x, s, bounds=(LO, HI))
        if r.cost < best_cost:
            best, best_cost = r.x, r.cost
    return best


def fmt(c: np.ndarray) -> str:
    return f"{c[LOW].mean():.2f} / {c[HIGH].mean():.2f}"


def main() -> None:
    print(f"# jeffreys_pull.py, run {date.today()}, numpy {np.__version__}, seeds {SEEDS}")
    print(f"# m={M} stakes in [1,5], sigma={SIGMA}, D_TRUE={D_TRUE}, observers D={D_OBS}")
    print("# fairness reported as mean over stakes 1-2 / mean over stakes 4-5\n")

    print("1. Posterior pull, same evidence, observers modelling D motives")
    for name, th_true in characters().items():
        x = curves(th_true[None, :])[0]
        print(f"\n{name}\n  seen: {fmt(x)}")
        for d in D_OBS:
            rng = np.random.default_rng(100 + d)
            th_ml = ml_fit(x, d, rng)
            y_ml = curves(th_ml[None, :])[0]
            print(f"  D={d:2d}  best fit: {fmt(y_ml)}  (misfit {np.linalg.norm(y_ml - x) / SIGMA:.2f} sigma)")
            for kind in ("jeffreys", "lognormal"):
                parts = []
                for seed in SEEDS:
                    rng = np.random.default_rng(seed)
                    # start inside the domain: a fit at the bounds has zero Jeffreys density
                    start = np.clip(th_ml, -4.0, 8.0) + 0.01 * rng.standard_normal(d)
                    ys, _, acc = ensemble(x, kind, start, rng)
                    mean = ys.mean(axis=0)
                    delta = np.linalg.norm(mean - y_ml) / SIGMA
                    parts.append(f"{fmt(mean)}  Delta {delta:5.2f}  acc {acc:.2f}")
                print(f"        {kind:9s} " + "  |  ".join(parts))
            sys.stdout.flush()

    print("\n2. Jeffreys prior alone (seed 7)")
    rng = np.random.default_rng(7)
    for d in D_OBS:
        ys, ths, _ = ensemble(None, "jeffreys", np.full(d, 1.0), rng, steps=8000, burn=3000, spread=1.5)
        p10, p50, p90 = np.exp(np.percentile(ths, [10, 50, 90]))
        print(f"  D={d:2d}: fairness {fmt(ys.mean(axis=0))}; breaking points 10/50/90%: "
              f"stake {p10:.2f} / {p50:.2f} / {p90:.1f}")
        sys.stdout.flush()

    print("\n3. Check: broad initialisation (uniform on [-1, 4]), D=8, 15000 steps, seed 3")
    rng = np.random.default_rng(3)
    for name, th_true in list(characters().items())[:2]:
        x = curves(th_true[None, :])[0]
        th_ml = ml_fit(x, 8, np.random.default_rng(108))
        y_ml = curves(th_ml[None, :])[0]
        ys, _, acc = ensemble(x, "jeffreys", rng.uniform(-1.0, 4.0, 8), rng, steps=15000,
                              burn=6000, spread=1.0)
        mean = ys.mean(axis=0)
        print(f"  {name[:40]:40s} {fmt(mean)}  Delta {np.linalg.norm(mean - y_ml) / SIGMA:5.2f}")

    print("\n4. Check: SVD conditioning of the Jacobian at D=12 posterior samples")
    x = curves(characters()["honest up to one price: every motive gives way at stake 2.5"][None, :])[0]
    _, ths, _ = ensemble(x, "jeffreys", np.full(12, np.log(2.5)), np.random.default_rng(5), steps=3000, burn=1000)
    kt = np.exp(-ths[::50])[:, None, :] * T[None, :, None]
    s = np.linalg.svd(kt * np.exp(-kt) / 12, compute_uv=False)
    r = s[:, -1] / s[:, 0]
    print(f"  smallest/largest singular value: median {np.median(r):.1e}, min {r.min():.1e}")


if __name__ == "__main__":
    main()
