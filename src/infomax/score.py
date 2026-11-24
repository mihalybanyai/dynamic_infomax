"""The two scores of spec 002 and their pieces (§2.1, §4.4).

`R_N` is the cumulative redundancy (2.1.1), estimated from one draw of the sufficient
statistic `xbar`; `r_N` is the one-step excess log-loss on `x'` at noise `sigma` (2.1.5).
Stubs until the implementation stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model


@dataclass(frozen=True)
class CellScores:
    """One cell's scores per prior, with Monte-Carlo errors, floors and mismatches (§4.4).

    Dict keys are prior names. `draws_R` and `draws_r` hold the per-draw arrays. The
    errors of mismatches come from per-draw differences (§4.4, "Errors of differences").
    `theta` and `labels` are the nature's draws and their labels (§4.3). `floor_sub` is the
    submodel's own floor for a nested hypercone nature, `None` otherwise. `mean_shift` and
    `spread_mismatch` are the two terms of (3.3.1) per prior, averaged over draws (§4.5).
    """

    R_mean: dict
    R_mcse: dict
    r_mean: dict
    r_mcse: dict
    floor_R: float
    floor_r: float
    mismatch_R: dict
    mismatch_r: dict
    draws_R: dict
    draws_r: dict
    mismatch_R_mcse: dict | None = None
    mismatch_r_mcse: dict | None = None
    theta: np.ndarray | None = None
    labels: np.ndarray | None = None
    floor_sub: float | None = None
    mean_shift: dict | None = None
    spread_mismatch: dict | None = None


def score_cell(
    model: Model,
    priors: dict,
    nature: tuple,
    *,
    S_q: int,
    rng: np.random.Generator,
    literal_nfold: bool = False,
    nature_model: Model | None = None,
) -> CellScores:
    """Score every prior in `priors` on one cell, under common random numbers (§4.4).

    `model` is the agent's model. For a nested hypercone nature, `nature_model` is the
    `D_max` cone the nature lives in (§2.3); the agent's predictions share its data space.
    """
    raise NotImplementedError("spec 002 §4.4: score_cell")


def log_marginal(prior, model: Model, xbar: np.ndarray, *, method: str = "auto") -> np.ndarray:
    """`log m_pi(xbar)`: an exact sum for discrete priors, quadrature or importance
    sampling for continuous ones (`method` in {"auto", "atoms", "quadrature"})."""
    raise NotImplementedError("spec 002 §4.4: log_marginal")


def matched_floor(model: Model, nature: tuple, *, S_q: int, rng: np.random.Generator, score: str = "R") -> tuple[float, float]:
    """Nature's own information, `I_q` (or the conditional one for `score="r"`), with its error."""
    raise NotImplementedError("spec 002 §4.3: matched_floor")


def marginal_mismatch(model: Model, nature: tuple, prior, *, S_q: int, rng: np.random.Generator, score: str = "R") -> tuple[float, float]:
    """`D_KL(m_q || m_pi)` (or the posterior-predictive mismatch of (2.1.6)), with its error."""
    raise NotImplementedError("spec 002 §2.1: marginal_mismatch")


def per_state_redundancy(prior, model: Model, theta: np.ndarray, *, rng: np.random.Generator | None = None, n_x: int = 64) -> np.ndarray:
    """`R_N^theta(pi) = D_KL(p(xbar|theta) || m_pi)` per state (§3.2, §4.5)."""
    raise NotImplementedError("spec 002 §4.5: per_state_redundancy")


def mutual_information(prior, model: Model, *, rng: np.random.Generator | None = None) -> float:
    """`I_pi(Theta; X_{1:N})` in nats, at `sigma_eff`."""
    raise NotImplementedError("spec 002 §4.2: mutual_information")


def bias_pressure(prior, model: Model, theta: np.ndarray, *, rng: np.random.Generator | None = None) -> np.ndarray:
    """A&M's bias pressure `b(theta) = D_KL(p(x|theta) || m_pi) - I_pi`, single observation."""
    raise NotImplementedError("spec 002 §4.2: bias_pressure")
