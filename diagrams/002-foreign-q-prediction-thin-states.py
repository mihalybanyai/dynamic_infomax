"""Thin-states figure for spec 002-foreign-q-prediction (§4.4, OQ-14).

Why a sampled prior's marginal fails where the prior is thin, and how a per-point estimator
that finds the posterior itself fixes it. Exp-decay, `sigma = 0.1`, `N = 1`, prior `p_LN`.

  (a) The problem, at D = 2, in A&M's coordinate xi (ordered, xi_1 <= xi_2). Grey: the
      cloud of 20000 draws that carries the prior beyond its grid. Star: a state at the
      no-decay corner xi = (1, 1). Inset: the posterior for one datum x drawn from that
      state, a sliver against the corner, where the cloud has no draws. The cloud's
      mixture m(x) is then set by draws far from the posterior, so it underestimates m.
  (b) The same datum in log decay times theta = -log(-log xi), unordered. The faces xi = 0, 1
      go to infinity, and the posterior (blue) becomes a smooth blob, mirrored across the
      diagonal because swapping the two rates changes nothing. Orange: the draws of the
      current per-point proposal, kernels around the cloud draws that best explain x,
      which sit at the cloud's edge, short of the posterior. Aqua: the proposed one, a
      Student-t at the posterior's mode with its curvature, mirrored across the diagonal.
  (c, d) At D = 3, against a grid of half the default cell length, the error of the mean
      log m over 64 data per state, for p_LN (c) and Jeffreys (d), three estimators: the
      cloud (what the scores use), the current per-point estimate, and the proposed one.
      Dashed: T7(a)'s bar, 0.1 nats. At the no-decay corner the reference itself is good
      to about 0.16 nats only (default and fine grids differ by that much).

The proposed estimator is the prototype of `SampledPrior.per_point_log_marginal` (spec §4.4,
OQ-14), kept here as it was drawn: it sums over all D! relabellings. In unordered log decay times it finds the mode of prior times likelihood
by L-BFGS from the three cloud draws that best explain x, takes the Hessian there, and
draws from 0.8 t_5(mode, 1.5^2 Sigma) + 0.2 t_5(mode, 9 Sigma), relabelled at random; the
proposal density sums over all D! relabellings. The current estimator is
`SampledPrior.kernel_log_marginal` (superseded); its draws in (b) are re-drawn here the same way, for
display only.

Run:      uv run python diagrams/002-foreign-q-prediction-thin-states.py [--recompute]
Output:   diagrams/002-foreign-q-prediction-thin-states.svg
Cache:    diagrams/002-foreign-q-prediction-thin-states.json, panels (c, d), written by
          --recompute (about 5 min; the fine D = 3 grid is set before any build).
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import infomax.quadrature as Q

RECOMPUTE = "--recompute" in sys.argv
if RECOMPUTE:  # the D = 3 reference: cells of 0.3 noise units, set before any grid is built
    Q.ARC_CELL_BY_D[3] = 0.3
    Q.MAX_GRID_NODES = 6_000_000

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # headless: write SVG, no display
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import scipy.optimize  # noqa: E402
import scipy.special  # noqa: E402

from infomax.jeffreys import build_jeffreys  # noqa: E402
from infomax.mixture import log_normal_iso  # noqa: E402
from infomax.models import build_model  # noqa: E402
from infomax.plognormal import build_pln  # noqa: E402
from infomax.sampled import (  # noqa: E402
    LOCAL_SHARE,
    N_CENTRES,
    N_PROPOSAL,
    build_sampled_jeffreys,
    sampled_from,
)

HERE = Path(__file__).parent
STEM = HERE / "002-foreign-q-prediction-thin-states"

# ---- style: reference categorical slots 1-3 (validated all-pairs), grey for the cloud ----
POSTERIOR = "#2a78d6"   # blue
CURRENT = "#eb6834"     # orange
PROPOSED = "#1baf7a"    # aqua
CLOUD = "#a9a8a2"       # neutral grey, recessive
INK, INK2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2})

NU = 5.0
N_DRAW = 1000


# ---- the proposed estimator (prototype) ---------------------------------------------------
def xi_of(th):
    return np.exp(-np.exp(-th))


def theta_of(xi):
    return -np.log(-np.log(np.clip(xi, 1e-300, 1 - 1e-12)))


def make_log_f(prior, model, x):
    """`log` of prior times likelihood in unordered log decay times."""
    log_dfact = math.lgamma(model.D + 1)

    def log_f(th):
        th = np.atleast_2d(th)
        xi = np.sort(xi_of(th), axis=-1)
        with np.errstate(divide="ignore", invalid="ignore"):
            out = (prior.log_density(xi) - log_dfact + np.sum(-np.exp(-th) - th, axis=-1)
                   + log_normal_iso(x, model.y(xi), model.sigma_eff))
        out[~np.isfinite(out)] = -np.inf
        return out
    return log_f


def mvt_logpdf(z, mu, L, nu):
    d = z.shape[-1]
    u = np.linalg.solve(L, (z - mu).T).T
    return (scipy.special.gammaln((nu + d) / 2) - scipy.special.gammaln(nu / 2) - 0.5 * d * np.log(nu * np.pi)
            - np.sum(np.log(np.diag(L))) - 0.5 * (nu + d) * np.log1p(np.sum(u * u, -1) / nu))


def proposed(prior, cloud, model, x, rng):
    """`(log m(x), ESS share, draws)` of the prototype per-point estimator."""
    D = model.D
    perms = np.array(list(itertools.permutations(range(D))))
    log_f = make_log_f(prior, model, x)
    lw0 = np.log(np.maximum(cloud.weights, 1e-300)) + log_normal_iso(x, model.y(cloud.atoms), model.sigma_eff)
    obj = lambda t: -float(log_f(t)[0])  # noqa: E731
    mode, val = None, np.inf
    for t0 in theta_of(cloud.atoms[np.argsort(-lw0)[:3]]):
        r = scipy.optimize.minimize(obj, t0, method="L-BFGS-B")
        if r.fun < val:
            mode, val = r.x, r.fun
    h, E = 1e-3, np.eye(D) * 1e-3
    H = np.array([[(obj(mode + E[i] + E[j]) - obj(mode + E[i] - E[j]) - obj(mode - E[i] + E[j])
                    + obj(mode - E[i] - E[j])) / (4 * h * h) for j in range(D)] for i in range(D)])
    w, V = np.linalg.eigh(0.5 * (H + H.T))
    Sigma = (V / np.maximum(w, 1e-2)) @ V.T
    comps = [(0.8, np.linalg.cholesky(1.5**2 * Sigma)), (0.2, np.linalg.cholesky(9.0 * Sigma))]
    n1 = rng.binomial(N_DRAW, 0.8)
    z = np.concatenate([mode + (rng.standard_normal((n, D)) @ L.T) * np.sqrt(NU / rng.chisquare(NU, (n, 1)))
                        for (_, L), n in zip(comps, (n1, N_DRAW - n1))])
    z = np.take_along_axis(z, perms[rng.integers(0, len(perms), N_DRAW)], axis=1)
    log_q = np.full(N_DRAW, -np.inf)
    for a, L in comps:
        per = np.stack([mvt_logpdf(z[:, p], mode, L, NU) for p in perms])
        log_q = np.logaddexp(log_q, np.log(a) + scipy.special.logsumexp(per, axis=0) - np.log(len(perms)))
    lw = log_f(z) - log_q
    lw[~np.isfinite(lw)] = -np.inf
    wn = np.exp(lw - lw.max())
    return float(scipy.special.logsumexp(lw) - np.log(N_DRAW)), float(1 / np.sum((wn / wn.sum()) ** 2) / N_DRAW), z


def current_draws(cloud, model, x, rng):
    """The draws of `kernel_log_marginal`'s proposal for one datum, re-drawn for display."""
    D = model.D
    l0 = np.log(np.maximum(cloud.weights, 1e-300)) + log_normal_iso(x, model.y(cloud.atoms), model.sigma_eff)
    w0 = np.exp(l0 - l0.max())
    w0 /= w0.sum()
    n0 = 1.0 / np.sum(w0**2)
    top, counts = np.unique(rng.choice(len(w0), size=N_CENTRES, p=w0), return_counts=True)
    C = np.atleast_2d(np.cov(cloud.atoms.T, aweights=w0)) if n0 > 2 else np.diag(cloud._kde_bw**2)
    L = np.linalg.cholesky(C * n0 ** (-2.0 / (D + 4)) + 1e-12 * np.eye(D))
    n_loc = rng.binomial(N_PROPOSAL, LOCAL_SHARE)
    loc = cloud.atoms[top[rng.choice(len(top), n_loc, p=counts / counts.sum())]] + rng.standard_normal((n_loc, D)) @ L.T
    far = cloud._kde_atoms[rng.integers(0, len(cloud._kde_atoms), N_PROPOSAL - n_loc)]
    far = far + cloud._kde_bw * rng.standard_normal(far.shape)
    z = np.concatenate([loc, far])
    return z[np.all((z > 0) & (z < 1), axis=1)]


