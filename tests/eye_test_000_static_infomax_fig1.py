"""Eye test for spec 000 — manual gate before the full suite.

Produces a single figure for human review: the converged BA prior at
`m = 2`, `N_θ = 21`, after 10 000 iterations from uniform initialisation.
The reviewer checks that the plot shows the three-atom structure
expected of the Bernoulli m=2 capacity-achieving prior (a central
atom plus two off-centre atoms, roughly symmetric about θ=½).

This is NOT a pytest test — there are no quantitative assertions. Run
it directly:

    uv run python tests/eye_test_000_static_infomax_fig1.py

Output figure is written to
`experiments/000-static-fig1/figures/eye_test_m2_n100.png`. Approval
status is recorded in `experiments/000-static-fig1/CODEGEN_LOG.md`.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from infomax.ba import blahut_arimoto
from infomax.likelihood import binomial_log_likelihood, cell_centred_grid

N_THETA = 21
M = 2
N_ITERATIONS = 10_000

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURE_PATH = (
    REPO_ROOT / "experiments" / "000-static-fig1" / "figures" / "eye_test_m2_n21.png"
)


def main() -> None:
    grid = cell_centred_grid(N_THETA)
    log_lik = binomial_log_likelihood(grid, m=M)
    # Fixed iteration count: eps_i effectively disabled so BA runs the
    # full 1000 iterations regardless of convergence.
    result = blahut_arimoto(
        log_lik, grid, eps_i=0.0, tau_min=N_ITERATIONS, tau_max=N_ITERATIONS
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    masses = result.prior.masses()
    ax.stem(grid, masses, basefmt=" ", linefmt="C0-", markerfmt="C0o")
    ax.set_xlabel(r"$\theta$")
    ax.set_ylabel(r"$p^*(\theta_i)$")
    ax.set_title(
        f"Eye test — BA prior at m={M}, $N_\\theta$={N_THETA}, "
        f"{N_ITERATIONS} iterations\n"
        f"MI* ≈ {result.mi:.4f} nats   (iters used: {result.n_iters}, "
        f"converged: {result.converged})"
    )
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, max(0.05, float(masses.max()) * 1.1))
    ax.grid(True, alpha=0.3)

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=150)
    plt.close(fig)
    print(f"figure written to {FIGURE_PATH}")
    print(f"MI = {result.mi:.6f} nats; max mass = {masses.max():.4f}")


if __name__ == "__main__":
    main()
