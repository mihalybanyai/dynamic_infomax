"""Atom extraction from a converged grid prior.

Spec: specs/000-static-infomax-fig1.md §3.5. Deferred choice DC-2 — the
threshold and adjacency criterion are heuristic; grid-invariance under
refinement (test T5) is the substantive property.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.prior import GridPrior


@dataclass(frozen=True)
class Atom:
    """One detected atom: mass-weighted centroid and total mass of a run."""

    theta: float
    mass: float


def extract_atoms(prior: GridPrior, p_thresh: float | None = None) -> list[Atom]:
    """Detect atoms as runs of adjacent grid cells with mass > p_thresh.

    Default p_thresh = 1 / (10 * n_theta) per spec §3.5.

    Each detected run is reduced to (mass-weighted centroid, total mass).
    """
    raise NotImplementedError


def count_support(prior: GridPrior, floor: float = 1e-12) -> int:
    """Permissive count of support cells: `#{ i : p_i > floor }`.

    Spec §4 T3: this is `K_upper`, an upper bound on the true atom count
    used by the capacity-bound test. Decoupled from `extract_atoms` (and
    its DC-2 heuristic) — `floor` is set well below any real support mass.
    """
    raise NotImplementedError
