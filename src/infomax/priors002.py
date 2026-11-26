"""The prior interface shared by spec 002's cast.

Spec: specs/002-foreign-q-prediction.md §2.2, §4.2, §4.4. Every prior of the cast,
discrete (`p*`, `p_lat` on a candidate set), sample-backed (`p_proj`) or continuous
(`p_J`, `p_U`, `p_LN`, `p_LN^*`, `p_ref`), exposes the methods below, so that the
scores of §4.4 treat them alike.

Every prior evaluates its marginal at an explicit noise `s` (`_lmn`). The marginal at the
budget is `_lmn(model, xbar, sigma_eff)`, and the posterior predictive follows from two
marginals in closed form (§4.4; T17(c)): with `a = sigma_eff^2`, `b = sigma^2`,
`m(x', xbar) = N(xbar; x', (a + b) 1) m^(v)(c)`, `v = ab/(a+b)`, `c = (b xbar + a x')/(a+b)`,
so `log m(x'|xbar) = log N(xbar; x', a + b) + log m^(v)(c) - log m(xbar)`.

Continuous priors integrate by quadrature (`infomax.quadrature`): node sets whose
weights are normalised to one, so every mixture is a proper distribution (DD-Q2).
"""
from __future__ import annotations

from typing import Callable, Protocol

import numpy as np
import scipy.special
import scipy.stats

from scipy.spatial import cKDTree

from infomax.mixture import log_normal_iso, mixture_logpdf, posterior_weights, sparse_mixture_logpdf, sq_dists
from infomax.models import Model
from infomax.quadrature import cone_theta1_rule, exp_decay_grid


class Prior002(Protocol):
    """What the scores and natures need from a prior."""

    name: str

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """`n` states drawn from the prior, shape (n, D); its own world's sampler."""
        ...

    def log_marginal(self, model: Model, xbar: np.ndarray) -> np.ndarray:
        """`log m_pi(xbar)` at `sigma_eff`, shape (...,) for `xbar` (..., m_out)."""
        ...

    def log_predictive(
        self, model: Model, x_prime: np.ndarray, xbar: np.ndarray
    ) -> np.ndarray:
        """`log m_pi(x' | xbar)`, the posterior predictive at noise `sigma` (§4.4)."""
        ...


class ContinuousPrior002(Prior002, Protocol):
    """Continuous priors (`p_J`, `p_U`, `p_LN`, `p_LN^*`, `p_ref`) also expose a density."""

    log_normaliser: float

    def log_density(self, theta: np.ndarray) -> np.ndarray:
        """Normalised log density on `Theta`, in the model's own coordinates."""
        ...


# ---------------------------------------------------------------------------
# Shared behaviour
# ---------------------------------------------------------------------------


def _model_key(model: Model) -> tuple:
    fixed = None if model.fixed is None else tuple(np.round(np.asarray(model.fixed, float), 14))
    return (
        model.family, model.D, model.m, float(model.W), float(model.taper), float(model.falloff),
        float(model.curvature), round(model.rho, 14) if model.curvature != 1.0 else None, fixed,
        tuple(np.asarray(model.box.low, float)), tuple(np.asarray(model.box.high, float)),
    )


SPARSE_NODES: int = 10**9
"""Node sets larger than this would be summed sparsely (`mixture.sparse_mixture_logpdf`);
off, since the dense BLAS sum is 40 times faster at 4e4 nodes."""

ROW_BATCH_ENTRIES: int = 4_000_000
"""Data rows times nodes per batch in `posterior_predictive_moments` and `mass_within`:
their temporaries take about 51 bytes per entry, so about 200 MB per batch (DD-K4)."""


