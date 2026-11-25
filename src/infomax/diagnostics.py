"""Diagnostics of spec 002 (§3.3, §3.2, §4.5, §2.4) and the closed forms the tests check.

"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.models import Model


def gaussian_kl_split(mu_q: np.ndarray, Sigma_q: np.ndarray, mu_pi: np.ndarray, Sigma_pi: np.ndarray) -> tuple[float, float]:
    """The two terms of (3.3.1), `(mean_shift, spread_mismatch)`; their half-sum is the KL."""
    mu_q, mu_pi = np.asarray(mu_q, float), np.asarray(mu_pi, float)
    Sigma_q, Sigma_pi = np.asarray(Sigma_q, float), np.asarray(Sigma_pi, float)
    m = mu_q.size
    L = np.linalg.cholesky(Sigma_pi)
    d = mu_pi - mu_q
    z = np.linalg.solve(L, d)
    shift = float(z @ z)
    Linv_Sq = np.linalg.solve(L, Sigma_q)
    tr = float(np.trace(np.linalg.solve(L.T, Linv_Sq)))
    _, ld_pi = np.linalg.slogdet(Sigma_pi)
    _, ld_q = np.linalg.slogdet(Sigma_q)
    spread = tr - m + float(ld_pi - ld_q)
    return shift, spread


def moment_matched_predictive(prior, model: Model, xbar: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean and covariance of the posterior predictive of `x'` given `xbar` (§4.5)."""
    xbar = np.asarray(xbar, dtype=float)
    mu, S = prior.posterior_predictive_moments(model, xbar[None, :] if xbar.ndim == 1 else xbar)
    return (mu[0], S[0]) if xbar.ndim == 1 else (mu, S)


def hypercone_jeffreys_mode(x1: float, D: int) -> float:
    """The closed-form mode of Jeffreys' posterior on `theta_1` (9.2.1), noise 1."""
    return 0.5 * (x1 + np.sqrt(x1 * x1 + 4.0 * (D - 1)))


