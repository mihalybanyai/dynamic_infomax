"""The privileged-information priors `p_U` and `p_ref` (spec 002 §2.2, §3.5, §4.2).

`p_U` is uniform on `Theta` in its own coordinates (in `xi` in exp-decay). `p_ref` is
the ranked reference prior: `p_U` in the cones with the curvature knob off; otherwise
the two-group Berger–Bernardo formula of `[^3-schur]` by quadrature, once per ranking
in exp-decay. Stubs until the implementation stage.
"""
from __future__ import annotations

import numpy as np

from infomax.models import Model

RANKINGS: tuple[str, ...] = ("slowest", "fastest", "stiffest")
"""Exp-decay rankings (OQ-8); "stiffest" only at D = 2 (§4.2)."""


def build_uniform(model: Model):
    """`p_U`: uniform on `Theta` in its own coordinates (§4.2)."""
    raise NotImplementedError("spec 002 §4.2: build_uniform")


def build_pref(model: Model, ranking: str | None = None, *, transversal: np.ndarray | None = None):
    """`p_ref` for the cones (`ranking=None`) or one exp-decay ranking (§4.2).

    `transversal` chooses the curve from which the stiffest-direction coordinate is
    traced; the prior must not depend on it (T15(e)).
    """
    raise NotImplementedError("spec 002 §4.2: build_pref")


def ranking_coordinate(
    model: Model, ranking: str, theta: np.ndarray, *, transversal: np.ndarray | None = None
) -> np.ndarray:
    """`psi(theta)`, the coordinate a ranking names (§3.5, §4.2): `xi_D` for slowest first,
    `xi_1` for fastest first, and for stiffest first the label of the sloppy eigenvector's
    integral curve through `theta`, traced from `transversal`."""
    raise NotImplementedError("spec 002 §4.2: ranking_coordinate")
