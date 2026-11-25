"""The natures of spec 002 (§2.3, §4.3): round robin, nested and stress natures.

A nature is a tuple `(kind, arg)`: `("own", prior)` for a prior's own world,
`("nested", name)` with `name` in `NESTED`, or `("stress", name)` with `name` in
`STRESS`.

Each nature is represented by a prior-like object (`nature_prior`) with the same
interface as the cast, so its data marginal (the row's floor, §4.3) and its posterior
predictive come from the same code: the cone natures are `ConeProductPrior`s (a
`theta_1` law and a uniform cross-section, integrated in closed form); few rates is a
one-dimensional law on the diagonal of exp-decay's `Theta`; the sharpened vertex is a
quadrature over the face pieces within `rho` of `v`.
"""
from __future__ import annotations

import numpy as np
import scipy.special
import scipy.stats

from infomax.models import Model
from infomax.priors002 import ConeProductPrior, PriorBase

NESTED: tuple[str, ...] = ("thin", "thick", "few_rates")
"""Nested natures: the hypercone's thin and thick halves (at `D_max`), exp-decay's few rates."""

STRESS: tuple[str, ...] = ("vertex", "interior")
"""Stress natures, hypercone only: the sharpened vertex and the smooth interior."""

D_MAX: int = 26
"""Dimension of the hypercone in which the nested natures live (§4.3)."""

FEW_RATES_WINDOW: tuple[float, float] = (0.0, float(np.log(5.0)))
"""The few-rates nature's log decay time is uniform on the observation window (§4.3)."""


# ---------------------------------------------------------------------------
# Nature objects
# ---------------------------------------------------------------------------


def _uniform_half(model: Model, which: str) -> ConeProductPrior:
    W = model.W
    lo = 0.0 if which == "thin" else W / 2

    def log_pdf1(t):
        t = np.asarray(t, float)
        return np.where((t >= lo) & (t <= lo + W / 2), -np.log(W / 2), -np.inf)

    return ConeProductPrior(f"nested:{which}", model, log_pdf1, lambda n, rng: lo + (W / 2) * rng.uniform(size=n))


def _interior(model: Model) -> ConeProductPrior:
    W = model.W
    s = 7.5 * model.sigma_eff  # three atom spacings of 2.5 Fisher lengths ([^1-spacing])
    law = scipy.stats.truncnorm(-W / 2 / s, W / 2 / s, loc=W / 2, scale=s)
    return ConeProductPrior(
        "stress:interior", model, lambda t: law.logpdf(np.asarray(t, float)), lambda n, rng: law.rvs(size=n, random_state=rng)
    )