def hypercone_jeffreys_mean(x1: float, D: int, W: float, sigma: float = 1.0) -> float:
    """Jeffreys' posterior mean of `theta_1` given the relevant datum, by quadrature (T6):
    prior `∝ theta_1^(D-1)` on `[0, W]` times `N(x1; theta_1, sigma^2)`, Gauss–Legendre in
    log space on cells of a twentieth of the noise."""
    from scipy.special import logsumexp

    n_cells = int(np.ceil(W / (0.05 * sigma)))
    edges = np.linspace(0.0, W, n_cells + 1)
    gx, gw = np.polynomial.legendre.leggauss(8)
    h = np.diff(edges)
    t = (edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel()
    lw = np.log((0.5 * h[:, None] * gw).ravel()) + (D - 1) * np.log(t) - 0.5 * ((x1 - t) / sigma) ** 2
    p = np.exp(lw - logsumexp(lw))
    return float(p @ t)


def beyond_cap(R_mean: float, R_mcse: float, C_N: float, capacity_gap: float) -> bool:
    """The label of §3.7: `R - C_N` exceeds its Monte-Carlo error plus the capacity gap."""
    return bool((R_mean - C_N) > (R_mcse + capacity_gap))


def capacity_gap(
    pstar_result, model: Model, rng: np.random.Generator, *, n: int = 256, states: np.ndarray | None = None
) -> float:
    """Largest `R_N^theta(p*) - C_N` over random states off the candidate set (§4.5, T3)."""
    from infomax.score import per_state_redundancy

    if states is None:
        states = model.box.sample_uniform(n, rng)
    b = per_state_redundancy(pstar_result.prior, model, states, rng=rng) - pstar_result.capacity
    return float(np.max(b))


@dataclass(frozen=True)
class FailureMapPoint:
    """One row on one prior's failure map (§2.4)."""

    breadth: float
    best_rival: float
    gap_to_rival: float


def failure_map_point(mismatch: dict, prior_name: str, own_prior: str | None, floor: float, capacity: float) -> FailureMapPoint:
    """Coordinates of a row on `prior_name`'s map: breadth `floor / capacity`, the best
    rival's mismatch (other priors away in the row) and the signed gap to it."""
    rivals = [v for k, v in mismatch.items() if k != prior_name and k != own_prior]
    best = float(min(rivals))
    return FailureMapPoint(breadth=float(floor / capacity), best_rival=best, gap_to_rival=float(mismatch[prior_name] - best))


def mass_near(prior, model: Model, theta: np.ndarray) -> np.ndarray:
    """`pi(A(theta))`: the prior's mass within one noise unit of `y(theta)` at budget `N`."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    return prior.mass_within(model, model.y(theta), model.sigma_eff)


def covered_fraction(model: Model, nature: tuple, C_N: float, rng: np.random.Generator, *, K: int = 200, J: int = 64) -> float:
    """`covered_J`: the share of `K` draws with `R_N^theta(p_J) <= C_N` (§4.5)."""
    from infomax.jeffreys import build_jeffreys
    from infomax.qfamily import sample_nature
    from infomax.score import per_state_redundancy

    theta, _ = sample_nature(model, nature, K, rng)
    loss = per_state_redundancy(build_jeffreys(model), model, theta, rng=rng, n_x=J)
    return float(np.mean(loss <= C_N))


def jeffreys_cone_loss(theta1: np.ndarray, D: int, W: float, sigma: float, N: int, *, second_order: bool = True) -> np.ndarray:
    """Jeffreys' loss on the relevant datum, (9.5.1), with the second-order correction."""
    theta1 = np.asarray(theta1, dtype=float)
    out = (D - 1) * np.log(W / theta1) + np.log(W / D) - 0.5 * np.log(2 * np.pi * np.e * sigma**2 / N)
    if second_order:
        out = out - (D - 1) * (D - 3) * sigma**2 / (2 * N * theta1**2)
    return out


def relevant_datum_divergence(theta1: np.ndarray, D: int, W: float, sigma: float, N: int) -> np.ndarray:
    """Numerical KL between the laws of the relevant datum under `theta` and under `p_J` (T21(c)):
    `N(theta_1, s^2)` against its mixture over `D t^(D-1) / W^D` on `[0, W]`, `s = sigma/sqrt(N)`;
    Gauss–Hermite in the datum, Gauss–Legendre in `t`."""
    from scipy.special import logsumexp

    s = sigma / np.sqrt(N)
    theta1 = np.atleast_1d(np.asarray(theta1, dtype=float))
    z, om = np.polynomial.hermite.hermgauss(120)
    n_cells = int(np.ceil(W / (0.1 * s)))
    edges = np.linspace(0.0, W, n_cells + 1)
    gx, gw = np.polynomial.legendre.leggauss(6)
    h = np.diff(edges)
    t = (edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel()
    lw = np.log((0.5 * h[:, None] * gw).ravel()) + np.log(D) + (D - 1) * np.log(t) - D * np.log(W)
    out = np.empty(theta1.size)
    for i, th in enumerate(theta1):
        x = th + np.sqrt(2.0) * s * z
        log_p = -0.5 * ((x - th) / s) ** 2 - 0.5 * np.log(2 * np.pi * s * s)
        log_m = logsumexp(lw[None, :] - 0.5 * ((x[:, None] - t[None, :]) / s) ** 2, axis=1) - 0.5 * np.log(2 * np.pi * s * s)
        out[i] = float(np.sum(om / np.sqrt(np.pi) * (log_p - log_m)))
    return out


def joint_width2(model: Model) -> float:
    """The largest `sum_mu L_mu(theta)^2` over `Theta`, over sub-resolution directions (§4.5)."""
    if model.family == "hypercone":
        w = model.widths[: model.D - 1] / model.sigma_eff
        r_hi = float(model.taper_r(model.W))
        r_lo = float(model.taper_r(0.0))
        rs = np.concatenate([np.linspace(min(r_lo, r_hi), max(r_lo, r_hi), 2001), [1.0 / x - 1e-12 for x in w if x > 0]])
        rs = rs[(rs >= min(r_lo, r_hi)) & (rs <= max(r_lo, r_hi))]
        L = rs[:, None] * w[None, :]
        return float(np.max(np.sum(np.where(L < 1.0, L * L, 0.0), axis=1)))
    from infomax.pstar import candidate_set

    theta = candidate_set(model, spacing=1.0)
    L = _proxy_widths(model, theta)
    return float(np.max(np.sum(np.where(L < 1.0, L * L, 0.0), axis=1)))


def _chord(model: Model, theta: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Length of the chord of `Theta` through each `theta` along unit direction `v`."""
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    tmax = np.full(theta.shape[0], np.inf)
    tmin = np.full(theta.shape[0], -np.inf)
    for d in range(theta.shape[1]):
        vd = v[:, d]
        with np.errstate(divide="ignore", invalid="ignore"):
            a = (lo[d] - theta[:, d]) / vd
            b = (hi[d] - theta[:, d]) / vd
        a, b = np.where(vd != 0, np.minimum(a, b), -np.inf), np.where(vd != 0, np.maximum(a, b), np.inf)
        tmin, tmax = np.maximum(tmin, a), np.minimum(tmax, b)
    if model.box.ordered:
        for d in range(theta.shape[1] - 1):
            dv = v[:, d + 1] - v[:, d]
            gap = theta[:, d + 1] - theta[:, d]
            with np.errstate(divide="ignore", invalid="ignore"):
                t = -gap / dv
            tmax = np.where(dv < 0, np.minimum(tmax, t), tmax)
            tmin = np.where(dv > 0, np.maximum(tmin, t), tmin)
    return np.maximum(tmax - tmin, 0.0)


def _proxy_widths(model: Model, theta: np.ndarray) -> np.ndarray:
    """§4.5's proxy: `sqrt(lambda_mu) x chord length along v_mu`, shape (n, D)."""
    g = model.fim(theta)
    lam, vec = np.linalg.eigh(g)
    out = np.empty_like(lam)
    for mu in range(lam.shape[1]):
        out[:, mu] = np.sqrt(np.maximum(lam[:, mu], 0.0)) * _chord(model, theta, vec[:, :, mu])
    return out


def _geodesic_width(model: Model, theta: np.ndarray, mu: int, *, h: float = 2e-3, max_steps: int = 4000) -> np.ndarray:
    """`∫ ds` along the integral curve of the `mu`-th eigenvector through each state, to
    the boundary of `Theta` both ways (RK2 in `xi`)."""
    out = np.zeros(theta.shape[0])
    for sign in (1.0, -1.0):
        th = theta.copy()
        g = model.fim(th)
        lam, vec = np.linalg.eigh(g)
        prev = sign * vec[:, :, mu]
        alive = np.ones(th.shape[0], dtype=bool)
        for _ in range(max_steps):
            if not np.any(alive):
                break
            lam, vec = np.linalg.eigh(model.fim(th))
            v = vec[:, :, mu]
            v *= np.where(np.sum(v * prev, axis=1) < 0, -1.0, 1.0)[:, None]
            mid = th + 0.5 * h * v
            lam_m, vec_m = np.linalg.eigh(model.fim(np.clip(mid, model.box.low, model.box.high)))
            vm = vec_m[:, :, mu]
            vm *= np.where(np.sum(vm * v, axis=1) < 0, -1.0, 1.0)[:, None]
            new = th + h * vm
            inside = model.box.contains(new)
            step_len = np.sqrt(np.maximum(lam_m[:, mu], 0.0)) * h
            out += np.where(alive & inside, step_len, 0.0)
            alive &= inside
            th = np.where(alive[:, None], new, th)
            prev = np.where(alive[:, None], vm, prev)
    return out


def joint_width_ratio(model: Model, theta: np.ndarray) -> np.ndarray:
    """Exp-decay at `D = 2`: the proxy width over the geodesic width, per state and direction (T22(d))."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    proxy = _proxy_widths(model, theta)
    geo = np.column_stack([_geodesic_width(model, theta, mu) for mu in range(theta.shape[1])])
    return proxy / np.maximum(geo, 1e-300)


PROTAGONISTS: tuple[str, ...] = ("p*", "p_lat", "p_proj", "p_LN^*")
"""The priors whose row summaries §2.4 reports; `p_LN^*` in exp-decay only."""

RELATIVES: tuple[str, ...] = ("p*_N/10", "p*_10N", "p_lat", "p_proj", "p_LN^*")
"""`p*`'s relatives, whose own worlds form their own group (§2.4, §6.3)."""

PRIVILEGED_BASE: tuple[str, ...] = ("p_U", "p_LN")
"""Privileged-information priors besides `p_ref` (§2.2)."""


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


def _diff(draws: dict, a: str, b: str) -> tuple[float, float]:
    d = np.asarray(draws[a], float) - np.asarray(draws[b], float)
    se = float(np.std(d, ddof=1) / np.sqrt(d.size)) if d.size > 1 else 0.0
    return float(d.mean()), se


def row_summaries(draws_R: dict, draws_r: dict, own_prior: str | None) -> RowSummaries:
    """The row summaries of §2.4 from one row's per-draw scores, keyed by prior name
    (`p_ref[<ranking>]` in exp-decay). `own_prior` is the row's own prior in the round
    robin, `None` for a nested or stress row. Only priors present in the dicts enter."""
    present = set(draws_R)
    by = {"R": draws_R, "r": draws_r}
    prot = [p for p in PROTAGONISTS if p in present]
    priv = [p for p in present if (p in PRIVILEGED_BASE or p == "p_ref" or p.startswith("p_ref[")) and p != own_prior]
    gap_J, gap_pi, gap_pair = {}, {}, {}
    for pi in prot:
        if "p_J" in present and own_prior != "p_J":
            gap_J[pi] = {S: _diff(d, pi, "p_J") for S, d in by.items()}
        if priv:
            gap_pi[pi] = {}
            for S, d in by.items():
                best = min(priv, key=lambda q: float(np.mean(d[q])))
                gap_pi[pi][S] = _diff(d, pi, best)
    for a, b in (("p*", "p_lat"), ("p*", "p_proj"), ("p_lat", "p_proj"), ("p*", "p_LN^*")):
        if a in present and b in present:
            gap_pair[(a, b)] = {S: _diff(d, a, b) for S, d in by.items()}
    gap_coarse, gap_fine, gap_budget = {}, {}, {}
    if "p*" in present:
        for S, d in by.items():
            if "p*_N/10" in present:
                gap_coarse[S] = _diff(d, "p*", "p*_N/10")
            if "p*_10N" in present:
                gap_fine[S] = _diff(d, "p*", "p*_10N")
            budgets = [b for b in ("p*_N/10", "p*_10N") if b in present]
            if budgets:
                best = min(budgets, key=lambda q: float(np.mean(d[q])))
                gap_budget[S] = _diff(d, "p*", best)
    gap_tune = {}
    if "p_LN^*" in present and "p_LN" in present:
        gap_tune = {S: _diff(d, "p_LN^*", "p_LN") for S, d in by.items()}
    delta_R_pref = {}
    if "p*" in present:
        for p in present:
            if p == "p_ref":
                delta_R_pref["p_ref"] = _diff(draws_R, "p*", p)
            elif p.startswith("p_ref["):
                delta_R_pref[p[len("p_ref[") : -1]] = _diff(draws_R, "p*", p)
    return RowSummaries(
        gap_J=gap_J, gap_pi=gap_pi, gap_pair=gap_pair, gap_budget=gap_budget, gap_coarse=gap_coarse,
        gap_fine=gap_fine, gap_tune=gap_tune, delta_R_pref=delta_R_pref,
        relatives_world=own_prior in RELATIVES,
    )


def exchange(mismatch_by_world: dict, a: str, b: str) -> float:
    """§2.4's exchange: what `a` loses in `b`'s world minus what `b` loses in `a`'s, from
    `mismatch_by_world[world][prior]`; negative when `a` loses less away than `b` does."""
    return float(mismatch_by_world[b][a] - mismatch_by_world[a][b])


def cast_present_at_every_D(cast_by_D: dict) -> set:
    """The priors present at every `D` of a trend (§2.4), from `cast_by_D[D]`, a set of
    names, so that a prior dropping out cannot tilt the trend."""
    sets = [set(v) for v in cast_by_D.values()]
    return set.intersection(*sets) if sets else set()


def on_faces(model: Model, theta: np.ndarray, *, eps: float = 1e-12) -> np.ndarray:
    """True for states on a face of `Theta`: a coordinate at its bound, or (exp-decay) two
    rates coinciding."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    face = np.any((theta <= lo + eps) | (theta >= hi - eps), axis=1)
    if model.box.ordered and theta.shape[1] > 1:
        face |= np.any(np.diff(theta, axis=1) <= eps, axis=1)
    return face


def worst_case_bias_pressure(
    prior,
    model: Model,
    states: np.ndarray,
    rng: np.random.Generator,
    *,
    n_own: int = 2000,
    screen_spacing: float = 2.0,
    n_screen: int = 64,
    n_refine: int = 512,
    top: int = 32,
) -> tuple[float, float]:
    """The eye test's band for `B = max_theta b(theta)` (§5.3, §5.3.1), in nats:
    `(B over n_own draws from the prior itself, B over all of `states`)`.

    `states` is a state set that includes the faces of `Theta` (`p*`'s candidate set).
    Each maximum is found in two stages: `b` on a subset thinned to `screen_spacing` Fisher
    lengths, with `n_screen` draws of `x`; then the states within half that spacing of the
    best screened ones (at most `2 top`) re-evaluated with `n_refine` draws, so that noise in
    the screen does not inflate the maximum and thinning does not lose it."""
    from scipy.spatial import cKDTree

    from infomax.pstar import _initial_support
    from infomax.score import mutual_information, per_state_redundancy

    info = mutual_information(prior, model, rng=rng)

    def two_stage(pts: np.ndarray) -> float:
        Yh = model.y(pts) / model.sigma_eff
        net = _initial_support(Yh, radius=0.5 * screen_spacing, max_size=10**7)
        f_screen = per_state_redundancy(prior, model, pts[net], rng=rng, n_x=n_screen)
        best = net[np.argsort(-f_screen)[: max(1, top // 2)]]
        near = cKDTree(Yh).query_ball_point(Yh[best], r=0.5 * screen_spacing)
        cand = np.unique(np.concatenate([best] + [np.asarray(n, dtype=int) for n in near]))
        if cand.size > 2 * top:  # keep the best-screened neighbourhoods first
            cand = np.concatenate([best, np.setdiff1d(cand, best)[: 2 * top - best.size]])
        f_ref = per_state_redundancy(prior, model, pts[cand], rng=rng, n_x=n_refine)
        return float(np.max(f_ref)) - info

    own = prior.sample(n_own, rng)
    return two_stage(own), two_stage(np.atleast_2d(np.asarray(states, dtype=float)))