class PriorBase:
    """Common methods: the marginal at the budget, the predictive and posterior moments."""

    name: str

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:  # pragma: no cover - abstract
        raise NotImplementedError

    def nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:  # pragma: no cover - abstract
        """States and normalised log weights that represent the prior at noise `s`."""
        raise NotImplementedError

    def log_marginal(self, model: Model, xbar: np.ndarray) -> np.ndarray:
        xbar = np.asarray(xbar, dtype=float)
        lead = xbar.shape[:-1]
        out = self._lmn(model, xbar.reshape(-1, xbar.shape[-1]), model.sigma_eff)
        return out.reshape(lead)

    def log_predictive(self, model: Model, x_prime: np.ndarray, xbar: np.ndarray) -> np.ndarray:
        x_prime = np.asarray(x_prime, dtype=float)
        xbar = np.asarray(xbar, dtype=float)
        lead = xbar.shape[:-1]
        xp = x_prime.reshape(-1, x_prime.shape[-1])
        xb = xbar.reshape(-1, xbar.shape[-1])
        a, b = model.sigma_eff**2, model.sigma**2
        if not np.isfinite(a):
            return self._lmn(model, xp, model.sigma).reshape(lead)
        v = a * b / (a + b)
        c = (b * xb + a * xp) / (a + b)
        out = log_normal_iso(xb, xp, np.sqrt(a + b)) + self._lmn(model, c, np.sqrt(v)) - self._lmn(model, xb, np.sqrt(a))
        return out.reshape(lead)

    def _node_predictions(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        """`y` at the nodes and their log weights. A continuous prior's node cache already
        holds `y` for the very states `nodes` returned; anything else recomputes it (DD-K4)."""
        theta, logw = self.nodes(model, s)
        cache = getattr(self, "_node_cache", None)
        hit = None if cache is None else cache.get((_model_key(model), round(float(s), 14)))
        if hit is not None and len(hit) == 3 and hit[0] is theta:
            return hit[2], logw
        return model.y(theta), logw

    def posterior_predictive_moments(self, model: Model, xbar: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Mean and covariance of the posterior predictive of `x'` given each `xbar` (§4.5):
        `sigma^2 1 + Cov[y | xbar]`, from the prior's node representation. The posterior
        weights are formed for a batch of rows at a time (`ROW_BATCH_ENTRIES`, DD-K4)."""
        xbar = np.atleast_2d(np.asarray(xbar, dtype=float))
        Y, logw = self._node_predictions(model, model.sigma_eff)
        m = Y.shape[1]
        mus = np.empty((xbar.shape[0], m))
        covs = np.empty((xbar.shape[0], m, m))
        rows = max(1, ROW_BATCH_ENTRIES // max(1, Y.shape[0]))
        for a in range(0, xbar.shape[0], rows):
            W = posterior_weights(xbar[a : a + rows], Y, logw, model.sigma_eff)
            for j, w in enumerate(W):
                keep = w > 1e-14 * w.max()
                wk = w[keep] / w[keep].sum()
                Yk = Y[keep]
                mu = wk @ Yk
                d = Yk - mu
                mus[a + j] = mu
                covs[a + j] = model.sigma**2 * np.eye(m) + (d.T * wk) @ d
        return mus, covs

    def mass_within(self, model: Model, y0: np.ndarray, radius: float) -> np.ndarray:
        """The prior's mass on the states whose prediction lies within `radius` of each `y0`,
        a batch of rows at a time (`ROW_BATCH_ENTRIES`, DD-K4)."""
        Y, logw = self._node_predictions(model, model.sigma_eff)
        w = np.exp(logw)
        y0 = np.atleast_2d(y0)
        out = np.empty(y0.shape[0])
        rows = max(1, ROW_BATCH_ENTRIES // max(1, Y.shape[0]))
        for a in range(0, y0.shape[0], rows):
            out[a : a + rows] = (sq_dists(y0[a : a + rows], Y) <= radius**2) @ w
        return out


# ---------------------------------------------------------------------------
# Discrete and sample-backed priors
# ---------------------------------------------------------------------------


class DiscretePrior(PriorBase):
    """Atoms and weights: `p*`, the mis-budgeted `p*`, and `p_lat` on a candidate set."""

    def __init__(self, name: str, atoms: np.ndarray, weights: np.ndarray) -> None:
        atoms = np.asarray(atoms, dtype=float)
        if atoms.ndim == 1:
            atoms = atoms[:, None]
        weights = np.asarray(weights, dtype=float)
        if weights.shape != (atoms.shape[0],):
            raise ValueError(f"weights {weights.shape} do not match atoms {atoms.shape}")
        if not (np.all(np.isfinite(weights)) and np.all(weights >= 0)):
            raise ValueError("weights must be non-negative and finite")
        total = weights.sum()
        if not total > 0:
            raise ValueError("weights must not all be zero")
        self.name = name
        self.atoms = atoms
        self.weights = weights / total
        with np.errstate(divide="ignore"):
            self.log_weights = np.log(self.weights)

    @property
    def support(self) -> np.ndarray:
        return self.weights > 0

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        idx = rng.choice(self.atoms.shape[0], size=n, p=self.weights)
        return self.atoms[idx]

    def nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        keep = self.support
        return self.atoms[keep], self.log_weights[keep]

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        keep = self.support
        return mixture_logpdf(x, model.y(self.atoms[keep]), self.log_weights[keep], s)


class CloudPrior(DiscretePrior):
    """A sample-backed prior: `p_proj`'s cloud of maximum-likelihood estimates (§4.2).

    Its mixture is the weighted sum over the cloud,
    `m(x) = sum_j w_j N(x; y(theta-hat_j), sigma_eff^2 1)`, equal weights unless given (the
    importance weights of `pproj.build_pproj`), and its own sampler draws from the cloud by
    weight, so its own world matches its mixture exactly (T20). `ess` is the effective
    sample size `1 / sum w_j^2`."""

    def __init__(self, name: str, atoms: np.ndarray, weights: np.ndarray | None = None) -> None:
        atoms = np.asarray(atoms, dtype=float)
        if weights is None:
            weights = np.full(atoms.shape[0], 1.0 / atoms.shape[0])
        super().__init__(name, atoms, weights)
        self.ess = float(1.0 / np.sum(self.weights**2))


# ---------------------------------------------------------------------------
# Continuous priors
# ---------------------------------------------------------------------------


class ContinuousPrior(PriorBase):
    """A continuous prior on a model's `Theta`, integrated by quadrature.

    Subclasses set `self.model` and `self.log_normaliser`, and implement
    `_log_density_unnorm`, `sample` and `_build_nodes(model, s)`.
    """

    model: Model
    log_normaliser: float

    def __init__(self) -> None:
        self._node_cache: dict = {}

    def _log_density_unnorm(self, theta: np.ndarray) -> np.ndarray:  # pragma: no cover - abstract
        raise NotImplementedError

    def log_density(self, theta: np.ndarray) -> np.ndarray:
        theta = np.asarray(theta, dtype=float)
        inside = self.model.box.contains(theta)
        out = np.full(theta.shape[:-1], -np.inf)
        if np.any(inside):
            out[inside] = self._log_density_unnorm(theta[inside]) - self.log_normaliser
        return out

    def _build_nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:  # pragma: no cover
        raise NotImplementedError

    def nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        key = (_model_key(model), round(float(s), 14))
        hit = self._node_cache.get(key)
        if hit is None:
            theta, logw = self._build_nodes(model, s)
            keep = np.isfinite(logw)
            theta, logw = theta[keep], logw[keep]
            logw = logw - scipy.special.logsumexp(logw)
            hit = (theta, logw, model.y(theta))
            self._node_cache[key] = hit
        return hit[0], hit[1]

    def _node_y(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        self.nodes(model, s)
        hit = self._node_cache[(_model_key(model), round(float(s), 14))]
        return hit[2], hit[1]

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        Y, logw = self._node_y(model, s)
        x = np.atleast_2d(x)
        if Y.shape[0] > SPARSE_NODES and x.shape[0] > 64:
            key = ("tree", _model_key(model), round(float(s), 14))
            tree = self._node_cache.get(key)
            if tree is None:
                tree = cKDTree(Y / s)
                self._node_cache[key] = tree
            return sparse_mixture_logpdf(x, Y, logw, s, tree)
        return mixture_logpdf(x, Y, logw, s)


class GridPrior002(ContinuousPrior):
    """A continuous prior given by a log density, integrated on a quadrature grid of
    `Theta` (exp-decay's ordered grid, or a box grid for the warped cone)."""

    def __init__(
        self,
        name: str,
        model: Model,
        log_density_unnorm: Callable[[np.ndarray], np.ndarray],
        *,
        sampler: Callable[[int, np.random.Generator], np.ndarray] | None = None,
        cell_mass: Callable | None = None,
        normaliser_points: int | None = None,
        log_normaliser: float | None = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.model = model
        self._f = log_density_unnorm
        self._sampler = sampler
        self._cell_mass = cell_mass
        if log_normaliser is None:
            theta, log_vol, _ = self._grid(model, model.sigma_eff, n_per_axis=normaliser_points, for_normaliser=True)
            log_normaliser = float(scipy.special.logsumexp(log_vol + self._f(theta)))
        self.log_normaliser = log_normaliser

    def _log_density_unnorm(self, theta: np.ndarray) -> np.ndarray:
        return self._f(theta)

    def _grid(self, model: Model, s: float, *, n_per_axis: int | None = None, for_normaliser: bool = False):
        if model.family == "exp_decay":
            if for_normaliser:
                n = n_per_axis or (400 if model.D <= 2 else (90 if model.D == 3 else 40))
                nodes, log_vol, cell, edges = exp_decay_grid(model, 1.0, n_per_axis=n)
            else:
                nodes, log_vol, cell, edges = exp_decay_grid(model, s)
            return nodes, log_vol, (cell, edges)
        return box_grid(model, s, n_per_axis=n_per_axis)

    def _build_nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        theta, log_vol, extra = self._grid(model, s)
        logw = log_vol + self._f(theta)
        if self._cell_mass is not None and model.family == "exp_decay":
            cell, edges = extra
            logw = _rescale_to_cell_masses(logw, cell, self._cell_mass(edges, cell, theta))
        return theta, logw

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        if self._sampler is not None:
            return self._sampler(n, rng)
        return grid_rejection_sample(self, n, rng)


def _rescale_to_cell_masses(logw: np.ndarray, cell: np.ndarray, log_mass_by_cell: np.ndarray) -> np.ndarray:
    """Rescale node log weights so that each cell's total is its exact log mass."""
    n_cells = int(cell.max()) + 1
    tot = np.full(n_cells, -np.inf)
    np.logaddexp.at(tot, cell, logw)
    return logw - tot[cell] + log_mass_by_cell[cell]


def box_grid(model: Model, s: float, *, n_per_axis: int | None = None):
    """A Gauss–Legendre product grid on a (non-ordered) box `Theta` at noise `s`: cells of
    at most half a noise unit along each axis's largest Fisher speed (cone with curvature)."""
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    D = lo.size
    probe = model.box.sample_uniform(256, np.random.default_rng(0))
    speed = np.sqrt(np.max(np.sum(model.jacobian(probe) ** 2, axis=-2), axis=0)) / s
    q = 2
    axes, wts = [], []
    gx, gw = np.polynomial.legendre.leggauss(q)
    for d in range(D):
        L = speed[d] * (hi[d] - lo[d])
        n_cells = n_per_axis // q if n_per_axis else int(np.clip(np.ceil(L / 0.5), 2, 400))
        edges = np.linspace(lo[d], hi[d], n_cells + 1)
        h = np.diff(edges)
        axes.append((edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel())
        wts.append((0.5 * h[:, None] * gw).ravel())
    mesh = np.meshgrid(*axes, indexing="ij")
    wmesh = np.meshgrid(*wts, indexing="ij")
    theta = np.stack([g.ravel() for g in mesh], axis=-1)
    log_vol = np.sum(np.log(np.stack([g.ravel() for g in wmesh], axis=-1)), axis=-1)
    return theta, log_vol, None


def grid_rejection_sample(prior: GridPrior002, n: int, rng: np.random.Generator) -> np.ndarray:
    """Exact draws from a grid prior by rejection (DD-Q3): a cell is proposed with
    probability proportional to its volume times the largest density at its nodes, a point
    is drawn uniformly in the cell's part of `Theta`, and accepted with probability
    `f(point) / (K f_max(cell))`."""
    model = prior.model
    D = model.D
    if model.family == "exp_decay":
        theta, log_vol, cell, edges = exp_decay_grid(model, 0.05 if D <= 2 else 0.2, q=2)
        n_cells = int(cell.max()) + 1
        first = np.full(n_cells, -1)
        first[cell[::-1]] = np.arange(cell.size)[::-1]
        idx = np.clip(np.searchsorted(edges, theta[first], side="right") - 1, 0, edges.size - 2)
        cidx = np.sort(idx, axis=-1)
        c_lo, c_hi = edges[cidx], edges[cidx + 1]
        log_cvol = np.full(n_cells, -np.inf)
        np.logaddexp.at(log_cvol, cell, log_vol)
        ld = prior._log_density_unnorm(theta)
        f_max = np.full(n_cells, -np.inf)
        np.maximum.at(f_max, cell, ld)
    else:
        lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
        n_ax = 24
        edges = [np.linspace(lo[d], hi[d], n_ax + 1) for d in range(D)]
        grids = np.meshgrid(*[np.arange(n_ax)] * D, indexing="ij")
        cidx = np.stack([g.ravel() for g in grids], axis=-1)
        c_lo = np.stack([edges[d][cidx[:, d]] for d in range(D)], axis=-1)
        c_hi = np.stack([edges[d][cidx[:, d] + 1] for d in range(D)], axis=-1)
        n_cells = cidx.shape[0]
        log_cvol = np.sum(np.log(c_hi - c_lo), axis=-1)
        probe = c_lo[:, None, :] + (c_hi - c_lo)[:, None, :] * np.array(np.meshgrid(*[[0.15, 0.5, 0.85]] * D, indexing="ij")).reshape(D, -1).T[None]
        ld = prior._log_density_unnorm(probe.reshape(-1, D)).reshape(n_cells, -1)
        f_max = np.max(ld, axis=1)
    logp = log_cvol + f_max
    ok = np.isfinite(logp)
    p = np.zeros(n_cells)
    p[ok] = np.exp(logp[ok] - scipy.special.logsumexp(logp[ok]))
    p /= p.sum()
    K = 4.0
    out = []
    got = 0
    while got < n:
        m = int(2.0 * K * (n - got)) + 64
        k = rng.choice(n_cells, size=m, p=p)
        pt = c_lo[k] + (c_hi[k] - c_lo[k]) * rng.uniform(size=(m, D))
        if model.box.ordered:
            pt = np.sort(pt, axis=-1)
        ld_pt = prior._log_density_unnorm(pt)
        acc = np.log(rng.uniform(size=m)) < ld_pt - f_max[k] - np.log(K)
        pts = pt[acc & np.isfinite(ld_pt)]
        out.append(pts)
        got += pts.shape[0]
    return np.concatenate(out)[:n]


class ExpDecayProductPrior(GridPrior002):
    """An exp-decay prior whose unordered law is i.i.d. across rates with per-axis density
    `h`, interval log mass `log_H_interval(a, b)` and quantile map `inv_H(a, b, u)` (the
    point at a fraction `u` of the law's mass between `a` and `b`): the ordered density is
    `D! prod_mu h(xi_mu)`. Its quadrature places the nodes by Gauss–Legendre in each rate's
    CDF within each cell, so every cell carries its exact mass and a density spike (as
    `p_LN`'s at `xi -> 0`) is integrated exactly along each axis (DD-Q2)."""

    def __init__(
        self,
        name: str,
        model: Model,
        log_h: Callable[[np.ndarray], np.ndarray],
        log_H_interval: Callable[[np.ndarray, np.ndarray], np.ndarray],
        sampler: Callable[[int, np.random.Generator], np.ndarray],
        inv_H: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray] | None = None,
    ) -> None:
        D = model.D
        self._log_dfact = float(scipy.special.gammaln(D + 1))
        self._log_h = log_h
        self._log_H_interval = log_H_interval
        self._inv_H = inv_H

        def f(theta):
            return self._log_dfact + np.sum(log_h(theta), axis=-1)

        super().__init__(name, model, f, sampler=sampler, log_normaliser=0.0)

    def _build_nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        if model.family != "exp_decay" or self._inv_H is None:
            return super()._build_nodes(model, s)
        nodes, log_vol, _, _ = exp_decay_grid(model, s, axis_measure=(self._log_H_interval, self._inv_H))
        return nodes, log_vol + self._log_dfact


class ConeProductPrior(ContinuousPrior):
    """A hypercone prior with a `theta_1` law and a uniform cross-section (`p_U`, `p_J`,
    and the cone natures), curvature off. The cross-section integrates in closed form:
    `∫_0^1 N(x_mu; a theta, s^2) d theta = [Phi((a - x_mu)/s) - Phi(-x_mu/s)] / a` with
    `a = r(theta_1) phi^(mu-2)` (§4.3, "Floors")."""

    def __init__(
        self,
        name: str,
        model: Model,
        log_pdf1: Callable[[np.ndarray], np.ndarray],
        sample1: Callable[[int, np.random.Generator], np.ndarray],
    ) -> None:
        super().__init__()
        if model.family != "hypercone" or model.curvature != 1.0:
            raise ValueError("ConeProductPrior needs the hypercone with the curvature knob off")
        self.name = name
        self.model = model
        self._log_pdf1 = log_pdf1
        self._sample1 = sample1
        self.log_normaliser = 0.0  # log_pdf1 is normalised on [0, W]; the cross-section has volume 1

    def _log_density_unnorm(self, theta: np.ndarray) -> np.ndarray:
        return self._log_pdf1(np.asarray(theta)[..., 0])

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        t1 = self._sample1(n, rng)
        rest = rng.uniform(size=(n, self.model.D - 1))
        return np.column_stack([t1, rest])

    def _theta1_rule(self, model: Model, s: float):
        key = ("t1", model.W, round(float(s), 14))
        hit = self._node_cache.get(key)
        if hit is None:
            t, w = cone_theta1_rule(model.W, s)
            lw = np.log(w) + self._log_pdf1(t)
            keep = np.isfinite(lw)
            t, lw = t[keep], lw[keep]
            lw -= scipy.special.logsumexp(lw)
            hit = (t, lw)
            self._node_cache[key] = hit
        return hit

    def _per_node_terms(self, model: Model, x: np.ndarray, s: float):
        """`log` of each `theta_1` node's contribution, shape (n, K)."""
        t, lw = self._theta1_rule(model, s)
        r = model.taper_r(t)  # (K,)
        w = model.widths  # (D_full - 1,)
        x = np.atleast_2d(x)
        out = lw[None, :] - 0.5 * ((x[:, :1] - t[None, :]) / s) ** 2 - 0.5 * np.log(2 * np.pi * s**2)
        D = model.D
        for mu in range(1, model.D_full):
            a = r * w[mu - 1]  # (K,)
            xm = x[:, mu : mu + 1]  # (n, 1)
            if mu < D:
                out += _log_uniform_gauss(xm, a[None, :], s)
            else:
                fix = float(np.asarray(model.fixed)[mu - D])
                out += -0.5 * ((xm - a[None, :] * fix) / s) ** 2 - 0.5 * np.log(2 * np.pi * s**2)
        return out

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        x = np.atleast_2d(x)
        out = np.empty(x.shape[0])
        step = 256
        for a in range(0, x.shape[0], step):
            out[a : a + step] = scipy.special.logsumexp(self._per_node_terms(model, x[a : a + step], s), axis=1)
        return out

    def nodes(self, model: Model, s: float) -> tuple[np.ndarray, np.ndarray]:
        """A quasi-random sample of the prior (Sobol, fixed scramble), equal weights: used
        only where a node set over the whole cross-section is needed (`mass_within`)."""
        key = ("qmc", model.D)
        hit = self._node_cache.get(key)
        if hit is None:
            u = scipy.stats.qmc.Sobol(d=self.model.D, scramble=True, seed=7).random(2**14)
            t_grid = np.linspace(0.0, self.model.W, 20001)
            lp = self._log_pdf1(t_grid)
            cdf = np.concatenate([[0.0], np.cumsum(0.5 * (np.exp(lp[1:]) + np.exp(lp[:-1])) * np.diff(t_grid))])
            cdf /= cdf[-1]
            t1 = np.interp(u[:, 0], cdf, t_grid)
            theta = np.column_stack([t1, u[:, 1:]])
            hit = (theta, np.full(theta.shape[0], -np.log(theta.shape[0])))
            self._node_cache[key] = hit
        return hit

    def posterior_predictive_moments(self, model: Model, xbar: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        xbar = np.atleast_2d(np.asarray(xbar, dtype=float))
        s = model.sigma_eff
        t, lw = self._theta1_rule(model, s)
        terms = self._per_node_terms(model, xbar, s)
        post = np.exp(terms - scipy.special.logsumexp(terms, axis=1, keepdims=True))  # (n, K)
        r = model.taper_r(t)
        w = model.widths
        n, m = xbar.shape[0], model.m_out
        D = model.D
        mus = np.empty((n, m))
        covs = np.empty((n, m, m))
        for i in range(n):
            p = post[i]
            keep = p > 1e-14 * p.max()
            pk = p[keep] / p[keep].sum()
            tk, rk = t[keep], r[keep]
            M = np.empty((pk.size, m))
            V = np.zeros((pk.size, m))
            M[:, 0] = tk
            for mu in range(1, model.D_full):
                a = rk * w[mu - 1]
                if mu < D:
                    mean_y, var_y = _truncated_gauss_moments(xbar[i, mu], a, s)
                    M[:, mu], V[:, mu] = mean_y, var_y
                else:
                    M[:, mu] = a * float(np.asarray(model.fixed)[mu - D])
            mu_i = pk @ M
            d = M - mu_i
            mus[i] = mu_i
            covs[i] = model.sigma**2 * np.eye(m) + (d.T * pk) @ d + np.diag(pk @ V)
        return mus, covs


def _log_uniform_gauss(x: np.ndarray, a: np.ndarray, s: float) -> np.ndarray:
    """`log [(Phi((a - x)/s) - Phi(-x/s)) / a]`, the density of `x = y + noise` for `y`
    uniform on `[0, a]`; the `a -> 0` limit is `N(x; a/2, s^2)`."""
    x, a = np.broadcast_arrays(np.asarray(x, float), np.asarray(a, float))
    out = np.empty(x.shape)
    small = a < 1e-6 * s
    if np.any(small):
        out[small] = -0.5 * ((x[small] - 0.5 * a[small]) / s) ** 2 - 0.5 * np.log(2 * np.pi * s**2)
    big = ~small
    if np.any(big):
        out[big] = log_diff_ndtr((a[big] - x[big]) / s, -x[big] / s) - np.log(a[big])
    return out


def log_diff_ndtr(u: np.ndarray, l: np.ndarray) -> np.ndarray:
    """`log(Phi(u) - Phi(l))` for `u > l`, stable in both tails."""
    u, l = np.broadcast_arrays(np.asarray(u, float), np.asarray(l, float))
    out = np.empty(u.shape)
    pos = l > 0
    # right tail: Phi(u) - Phi(l) = Phi(-l) - Phi(-u)
    a = scipy.special.log_ndtr(-l[pos])
    b = scipy.special.log_ndtr(-u[pos])
    out[pos] = a + np.log1p(-np.exp(np.minimum(b - a, 0.0)) + 0.0)
    a = scipy.special.log_ndtr(u[~pos])
    b = scipy.special.log_ndtr(l[~pos])
    out[~pos] = a + np.log1p(-np.exp(np.minimum(b - a, 0.0)) + 0.0)
    return out


def _truncated_gauss_moments(x: float, a: np.ndarray, s: float) -> tuple[np.ndarray, np.ndarray]:
    """Mean and variance of `y` uniform on `[0, a]` given `x = y + N(0, s^2)`: the normal
    `N(x, s^2)` truncated to `[0, a]`."""
    a = np.asarray(a, dtype=float)
    mean = np.empty(a.shape)
    var = np.empty(a.shape)
    small = a < 1e-6 * s
    mean[small] = 0.5 * a[small]
    var[small] = a[small] ** 2 / 12.0
    big = ~small
    if np.any(big):
        lo, hi = (0.0 - x) / s, (a[big] - x) / s
        m_, v_ = scipy.stats.truncnorm.stats(lo, hi, loc=x, scale=s, moments="mv")
        mean[big], var[big] = m_, v_
    return mean, var