# ---- panels (c, d): D = 3 errors against the fine grid ------------------------------------
STATES_D3 = {
    "no-decay corner\n(1, 1, 1)*": [1.0, 1.0, 1.0],
    "near corner\n(.97, .97, .97)": [0.97, 0.97, 0.97],
    "fast and slow\n(0, 1, 1)": [0.0, 1.0, 1.0],
    "(0.02, 1, 1)": [0.02, 1.0, 1.0],
    "coincident\n(.5, .5, .5)": [0.5, 0.5, 0.5],
    "mixed faces\n(0, .5, 1)": [0.0, 0.5, 1.0],
    "typical\n(.3, .6, .8)": [0.3, 0.6, 0.8],
}


def recompute_d3() -> dict:
    model = build_model("exp_decay", 3, m=26, sigma=0.1, N=1)
    s = model.sigma_eff
    rng = np.random.default_rng(20261240)
    out = {}
    for name in ("p_LN", "p_J"):
        grid = build_pln(model) if name == "p_LN" else build_jeffreys(model)
        cloud = sampled_from(grid, model, "p_LN") if name == "p_LN" else build_sampled_jeffreys(model)
        rows = {}
        for k, (label, th) in enumerate(STATES_D3.items()):
            y = model.y(np.asarray(th, float)[None])[0]
            x = y + s * np.random.default_rng(20261230 + k).standard_normal((64, y.size))
            ref = grid.log_marginal(model, x)
            cur, _ = cloud.kernel_log_marginal(model, x, np.random.default_rng(k))
            prop = np.array([proposed(grid, cloud, model, xi, rng)[:2] for xi in x])
            rows[label] = {
                "cloud": float(np.mean(ref - cloud.cloud().log_marginal(model, x))),  # the plain cloud
                "current": float(np.mean(ref - cur)),
                "proposed": float(np.mean(ref - prop[:, 0])),
                "proposed_ess_median": float(np.median(prop[:, 1])),
            }
            print(name, label.replace("\n", " "), rows[label], flush=True)
        out[name] = rows
    return out


