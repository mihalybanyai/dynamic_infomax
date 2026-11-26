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
    """`p_U`: uniform on `Theta` in its own coordinates (§4.2).

    Exp-decay: uniform on the ordered cube in `xi`, density `D! / (hi - lo)^D`, i.e. each
    rate `k_mu ~ Exp(1)` before ordering on the whole manifold. Hypercone: density `1/W`.
    """
    from infomax.priors002 import ConeProductPrior, ExpDecayProductPrior, GridPrior002

    if model.family == "exp_decay":
        lo, hi = float(model.box.low[0]), float(model.box.high[0])
        width = hi - lo

        def log_h(xi):
            return np.full(np.shape(xi), -np.log(width))

        def log_H_interval(a, b):
            return np.log((np.asarray(b) - np.asarray(a)) / width)

        def inv_H(a, b, u):
            return a + (b - a) * u

        prior = ExpDecayProductPrior(
            "p_U", model, log_h, log_H_interval, lambda n, rng: model.box.sample_uniform(n, rng), inv_H=inv_H
        )
        from infomax.sampled import GRID_MAX_D, sampled_from

        return sampled_from(prior, model, "p_U") if model.D > GRID_MAX_D else prior  # §4.4, OQ-13
    if model.family == "hypercone":
        W = model.W
        if model.curvature == 1.0:
            return ConeProductPrior(
                "p_U", model, lambda t: np.full(np.shape(t), -np.log(W)), lambda n, rng: W * rng.uniform(size=n)
            )
        log_c = -float(model.box.log_volume)
        return GridPrior002(
            "p_U", model, lambda th: np.full(np.shape(th)[:-1], log_c), sampler=lambda n, rng: model.box.sample_uniform(n, rng),
            log_normaliser=0.0,
        )
    raise ValueError(f"no uniform prior for family {model.family!r}")


# ---------------------------------------------------------------------------
# Exp-decay at D = 2: the two coordinate rankings (Berger–Bernardo by quadrature)
# ---------------------------------------------------------------------------

_GL_V = np.polynomial.legendre.leggauss(64)


def _columns(model: Model, xi: np.ndarray) -> np.ndarray:
    """`dy/dxi_mu` as a function of `xi_mu` alone (exp-decay), shape (..., m)."""
    t = model.times
    return t * np.asarray(xi)[..., None] ** (t - 1.0) / model.D


