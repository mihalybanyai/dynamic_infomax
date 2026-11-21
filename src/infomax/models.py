"""Model families of spec 002: exponential decay, the hypercone, the constant cross-section.

Spec: specs/002-foreign-q-prediction.md §4.1 (maps, parameter sets, knobs) and §2.3
(nested natures, whose agents use a submodel). Every function is a stub until the
implementation stage (`workflows/implement-spec.md`); the tests in
`tests/test_002_*.py` pin the interface.

Coordinates. In the hypercone, `theta` is the cone's own coordinates
`(theta_1, theta_2, ..., theta_D)` on `[0, W] x [0, 1]^(D-1)`. In exp-decay the model
is held in A&M's compact coordinate `xi_mu = exp(-k_mu)` on the ordered part of
`[0, 1]^D` (spec §4.1), so `Model.y` and `Model.fim` take `xi`; the log decay time
`theta_mu = -log k_mu` is used only by the priors defined in it (`p_LN`, the
stiffest-direction ranking).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FAMILIES: tuple[str, ...] = ("exp_decay", "hypercone")
"""Model families; the constant cross-section is the hypercone with `taper = 0`."""

BOX: dict[str, tuple[float, float]] = {
    "full": (0.0, 1.0),
    "matched": (float(np.exp(-1.0)), float(np.exp(-0.2))),
}
"""Exp-decay ranges of `xi` (spec §4.1, OQ-9): the whole manifold, and the window's range
(decay times 1 to 5)."""

OBSERVATION_WINDOW: tuple[float, float] = (1.0, 5.0)
"""A&M's observation times run evenly over this window (spec §4.1)."""


@dataclass(frozen=True)
class ParameterSet:
    """The parameter set `Theta` of a model (spec §1.1, §4.1).

    `low` and `high` bound each coordinate; `ordered` restricts to
    `theta_1 <= ... <= theta_D` (exp-decay).
    """

    low: np.ndarray
    high: np.ndarray
    ordered: bool

    def contains(self, theta: np.ndarray) -> np.ndarray:
        """Boolean mask over the leading axes of `theta` (shape (..., D))."""
        raise NotImplementedError("spec 002 §4.1: ParameterSet.contains")

    def sample_uniform(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """`n` states uniform on `Theta` in its own coordinates, shape (n, D)."""
        raise NotImplementedError("spec 002 §4.1: ParameterSet.sample_uniform")


@dataclass(frozen=True)
class Model:
    """A model of spec 002: the map `y`, its Fisher metric, `Theta` and the budget.

    `fixed` is `None` for a full model. For an agent's submodel of a nested nature
    (spec §2.3) it holds the values at which the ignored coordinates are fixed.
    """

    family: str
    D: int
    m: int
    sigma: float
    N: int
    box: ParameterSet
    W: float = 50.0
    taper: float = 1.0
    falloff: float = 1.0
    curvature: float = 1.0
    fixed: np.ndarray | None = None

    @property
    def sigma_eff(self) -> float:
        """The budget through the noise, `sigma / sqrt(N)` (spec §4)."""
        raise NotImplementedError("spec 002 §4: Model.sigma_eff")

    @property
    def m_out(self) -> int:
        """Data dimension: `m` in exp-decay, the full model's `D` in the hypercone."""
        raise NotImplementedError("spec 002 §4.1: Model.m_out")

    def y(self, theta: np.ndarray) -> np.ndarray:
        """Prediction map, shape (..., D) -> (..., m_out) (spec §4.1)."""
        raise NotImplementedError("spec 002 §4.1: Model.y")

    def fim(self, theta: np.ndarray) -> np.ndarray:
        """Fisher metric (1.2.1) at `sigma_eff`, shape (..., D) -> (..., D, D)."""
        raise NotImplementedError("spec 002 §4.1: Model.fim")


def build_model(
    family: str,
    D: int,
    m: int = 26,
    sigma: float = 0.1,
    N: int = 1,
    *,
    box: str = "full",
    W: float = 50.0,
    taper: float = 1.0,
    falloff: float = 1.0,
    curvature: float = 1.0,
) -> Model:
    """Build a model of spec 002 §4.1.

    `curvature` is the warp's `kappa` (1.0 is off); `taper = 0` gives the constant
    cross-section (family 3).
    """
    raise NotImplementedError("spec 002 §4.1: build_model")


def submodel(model_max: Model, D: int, fixed_value: float = 0.5) -> Model:
    """The agent's model of a nested nature (spec §2.3, §4.3).

    It frees the first `D` coordinates of `model_max` and fixes the rest at
    `fixed_value` (the box's centre); its predictions live in `model_max`'s data space.
    """
    raise NotImplementedError("spec 002 §4.3: submodel")


def warp_vertex(y: np.ndarray, v: np.ndarray, kappa: float, rho: float) -> np.ndarray:
    """The curvature knob's local warp of prediction space (spec §4.1, OQ-12).

    Narrows the angle at the vertex `v` from pi/2 to `kappa * pi / 2` inside the ball
    of radius `rho`, and is the identity outside it.
    """
    raise NotImplementedError("spec 002 §4.1: warp_vertex")
