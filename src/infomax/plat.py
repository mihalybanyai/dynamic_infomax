"""The latent information prior `p_lat` (spec 002 §4.2; Komaki 2011; Fogel & Feder 2024).

Maximises `I_pi(Theta; X_{N+1:N+M} | X_{1:N})` by the Blahut–Arimoto variant whose update
uses `f^(N+M) - f^(N)`; the spec's cast uses `M = 1`. The same build runs on the binomial
model of `infomax.models.binomial_model` for T18 and the second eye test. Stubs until the
implementation stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model
from infomax.priors002 import DiscretePrior


@dataclass(frozen=True)
class PLatResult:
    """A `p_lat` build with its two-sided bound on the minimax one-step loss."""

    prior: DiscretePrior
    conditional_capacity: float
    lower_bound: float
    upper_bound: float


def build_plat(
    model: Model,
    *,
    M: int = 1,
    spacing: float = 0.5,
    candidates: np.ndarray | None = None,
    tol: float = 1e-6,
) -> PLatResult:
    """`p_lat` at `(N, M)` on the model's candidate set, or on `candidates` (§4.2).

    `model.N = 0` is allowed: then `p_lat` is `p*` at budget `M` (T16(c)). No atoms are
    extracted: `prior.atoms` is the candidate set in the order given, `prior.weights` its
    weights. On a binomial model the divergences are the binomial ones (§5.3).
    """
    raise NotImplementedError("spec 002 §4.2: build_plat")


def conditional_divergence(result: PLatResult, model: Model, theta: np.ndarray, *, M: int = 1) -> np.ndarray:
    """Per-state `f^(N+M)(theta) - f^(N)(theta)` under `result.prior` (T16)."""
    raise NotImplementedError("spec 002 §4.2: conditional_divergence")
