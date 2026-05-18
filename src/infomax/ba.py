"""Blahut-Arimoto loop for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §1.4, §3.4. The loop is fully
deterministic (uniform init, deterministic likelihood, deterministic
fixed-point updates), so no RNG is threaded through the API — see the
`manage-randomness` skill, rule 7: the API needs what it actually uses.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.prior import GridPrior


@dataclass(frozen=True)
class BAResult:
    """Output of one BA run."""

    prior: GridPrior
    mi: float                  # achieved MI in nats
    f_kl: np.ndarray           # f_KL(theta_i; prior), shape (n_theta,)
    mi_history: np.ndarray     # I_tau for tau = 0, 1, ..., n_iters; for T6
    n_iters: int               # iterations taken
    converged: bool            # whether |I_{tau+1} - I_tau| < eps_I within tau_max


def blahut_arimoto(
    log_likelihood: np.ndarray,
    theta_grid: np.ndarray,
    *,
    init: np.ndarray | None = None,
    eps_i: float = 1e-10,
    tau_min: int = 10,
    tau_max: int = 5000,
) -> BAResult:
    """Find the MI-maximising prior on the grid implied by `log_likelihood`.

    Implements the log-space BA loop of spec §3.4. When `init is None`
    (the default), starts from a uniform `GridPrior(theta_grid)`;
    otherwise uses the supplied strictly-positive probability vector as
    the starting prior (used by tests T2c init-invariance and T7b
    perturbed-degenerate). Records `I_tau` at each step in `mi_history`
    so T6 (monotonicity) can be checked without re-running the loop.

    Args:
        log_likelihood: log p(x | theta_i), shape (n_theta, n_x).
        theta_grid: cell-centred grid, shape (n_theta,); used to construct
            the returned `GridPrior`.
        init: optional initial prior over the grid; strictly positive,
            normalised, shape (n_theta,). `None` ⇒ uniform.
        eps_i: convergence tolerance on |I_{tau+1} - I_tau| in nats.
        tau_min: minimum iterations before checking convergence.
        tau_max: hard iteration cap.

    Returns:
        BAResult with the converged prior, achieved MI in nats, the final
        f_KL(theta) vector, the full MI history, and convergence
        diagnostics.

    Spec §3.4.
    """
    raise NotImplementedError


def compute_f_kl(prior: GridPrior, log_likelihood: np.ndarray) -> np.ndarray:
    """f_KL(theta_i; prior) = D_KL[ p(.|theta_i) || p(.) ].

    Used inside BA and exposed because §1.3's optimality condition
    (f_KL = MI on support, < MI off support) is asserted directly in
    test T2.
    """
    raise NotImplementedError
