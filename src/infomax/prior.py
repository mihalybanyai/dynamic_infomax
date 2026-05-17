"""Prior abstraction for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §3.3. The interface is deliberately
narrow so that later AtomicPrior (sub-grid atoms) and ContinuousPrior
(particle / SMC) can plug in behind it without changes downstream.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np


class Prior(Protocol):
    """Minimal prior interface used by the BA loop and downstream tools."""

    def support(self) -> np.ndarray:
        """The theta values carrying probability mass."""
        ...

    def masses(self) -> np.ndarray:
        """Probability masses, summing to 1, aligned with `support()`."""
        ...

    def expected_data(self, log_likelihood: np.ndarray) -> np.ndarray:
        """p(x) = sum_theta p(x|theta) p(theta), given log p(x|theta)."""
        ...

    def updated(self, f_kl: np.ndarray) -> "Prior":
        """One Blahut-Arimoto step; returns a new Prior (immutable update)."""
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

    def expected_data(self, log_likelihood: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def updated(self, f_kl: np.ndarray) -> "GridPrior":
        raise NotImplementedError