if RECOMPUTE:
    STEM.with_suffix(".json").write_text(json.dumps(recompute_d3(), indent=1))
d3 = json.loads(STEM.with_suffix(".json").read_text())

# ---- panels (a, b): D = 2, one datum at the no-decay corner -------------------------------
model = build_model("exp_decay", 2, m=26, sigma=0.1, N=1)
s = model.sigma_eff
grid = build_pln(model)
cloud = sampled_from(grid, model, "p_LN")
state = np.array([1.0, 1.0])
x = model.y(state[None])[0] + s * np.random.default_rng(20261250).standard_normal(model.m_out)
rng = np.random.default_rng(20261251)
lm_grid = float(grid.log_marginal(model, x[None])[0])
lm_cloud = float(cloud.cloud().log_marginal(model, x[None])[0])  # the plain cloud, not the routed marginal
lm_cur, ess_cur = cloud.kernel_log_marginal(model, x[None], np.random.default_rng(20261252))
lm_prop, ess_prop, z_prop = proposed(grid, cloud, model, x, rng)
z_cur = current_draws(cloud, model, x, np.random.default_rng(20261252))
print(f"D = 2 corner datum: log m grid {lm_grid:.2f}; error cloud {lm_grid - lm_cloud:+.2f}, "
      f"current {lm_grid - lm_cur[0]:+.2f} (ESS {ess_cur[0]:.3f}), proposed {lm_grid - lm_prop:+.3f} (ESS {ess_prop:.2f})")

# posterior on a log-time grid (unordered, both labellings)
lim_b = (-4.0, 10.0)
g = np.linspace(*lim_b, 301)
T1, T2 = np.meshgrid(g, g)
log_f = make_log_f(grid, model, x)
LF = log_f(np.column_stack([T1.ravel(), T2.ravel()])).reshape(T1.shape)
P = np.exp(LF - np.nanmax(LF[np.isfinite(LF)]))


