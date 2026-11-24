"""The natures of spec 002 (§2.3, §4.3): round robin, nested and stress natures.

A nature is a tuple `(kind, arg)`: `("own", prior)` for a prior's own world,
`("nested", name)` with `name` in `NESTED`, or `("stress", name)` with `name` in
`STRESS`. Stubs until the implementation stage.
"""
from __future__ import annotations

import numpy as np

from infomax.models import Model

NESTED: tuple[str, ...] = ("thin", "thick", "few_rates")
"""Nested natures: the hypercone's thin and thick halves (at `D_max`), exp-decay's few rates."""

STRESS: tuple[str, ...] = ("vertex", "interior")
"""Stress natures, hypercone only: the sharpened vertex and the smooth interior."""

D_MAX: int = 26
"""Dimension of the hypercone in which the nested natures live (§4.3)."""


def sample_nature(model: Model, nature: tuple, n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """`n` draws of `theta` from the nature, with a label per draw (§4.3).

    For a nested hypercone nature `model` is the `D_max` model; for few rates it is the
    agent's model, in whose coordinates all components share the drawn rate.
    """
    raise NotImplementedError("spec 002 §4.3: sample_nature")


def nature_log_marginal(model: Model, nature: tuple, xbar: np.ndarray) -> np.ndarray:
    """`log m_q(xbar)` at `sigma_eff`, the integral behind a row's floor (§4.3)."""
    raise NotImplementedError("spec 002 §4.3: nature_log_marginal")


def submodel_floor(model_max: Model, D: int, theta: np.ndarray) -> np.ndarray:
    """The submodel's own floor per draw, `N ||y(theta) - y(theta^(D))||^2 / (2 sigma^2)` (§4.3)."""
    raise NotImplementedError("spec 002 §4.3: submodel_floor")


def build_qbar(rows: list[tuple]):
    """`q̄`: the equal-weight mixture of one cell's rows; not itself a row (§4.2, §2.5)."""
    raise NotImplementedError("spec 002 §4.2: build_qbar")


def cell_rows(model: Model, cast: dict) -> list[tuple]:
    """The rows (natures) of a cell whose agent model is `model` (§2.3, §4.3): the own
    world of every prior in `cast` except `q̄`, which is not a row; few rates in exp-decay;
    in the hypercone the interior stress nature, and the vertex one with curvature on. The
    hypercone's nested halves are rows only of a submodel agent's cell, whose nature model
    is the `D_max` cone."""
    raise NotImplementedError("spec 002 §4.3: cell_rows")
