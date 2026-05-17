"""Prior abstraction for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §3.3. The interface is deliberately
narrow and queries the likelihood / f_KL through callables so each prior
can evaluate them on its own support (grid cells now; atom positions or
particle samples later) without a fixed grid-shaped buffer baked into the
interface. Per the spec, the per-subclass `updated()` step is a different
algorithm underneath — BA for GridPrior; gradient on `(theta_a, lambda_a)`
for the future AtomicPrior; SMC for the future ContinuousPrior.
"""
from __future__ import annotations

from typing import Callable, Protocol

import numpy as np

LogLikelihoodFn = Callable[[np.ndarray], np.ndarray]
"""Maps a theta-vector of shape (k,) to log p(x | theta) of shape (k, n_x)."""

FKLFn = Callable[[np.ndarray], np.ndarray]
"""Maps a theta-vector of shape (k,) to f_KL(theta) of shape (k,)."""


class Prior(Protocol):
    """Minimal prior interface used by the BA loop and downstream tools."""

    def support(self) -> np.ndarray:
        """The theta values carrying probability mass."""
        ...

    def masses(self) -> np.ndarray:
        """Probability masses, summing to 1, aligned with `support()`."""
        ...

    def expected_data(self, log_likelihood_fn: LogLikelihoodFn) -> np.ndarray:
        """p(x) = sum_theta p(x|theta) p(theta).

        The callable is evaluated on this prior's own support.
        """
        ...

    def updated(self, f_kl_fn: FKLFn) -> "Prior":
        """One MI-improvement step; returns a new Prior (immutable update).

        BA for GridPrior; gradient on atoms for AtomicPrior; SMC for
        ContinuousPrior.
        """
        ...


class GridPrior:
    """Prior as a PMF over a fixed cell-centred theta grid (spec §3.1)."""

    def __init__(self, theta_grid: np.ndarray, masses: np.ndarray) -> None:
        raise NotImplementedError

    @classmethod
    def uniform(cls, theta_grid: np.ndarray) -> "GridPrior":
        """Uniform initialisation (spec §1.4, §3.4)."""
        raise NotImplementedError

    def support(self) -> np.ndarray:
        raise NotImplementedError

    def masses(self) -> np.ndarray:
        raise NotImplementedError

    def expected_data(self, log_likelihood_fn: LogLikelihoodFn) -> np.ndarray:
        raise NotImplementedError

    def updated(self, f_kl_fn: FKLFn) -> "GridPrior":
        """One Blahut-Arimoto step in log-space per spec §3.4:

            log_p_new = f_KL + log_p
            log_p_new -= logsumexp(log_p_new)
        """
        raise NotImplementedError