def hpd_levels(P, masses=(0.99, 0.9, 0.5)):
    v = np.sort(P.ravel())[::-1]
    c = np.cumsum(v) / v.sum()
    return [v[np.searchsorted(c, m)] for m in masses]


fig, ((axA, axB), (axC, axD)) = plt.subplots(2, 2, figsize=(11.5, 10.2))
cl = cloud.atoms[np.random.default_rng(1).choice(len(cloud.atoms), 4000, replace=False)]

# (a) xi, ordered
axA.fill([0, 0, 1], [0, 1, 1], color="#f3f2ef", zorder=0)
axA.scatter(cl[:, 0], cl[:, 1], s=2, color=CLOUD, alpha=0.6, lw=0, zorder=1)
axA.plot(*state, marker="*", ms=15, color=INK, mec="white", mew=1.0, zorder=5, ls="none")
axA.set(xlim=(-0.02, 1.04), ylim=(-0.02, 1.04), xlabel=r"$\xi_1$ (the faster rate)", ylabel=r"$\xi_2$ (the slower rate; $\xi_1 \leq \xi_2$)",
        aspect="equal")
axA.set_title(r"(a) The problem, in $\xi$: the posterior sits where the cloud has no draws", fontsize=10, loc="left")
ins = axA.inset_axes([0.47, 0.06, 0.47, 0.47])
zx = np.linspace(0.88, 1.0, 361)
X1, X2 = np.meshgrid(zx, zx)
ordered = X1 <= X2
XI = np.column_stack([X1.ravel(), X2.ravel()])
with np.errstate(divide="ignore", invalid="ignore"):
    lxi = grid.log_density(np.sort(XI, axis=-1)) + log_normal_iso(x, model.y(np.sort(XI, axis=-1)), s)
lxi = np.where(ordered.ravel() & np.isfinite(lxi), lxi, -np.inf).reshape(X1.shape)
PX = np.exp(lxi - lxi[np.isfinite(lxi)].max())
ins.contourf(X1, X2, PX, levels=sorted(hpd_levels(PX)) + [1.01], colors=[POSTERIOR], alpha=0.25)
ins.contour(X1, X2, PX, levels=sorted(hpd_levels(PX)), colors=[POSTERIOR], linewidths=1.0)
inside = np.all(cloud.atoms >= 0.88, axis=1)
ins.scatter(cloud.atoms[inside, 0], cloud.atoms[inside, 1], s=6, color=CLOUD, lw=0)
ins.plot(*state, marker="*", ms=12, color=INK, mec="white", mew=0.8, ls="none")
ins.set(xlim=(0.88, 1.002), ylim=(0.88, 1.002), xticks=[0.88, 0.94, 1.0], yticks=[0.88, 0.94, 1.0])
ins.tick_params(labelsize=8)
ins.set_title(f"zoom: posterior for one datum\n{int(inside.sum())} of 20000 cloud draws in view", fontsize=8.5, color=INK)
axA.indicate_inset_zoom(ins, edgecolor=INK2)
axA.legend(handles=[
    plt.Line2D([], [], ls="none", marker="o", ms=5, color=CLOUD, label="cloud: 20000 draws of $p_{LN}$"),
    plt.Line2D([], [], ls="none", marker="*", ms=11, color=INK, label=r"state: no-decay corner, $\xi = (1, 1)$"),
    plt.Rectangle((0, 0), 1, 1, fc=POSTERIOR, alpha=0.35, ec=POSTERIOR, label="posterior for one datum (50, 90, 99%)"),
], loc="upper left", fontsize=8.5, frameon=True, framealpha=0.92, edgecolor="none")

