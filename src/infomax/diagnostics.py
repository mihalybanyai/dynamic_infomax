"""Diagnostics of spec 002 (§3.3, §3.2, §4.5, §2.4) and the closed forms the tests check.

Stubs until the implementation stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model


def gaussian_kl_split(mu_q: np.ndarray, Sigma_q: np.ndarray, mu_pi: np.ndarray, Sigma_pi: np.ndarray) -> tuple[float, float]:
    """The two terms of (3.3.1), `(mean_shift, spread_mismatch)`; their half-sum is the KL."""
    raise NotImplementedError("spec 002 §3.3: gaussian_kl_split")


def moment_matched_predictive(prior, model: Model, xbar: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean and covariance of the posterior predictive of `x'` given `xbar` (§4.5)."""
    raise NotImplementedError("spec 002 §4.5: moment_matched_predictive")


def hypercone_jeffreys_mode(x1: float, D: int) -> float:
    """The closed-form mode of Jeffreys' posterior on `theta_1` (9.2.1), noise 1."""
    raise NotImplementedError("spec 002 §9.2: hypercone_jeffreys_mode")


def hypercone_jeffreys_mean(x1: float, D: int, W: float, sigma: float = 1.0) -> float:
    """Jeffreys' posterior mean of `theta_1` given the relevant datum, by quadrature (T6)."""
    raise NotImplementedError("spec 002 §9.2: hypercone_jeffreys_mean")


def beyond_cap(R_mean: float, R_mcse: float, C_N: float, capacity_gap: float) -> bool:
    """The label of §3.7: `R - C_N` exceeds its Monte-Carlo error plus the capacity gap."""
    raise NotImplementedError("spec 002 §4.5: beyond_cap")


def capacity_gap(
    pstar_result, model: Model, rng: np.random.Generator, *, n: int = 256, states: np.ndarray | None = None
) -> float:
    """Largest `R_N^theta(p*) - C_N` over random states off the candidate set (§4.5, T3)."""
    raise NotImplementedError("spec 002 §4.5: capacity_gap")


@dataclass(frozen=True)
class FailureMapPoint:
    """One row on one prior's failure map (§2.4)."""

    breadth: float
    best_rival: float
    gap_to_rival: float


def failure_map_point(mismatch: dict, prior_name: str, own_prior: str | None, floor: float, capacity: float) -> FailureMapPoint:
    """Coordinates of a row on `prior_name`'s map: breadth `floor / capacity`, the best
    rival's mismatch (other priors away in the row) and the signed gap to it."""
    raise NotImplementedError("spec 002 §4.5: failure_map_point")


def mass_near(prior, model: Model, theta: np.ndarray) -> np.ndarray:
    """`pi(A(theta))`: the prior's mass within one noise unit of `y(theta)` at budget `N`."""
    raise NotImplementedError("spec 002 §4.5: mass_near")


def covered_fraction(model: Model, nature: tuple, C_N: float, rng: np.random.Generator, *, K: int = 200, J: int = 64) -> float:
    """`covered_J`: the share of `K` draws with `R_N^theta(p_J) <= C_N` (§4.5)."""
    raise NotImplementedError("spec 002 §4.5: covered_fraction")


def jeffreys_cone_loss(theta1: np.ndarray, D: int, W: float, sigma: float, N: int, *, second_order: bool = True) -> np.ndarray:
    """Jeffreys' loss on the relevant datum, (9.5.1), with the second-order correction."""
    raise NotImplementedError("spec 002 §9.5: jeffreys_cone_loss")


def relevant_datum_divergence(theta1: np.ndarray, D: int, W: float, sigma: float, N: int) -> np.ndarray:
    """Numerical KL between the laws of the relevant datum under `theta` and under `p_J` (T21(c))."""
    raise NotImplementedError("spec 002 §9.5: relevant_datum_divergence")


def joint_width2(model: Model) -> float:
    """The largest `sum_mu L_mu(theta)^2` over `Theta`, over sub-resolution directions (§4.5)."""
    raise NotImplementedError("spec 002 §4.5: joint_width2")


def joint_width_ratio(model: Model, theta: np.ndarray) -> np.ndarray:
    """Exp-decay at `D = 2`: the proxy width over the geodesic width, per state and direction (T22(d))."""
    raise NotImplementedError("spec 002 §4.5: joint_width_ratio")


PROTAGONISTS: tuple[str, ...] = ("p*", "p_lat", "p_proj", "p_LN^*")
"""The priors whose row summaries §2.4 reports; `p_LN^*` in exp-decay only."""

RELATIVES: tuple[str, ...] = ("p*_N/10", "p*_10N", "p_lat", "p_proj", "p_LN^*")
"""`p*`'s relatives, whose own worlds form their own group (§2.4, §6.3)."""


@dataclass(frozen=True)
class RowSummaries:
    """The row summaries of §2.4 for one row, as named in §6.3.

    Each value is `(estimate, error)` per score `S` in `{"R", "r"}`, the error from the
    per-draw differences (§4.4): `gap_J[pi][S]` (absent in Jeffreys' own world),
    `gap_pi[pi][S]`, `gap_pair[(pi, pi2)][S]`, `gap_budget[S]`, `gap_coarse[S]`,
    `gap_fine[S]`, `gap_tune[S]` (exp-decay only), and `delta_R_pref[ranking]` (`R` only;
    one key `"p_ref"` in the cones). `relatives_world` is true in the worlds of `RELATIVES`.
    """

    gap_J: dict
    gap_pi: dict
    gap_pair: dict
    gap_budget: dict
    gap_coarse: dict
    gap_fine: dict
    gap_tune: dict
    delta_R_pref: dict
    relatives_world: bool


def row_summaries(draws_R: dict, draws_r: dict, own_prior: str | None) -> RowSummaries:
    """The row summaries of §2.4 from one row's per-draw scores, keyed by prior name
    (`p_ref[<ranking>]` in exp-decay). `own_prior` is the row's own prior in the round
    robin, `None` for a nested or stress row. Only priors present in the dicts enter."""
    raise NotImplementedError("spec 002 §2.4: row_summaries")


def exchange(mismatch_by_world: dict, a: str, b: str) -> float:
    """§2.4's exchange: what `a` loses in `b`'s world minus what `b` loses in `a`'s, from
    `mismatch_by_world[world][prior]`; negative when `a` loses less away than `b` does."""
    raise NotImplementedError("spec 002 §2.4: exchange")


def cast_present_at_every_D(cast_by_D: dict) -> set:
    """The priors present at every `D` of a trend (§2.4), from `cast_by_D[D]`, a set of
    names, so that a prior dropping out cannot tilt the trend."""
    raise NotImplementedError("spec 002 §2.4: cast_present_at_every_D")
