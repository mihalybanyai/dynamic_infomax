"""
Exploratory visualisation of candidate q-families for spec 002 (OQ-2).

UNTRUSTED / exploratory — lives in notes/, NOT a spec implementation. It uses a quick
standalone exp-decay model + a rough grid-BA p* at d=2, purely to *picture* how
different "cooperativeness" families place nature's data relative to p*'s atoms, so the
choice of q-family (OQ-2) can be a look-and-pick rather than a blind one.

Two candidate families are drawn:
  (A) atom-anchored (p*-relative): coop = blobs ON p*'s atoms; non = the Voronoi gaps.
  (B) geometry-relative (Fisher):  coop = uniform in Fisher volume (Jeffreys pullback);
                                    non = the low-Fisher boundary / thin end.
Each is shown across the cooperativeness knob c in {0, 0.5, 1}, in both parameter space
(theta_1, theta_2) and a 2D prediction-space projection (PCA of the manifold image).

Run:  uv run python notes/q-family-viz/q_family_viz.py
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

RNG = np.random.default_rng(20260605)
OUT = Path(__file__).parent

# --------------------------------------------------------------------------- model
D = 2
M = 12
TIMES = np.linspace(1.0, 5.0, M)
SIGMA = 0.04
BOX = np.array([[-1.0, 3.0], [-1.0, 3.0]])  # theta box; decay rate k_mu = e^{-theta_mu}


def y(theta):
    """Exp-decay mean map. theta (..., D) -> y (..., M).  k = e^{-theta}, a_mu = 1/D."""
    theta = np.asarray(theta, dtype=float)
    k = np.exp(-theta)
    return np.exp(-k[..., :, None] * TIMES).mean(axis=-2)


def fim(theta):
    """Fisher information g_{mu nu} at one theta, via central differences of y."""
    eps = 1e-5
    J = np.empty((D, M))
    for mu in range(D):
        dp = theta.copy(); dp[mu] += eps
        dm = theta.copy(); dm[mu] -= eps
        J[mu] = (y(dp) - y(dm)) / (2 * eps)
    return (J @ J.T) / SIGMA**2


def sqrt_det_g(grid):
    out = np.empty(len(grid))
    for i, t in enumerate(grid):
        out[i] = np.sqrt(max(np.linalg.det(fim(t)), 1e-300))
    return out


def logsumexp(a, axis=None):
    m = np.max(a, axis=axis, keepdims=True)
    return (m + np.log(np.exp(a - m).sum(axis=axis, keepdims=True))).squeeze(axis)


# --------------------------------------------------------------------- grid + p* (BA)
G = 22
axes = [np.linspace(*BOX[i], G) for i in range(D)]
TH = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, D)  # (G^D, D)
Y = y(TH)                                                                 # (G^D, M)


def grid_ba(n_iter=120, n_mc=24):
    """Rough Blahut-Arimoto for the capacity prior on the grid (MC continuous f_KL)."""
    w = np.full(len(TH), 1.0 / len(TH))
    for _ in range(n_iter):
        keep = w > 1e-6
        Yk, logwk = Y[keep], np.log(w[keep])
        x = Y[:, None, :] + SIGMA * RNG.standard_normal((len(TH), n_mc, M))  # (N, mc, M)
        d2 = ((x[:, :, None, :] - Yk[None, None, :, :]) ** 2).sum(-1)        # (N, mc, K)
        log_m = logsumexp(logwk[None, None, :] - d2 / (2 * SIGMA**2), axis=-1)
        log_pi = -((x - Y[:, None, :]) ** 2).sum(-1) / (2 * SIGMA**2)        # (N, mc)
        f_kl = (log_pi - log_m).mean(1)
        w = w * np.exp(f_kl - f_kl.max())
        w /= w.sum()
    return w


print("running grid-BA for p* ...")
W = grid_ba()
atom_mask = W > (0.2 / np.sqrt(len(TH)))     # keep meaningfully-weighted cells
ATOMS = TH[atom_mask]
ATOM_W = W[atom_mask] / W[atom_mask].sum()
ATOM_Y = y(ATOMS)
print(f"p* has ~{len(ATOMS)} atoms")

# --------------------------------------------------------------- prediction-space PCA
Ymean = Y.mean(0)
_, _, Vt = np.linalg.svd(Y - Ymean, full_matrices=False)
P2 = Vt[:2].T                                # (M, 2): project y -> 2 stiffest directions
proj = lambda yy: (np.asarray(yy) - Ymean) @ P2

N_SAMP = 1200


def resample(grid, weights, n):
    weights = np.clip(weights, 0, None)
    idx = RNG.choice(len(grid), size=n, p=weights / weights.sum())
    jitter = (BOX[:, 1] - BOX[:, 0]) / G * RNG.standard_normal((n, D)) * 0.5
    return np.clip(grid[idx] + jitter, BOX[:, 0], BOX[:, 1])


# ----- family A: atom-anchored (p*-relative) -----
def fisher_gap_weight(grid):
    """High where a grid point is FAR (in prediction/noise units) from every p* atom."""
    d = np.linalg.norm(y(grid)[:, None, :] - ATOM_Y[None, :, :], axis=-1) / SIGMA
    return d.min(1) ** 2                      # squared min Fisher-ish distance to nearest atom


def sample_A(c, n):
    coop = ATOMS[RNG.choice(len(ATOMS), n, p=ATOM_W)] + \
        (BOX[:, 1] - BOX[:, 0]) / G * RNG.standard_normal((n, D)) * 0.6
    coop = np.clip(coop, BOX[:, 0], BOX[:, 1])
    non = resample(TH, fisher_gap_weight(TH), n)
    take_non = RNG.random(n) < c
    return np.where(take_non[:, None], non, coop)


# ----- family B: geometry-relative (Fisher) -----
SDG = sqrt_det_g(TH)


def sample_B(c, n):
    coop = resample(TH, SDG, n)                       # ∝ sqrt(det g)  (Jeffreys pullback)
    non = resample(TH, 1.0 / (SDG + SDG.mean()), n)   # ∝ 1/sqrt(det g): low-Fisher edge/thin end
    take_non = RNG.random(n) < c
    return np.where(take_non[:, None], non, coop)


FAMILIES = {"A: atom-anchored (p*-relative)": sample_A,
            "B: geometry-relative (Fisher)": sample_B}
CS = [0.0, 0.5, 1.0]


def make_figure(space):
    fig, axs = plt.subplots(len(FAMILIES), len(CS), figsize=(11, 7.2), sharex=True, sharey=True)
    for r, (name, sampler) in enumerate(FAMILIES.items()):
        for k, c in enumerate(CS):
            ax = axs[r, k]
            th = sampler(c, N_SAMP)
            if space == "param":
                ax.scatter(TH[:, 0], TH[:, 1], s=2, c="0.9", zorder=0)        # grid
                ax.scatter(th[:, 0], th[:, 1], s=4, c="C0", alpha=0.25, zorder=1)
                ax.scatter(ATOMS[:, 0], ATOMS[:, 1], s=80 * np.sqrt(ATOM_W / ATOM_W.max()),
                           c="crimson", edgecolor="k", lw=0.4, zorder=3)
                if r == len(FAMILIES) - 1: ax.set_xlabel(r"$\theta_1$")
                if k == 0: ax.set_ylabel(name.split(":")[0] + "\n" + r"$\theta_2$")
            else:
                py = proj(Y); pq = proj(y(th)); pa = proj(ATOM_Y)
                ax.scatter(py[:, 0], py[:, 1], s=2, c="0.9", zorder=0)
                ax.scatter(pq[:, 0], pq[:, 1], s=4, c="C0", alpha=0.25, zorder=1)
                ax.scatter(pa[:, 0], pa[:, 1], s=80 * np.sqrt(ATOM_W / ATOM_W.max()),
                           c="crimson", edgecolor="k", lw=0.4, zorder=3)
                if r == len(FAMILIES) - 1: ax.set_xlabel("pred PC1")
                if k == 0: ax.set_ylabel(name.split(":")[0] + "\npred PC2")
            if r == 0: ax.set_title(f"c = {c:g}")
            ax.tick_params(labelsize=7)
    sub = "parameter space" if space == "param" else "prediction space (2 stiffest dirs)"
    fig.suptitle(f"Candidate q-families vs cooperativeness c — {sub}\n"
                 f"(red = p* atoms, blue = q_c samples; exp-decay d=2, σ={SIGMA})",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = OUT / f"q_families_{space}.png"
    fig.savefig(path, dpi=130)
    print("wrote", path)


make_figure("param")
make_figure("pred")
print("done.")