# (b) log decay times, unordered
both = lambda a: np.concatenate([a, a[:, ::-1]])  # noqa: E731
tc = both(theta_of(cl))
axB.scatter(tc[:, 0], tc[:, 1], s=2, color=CLOUD, alpha=0.5, lw=0, zorder=1)
lev = sorted(hpd_levels(P))
axB.contourf(T1, T2, P, levels=lev + [1.01], colors=[POSTERIOR], alpha=0.22, zorder=2)
axB.contour(T1, T2, P, levels=lev, colors=[POSTERIOR], linewidths=1.0, zorder=2)
tcur = theta_of(np.sort(z_cur, axis=-1))
pick = np.random.default_rng(2).choice(len(tcur), min(400, len(tcur)), replace=False)
axB.scatter(*both(tcur[pick]).T, s=7, color=CURRENT, marker="^", lw=0, alpha=0.8, zorder=3)
pick = np.random.default_rng(3).choice(len(z_prop), 400, replace=False)
axB.scatter(z_prop[pick, 0], z_prop[pick, 1], s=7, color=PROPOSED, marker="o", lw=0, alpha=0.8, zorder=4)
axB.plot(lim_b, lim_b, ls=(0, (4, 3)), color=INK2, lw=1.0, zorder=0)
axB.set(xlim=lim_b, ylim=lim_b, aspect="equal", xlabel=r"$\theta_1 = -\log(-\log \xi_1)$ (log decay time)",
        ylabel=r"$\theta_2$")
axB.set_title("(b) The same datum in log decay times: where each looks", fontsize=10, loc="left")
handles = [
    plt.Line2D([], [], ls="none", marker="o", ms=5, color=CLOUD, label="cloud (prior draws)"),
    plt.Rectangle((0, 0), 1, 1, fc=POSTERIOR, alpha=0.35, ec=POSTERIOR, label="posterior (50, 90, 99%)"),
    plt.Line2D([], [], ls="none", marker="^", ms=6, color=CURRENT,
               label=f"current proposal: ESS {ess_cur[0]:.1%}, off by {lm_grid - lm_cur[0]:+.1f} nats"),
    plt.Line2D([], [], ls="none", marker="o", ms=6, color=PROPOSED,
               label=f"proposed: ESS {ess_prop:.0%}, off by {lm_grid - lm_prop:+.2f} nats"),
]
axB.legend(handles=handles, loc="upper left", fontsize=8.5, frameon=True, framealpha=0.92, edgecolor="none")
axB.text(9.7, -3.7, "dashed: swapping the two rates changes\nnothing, so the posterior is mirrored across\n"
         f"it (the fold). The cloud is off by {lm_grid - lm_cloud:+.1f} nats.", fontsize=8.5, color=INK,
         ha="right", va="bottom")


# (c, d) errors at D = 3
def dot_panel(ax, rows, title):
    labels = list(rows)
    y = np.arange(len(labels))[::-1]
    for key, colour, marker, name in (("cloud", CLOUD, "s", "cloud (the scores)"),
                                      ("current", CURRENT, "^", "current per-point"),
                                      ("proposed", PROPOSED, "o", "proposed")):
        v = np.clip(np.abs([rows[k][key] for k in labels]), 1e-3, None)
        ax.scatter(v, y, s=46, color=colour, marker=marker, edgecolor="white", linewidth=1.0, zorder=3, label=name)
    ax.axvline(0.1, ls=(0, (4, 3)), color=INK2, lw=1.0, zorder=1)
    ax.text(0.105, len(labels) - 0.45, "T7(a) bar\n0.1 nats", fontsize=8, color=INK2, va="top")
    ax.set_xscale("log")
    ax.set(xlim=(8e-4, 400), ylim=(-0.6, len(labels) - 0.4), yticks=y)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.grid(axis="x", color="#e6e5e0", lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_xlabel("|error of mean log m| (nats; below 1e-3 drawn at 1e-3)")
    ax.set_title(title, fontsize=10, loc="left")
    ess = np.median([rows[k]["proposed_ess_median"] for k in labels])
    ax.text(0.99, 0.02, f"proposed: median ESS {ess:.0%}", transform=ax.transAxes, fontsize=8, color=INK2,
            ha="right", va="bottom")


dot_panel(axC, d3["p_LN"], r"(c) $D = 3$, $p_{LN}$: error against a fine grid, 64 data per state")
dot_panel(axD, d3["p_J"], r"(d) $D = 3$, Jeffreys: the same")
axC.legend(loc="lower right", bbox_to_anchor=(1.0, 0.07), fontsize=8.5, frameon=False)
fig.text(0.01, 0.005, "* At the no-decay corner the reference grid itself is good to about 0.16 nats only.",
         fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.015, 1, 1))
fig.savefig(STEM.with_suffix(".svg"))
print("wrote", STEM.with_suffix(".svg"))
