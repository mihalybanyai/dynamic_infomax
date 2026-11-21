"""The capacity prior `p*` and its mis-budgeted copies (spec 002 §4.2).

Blahut–Arimoto on a candidate set placed by Fisher distance (points at most 0.5 Fisher
lengths apart at `sigma_eff`, seeded with the faces of `Theta`); beyond the sets'
reach, AtomicPriors.jl through `juliacall` (OQ-1). Stubs until the implementation
stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model
from infomax.priors002 import DiscretePrior


@dataclass(frozen=True)
class PStarResult:
    """A `p*` build: the prior, the capacity `C_N` (nats) and how it was built."""

    prior: DiscretePrior
    capacity: float
    candidates: np.ndarray
    masses: np.ndarray
    method: str  # "candidates" or "atomic"
    budget: float


def candidate_set(model: Model, spacing: float = 0.5, *, max_points: int = 10**6) -> np.ndarray:
    """Candidate states at most `spacing` Fisher lengths apart at `sigma_eff` (§4.2, F9).

    Seeded with the faces of `Theta`; shape (n, D).
    """
    raise NotImplementedError("spec 002 §4.2: candidate_set")


def build_pstar(
    model: Model,
    *,
    budget: float | None = None,
    spacing: float = 0.5,
    candidates: np.ndarray | None = None,
    method: str = "auto",
    literal_nfold: bool = False,
    tol: float = 1e-8,
) -> PStarResult:
    """`p*` of the budget-`budget` channel (default: the model's `N`), at `sigma/sqrt(budget)`.

    `budget != model.N` gives the mis-budgeted `p*_M` (§2.2). `candidates` overrides the
    candidate set, so two builds can share one (T16(c), T19(a)). `literal_nfold=True`
    builds the explicit `N`-fold channel instead of the `sigma_eff` reduction (T7c).
    """
    raise NotImplementedError("spec 002 §4.2: build_pstar")
