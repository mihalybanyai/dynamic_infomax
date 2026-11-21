"""The log-normal priors `p_LN` and `p_LN^*`, exp-decay only (spec 002 §4.2, OQ-3).

`p_LN`: each log decay time normal with `(theta_bar, tau) = (0, 1)`, as A&M, sorted.
`p_LN^*`: the member of the same family whose `(theta_bar, tau)` maximise
`I_pi(Theta; X_{1:N})`, found by Nelder–Mead with common random numbers. Stubs until the
implementation stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model


def build_pln(model: Model, theta_bar: float = 0.0, tau: float = 1.0):
    """`p_LN` with the given parameters (A&M's are the default)."""
    raise NotImplementedError("spec 002 §4.2: build_pln")


@dataclass(frozen=True)
class TunedLogNormal:
    """`p_LN^*` and the information it reaches."""

    prior: object
    theta_bar: float
    tau: float
    information: float


def build_pln_star(model: Model, rng: np.random.Generator, *, n: int = 4096) -> TunedLogNormal:
    """`p_LN^*`, the budget-tuned log-normal (§4.2)."""
    raise NotImplementedError("spec 002 §4.2: build_pln_star")
