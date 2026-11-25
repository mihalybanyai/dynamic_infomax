"""Model families of spec 002: exponential decay, the hypercone, the constant cross-section.

Spec: specs/002-foreign-q-prediction.md §4.1 (maps, parameter sets, knobs) and §2.3
(nested natures, whose agents use a submodel).

Coordinates. In the hypercone, `theta` is the cone's own coordinates
`(theta_1, theta_2, ..., theta_D)` on `[0, W] x [0, 1]^(D-1)`. In exp-decay the model
is held in A&M's compact coordinate `xi_mu = exp(-k_mu)` on the ordered part of
`[0, 1]^D` (spec §4.1), so `Model.y` and `Model.fim` take `xi`; the log decay time
`theta_mu = -log k_mu` is used only by the priors defined in it (`p_LN`, the
stiffest-direction ranking).
"""
from __future__ import annotations

import dataclasses
import functools
from dataclasses import dataclass

import numpy as np

FAMILIES: tuple[str, ...] = ("exp_decay", "hypercone", "binomial")
"""Model families; the constant cross-section is the hypercone with `taper = 0`. The
binomial model (spec 000's Bernoulli likelihood) serves only T18 and the Komaki eye test
(§5.3), so that they run `build_plat`'s own update."""

BOX: dict[str, tuple[float, float]] = {
    "full": (0.0, 1.0),
    "matched": (float(np.exp(-1.0)), float(np.exp(-0.2))),
}
"""Exp-decay ranges of `xi` (spec §4.1, OQ-9): the whole manifold, and the window's range
(decay times 1 to 5)."""

OBSERVATION_WINDOW: tuple[float, float] = (1.0, 5.0)
"""A&M's observation times run evenly over this window (spec §4.1)."""

R0: float = 1.0
"""Cross-section scale of the constant cross-section (`taper = 0`): the cone's base
cross-section carried along the whole relevant axis. Not fixed by the spec (design
decision DD-M1 in `docs/002-foreign-q-prediction/README.md`)."""

_CONTAIN_TOL = 1e-12


@functools.lru_cache(maxsize=8)
def _times(m: int) -> np.ndarray:
    t = np.linspace(OBSERVATION_WINDOW[0], OBSERVATION_WINDOW[1], m)
    t.setflags(write=False)
    return t


