"""Blahut-Arimoto loop for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §1.4, §3.4. The loop is fully
deterministic (uniform init, deterministic likelihood, deterministic
fixed-point updates), so no RNG is threaded through the API — see the
`manage-randomness` skill, rule 7: the API needs what it actually uses.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp

from infomax.prior import GridPrior


@dataclass(frozen=True)
class BAResult:
    """Output of one BA run."""

    prior: GridPrior
    mi: float                  # achieved MI in nats
    f_kl: np.ndarray           # f_KL(theta_i; prior), shape (n_theta,)
    mi_history: np.ndarray     # I_tau per iter; len = n_iters+1 normally, n_iters+2 on tau_max exhaustion (DD6); for T6
    n_iters: int               # iterations taken
    converged: bool            # whether Csiszar gap max(f_kl) - mi < eps_i within tau_max


def _f_kl_from_masses(
    masses: np.ndarray, log_likelihood: np.ndarray, P: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return (log_p_x, f_KL_i, I_τ) for a prior of given masses.

    Implements the per-iteration arithmetic of spec §3.4 directly:

        p(x)         = Σ_i p_i p(x|θ_i)            (linear combination)
        f_KL_i       = Σ_x p(x|θ_i) * (log p(x|θ_i) − log p(x))
        I_τ          = Σ_i p_i * f_KL_i

    The marginal goes through the direct sum, not `logsumexp` — for
    normalised masses with full support this is numerically clean, and it
    matches the per-bit arithmetic the test's independent recomputation
    uses (T10 demands 1e-12 agreement).

    `P` = exp(log_likelihood) is precomputed by the caller and passed in
    to avoid recomputing it on every iteration of the BA loop.
    """
    p_x = masses @ P
    log_p_x = np.log(p_x)
    f_kl = np.einsum("ix,ix->i", P, log_likelihood - log_p_x)
    mi = float(masses @ f_kl)
    return log_p_x, f_kl, mi


def blahut_arimoto(
    log_likelihood: np.ndarray,
    theta_grid: np.ndarray,
    *,
    init: np.ndarray | None = None,
    alpha: float = 2.0,
    eps_i: float = 1e-12,
    tau_min: int = 10,
    tau_max: int = 500_000,
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
            normalised, shape (n_theta,). `None` ⇒ uniform. Raises
            `ValueError` if not finite, strictly positive, and normalised
            (sum within 1e-8 of 1).
        alpha: overrelaxation step-size per spec §3.4 (default 2.0). `α = 1`
            is vanilla BA (monotone, slow); `α > 1` accelerates near
            multi-atom optima. Steps that would decrease MI fall back to
            `α = 1` so monotonicity (T6) is preserved.
        eps_i: convergence tolerance on the Csiszar gap max_i(f_KL_i) − I_τ
            in nats (default 1e-12). See DD3 in docs/ for why this is
            stricter than the spec's |ΔI| criterion.
        tau_min: minimum iterations before checking convergence (default 10).
        tau_max: hard iteration cap (default 500_000).

    Returns:
        BAResult with the converged prior, achieved MI in nats, the final
        f_KL(theta) vector, the full MI history, and convergence
        diagnostics.

    Spec §3.4.
    """
    theta = np.asarray(theta_grid, dtype=np.float64)
    n_theta = theta.size
    if init is None:
        p = np.full(n_theta, 1.0 / n_theta, dtype=np.float64)
    else:
        p = np.asarray(init, dtype=np.float64).copy()
        if p.shape != (n_theta,):
            raise ValueError(
                f"init shape {p.shape} does not match grid {(n_theta,)}"
            )
        if not (np.isfinite(p).all() and np.all(p > 0)):
            raise ValueError("init must be strictly positive and finite")
        if abs(p.sum() - 1.0) > 1e-8:
            raise ValueError(
                f"init must sum to 1 within 1e-8 (got {p.sum():.6g})"
            )
    P = np.exp(log_likelihood)  # precomputed once; passed into _f_kl_from_masses
    log_p = np.log(p)

    history: list[float] = []
    f_kl = np.zeros(n_theta)
    mi = 0.0
    converged = False
    tau = 0
    # Convergence criterion: Csiszár's tight bound
    #   |MI* − I_τ| ≤ max_i f_KL_i − I_τ
    # is strictly sharper than the spec's `|I_{τ+1} − I_τ| < ε_I`. The
    # `|ΔI|` criterion in spec §3.4 plateaus before masses settle (MI is
    # quadratically insensitive to small mass perturbations near the
    # optimum), so it stops too early for the test suite's 1e-6 mass
    # tolerance. Csiszár's gap directly bounds distance-to-optimum in MI;
    # the spec's looser criterion is a candidate for a follow-up
    # refinement.
    for tau in range(tau_max + 1):
        _, f_kl, mi = _f_kl_from_masses(p, log_likelihood, P)
        history.append(mi)
        csiszar_gap = float(np.max(f_kl)) - mi
        if tau >= tau_min and csiszar_gap < eps_i:
            converged = True
            break
        # Overrelaxed step (spec §3.4): try alpha * f_kl, fall back to
        # alpha = 1 if the step would decrease MI. The fallback is what
        # preserves the spec's monotonicity guarantee (T6) under
        # arbitrary alpha ≥ 1.
        log_p_try = alpha * f_kl + log_p
        log_p_try = log_p_try - logsumexp(log_p_try)
        if alpha != 1.0:
            p_try = np.exp(log_p_try)
            _, _, mi_try = _f_kl_from_masses(p_try, log_likelihood, P)
            if mi_try < mi:
                log_p_try = f_kl + log_p
                log_p_try = log_p_try - logsumexp(log_p_try)
        log_p = log_p_try
        p = np.exp(log_p)
    else:
        # tau_max exhausted without breaking. The trailing `p = exp(log_p)`
        # above advanced the prior past the (f_kl, mi) we appended; recompute
        # so the returned (prior, mi, f_kl, history[-1]) are mutually
        # consistent and T6/T10 still hold.
        _, f_kl, mi = _f_kl_from_masses(p, log_likelihood, P)
        history.append(mi)
        tau = tau_max

    return BAResult(
        prior=GridPrior(theta, p),
        mi=mi,
        f_kl=f_kl,
        mi_history=np.asarray(history, dtype=np.float64),
        n_iters=tau,
        converged=converged,
    )


def compute_f_kl(prior: GridPrior, log_likelihood: np.ndarray) -> np.ndarray:
    """f_KL(theta_i; prior) = D_KL[ p(.|theta_i) || p(.) ].

    Used inside BA and exposed because §1.3's optimality condition
    (f_KL = MI on support, < MI off support) is asserted directly in
    test T2.
    """
    P = np.exp(log_likelihood)
    _, f_kl, _ = _f_kl_from_masses(prior.masses(), log_likelihood, P)
    return f_kl
