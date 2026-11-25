"""The latent information prior `p_lat` (spec 002 §4.2; Komaki 2011; Fogel & Feder 2024).

Maximises `I_pi(Theta; X_{N+1:N+M} | X_{1:N})` by the Blahut–Arimoto variant whose update
uses `f^(N+M) - f^(N)`; the spec's cast uses `M = 1`. The same build runs on the binomial
model of `infomax.models.binomial_model` for T18 and the second eye test.

The fixed point is found by the solver shared with `p*` (`infomax.capacity`, DD-S1): the
objective is the difference of the two per-state divergences, each at its own noise
(`sigma/sqrt(N+M)` and `sigma/sqrt(N)`), estimated on the same quadrature nodes, which are
the common random numbers of §4.2. At `N = 0` the second term is absent and the build is
`p*`'s at budget `M`, on the same path and with the same settings (T16(c)).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.capacity import BinomialObjective, DifferenceObjective, GaussianObjective, solve_capacity
from infomax.mixture import kl_to_mixture
from infomax.models import Model
from infomax.priors002 import DiscretePrior


@dataclass(frozen=True)
class PLatResult:
    """A `p_lat` build with its two-sided bound on the minimax one-step loss."""

    prior: DiscretePrior
    conditional_capacity: float
    lower_bound: float
    upper_bound: float


def _objectives(model: Model, cand: np.ndarray, M: int):
    N = model.N
    if model.family == "binomial":
        a = BinomialObjective(cand[:, 0], int(N + M))
        b = BinomialObjective(cand[:, 0], int(N)) if N > 0 else None
        return DifferenceObjective(a, b), None
    Y = model.y(cand)
    s_a = model.sigma / np.sqrt(N + M)
    a = GaussianObjective(Y, s_a)
    b = GaussianObjective(Y, model.sigma / np.sqrt(N)) if N > 0 else None
    if Y.shape[1] == 1:
        return DifferenceObjective(a, b), None
    fa = GaussianObjective(Y, s_a, fast=True)
    fb = GaussianObjective(Y, model.sigma / np.sqrt(N), fast=True) if N > 0 else None
    return DifferenceObjective(a, b), DifferenceObjective(fa, fb)


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
    from infomax.pstar import _initial_support, candidate_set

    if candidates is None:
        if model.family == "binomial":
            raise ValueError("the binomial build needs its grid of theta as candidates")
        base = model if model.N > 0 else model.at_budget(M)
        candidates = candidate_set(base, spacing)
    cand = np.asarray(candidates, dtype=float)
    if cand.ndim == 1:
        cand = cand[:, None]
    obj, fast = _objectives(model, cand, M)
    if model.N == 0 and model.family != "binomial":
        tol = min(tol, 1e-8)  # the same settings as build_pstar (T16(c))
    initial = None
    if model.family != "binomial" and cand.shape[0] > 600:
        Y = model.y(cand)
        initial = _initial_support(Y / (model.sigma / np.sqrt(model.N + M)))
    sol = solve_capacity(obj, fast=fast, initial=initial, tol=tol)
    upper = float(np.max(sol.f_all))
    prior = DiscretePrior("p_lat", cand, sol.masses)
    return PLatResult(prior=prior, conditional_capacity=sol.value, lower_bound=sol.value, upper_bound=max(upper, sol.value))


def conditional_divergence(result: PLatResult, model: Model, theta: np.ndarray, *, M: int = 1) -> np.ndarray:
    """Per-state `f^(N+M)(theta) - f^(N)(theta)` under `result.prior` (T16)."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    prior = result.prior
    keep = prior.weights > 0
    atoms, w = prior.atoms[keep], prior.weights[keep]
    N = model.N
    if model.family == "binomial":
        all_theta = np.concatenate([theta[:, 0], atoms[:, 0]])
        n_t = theta.shape[0]
        S = np.arange(n_t, n_t + atoms.shape[0])
        st = np.arange(n_t)
        out = BinomialObjective(all_theta, int(N + M)).f(st, S, w)
        if N > 0:
            out = out - BinomialObjective(all_theta, int(N)).f(st, S, w)
        return out
    Yt, Ya = model.y(theta), model.y(atoms)
    lw = np.log(w)
    out = kl_to_mixture(Yt, Ya, lw, model.sigma / np.sqrt(N + M))
    if N > 0:
        out = out - kl_to_mixture(Yt, Ya, lw, model.sigma / np.sqrt(N))
    return out