def _bb_coordinate_log_density(model: Model, xi: np.ndarray, ranking: str, *, chunk: int = 8000) -> np.ndarray:
    """Unnormalised `log p_ref` at `D = 2` for slowest first (`psi = xi_2`, nuisance
    `xi_1 in [lo, psi]`) or fastest first (`psi = xi_1`, nuisance `xi_2 in [psi, hi]`):
    `j(lambda|psi) exp{∫ j(.|psi) log sqrt(Schur_psi)}` with `j` the conditional Jeffreys
    density (`[^3-schur]`). The nuisance integral uses `t = psi -+ (range) v^2`, which
    removes the logarithmic singularity of the Schur complement where the rates coincide."""
    lo, hi = float(model.box.low[0]), float(model.box.high[0])
    xi = np.atleast_2d(np.asarray(xi, dtype=float))
    v, wv = _GL_V
    v = 0.5 * (v + 1.0)
    wv = 0.5 * wv
    out = np.empty(xi.shape[0])
    for a in range(0, xi.shape[0], chunk):
        x = xi[a : a + chunk]
        if ranking == "slowest":
            psi, lam = x[:, 1], x[:, 0]
            span = psi - lo
            t = psi[:, None] - span[:, None] * v[None, :] ** 2
        else:
            psi, lam = x[:, 0], x[:, 1]
            span = hi - psi
            t = psi[:, None] + span[:, None] * v[None, :] ** 2
        jac = 2.0 * span[:, None] * v[None, :] * wv[None, :]  # dt for the GL rule in v
        Jp = _columns(model, psi)  # (n, m)
        Jt = _columns(model, t)  # (n, q, m)
        g_pp = np.sum(Jp * Jp, axis=-1)
        g_tt = np.sum(Jt * Jt, axis=-1)
        g_pt = np.sum(Jp[:, None, :] * Jt, axis=-1)
        root_t = np.sqrt(g_tt)
        norm = np.sum(jac * root_t, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            schur = g_pp[:, None] - g_pt**2 / g_tt
            half_log_schur = 0.5 * np.log(np.maximum(schur, 1e-300))
            E = np.sum(jac * root_t * half_log_schur, axis=1) / norm
            Jl = _columns(model, lam)
            val = 0.5 * np.log(np.sum(Jl * Jl, axis=-1)) - np.log(norm) + E
        out[a : a + chunk] = np.where((span > 0) & np.isfinite(val), val, -np.inf)
    return out


# ---------------------------------------------------------------------------
# Exp-decay at D = 2: stiffest first, along the sloppy eigenvector's integral curves
# ---------------------------------------------------------------------------

THETA_RANGE: tuple[float, float] = (-4.0, 9.0)
"""Log decay times beyond which a rate is frozen (`xi = 1`) or gone (`xi = 0`) at every
observation time: the integral curves are traced inside this range (DD-R1)."""


def _xi_of(theta):
    return np.exp(-np.exp(-np.asarray(theta, float)))


def _theta_of(xi):
    xi = np.clip(np.asarray(xi, float), 1e-300, 1.0 - 1e-16)
    return -np.log(-np.log(xi))


def _g_theta(model: Model, th: np.ndarray) -> np.ndarray:
    """The metric in log decay times (noise 1), shape (n, 2, 2)."""
    xi = _xi_of(th)
    dxi = xi * np.exp(-th)
    J = _columns(model, xi) * dxi[..., None]  # (n, 2, m)
    return np.einsum("nam,nbm->nab", J, J)


def _eig(g: np.ndarray):
    a, b, c = g[:, 0, 0], g[:, 0, 1], g[:, 1, 1]
    phi = 0.5 * np.arctan2(2.0 * b, a - c)
    tr, det = a + c, a * c - b * b
    disc = np.sqrt(np.maximum(0.25 * (a - c) ** 2 + b * b, 0.0))
    return phi, 0.5 * tr + disc, np.maximum(0.5 * tr - disc, 0.0)


def _grad_phi(model: Model, th: np.ndarray, h: float = 1e-5) -> np.ndarray:
    out = np.empty_like(th)
    for d in range(2):
        e = np.zeros(2)
        e[d] = h
        dp = _eig(_g_theta(model, th + e))[0] - _eig(_g_theta(model, th - e))[0]
        dp = (dp + 0.5 * np.pi) % np.pi - 0.5 * np.pi
        out[:, d] = dp / (2 * h)
    return out


def _trace(model: Model, seeds: np.ndarray, *, h: float = 0.02, max_steps: int = 1500):
    """Integral curves of the sloppy eigenvector field through each seed (log-time
    coordinates), both ways, until the diagonal or `THETA_RANGE`. Returns, per seed, the
    positions and the running `log a` (the integrating factor, `d log a/ds = v_1 . grad phi`)
    and eigenvalues along the curve, ordered from one end to the other."""
    lo, hi = THETA_RANGE

    def direction(th, prev):
        phi, _, _ = _eig(_g_theta(model, th))
        u = np.column_stack([-np.sin(phi), np.cos(phi)])
        flip = np.sum(u * prev, axis=1) < 0
        u[flip] *= -1.0
        return u

    curves = []
    for sign in (1.0, -1.0):
        th = seeds.copy()
        n = th.shape[0]
        phi0, _, _ = _eig(_g_theta(model, th))
        u0 = np.column_stack([-np.sin(phi0), np.cos(phi0)])
        # orient: forward runs toward theta_2 - theta_1 growing (away from the diagonal)
        u0 *= np.where((u0[:, 1] - u0[:, 0]) >= 0, 1.0, -1.0)[:, None]
        prev = sign * u0
        pts = [th.copy()]
        alive = np.ones(n, dtype=bool)
        for _ in range(max_steps):
            if not np.any(alive):
                break
            k1 = direction(th, prev)
            k2 = direction(th + 0.5 * h * k1, k1)
            k3 = direction(th + 0.5 * h * k2, k2)
            k4 = direction(th + h * k3, k3)
            step = (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
            step /= np.linalg.norm(step, axis=1, keepdims=True)
            new = np.where(alive[:, None], th + h * step, th)
            out = (new[:, 1] - new[:, 0] <= 1e-6) | np.any(new < lo, axis=1) | np.any(new > hi, axis=1)
            alive &= ~out
            th = np.where(alive[:, None], new, th)
            prev = np.where(alive[:, None], step, prev)
            pts.append(np.where(alive[:, None], th, np.nan))
        curves.append(np.stack(pts, axis=1))  # (n, steps, 2)
    fwd, bwd = curves
    result = []
    for i in range(seeds.shape[0]):
        b = bwd[i][~np.isnan(bwd[i][:, 0])][::-1]
        f = fwd[i][~np.isnan(fwd[i][:, 0])][1:]
        result.append(np.concatenate([b, f], axis=0))
    return result


def _curve_fields(model: Model, curve: np.ndarray):
    """`r = log n - mean_g(log n) - log L` at each point of one curve (DD-R1)."""
    g = _g_theta(model, curve)
    phi, l1, l2 = _eig(g)
    seg = np.diff(curve, axis=0)
    ds = np.linalg.norm(seg, axis=1)
    u = seg / np.maximum(ds[:, None], 1e-300)
    v1 = np.column_stack([u[:, 1], -u[:, 0]])
    mid = 0.5 * (curve[1:] + curve[:-1])
    dlog_a = np.sum(v1 * _grad_phi(model, mid), axis=1) * ds
    log_a = np.concatenate([[0.0], np.cumsum(dlog_a)])
    log_n = log_a - 0.5 * np.log(np.maximum(l1, 1e-300))
    speed = np.sqrt(l2)
    dsg = 0.5 * (speed[1:] + speed[:-1]) * ds
    L = float(np.sum(dsg))
    mean_log_n = float(np.sum(0.5 * (log_n[1:] + log_n[:-1]) * dsg) / L)
    return log_n - mean_log_n - np.log(L)


class _StiffestField:
    """`log(p_ref / p_J)` for stiffest first at `D = 2`, interpolated in log decay times
    from a family of integral curves seeded along the diagonal and inside the domain."""

    def __init__(self, model: Model) -> None:
        from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

        lo, hi = THETA_RANGE
        c = np.linspace(lo + 0.05, hi - 0.05, 160)
        seeds = [np.column_stack([c - 1e-3, c + 1e-3])]
        for off in (1.5, 4.0, 8.0):
            cc = c[(c + off) < hi]
            seeds.append(np.column_stack([cc, cc + off]))
        seeds = np.concatenate(seeds)
        pts, vals = [], []
        for curve in _trace(model, seeds):
            if curve.shape[0] < 3:
                continue
            r = _curve_fields(model, curve)
            ok = np.isfinite(r)
            pts.append(curve[ok][::2])
            vals.append(r[ok][::2])
        P, V = np.concatenate(pts), np.concatenate(vals)
        self._lin = LinearNDInterpolator(P, V)
        self._near = NearestNDInterpolator(P, V)

    def __call__(self, xi: np.ndarray) -> np.ndarray:
        th = np.clip(_theta_of(xi), THETA_RANGE[0], THETA_RANGE[1])
        out = self._lin(th)
        bad = ~np.isfinite(out)
        if np.any(bad):
            out[bad] = self._near(th[bad])
        return out


def _segment_param(p0, p1, a, b):
    """Parameter along `p0 -> p1` where segment `a -> b` crosses it, or NaN."""
    d1, d2 = p1 - p0, b - a
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-15:
        return np.nan
    w = a - p0
    t = (w[0] * d2[1] - w[1] * d2[0]) / den
    u = (w[0] * d1[1] - w[1] * d1[0]) / den
    return t if (0.0 <= t <= 1.0 and 0.0 <= u <= 1.0) else np.nan


DEFAULT_TRANSVERSAL = np.array([[0.05, 0.6], [0.6, 0.95]])
"""A segment in `xi` across the sloppy curves (used when none is given)."""


def build_pref(model: Model, ranking: str | None = None, *, transversal: np.ndarray | None = None):
    """`p_ref` for the cones (`ranking=None`) or one exp-decay ranking (§4.2).

    `transversal` chooses the curve from which the stiffest-direction coordinate is
    traced; the prior must not depend on it (T15(e)). The stiffest-first density is
    computed from the labelling-free form of the Berger–Bernardo formula,
    `p_ref / p_J ∝ n(theta) / (L(psi) G(psi))` with `n = |d psi|_{g^-1}`, `L` the curve's
    Fisher length and `G` the Fisher-length geometric mean of `n` along it, in which any
    relabelling of `psi` cancels (DD-R1); the transversal enters `ranking_coordinate` only.
    """
    from infomax.jeffreys import build_jeffreys
    from infomax.priors002 import GridPrior002

    if model.family == "hypercone":
        if ranking is not None:
            raise ValueError("the cones have one ranking (relevant direction first)")
        if model.curvature == 1.0:
            prior = build_uniform(model)
            prior.name = "p_ref"
            return prior
        return _cone_pref_with_curvature(model)
    if model.family != "exp_decay":
        raise ValueError(f"no reference prior for family {model.family!r}")
    if ranking not in RANKINGS:
        raise ValueError(f"ranking must be one of {RANKINGS}")
    if model.D == 1:
        prior = build_jeffreys(model)
        prior.name = f"p_ref[{ranking}]"
        return prior
    if model.D != 2:
        raise NotImplementedError("exp-decay p_ref at D >= 3 is not implemented yet (coverage table: D <= 4)")
    if ranking in ("slowest", "fastest"):
        prior = GridPrior002(f"p_ref[{ranking}]", model, lambda xi: _bb_coordinate_log_density(model, xi, ranking))
        return prior
    field = _StiffestField(model)
    p_J = build_jeffreys(model)

    def log_unnorm(xi):
        return p_J._log_density_unnorm(xi) + field(xi)

    prior = GridPrior002("p_ref[stiffest]", model, log_unnorm)
    prior.transversal = DEFAULT_TRANSVERSAL if transversal is None else np.asarray(transversal, float)
    return prior


def ranking_coordinate(
    model: Model, ranking: str, theta: np.ndarray, *, transversal: np.ndarray | None = None
) -> np.ndarray:
    """`psi(theta)`, the coordinate a ranking names (§3.5, §4.2): `xi_D` for slowest first,
    `xi_1` for fastest first, and for stiffest first the label of the sloppy eigenvector's
    integral curve through `theta`, traced from `transversal`: the parameter in `[0, 1]`
    along the transversal segment (in `xi`) where the curve crosses it, or, for a curve
    that misses it, that of the transversal point closest to the curve (DD-R1)."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    if ranking == "slowest":
        return theta[:, -1]
    if ranking == "fastest":
        return theta[:, 0]
    if ranking != "stiffest" or model.D != 2:
        raise ValueError("stiffest first is defined at D = 2 only")
    tr = DEFAULT_TRANSVERSAL if transversal is None else np.asarray(transversal, float)
    p0, p1 = tr[0], tr[1]
    seeds = np.clip(_theta_of(theta), THETA_RANGE[0] + 1e-3, THETA_RANGE[1] - 1e-3)
    seeds[:, 1] = np.maximum(seeds[:, 1], seeds[:, 0] + 2e-6)
    out = np.empty(theta.shape[0])
    d = p1 - p0
    for i, curve in enumerate(_trace(model, seeds)):
        xi = _xi_of(curve)
        hit = np.nan
        for k in range(xi.shape[0] - 1):
            hit = _segment_param(p0, p1, xi[k], xi[k + 1])
            if np.isfinite(hit):
                break
        if not np.isfinite(hit):
            t = np.clip(((xi - p0) @ d) / (d @ d), 0.0, 1.0)
            dist = np.linalg.norm(p0 + t[:, None] * d - xi, axis=1)
            hit = float(t[np.argmin(dist)])
        out[i] = hit
    return out


# ---------------------------------------------------------------------------
# The cone with the curvature knob on
# ---------------------------------------------------------------------------


def _cone_pref_with_curvature(model: Model):
    """Berger–Bernardo with `theta_1` first and the cross-section as the rest, by
    quadrature over each cross-section (`[^3-schur]`); `norm(theta_1)` and the exponent are
    interpolated in `theta_1` between Gauss–Legendre nodes."""
    from infomax.priors002 import GridPrior002
    from infomax.quadrature import cone_theta1_rule

    D = model.D
    t1, _ = cone_theta1_rule(model.W, model.sigma_eff, q=4, cell=0.5)
    gx, gw = np.polynomial.legendre.leggauss(2)
    axes, wts = [], []
    for d in range(1, D):
        n_cells = 24 if d == 1 else 4
        edges = np.linspace(0.0, 1.0, n_cells + 1)
        h = np.diff(edges)
        axes.append((edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel())
        wts.append((0.5 * h[:, None] * gw).ravel())
    mesh = np.meshgrid(*axes, indexing="ij")
    wmesh = np.meshgrid(*wts, indexing="ij")
    cross = np.stack([g.ravel() for g in mesh], axis=-1)
    cw = np.prod(np.stack([g.ravel() for g in wmesh], axis=-1), axis=-1)

    def parts(theta):
        g = model.fim(theta)
        _, logdet = np.linalg.slogdet(g)
        _, logdet_perp = np.linalg.slogdet(g[..., 1:, 1:])
        return 0.5 * logdet_perp, 0.5 * (logdet - logdet_perp)

    log_norm = np.empty(t1.size)
    E = np.empty(t1.size)
    for k, t in enumerate(t1):
        th = np.column_stack([np.full(cross.shape[0], t), cross])
        half_ld_perp, half_log_schur = parts(th)
        root = np.exp(half_ld_perp - half_ld_perp.max())
        nrm = np.sum(cw * root)
        log_norm[k] = np.log(nrm) + half_ld_perp.max()
        E[k] = np.sum(cw * root * half_log_schur) / nrm

    # interpolate the smooth remainder of log norm: the cross-section's volume scales as
    # r(theta_1)^(D-1) outside the warped ball, which is singular in log at the tip
    log_r = lambda x: (D - 1) * np.log(np.maximum(model.taper_r(x), 1e-300))
    rem = log_norm - log_r(t1)

    def log_unnorm(theta):
        theta = np.atleast_2d(theta)
        half_ld_perp, _ = parts(theta)
        x = theta[:, 0]
        return half_ld_perp - (np.interp(x, t1, rem) + log_r(x)) + np.interp(x, t1, E)

    return GridPrior002("p_ref", model, log_unnorm)