@dataclass(frozen=True)
class ParameterSet:
    """The parameter set `Theta` of a model (spec §1.1, §4.1).

    `low` and `high` bound each coordinate; `ordered` restricts to
    `theta_1 <= ... <= theta_D` (exp-decay).
    """

    low: np.ndarray
    high: np.ndarray
    ordered: bool

    @property
    def D(self) -> int:
        return int(np.asarray(self.low).size)

    def contains(self, theta: np.ndarray) -> np.ndarray:
        """Boolean mask over the leading axes of `theta` (shape (..., D))."""
        theta = np.asarray(theta, dtype=float)
        lo, hi = np.asarray(self.low), np.asarray(self.high)
        inside = np.all((theta >= lo - _CONTAIN_TOL) & (theta <= hi + _CONTAIN_TOL), axis=-1)
        if self.ordered and theta.shape[-1] > 1:
            inside &= np.all(np.diff(theta, axis=-1) >= -_CONTAIN_TOL, axis=-1)
        return inside

    def sample_uniform(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """`n` states uniform on `Theta` in its own coordinates, shape (n, D)."""
        lo, hi = np.asarray(self.low, dtype=float), np.asarray(self.high, dtype=float)
        theta = lo + (hi - lo) * rng.uniform(size=(n, lo.size))
        if self.ordered:
            theta = np.sort(theta, axis=-1)
        return theta

    @property
    def log_volume(self) -> float:
        """Log of `Theta`'s volume in its own coordinates (`1/D!` of the cube when ordered)."""
        lo, hi = np.asarray(self.low, dtype=float), np.asarray(self.high, dtype=float)
        lv = float(np.sum(np.log(hi - lo)))
        if self.ordered:
            lv -= float(np.sum(np.log(np.arange(1, lo.size + 1))))
        return lv


@dataclass(frozen=True)
class Model:
    """A model of spec 002: the map `y`, its Fisher metric, `Theta` and the budget.

    `fixed` is `None` for a full model. For an agent's submodel of a nested nature
    (spec §2.3) it holds the values at which the ignored coordinates are fixed.
    `warp_radius` is the curvature knob's ball radius `rho`; it is fixed when the model is
    built (`5 sigma_eff` of the cell), so a mis-budgeted build keeps the cell's geometry.
    """

    family: str
    D: int
    m: int
    sigma: float
    N: float
    box: ParameterSet
    W: float = 50.0
    taper: float = 1.0
    falloff: float = 1.0
    curvature: float = 1.0
    fixed: np.ndarray | None = None
    warp_radius: float | None = None

    # -- budget -------------------------------------------------------------

    @property
    def sigma_eff(self) -> float:
        """The budget through the noise, `sigma / sqrt(N)` (spec §4)."""
        if self.N <= 0:
            return float("inf")
        return float(self.sigma / np.sqrt(self.N))

    def at_budget(self, N: float) -> "Model":
        """The same model at another budget (`sigma` unchanged); the warp keeps its radius."""
        return dataclasses.replace(self, N=N, warp_radius=self.rho)

    def at_noise(self, s: float) -> "Model":
        """The same model at effective noise `s` (`N = 1`, `sigma = s`), warp radius kept."""
        return dataclasses.replace(self, sigma=float(s), N=1, warp_radius=self.rho)

    @property
    def rho(self) -> float:
        """Radius of the curvature knob's warped ball (spec §4.1)."""
        if self.warp_radius is not None:
            return float(self.warp_radius)
        return 5.0 * self.sigma_eff

    # -- geometry -----------------------------------------------------------

    @property
    def D_full(self) -> int:
        """Dimension of the full model (the submodel's parent) in the hypercone."""
        return self.D + (0 if self.fixed is None else int(np.asarray(self.fixed).size))

    @property
    def m_out(self) -> int:
        """Data dimension: `m` in exp-decay, the full model's `D` in the hypercone."""
        if self.family == "exp_decay":
            return self.m
        if self.family == "hypercone":
            return self.D_full
        raise ValueError("the binomial model has no Gaussian data dimension")

    @property
    def times(self) -> np.ndarray:
        """Exp-decay's observation times, evenly spaced in A&M's window (§4.1)."""
        return _times(self.m)

    @property
    def vertex(self) -> np.ndarray:
        """The sharpened vertex `v = y(W, 0, ..., 0)` of the hypercone (§1.2, §4.1)."""
        v = np.zeros(self.D_full)
        v[0] = self.W
        return v

    @property
    def widths(self) -> np.ndarray:
        """Fall-off factors `phi^(mu-2)` of the cross-section directions (§4.1)."""
        return self.falloff ** np.arange(self.D_full - 1, dtype=float)

    def taper_r(self, theta1: np.ndarray) -> np.ndarray:
        """Cross-section scale `r(theta_1)`: `theta_1/W` with the taper on, `R0` with it
        off, and their linear interpolation in between (DD-M1)."""
        theta1 = np.asarray(theta1, dtype=float)
        return (1.0 - self.taper) * R0 + self.taper * theta1 / self.W

    def full_theta(self, theta: np.ndarray) -> np.ndarray:
        """Append the fixed coordinates of a submodel (identity for a full model)."""
        theta = np.asarray(theta, dtype=float)
        if self.fixed is None:
            return theta
        fixed = np.broadcast_to(np.asarray(self.fixed, dtype=float), theta.shape[:-1] + (np.asarray(self.fixed).size,))
        return np.concatenate([theta, fixed], axis=-1)

    def _cone_base(self, theta: np.ndarray) -> np.ndarray:
        full = self.full_theta(theta)
        r = self.taper_r(full[..., 0])
        return np.concatenate([full[..., :1], r[..., None] * self.widths * full[..., 1:]], axis=-1)

    def y(self, theta: np.ndarray) -> np.ndarray:
        """Prediction map, shape (..., D) -> (..., m_out) (spec §4.1)."""
        theta = np.asarray(theta, dtype=float)
        if self.family == "exp_decay":
            return np.mean(theta[..., :, None] ** self.times, axis=-2)
        if self.family == "hypercone":
            base = self._cone_base(theta)
            if self.curvature == 1.0:
                return base
            return warp_vertex(base, self.vertex, self.curvature, self.rho)
        raise ValueError("the binomial model has no Gaussian prediction map")

    def jacobian(self, theta: np.ndarray) -> np.ndarray:
        """`dy/dtheta`, shape (..., m_out, D), over the free coordinates."""
        theta = np.asarray(theta, dtype=float)
        if self.family == "exp_decay":
            t = self.times
            return (t[:, None] * theta[..., None, :] ** (t[:, None] - 1.0)) / self.D
        if self.family != "hypercone":
            raise ValueError("the binomial model has no Gaussian prediction map")
        full = self.full_theta(theta)
        r = self.taper_r(full[..., 0])
        dr = self.taper / self.W
        w = self.widths
        lead = theta.shape[:-1]
        Jb = np.zeros(lead + (self.D_full, self.D))
        Jb[..., 0, 0] = 1.0
        if self.D_full > 1:
            Jb[..., 1:, 0] = dr * w * full[..., 1:]
            for mu in range(1, self.D):
                Jb[..., mu, mu] = r * w[mu - 1]
        if self.curvature == 1.0:
            return Jb
        base = self._cone_base(theta)
        inside = np.linalg.norm(base - self.vertex, axis=-1) < self.rho + 1e-9
        if not np.any(inside):
            return Jb
        Jw = _warp_jacobian(base[inside], self.vertex, self.curvature, self.rho)
        Jb = Jb.copy()
        Jb[inside] = Jw @ Jb[inside]
        return Jb

    def fim(self, theta: np.ndarray) -> np.ndarray:
        """Fisher metric (1.2.1) at `sigma_eff`, shape (..., D) -> (..., D, D)."""
        J = self.jacobian(theta)
        return np.swapaxes(J, -1, -2) @ J / self.sigma_eff**2


def _ordered_box(D: int, lohi: tuple[float, float]) -> ParameterSet:
    lo, hi = lohi
    return ParameterSet(np.full(D, lo, dtype=float), np.full(D, hi, dtype=float), True)


def _cone_box(D: int, W: float) -> ParameterSet:
    low = np.zeros(D)
    high = np.ones(D)
    high[0] = W
    return ParameterSet(low, high, False)


def build_model(
    family: str,
    D: int,
    m: int = 26,
    sigma: float = 0.1,
    N: int = 1,
    *,
    box: str = "full",
    W: float = 50.0,
    taper: float = 1.0,
    falloff: float = 1.0,
    curvature: float = 1.0,
) -> Model:
    """Build a model of spec 002 §4.1.

    `curvature` is the warp's `kappa` (1.0 is off); `taper = 0` gives the constant
    cross-section (family 3).
    """
    if family == "exp_decay":
        theta_box = _ordered_box(D, BOX[box])
    elif family == "hypercone":
        theta_box = _cone_box(D, W)
    else:
        raise ValueError(f"unknown family {family!r}; binomial models come from binomial_model")
    if not (0.0 < curvature <= 1.0):
        raise ValueError("curvature (kappa) must lie in (0, 1]")
    model = Model(
        family=family, D=int(D), m=int(m), sigma=float(sigma), N=N, box=theta_box,
        W=float(W), taper=float(taper), falloff=float(falloff), curvature=float(curvature),
    )
    return dataclasses.replace(model, warp_radius=5.0 * model.sigma_eff)


def submodel(model_max: Model, D: int, fixed_value: float = 0.5) -> Model:
    """The agent's model of a nested nature (spec §2.3, §4.3).

    It frees the first `D` coordinates of `model_max` and fixes the rest at
    `fixed_value` (the box's centre); its predictions live in `model_max`'s data space.
    """
    if model_max.family != "hypercone":
        raise ValueError("nested submodels are defined in the hypercone only (§4.3)")
    if model_max.fixed is not None:
        raise ValueError("submodel of a submodel is not supported")
    if not (1 <= D <= model_max.D):
        raise ValueError(f"D = {D} must lie in [1, {model_max.D}]")
    box = ParameterSet(np.asarray(model_max.box.low)[:D].copy(), np.asarray(model_max.box.high)[:D].copy(), False)
    return dataclasses.replace(
        model_max, D=int(D), box=box, fixed=np.full(model_max.D - D, float(fixed_value)), warp_radius=model_max.rho
    )


def _smoothstep(s: np.ndarray) -> np.ndarray:
    """`S(s) = 3s^2 - 2s^3`: 0 to 1, zero slope at both ends (§4.1)."""
    return s * s * (3.0 - 2.0 * s)


def warp_vertex(y: np.ndarray, v: np.ndarray, kappa: float, rho: float) -> np.ndarray:
    """The curvature knob's local warp of prediction space (spec §4.1, OQ-12).

    Narrows the angle at the vertex `v` from pi/2 to `kappa * pi / 2` inside the ball
    of radius `rho`, and is the identity outside it.
    """
    y = np.asarray(y, dtype=float)
    if kappa == 1.0:
        return y
    v = np.asarray(v, dtype=float)
    d = y - v
    u = np.linalg.norm(d, axis=-1)
    a, d_perp = -d[..., 0], d[..., 1:]
    n_perp = np.linalg.norm(d_perp, axis=-1)
    beta = np.arctan2(n_perp, a)
    k = kappa + (1.0 - kappa) * _smoothstep(np.clip(2.0 * u / rho - 1.0, 0.0, 1.0))
    e_perp = d_perp / np.maximum(n_perp, np.finfo(float).tiny)[..., None]
    out = np.concatenate(
        [(v[0] - u * np.cos(k * beta))[..., None], (u * np.sin(k * beta))[..., None] * e_perp], axis=-1
    )
    return np.where((u < rho)[..., None], out, y)


def _warp_jacobian(y: np.ndarray, v: np.ndarray, kappa: float, rho: float, h: float = 1e-7) -> np.ndarray:
    """Central-difference Jacobian of `warp_vertex` at points `y` (n, m), shape (n, m, m)."""
    n, m = y.shape
    J = np.empty((n, m, m))
    for j in range(m):
        e = np.zeros(m)
        e[j] = h
        J[:, :, j] = (warp_vertex(y + e, v, kappa, rho) - warp_vertex(y - e, v, kappa, rho)) / (2 * h)
    return J


def binomial_model(N: int, M: int = 1) -> Model:
    """Spec 000's Bernoulli likelihood, `N` observations seen and `M` to predict, counted
    as a binomial (spec §5.2 T18, §5.3): `family = "binomial"`, `D = 1`, `Theta = [0, 1]`.

    `build_plat` on this model uses the binomial divergences and `N + M` in place of
    `N + 1`; its candidates are the grid of `theta` passed to it. The field `m` holds `M`.
    """
    return Model(
        family="binomial", D=1, m=int(M), sigma=1.0, N=int(N),
        box=ParameterSet(np.zeros(1), np.ones(1), False),
    )
