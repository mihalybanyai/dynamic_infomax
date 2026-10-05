"""
Exploratory drawing of B' (spec 002, OQ-2): nature spread with equal mass per cell that
the budget can resolve, against B's cooperative end (Jeffreys, mass proportional to
sqrt(det g)).

UNTRUSTED / exploratory, like q_family_viz.py next to it: a quick exp-decay model and a
rough grid Blahut-Arimoto p*, only to *picture* the candidate.

Figures:
  q_bprime_param.png, q_bprime_pred.png
      exp-decay d=2 at two noise levels; columns: Jeffreys (B at c=0) and B' (a greedy
      packing of the image at one noise unit, then one equal share per cell).
  q_bprime_hypercone.png
      square hypercone, D=26 (25 sub-resolution directions of equal width): the density
      along the relevant coordinate theta_1 under different ways of counting
      "distinguishable predictions" in each cross-section.

Run:  uv run python notes/q-family-viz/q_family_bprime.py
"""

from math import ceil, comb, lgamma, log, pi
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RNG = np.random.default_rng(20261005)
OUT = Path(__file__).parent

# ------------------------------------------------------------- exp-decay model (d=2)
D = 2
M = 12
TIMES = np.linspace(1.0, 5.0, M)
BOX = np.array([[-1.0, 3.0], [-1.0, 3.0]])  # decay rate k_mu = e^{-theta_mu}
SIGMAS = [0.04, 0.15]


def y(theta):
    """Exp-decay mean map, theta (..., D) -> y (..., M); a_mu = 1/D."""
    k = np.exp(-np.asarray(theta, dtype=float))
    return np.exp(-k[..., :, None] * TIMES).mean(axis=-2)


def sqrt_det_g(theta, sigma):
    """sqrt(det g) for each row of theta, by central differences."""
    eps = 1e-5
    J = np.empty((len(theta), D, M))
    for mu in range(D):
        dp, dm = theta.copy(), theta.copy()
        dp[:, mu] += eps
        dm[:, mu] -= eps
        J[:, mu] = (y(dp) - y(dm)) / (2 * eps)
    g = J @ J.transpose(0, 2, 1) / sigma**2
    return np.sqrt(np.clip(np.linalg.det(g), 1e-300, None))


def logsumexp(a, axis):
    m = a.max(axis=axis, keepdims=True)
    return (m + np.log(np.exp(a - m).sum(axis=axis, keepdims=True))).squeeze(axis)


def grid_ba(th, sigma, n_iter=120, n_mc=24):
    """Rough Blahut-Arimoto for the capacity prior on a grid (Monte Carlo divergences)."""
    Y = y(th)
    w = np.full(len(th), 1.0 / len(th))
    for _ in range(n_iter):
        keep = w > 1e-6
        Yk, logwk = Y[keep], np.log(w[keep])
        x = Y[:, None, :] + sigma * RNG.standard_normal((len(th), n_mc, M))
        d2 = ((x[:, :, None, :] - Yk[None, None]) ** 2).sum(-1)
        log_m = logsumexp(logwk[None, None] - d2 / (2 * sigma**2), axis=-1)
        log_p = -((x - Y[:, None, :]) ** 2).sum(-1) / (2 * sigma**2)
        f = (log_p - log_m).mean(1)
        w = w * np.exp(f - f.max())
        w /= w.sum()
    return w


def greedy_packing(z, eps=1.0):
    """Indices of a maximal eps-separated subset of the rows of z, in random order."""
    centers = []
    for i in RNG.permutation(len(z)):
        if not centers or np.min(((z[centers] - z[i]) ** 2).sum(1)) > eps**2:
            centers.append(i)
    return np.array(centers)


def sample_cells(cand, z, centers, n):
    """Equal mass per packing cell: pick a cell uniformly, then a candidate inside it."""
    d2 = ((z[:, None, :] - z[centers][None]) ** 2).sum(-1)
    cell = d2.argmin(1)
    members = [np.flatnonzero(cell == j) for j in range(len(centers))]
    picks = RNG.integers(len(centers), size=n)
    return cand[[RNG.choice(members[j]) for j in picks]]


# fine candidate set, uniform in theta
FG = 120
_ax = [np.linspace(*BOX[i], FG) for i in range(D)]
CAND = np.stack(np.meshgrid(*_ax, indexing="ij"), -1).reshape(-1, D)
CAND_Y = y(CAND)

# coarse grid for the rough p*
G = 22
_gx = [np.linspace(*BOX[i], G) for i in range(D)]
TH = np.stack(np.meshgrid(*_gx, indexing="ij"), -1).reshape(-1, D)

Ymean = CAND_Y.mean(0)
_, _, Vt = np.linalg.svd(CAND_Y - Ymean, full_matrices=False)


def proj(yy):
    return (np.asarray(yy) - Ymean) @ Vt[:2].T


N_SAMP = 1500
RESULTS = {}
for sigma in SIGMAS:
    print(f"sigma={sigma}: p* ...")
    w = grid_ba(TH, sigma)
    mask = w > 0.2 / np.sqrt(len(TH))
    atoms, atom_w = TH[mask], w[mask] / w[mask].sum()
    jeff = CAND[RNG.choice(len(CAND), N_SAMP, p=(s := sqrt_det_g(CAND, sigma)) / s.sum())]
    z = CAND_Y / sigma
    centers = greedy_packing(z)
    bprime = sample_cells(CAND, z, centers, N_SAMP)
    print(f"  {len(atoms)} atoms, {len(centers)} packing cells")
    RESULTS[sigma] = dict(atoms=atoms, atom_w=atom_w, jeff=jeff, bprime=bprime, ncell=len(centers))


