"""Produce the BA convergence-to-Jeffreys plot referenced in
`docs/000-static-infomax-fig1/README.md` (testing notes section).

Runs BA at m=100 for the default budget, logging KS distance to the
Jeffreys CDF every K iterations. Output:
`docs/000-static-infomax-fig1/figures/t4_ba_ks_vs_iter.png`.

Run directly:
    uv run python docs/000-static-infomax-fig1/figures/_make_t4_convergence.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import logsumexp

from infomax.atoms import extract_atoms
from infomax.ba import _f_kl_from_masses
from infomax.jeffreys import jeffreys_bernoulli_cdf
from infomax.likelihood import binomial_log_likelihood, cell_centred_grid
from infomax.prior import GridPrior

N_THETA = 1000
M = 100
TAU_MAX = 500_000
ALPHA = 2.0
LOG_STRIDE = 5_000

THIS_DIR = Path(__file__).resolve().parent
OUT = THIS_DIR / "t4_ba_ks_vs_iter.png"


def _step_cdf_at(theta_q: np.ndarray, atom_th: np.ndarray, atom_m: np.ndarray) -> np.ndarray:
    order = np.argsort(atom_th)
    sth = atom_th[order]
    sm = atom_m[order]
    cum = np.cumsum(sm)
    idx = np.searchsorted(sth, theta_q, side="right")
    return np.where(idx == 0, 0.0, cum[np.clip(idx - 1, 0, len(cum) - 1)])


def main() -> None:
    grid = cell_centred_grid(N_THETA)
    log_lik = binomial_log_likelihood(grid, M)
    theta_dense = np.linspace(0.0, 1.0, 10_000)
    cdf_j = jeffreys_bernoulli_cdf(theta_dense)

    p = np.full(N_THETA, 1.0 / N_THETA)
    log_p = np.log(p)

    iters: list[int] = []
    ks: list[float] = []

    for tau in range(TAU_MAX + 1):
        _, f_kl, mi = _f_kl_from_masses(p, log_lik)
        if tau % LOG_STRIDE == 0:
            atoms = extract_atoms(GridPrior(grid, p))
            atom_th = np.array([a.theta for a in atoms])
            atom_m = np.array([a.mass for a in atoms])
            cdf_atoms = _step_cdf_at(theta_dense, atom_th, atom_m)
            ks_val = float(np.max(np.abs(cdf_atoms - cdf_j)))
            iters.append(tau)
            ks.append(ks_val)
        log_p_try = ALPHA * f_kl + log_p
        log_p_try = log_p_try - logsumexp(log_p_try)
        p_try = np.exp(log_p_try)
        _, _, mi_try = _f_kl_from_masses(p_try, log_lik)
        if mi_try < mi:
            log_p_try = f_kl + log_p
            log_p_try = log_p_try - logsumexp(log_p_try)
        log_p = log_p_try
        p = np.exp(log_p)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(iters, ks, marker="o", markersize=3, lw=1)
    ax.axhline(0.05, color="C3", ls="--", lw=1, label="T4 original bound (0.05)")
    ax.axhline(0.15, color="C2", ls="--", lw=1, label="T4 loosened bound (0.15)")
    ax.set_xlabel("BA iteration")
    ax.set_ylabel("KS distance to Jeffreys CDF")
    ax.set_title(
        f"T4 convergence: BA prior at m={M}, $N_\\theta$={N_THETA}, α={ALPHA}"
    )
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
