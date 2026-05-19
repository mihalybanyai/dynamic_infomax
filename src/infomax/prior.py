"""Prior abstraction for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §3.3. The interface is deliberately
narrow and queries the likelihood / f_KL through callables so each prior
can evaluate them on its own support (grid cells now; atom positions or
particle samples later) without a fixed grid-shaped buffer baked into the
interface.

Note on `updated()`: the spec's §3.3 draft described a per-subclass
`updated()` method (BA step for GridPrior; gradient for AtomicPrior; SMC
for ContinuousPrior). For `GridPrior`, the BA loop needs direct access to
`log_p` arrays, line-search state, and history bookkeeping that do not fit
through a simple `f_kl_fn` callable. The update is therefore owned by
`blahut_arimoto` in `ba.py`. The `updated()` method is removed from the
protocol here; it will be re-introduced for future prior types (e.g.
`AtomicPrior`) where the update step is genuinely self-contained and can
plug into a shared loop driver.
"""
from __future__ import annotations

from typing import Callable, Protocol

import numpy as np

LogLikelihoodFn = Callable[[np.ndarray], np.ndarray]
"""Maps a theta-vector of shape (k,) to log p(x | theta) of shape (k, n_x)."""


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


class GridPrior:
    """Prior as a PMF over a fixed cell-centred theta grid (spec §3.1)."""

    def __init__(self, theta_grid: np.ndarray, masses: np.ndarray) -> None:
        theta = np.asarray(theta_grid, dtype=np.float64)
        m = np.asarray(masses, dtype=np.float64)
        if theta.shape != m.shape:
            raise ValueError(
                f"theta_grid {theta.shape} and masses {m.shape} must align"
            )
        if not (np.isfinite(m).all() and np.all(m >= 0)):
            raise ValueError("masses must be non-negative and finite")
        if abs(m.sum() - 1.0) > 1e-8:
            raise ValueError(
                f"masses must sum to 1 within 1e-8 (got {m.sum():.6g})"
            )
        self._theta_grid = theta
        self._masses = m

    @classmethod
    def uniform(cls, theta_grid: np.ndarray) -> "GridPrior":
        """Uniform initialisation (spec §1.4, §3.4)."""
        theta = np.asarray(theta_grid, dtype=np.float64)
        return cls(theta, np.full_like(theta, 1.0 / theta.size))

    def support(self) -> np.ndarray:
        return self._theta_grid

    def masses(self) -> np.ndarray:
        return self._masses

    def expected_data(self, log_likelihood_fn: LogLikelihoodFn) -> np.ndarray:
        log_lik = log_likelihood_fn(self._theta_grid)
        return self._masses @ np.exp(log_lik)