def draw(space):
    fig, axs = plt.subplots(len(SIGMAS), 2, figsize=(8.6, 7.4), sharex=True, sharey=True)
    for r, sigma in enumerate(SIGMAS):
        res = RESULTS[sigma]
        for k, (key, title) in enumerate(
            [("jeff", "B at c=0: Jeffreys, ∝ √det g"), ("bprime", "B′: equal mass per resolvable cell")]
        ):
            ax = axs[r, k]
            pts, atoms = res[key], res["atoms"]
            size = 70 * np.sqrt(res["atom_w"] / res["atom_w"].max())
            if space == "param":
                bg, q, a = CAND[::7], pts, atoms
            else:
                bg, q, a = proj(CAND_Y[::7]), proj(y(pts)), proj(y(atoms))
            ax.scatter(bg[:, 0], bg[:, 1], s=1, c="0.88", zorder=0)
            ax.scatter(q[:, 0], q[:, 1], s=4, c="C0", alpha=0.3, zorder=1)
            ax.scatter(a[:, 0], a[:, 1], s=size, c="crimson", edgecolor="k", lw=0.4, zorder=3)
            ax.tick_params(labelsize=7)
            if r == 0:
                ax.set_title(title, fontsize=9.5)
            if k == 0:
                lab = r"$\theta_2$" if space == "param" else "pred PC2"
                ax.set_ylabel(f"σ = {sigma}\n{lab}")
            if k == 1:
                ax.text(0.98, 0.02, f"{res['ncell']} cells", transform=ax.transAxes,
                        ha="right", fontsize=7.5, color="0.3")
            if r == len(SIGMAS) - 1:
                ax.set_xlabel(r"$\theta_1$" if space == "param" else "pred PC1")
    sub = "parameter space" if space == "param" else "prediction space (2 stiffest directions)"
    fig.suptitle(f"Jeffreys vs B′, exp-decay d=2 — {sub}\n(red = rough p* atoms, blue = nature's samples)",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = OUT / f"q_bprime_{space}.png"
    fig.savefig(path, dpi=130)
    print("wrote", path)


draw("param")
draw("pred")

# ------------------------------------------------- square hypercone, D = 26, sigma = 1
# Cross-section at theta_1 is a (D-1)-cube of side s = theta_1 / L in noise units.
DH, L = 26, 50.0
d = DH - 1
theta1 = np.linspace(0.25, L, 400)
s = theta1 / L


def log_kappa(j):
    """log volume of the unit j-ball."""
    return 0.5 * j * log(pi) - lgamma(0.5 * j + 1)


def log_steiner(si):
    """log vol(cube_s ⊕ unit ball) in d dims: sum_k C(d,k) s^k kappa_{d-k}."""
    terms = [log(comb(d, k)) + k * log(si) + log_kappa(d - k) for k in range(d + 1)]
    return float(np.logaddexp.reduce(terms))


def log_gv(si):
    """log of a lower bound on the 1-packing number of the s-cube: a binary code on its
    corners with Hamming distance >= ceil(1/s^2) (Gilbert-Varshamov)."""
    kmin = ceil(1.0 / si**2)
    if kmin > d:
        return 0.0
    vol = float(np.logaddexp.reduce([log(comb(d, i)) for i in range(kmin)]))
    return max(0.0, d * log(2) - vol)


_yy = np.linspace(-9, 9, 4001)


def capacity_binary(a):
    """Mutual information (nats) of an equiprobable +-a input in unit Gaussian noise; the
    capacity of a scalar channel with input range 2a when 2a is below Smith's threshold."""
    phi = lambda u: np.exp(-0.5 * u**2) / np.sqrt(2 * pi)
    p = 0.5 * (phi(_yy - a) + phi(_yy + a))
    h_y = -np.trapezoid(p * np.log(np.clip(p, 1e-300, None)), _yy)
    return h_y - 0.5 * log(2 * pi * np.e)


curves = {
    "volume: Jeffreys (B at c=0)": d * np.log(s),
    "B′ as first defined: pairwise packing at 1 noise unit (coding bound; tip at most this high)": np.array([log_gv(x) for x in s]),
    "noise-tube volume ≈ NML, so ≈ p_proj": np.array([log_steiner(x) for x in s]),
    "e^capacity: reliably distinguishable profiles": d * np.array([capacity_binary(x / 2) for x in s]),
    "one count per axis below resolution (= p_U, p_ref here)": np.zeros_like(s),
}

fig, ax = plt.subplots(figsize=(8.6, 5.0))
for (label, logc), col in zip(curves.items(), ["C3", "C0", "C2", "C1", "0.4"], strict=True):
    rel = (logc - logc[-1]) / log(10)
    ax.plot(theta1, rel, color=col, lw=2, label=label)
ax.set_xlabel(r"$\theta_1$ (relevant coordinate; 50 = thick base, 0 = tip)")
ax.set_ylabel("log$_{10}$ density along $\\theta_1$, relative to the base")
ax.set_ylim(-20, 1)
ax.axvline(3, color="0.7", lw=0.8, ls=":")
ax.text(3.6, -19.2, "x = 3, the detective's\nlog reading", fontsize=7.5, color="0.4")
ax.legend(fontsize=8, frameon=False, loc="lower right")
ax.set_title("Square hypercone, D = 26, σ = 1: where nature's mass sits along θ₁\n"
             "under five ways of counting distinguishable predictions", fontsize=10)
ax.tick_params(labelsize=8)
fig.tight_layout()
path = OUT / "q_bprime_hypercone.png"
fig.savefig(path, dpi=130)
print("wrote", path)
