"""The NML pushforward `p_proj` (spec 002 §4.2, OQ-6).

A port of AtomicPriors.jl's `transtrum`: an ensemble Markov chain on `x` targets
`p_NML(x) ∝ max_theta p(x|theta)`, and the maximum-likelihood `theta-hat` of each
retained step forms the cloud. Stubs until the implementation stage.
"""
from __future__ import annotations

import numpy as np

from infomax.models import Model
from infomax.priors002 import CloudPrior


def mle_project(model: Model, x: np.ndarray) -> np.ndarray:
    """The maximum-likelihood state for data `x` within `Theta`, at `sigma_eff`."""
    raise NotImplementedError("spec 002 §4.2: mle_project")


def nml_log_normaliser(model: Model, rng: np.random.Generator, *, n: int = 4096) -> float:
    """`log ∫ max_theta p(x|theta) dx` at `sigma_eff`; finite on a compact manifold (T11)."""
    raise NotImplementedError("spec 002 §4.2: nml_log_normaliser")


def build_pproj(
    model: Model,
    n_samples: int,
    rng: np.random.Generator,
    *,
    n_walkers: int = 64,
    burn: int = 1000,
) -> CloudPrior:
    """`p_proj` as a cloud of `n_samples` maximum-likelihood estimates (§4.2)."""
    raise NotImplementedError("spec 002 §4.2: build_pproj")
