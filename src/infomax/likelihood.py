"""Binomial likelihood for the static infomax problem.

Spec: specs/000-static-infomax-fig1.md §1.1, §3.2.
"""
from __future__ import annotations

import numpy as np


def cell_centred_grid(n_theta: int) -> np.ndarray:
    """Uniform cell-centred grid on [0, 1] with n_theta cells.

    Spec §3.1: theta_i = (i + 1/2) / n_theta for i = 0, ..., n_theta - 1.
    Avoids the endpoints 0 and 1 where the Bernoulli log-likelihood is
    singular for some x.
    """
    raise NotImplementedError


def binomial_log_likelihood(theta_grid: np.ndarray, m: int) -> np.ndarray:
    """log p(x | theta, m) for x in {0, ..., m}, all theta in the grid.

    Returns an array of shape (n_theta, m + 1) in nats.

    Spec §3.2.
    """
    raise NotImplementedError


def binomial_likelihood(theta_grid: np.ndarray, m: int) -> np.ndarray:
    """p(x | theta, m) — exponential of `binomial_log_likelihood`.

    Returns an array of shape (n_theta, m + 1).
    """
    raise NotImplementedError