class FewRatesNature(PriorBase):
    """`D_0 = 1`: one rate shared by every component, its log decay time uniform on
    `[0, log 5]` (§4.3). Integrated by Gauss–Legendre nodes in the log decay time."""

    def __init__(self, model: Model) -> None:
        self.name = "nested:few_rates"
        self.model = model
        self._cache: dict = {}

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        tau = rng.uniform(*FEW_RATES_WINDOW, size=n)
        xi = np.exp(-np.exp(-tau))
        return np.repeat(xi[:, None], self.model.D, axis=1)

    def nodes(self, model: Model, s: float):
        key = round(float(s), 14)
        hit = self._cache.get(key)
        if hit is None:
            a, b = FEW_RATES_WINDOW
            fine = np.linspace(a, b, 2001)
            xi = np.exp(-np.exp(-fine))
            Y = model.y(np.repeat(xi[:, None], model.D, axis=1))
            L = np.sum(np.linalg.norm(np.diff(Y, axis=0), axis=1)) / s
            n_cells = max(8, int(np.ceil(L / 0.25)))
            edges = np.linspace(a, b, n_cells + 1)
            gx, gw = np.polynomial.legendre.leggauss(4)
            h = np.diff(edges)
            tau = (edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel()
            w = (0.5 * h[:, None] * gw).ravel() / (b - a)
            xi = np.exp(-np.exp(-tau))
            theta = np.repeat(xi[:, None], model.D, axis=1)
            hit = (theta, np.log(w) - scipy.special.logsumexp(np.log(w)))
            self._cache[key] = hit
        return hit

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        from infomax.mixture import mixture_logpdf

        theta, logw = self.nodes(model, s)
        return mixture_logpdf(x, model.y(theta), logw, s)


class VertexNature(PriorBase):
    """The sharpened-vertex stress nature: uniform by area in `theta` on the parts of the
    faces that meet `v` (the base face `theta_1 = W` and the lateral faces `theta_mu = 0`)
    lying within `rho` of `v` in prediction space (§4.3). Distances are those of the
    unwarped cone, which the warp keeps (§4.1)."""

    def __init__(self, model: Model) -> None:
        if model.family != "hypercone" or model.fixed is not None:
            raise ValueError("the vertex nature lives in the full hypercone")
        self.name = "stress:vertex"
        self.model = model
        self._cache: dict = {}
        self._boxes = self._face_boxes()

    def _face_boxes(self):
        """Per face: (fixed coordinate, its value, lower and upper bounds of the box)."""
        m, W, rho = self.model, self.model.W, self.model.rho
        D = m.D
        w = m.widths
        r_min = max((W - rho) / W, 1e-12) if m.taper > 0 else 1.0
        boxes = []
        lo, hi = np.zeros(D), np.ones(D)
        lo[0], hi[0] = W, W
        for mu in range(1, D):
            hi[mu] = min(1.0, rho / w[mu - 1])
        boxes.append((0, W, lo.copy(), hi.copy()))
        for nu in range(1, D):
            lo, hi = np.zeros(D), np.ones(D)
            lo[0], hi[0] = max(0.0, W - rho), W
            hi[nu] = 0.0
            for mu in range(1, D):
                if mu != nu:
                    hi[mu] = min(1.0, rho / (r_min * w[mu - 1]))
            boxes.append((nu, 0.0, lo, hi))
        return boxes

    def _unwarped_u(self, theta: np.ndarray) -> np.ndarray:
        m = self.model
        return np.linalg.norm(m._cone_base(theta) - m.vertex, axis=-1)

    def _face_area_boxes(self):
        out = []
        for nu, val, lo, hi in self._boxes:
            free = [d for d in range(self.model.D) if d != nu]
            out.append(float(np.prod(hi[free] - lo[free])))
        return np.array(out)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        rho = self.model.rho
        box_area = self._face_area_boxes()
        p = box_area / box_area.sum()
        out, got = [], 0
        while got < n:
            k = 4 * (n - got) + 64
            face = rng.choice(len(self._boxes), size=k, p=p)
            th = np.empty((k, self.model.D))
            for f, (nu, val, lo, hi) in enumerate(self._boxes):
                sel = face == f
                th[sel] = lo + (hi - lo) * rng.uniform(size=(int(sel.sum()), self.model.D))
                th[sel, nu] = val
            keep = self._unwarped_u(th) <= rho
            out.append(th[keep])
            got += int(keep.sum())
        return np.concatenate(out)[:n]

    def nodes(self, model: Model, s: float):
        key = round(float(s), 14)
        hit = self._cache.get(key)
        if hit is None:
            rho = self.model.rho
            gx, gw = np.polynomial.legendre.leggauss(2)
            thetas, logws = [], []
            for nu, val, lo, hi in self._boxes:
                free = [d for d in range(self.model.D) if d != nu]
                axes, wts = [], []
                for d in free:
                    n_cells = 40 if (hi[d] - lo[d]) > 0 else 1
                    edges = np.linspace(lo[d], hi[d], n_cells + 1)
                    h = np.diff(edges)
                    axes.append((edges[:-1, None] + 0.5 * h[:, None] * (gx + 1.0)).ravel())
                    wts.append((0.5 * h[:, None] * gw).ravel())
                mesh = np.meshgrid(*axes, indexing="ij")
                wmesh = np.meshgrid(*wts, indexing="ij")
                th = np.empty((mesh[0].size, self.model.D))
                for j, d in enumerate(free):
                    th[:, d] = mesh[j].ravel()
                th[:, nu] = val
                wt = np.prod(np.stack([g.ravel() for g in wmesh], axis=-1), axis=-1)
                keep = self._unwarped_u(th) <= rho
                thetas.append(th[keep])
                logws.append(np.log(wt[keep]))
            theta, logw = np.concatenate(thetas), np.concatenate(logws)
            hit = (theta, logw - scipy.special.logsumexp(logw))
            self._cache[key] = hit
        return hit

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        from infomax.mixture import mixture_logpdf

        theta, logw = self.nodes(model, s)
        return mixture_logpdf(x, model.y(theta), logw, s)


class QbarPrior(PriorBase):
    """`q̄`: the equal-weight mixture of one cell's rows; not itself a row (§4.2, §2.5)."""

    def __init__(self, rows: list[tuple]) -> None:
        self.name = "q̄"
        self.rows = list(rows)

    def _row_objects(self, model: Model):
        return [nature_prior(model, row) for row in self.rows]

    def sample(self, n: int, rng: np.random.Generator, model: Model | None = None) -> np.ndarray:
        pick = rng.integers(0, len(self.rows), size=n)
        out = None
        for r, row in enumerate(self.rows):
            sel = pick == r
            k = int(sel.sum())
            if k == 0:
                continue
            if row[0] == "own":
                th = row[1].sample(k, rng)
            else:
                if model is None:
                    raise ValueError("q̄ with a nested or stress row needs the model to sample")
                th = nature_prior(model, row).sample(k, rng)
            if out is None:
                out = np.empty((n, th.shape[1]))
            out[sel] = th
        return out

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        each = np.stack([obj._lmn(model, x, s) for obj in self._row_objects(model)])
        return scipy.special.logsumexp(each, axis=0) - np.log(len(self.rows))

    def posterior_predictive_moments(self, model: Model, xbar: np.ndarray):
        xbar = np.atleast_2d(xbar)
        objs = self._row_objects(model)
        lm = np.stack([o.log_marginal(model, xbar) for o in objs])  # (R, n)
        pw = np.exp(lm - scipy.special.logsumexp(lm, axis=0))
        mus, covs = zip(*[o.posterior_predictive_moments(model, xbar) for o in objs])
        mus, covs = np.stack(mus), np.stack(covs)  # (R, n, m), (R, n, m, m)
        mu = np.einsum("rn,rnm->nm", pw, mus)
        d = mus - mu[None]
        cov = np.einsum("rn,rnab->nab", pw, covs + d[..., :, None] * d[..., None, :])
        return mu, cov


def nature_prior(model: Model, nature: tuple):
    """The prior-like object behind a nature (its sampler, marginal and predictive)."""
    kind, arg = nature
    if kind == "own":
        return arg
    if kind == "nested":
        if arg in ("thin", "thick"):
            return _uniform_half(model, arg)
        if arg == "few_rates":
            return FewRatesNature(model)
    if kind == "stress":
        if arg == "interior":
            return _interior(model)
        if arg == "vertex":
            return VertexNature(model)
    raise ValueError(f"unknown nature {nature!r}")


def label(nature: tuple) -> str:
    """The label recorded with each draw (§6.3): `own:<prior name>`, or the nature's name."""
    kind, arg = nature
    return f"own:{arg.name}" if kind == "own" else f"{kind}:{arg}"


def sample_nature(model: Model, nature: tuple, n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """`n` draws of `theta` from the nature, with a label per draw (§4.3).

    For a nested hypercone nature `model` is the `D_max` model; for few rates it is the
    agent's model, in whose coordinates all components share the drawn rate.
    """
    kind, arg = nature
    if kind == "own" and isinstance(arg, QbarPrior):
        theta = arg.sample(n, rng, model=model)
    else:
        theta = nature_prior(model, nature).sample(n, rng)
    return theta, np.full(n, label(nature), dtype=object)


def nature_log_marginal(model: Model, nature: tuple, xbar: np.ndarray) -> np.ndarray:
    """`log m_q(xbar)` at `sigma_eff`, the integral behind a row's floor (§4.3)."""
    return nature_prior(model, nature).log_marginal(model, xbar)


def submodel_floor(model_max: Model, D: int, theta: np.ndarray) -> np.ndarray:
    """The submodel's own floor per draw, `N ||y(theta) - y(theta^(D))||^2 / (2 sigma^2)` (§4.3)."""
    theta = np.asarray(theta, dtype=float)
    fixed = theta.copy()
    fixed[:, D:] = 0.5
    d = model_max.y(theta) - model_max.y(fixed)
    return model_max.N * np.sum(d * d, axis=-1) / (2.0 * model_max.sigma**2)


def build_qbar(rows: list[tuple]):
    """`q̄`: the equal-weight mixture of one cell's rows; not itself a row (§4.2, §2.5)."""
    return QbarPrior(rows)


def cell_rows(model: Model, cast: dict) -> list[tuple]:
    """The rows (natures) of a cell whose agent model is `model` (§2.3, §4.3): the own
    world of every prior in `cast` except `q̄`, which is not a row; few rates in exp-decay;
    in the hypercone the interior stress nature, and the vertex one with curvature on. The
    hypercone's nested halves are rows only of a submodel agent's cell, whose nature model
    is the `D_max` cone."""
    rows = [("own", p) for p in cast.values() if not isinstance(p, QbarPrior)]
    if model.family == "exp_decay":
        rows.append(("nested", "few_rates"))
    elif model.family == "hypercone":
        if model.fixed is not None:
            rows += [("nested", "thin"), ("nested", "thick")]
        else:
            rows.append(("stress", "interior"))
            if model.curvature != 1.0:
                rows.append(("stress", "vertex"))
    return rows
