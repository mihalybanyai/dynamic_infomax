"""The prior interface shared by spec 002's cast.

Spec: specs/002-foreign-q-prediction.md §2.2, §4.2, §4.4. Every prior of the cast,
discrete (`p*`, `p_lat` on a candidate set), sample-backed (`p_proj`) or continuous
(`p_J`, `p_U`, `p_LN`, `p_LN^*`, `p_ref`), exposes the methods below, so that the
scores of §4.4 treat them alike. Stubs until the implementation stage.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np

from infomax.models import Model


class Prior002(Protocol):
    """What the scores and natures need from a prior."""

    name: str

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """`n` states drawn from the prior, shape (n, D); its own world's sampler."""
        ...

    def log_marginal(self, model: Model, xbar: np.ndarray) -> np.ndarray:
        """`log m_pi(xbar)` at `sigma_eff`, shape (...,) for `xbar` (..., m_out)."""
        ...

    def log_predictive(
        self, model: Model, x_prime: np.ndarray, xbar: np.ndarray
    ) -> np.ndarray:
        """`log m_pi(x' | xbar)`, the posterior predictive at noise `sigma` (§4.4)."""
        ...


class ContinuousPrior002(Prior002, Protocol):
    """Continuous priors (`p_J`, `p_U`, `p_LN`, `p_LN^*`, `p_ref`) also expose a density."""

    log_normaliser: float

    def log_density(self, theta: np.ndarray) -> np.ndarray:
        """Normalised log density on `Theta`, in the model's own coordinates."""
        ...


class DiscretePrior:
    """Atoms and weights: `p*`, the mis-budgeted `p*`, and `p_lat` on a candidate set."""

    def __init__(self, name: str, atoms: np.ndarray, weights: np.ndarray) -> None:
        raise NotImplementedError("spec 002 §4.2: DiscretePrior")


class CloudPrior:
    """A sample-backed prior: `p_proj`'s cloud of maximum-likelihood estimates (§4.2)."""

    def __init__(self, name: str, atoms: np.ndarray) -> None:
        raise NotImplementedError("spec 002 §4.2: CloudPrior")
