"""Continuous priors beyond the quadrature grids (spec 002 §4.2, §4.4, OQ-13; DD-Q4).

Exp-decay's tensor grids in `xi` grow combinatorially with `D`, and Jeffreys' grid loses mass
where rates nearly coincide from `D = 4` (2026-11-26). There a continuous prior is a weighted
cloud of its own draws (`SampledPrior`, a `CloudPrior`). Its marginal is the mixture over the
cloud where the cloud has draws near `x`. Where the prior is thin near `x`, the cloud has none,
and `per_point_log_marginal` estimates `log m(x)` by importance sampling from the posterior
itself, found by optimisation in log decay times (OQ-14). `_lmn` routes between the two, so
`log_marginal` and `log_predictive` both use the routed marginal.

Jeffreys is sampled by adaptive importance sampling in unordered log decay times
`theta = -log(-log xi)`, where its density is `sqrt(det g)` times the Jacobian of `xi`
(Jeffreys is invariant) and symmetric under swapping rates. The first round draws independent
Student-t log times (`T_DF` degrees of freedom); each later round draws from a Gaussian kernel
density of the previous weighted cloud, with `ALPHA` of the first law as the defensive part.
Toward slow rates (`theta -> +inf`) Jeffreys' density in log time falls only exponentially, so
a normal defensive part left the weights unbounded there: at `D = 7` one final draw took
about 5000 times the mean weight and left 15 effective draws of 20000 (2026-11-26). The t's
polynomial tails bound them. Rounds stop once `log Z` has varied by less than `LOGZ_TOL` over
three rounds; a last round of `N_CLOUD` draws gives the cloud and the normaliser. A last round
whose effective sample share falls below `FINAL_ESS_SHARE` of the adaptive rounds' median is
redrawn, at most `FINAL_REDRAWS` times, and then the build fails. Builds are deterministic
(`SAMPLED_SEED`), since the builders take no generator (`skills/manage-randomness.md`, rule 7).
"""
from __future__ import annotations

import hashlib
import itertools
import math
import warnings
from math import lgamma

import numpy as np
import scipy.optimize
import scipy.special
import scipy.stats

from infomax.mixture import log_normal_iso, mixture_logpdf
from infomax.models import Model
from infomax.priors002 import CloudPrior

SAMPLED_SEED: int = 20261126
N_CLOUD: int = 20000
N_ROUND: int = 8000
ALPHA: float = 0.1
T_DF: float = 3.0
"""Degrees of freedom of the defensive Student-t in log time: tails heavier than Jeffreys'."""
LOGZ_TOL: float = 0.02
MAX_ROUNDS: int = 15
FINAL_ESS_SHARE: float = 0.5
FINAL_REDRAWS: int = 3
JEFFREYS_SAMPLED_FROM_D: int = 4
"""Exp-decay `p_J` is sampled from this `D` (its grid misses 5% of the mass at `D = 4`)."""
GRID_MAX_D: int = 5
"""Exp-decay product laws (`p_U`, `p_LN`) keep their grids up to this `D` (843k nodes at `D = 5`)."""
N_PROPOSAL: int = 1000
N_CENTRES: int = 200
LOCAL_SHARE: float = 0.8
"""The superseded kernel estimator's settings (`kernel_log_marginal`)."""

# the per-point estimate (§4.4, OQ-14)
N0_THIN: float = 300.0
"""A point is thin, and estimated per point, when the cloud weighted by its likelihood keeps
fewer effective draws than this. The cloud's mixture is an importance-sampling estimate of
`m(x)` with the prior as proposal, so its relative error is about `1 / sqrt(n0)`. At `D = 3`,
over 896 data at thin and typical states, the cloud's error per datum was at most 0.056 nats
for `n0 >= 300` and up to 0.26 for `n0 >= 100` (2026-11-26)."""
N_PER_POINT: int = 1000
N_STARTS: int = 3
MAX_MODES: int = 3
T_NU: tuple[float, float] = (5.0, 3.0)
CORE_SCALE: tuple[float, float] = (1.5, 2.0)
WIDE_SCALE: float = 3.0
WIDE_SHARE: float = 0.2
THETA_RANGE: tuple[float, float] = (-8.0, 35.0)
"""Log decay times the mode search may visit: beyond them `xi` rounds to 0 or 1 in double
precision."""
EIG_FLOOR: float = 1e-2
"""Laplace precision floor: a flat direction gets a scale of 10 log-time units."""
CLUSTER_GAP: float = 6.0
"""Neighbouring sorted mode coordinates closer than this many core scales share a block."""
MAX_GROUP: int = 5040
"""At most this many relabellings (7!); larger blocks are split at their widest gap."""
PERM_CHUNK: int = 256
PER_POINT_MAX_D: int = 5
"""Above this `D` the per-point estimate is not validated: at `D = 7` it kept 0.1-1% of its
draws effective for Jeffreys, and its two variants differed by up to 0.9 nats (2026-11-26).
It still runs there, with a warning (OQ-14)."""
MIN_EFFECTIVE: float = 20.0
"""A per-point estimate with fewer effective draws than this is flagged."""


def _theta_of(xi):
    """Log decay time `-log(-log xi)`, finite at the faces (`xi` clipped to (1e-300, 1 - 1e-16))."""
    return -np.log(-np.log(np.clip(xi, 1e-300, 1.0 - 1e-16)))


def _laplace_cov(obj, mu: np.ndarray, h: float = 1e-3) -> np.ndarray:
    """The inverse of `obj`'s finite-difference Hessian at `mu`, eigenvalues floored at
    `EIG_FLOOR`; a unit covariance if the Hessian is not finite (a mode on a bound)."""
    D = mu.size
    E = np.eye(D) * h
    H = np.empty((D, D))
    for i in range(D):
        for j in range(i, D):
            H[i, j] = H[j, i] = (obj(mu + E[i] + E[j]) - obj(mu + E[i] - E[j]) - obj(mu - E[i] + E[j])
                                 + obj(mu - E[i] - E[j])) / (4 * h * h)
    if not np.all(np.isfinite(H)) or np.max(np.abs(H)) > 1e250:
        return np.eye(D)
    w, V = np.linalg.eigh(H)
    return (V / np.maximum(w, EIG_FLOOR)) @ V.T


def _clusters(mu: np.ndarray, scale: np.ndarray) -> list[np.ndarray]:
    """Blocks of consecutive coordinates of the sorted `mu` closer than `CLUSTER_GAP` scales,
    split at their widest gap until the within-block permutations number at most `MAX_GROUP`."""
    gaps = np.diff(mu) / (CLUSTER_GAP * np.maximum(scale[:-1], scale[1:]))
    cuts = set((np.flatnonzero(gaps >= 1.0) + 1).tolist())
    while True:
        edges = [0] + sorted(cuts) + [mu.size]
        blocks = [np.arange(a, b) for a, b in zip(edges[:-1], edges[1:])]
        if np.prod([math.factorial(len(b)) for b in blocks]) <= MAX_GROUP:
            return blocks
        inner = max(blocks, key=len)[1:]
        cuts.add(int(inner[np.argmax(gaps[inner - 1])]))


def _block_permutations(blocks: list[np.ndarray]) -> np.ndarray:
    """Every permutation of the coordinates that permutes within each block, as index rows."""
    parts = [list(itertools.permutations(b.tolist())) for b in blocks]
    return np.array([sum((list(q) for q in combo), []) for combo in itertools.product(*parts)], dtype=int)


def _mvt_logpdf(z: np.ndarray, mu: np.ndarray, L: np.ndarray, nu: float) -> np.ndarray:
    """Multivariate t log density over the last axis, scale `L L^T`."""
    d = mu.size
    u = np.linalg.solve(L, (z - mu).reshape(-1, d).T).T.reshape(z.shape)
    return (scipy.special.gammaln((nu + d) / 2) - scipy.special.gammaln(nu / 2) - 0.5 * d * np.log(nu * np.pi)
            - np.sum(np.log(np.diag(L))) - 0.5 * (nu + d) * np.log1p(np.sum(u * u, -1) / nu))


class SampledPrior(CloudPrior):
    """A continuous prior carried as a weighted cloud of its draws in `xi`, with its
    normalised log density (`log_density`), for the per-point marginal (§4.4)."""

    def __init__(self, name: str, model: Model, atoms: np.ndarray, weights: np.ndarray, log_density, *,
                 log_normaliser: float = 0.0, log_normaliser_se: float = 0.0) -> None:
        super().__init__(name, atoms, weights)
        self.model = model
        self._log_density = log_density
        self.log_normaliser = float(log_normaliser)
        self.log_normaliser_se = float(log_normaliser_se)
        rng = np.random.default_rng(SAMPLED_SEED + 7)
        n_kde = min(2000, self.atoms.shape[0])
        self._kde_atoms = self.atoms[rng.choice(self.atoms.shape[0], size=n_kde, p=self.weights)]
        D = self.atoms.shape[1]
        sd = np.sqrt(self.weights @ (self.atoms - self.weights @ self.atoms) ** 2)
        self._kde_bw = np.maximum(1.06 * sd * n_kde ** (-1.0 / (D + 4)), 1e-6)

    def log_density(self, theta: np.ndarray) -> np.ndarray:
        return self._log_density(np.atleast_2d(np.asarray(theta, dtype=float)))

    def _kde_logpdf(self, z: np.ndarray) -> np.ndarray:
        D = z.shape[1]
        d = (z[:, None, :] - self._kde_atoms[None]) / self._kde_bw
        return (scipy.special.logsumexp(-0.5 * np.sum(d * d, -1), axis=1) - np.log(len(self._kde_atoms))
                - 0.5 * D * np.log(2 * np.pi) - np.sum(np.log(self._kde_bw)))

    def _in_box(self, z: np.ndarray) -> np.ndarray:
        box = self.model.box
        ok = np.all((z >= np.asarray(box.low)) & (z <= np.asarray(box.high)), axis=1)
        if box.ordered:
            ok &= np.all(np.diff(z, axis=1) >= 0, axis=1)
        return ok

    def cloud(self) -> CloudPrior:
        """The plain weighted cloud, whose marginal is the mixture over its draws everywhere:
        cheap, and accurate wherever the prior has draws near `x` (screens, §4.5)."""
        return CloudPrior(self.name, self.atoms, self.weights)

    def _lmn(self, model: Model, x: np.ndarray, s: float) -> np.ndarray:
        """`log m(x)` at noise `s`, routed (§4.4, OQ-14): the cloud's mixture where the cloud
        weighted by the likelihood keeps at least `N0_THIN` effective draws, the per-point
        estimate elsewhere. `log_marginal` and `log_predictive` both come through here."""
        x = np.atleast_2d(np.asarray(x, dtype=float))
        keep = self.weights > 0
        Y, lw = model.y(self.atoms[keep]), self.log_weights[keep]
        m = x.shape[-1]
        lse1 = mixture_logpdf(x, Y, lw, s) + 0.5 * m * np.log(2.0 * np.pi * s**2)
        lse2 = mixture_logpdf(x, Y, 2.0 * lw, s / np.sqrt(2.0)) + 0.5 * m * np.log(np.pi * s**2)
        out = lse1 - 0.5 * m * np.log(2.0 * np.pi * s**2)
        thin = np.exp(2.0 * lse1 - lse2) < N0_THIN
        if thin.any():
            if model.D > PER_POINT_MAX_D:
                warnings.warn(f"{self.name}: the per-point estimate is not validated above D = {PER_POINT_MAX_D} "
                              f"(OQ-14); {int(thin.sum())} thin points at D = {model.D}")
            lm, ess = self.per_point_log_marginal(model, x[thin], s)
            ok = np.isfinite(lm)
            weak = ok & (ess * N_PER_POINT < MIN_EFFECTIVE)
            if weak.any() or not ok.all():
                warnings.warn(f"{self.name}: the per-point estimate kept fewer than {MIN_EFFECTIVE:.0f} effective "
                              f"draws at {int(weak.sum())} and failed at {int((~ok).sum())} of {int(thin.sum())} "
                              "thin points; the cloud's value is used where it failed")
            idx = np.flatnonzero(thin)
            out[idx[ok]] = lm[ok]
        return out

    def per_point_log_marginal(self, model: Model, x: np.ndarray, s: float | None = None, *,
                               variant: int = 0) -> tuple[np.ndarray, np.ndarray]:
        """`log m(x)` at noise `s` (default `sigma_eff`) for each row of `x`, by importance
        sampling from the posterior itself (§4.4, OQ-14), and each point's ESS share.

        In unordered log decay times `theta = -log(-log xi)` the faces of `Theta` lie at
        infinity, and the target is `pi(sorted xi) / D!` times the Jacobian times the
        likelihood. The posterior's modes are found by L-BFGS from the `N_STARTS` cloud draws
        that best explain `x`, sorted, and given Laplace scales (a finite-difference Hessian,
        eigenvalues floored at `EIG_FLOOR`). The proposal mixes, per mode weighted by its
        Laplace mass, a Student-t core at `CORE_SCALE` times the Laplace scale and a wide t at
        `WIDE_SCALE` (share `WIDE_SHARE`), symmetrised over the permutations within blocks of
        near-equal coordinates of the main mode. Only draws whose blocks keep the main mode's
        order count, and the mean is multiplied by `D! / |G|`, which is exact for any blocking;
        the blocking sets only the efficiency. Validated to `D = PER_POINT_MAX_D` (OQ-14).
        `variant=1` changes the t's degrees of freedom and core scale (T4's second version).
        Each point's draws come from a generator seeded by its own bytes, so the estimate is a
        deterministic function of `x`, shared by every caller (common random numbers)."""
        s = model.sigma_eff if s is None else float(s)
        x = np.atleast_2d(np.asarray(x, dtype=float))
        keep = self.weights > 0
        atoms, lw = self.atoms[keep], self.log_weights[keep]
        Y = model.y(atoms)
        out, ess = np.empty(len(x)), np.empty(len(x))
        for i in range(len(x)):
            digest = hashlib.blake2b(x[i].tobytes() + bytes([variant]), digest_size=16).digest()
            rng = np.random.default_rng(np.frombuffer(digest, dtype=np.uint32))
            l0 = lw + log_normal_iso(x[i], Y, s)
            out[i], ess[i] = self._per_point_one(model, x[i], s, atoms[np.argsort(-l0)[:N_STARTS]], rng, variant)
        return out, ess

    def _per_point_one(self, model: Model, x: np.ndarray, s: float, starts: np.ndarray,
                       rng: np.random.Generator, variant: int) -> tuple[float, float]:
        D = self.atoms.shape[1]
        nu, core = T_NU[variant], CORE_SCALE[variant]
        box = model.box
        lo_t = [max(THETA_RANGE[0], float(_theta_of(b))) for b in np.asarray(box.low, float)]
        hi_t = [min(THETA_RANGE[1], float(_theta_of(b))) for b in np.asarray(box.high, float)]
        log_dfact = lgamma(D + 1)

        def log_f(th):
            th = np.atleast_2d(th)
            xi = np.sort(np.exp(-np.exp(-th)), axis=-1)
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                v = (self.log_density(xi) - log_dfact + np.sum(-np.exp(-th) - th, axis=-1)
                     + log_normal_iso(x, model.y(xi), s))
            v[~np.isfinite(v)] = -np.inf
            return v

        best = {"f": np.inf, "x": None}

        def obj(t):
            v = -float(log_f(t)[0])
            if not np.isfinite(v):
                return 1e300
            if v < best["f"]:
                best["f"], best["x"] = v, np.array(t, dtype=float)
            return v

        # L-BFGS can step onto states where the density vanishes numerically (Jeffreys at
        # coinciding rates, or rates that round to xi = 1) and stop there; the best state seen
        # is kept, and a derivative-free polish runs from it when L-BFGS ends worse.
        bounds = list(zip(lo_t, hi_t))
        modes = []
        for t0 in np.clip(_theta_of(np.sort(starts, axis=-1)), lo_t, hi_t):
            best["f"], best["x"] = np.inf, None
            r = scipy.optimize.minimize(obj, t0, method="L-BFGS-B", bounds=bounds)
            if best["x"] is not None and r.fun > best["f"] + 1e-9:
                scipy.optimize.minimize(obj, best["x"], method="Powell", bounds=bounds,
                                        options={"maxfev": 400 * D, "xtol": 1e-4, "ftol": 1e-10})
            if best["x"] is not None:
                modes.append((float(best["f"]), np.sort(best["x"])))
        modes.sort(key=lambda m: m[0])
        uniq = []
        for val, mu in modes:
            if all(np.max(np.abs(mu - u)) > 1e-3 for _, u in uniq):
                uniq.append((val, mu))
        if not uniq:
            return -np.inf, 0.0
        comps, log_a = [], []
        for val, mu in uniq[:MAX_MODES]:
            Sigma = _laplace_cov(obj, mu)
            comps.append((mu, np.linalg.cholesky(core**2 * Sigma), np.linalg.cholesky(WIDE_SCALE**2 * Sigma)))
            log_a.append(-val + 0.5 * np.linalg.slogdet(Sigma)[1])
        log_a = np.asarray(log_a) - scipy.special.logsumexp(log_a)
        blocks = _clusters(comps[0][0], np.sqrt(np.diag(comps[0][1] @ comps[0][1].T)))
        group = _block_permutations(blocks)
        # draws: a mode by its Laplace mass, core or wide, then a random relabelling within blocks
        k = rng.choice(len(comps), size=N_PER_POINT, p=np.exp(log_a))
        wide = rng.uniform(size=N_PER_POINT) < WIDE_SHARE
        z = np.empty((N_PER_POINT, D))
        for j, (mu, Lc, Lw) in enumerate(comps):
            for L, sel in ((Lc, (k == j) & ~wide), (Lw, (k == j) & wide)):
                n = int(sel.sum())
                z[sel] = mu + (rng.standard_normal((n, D)) @ L.T) * np.sqrt(nu / rng.chisquare(nu, (n, 1)))
        z = np.take_along_axis(z, group[rng.integers(0, len(group), N_PER_POINT)], axis=1)
        log_q = np.full(N_PER_POINT, -np.inf)
        for a in range(0, len(group), PERM_CHUNK):
            zp = z[:, group[a:a + PERM_CHUNK]]  # (n, perms, D)
            for j, (mu, Lc, Lw) in enumerate(comps):
                for L, share in ((Lc, 1.0 - WIDE_SHARE), (Lw, WIDE_SHARE)):
                    lp = _mvt_logpdf(zp, mu, L, nu)
                    log_q = np.logaddexp(log_q, log_a[j] + np.log(share) + scipy.special.logsumexp(lp, axis=1))
        log_q -= np.log(len(group))
        in_order = np.ones(N_PER_POINT, dtype=bool)
        for b0, b1 in zip(blocks[:-1], blocks[1:]):
            in_order &= z[:, b0].max(axis=1) < z[:, b1].min(axis=1)
        lw = np.where(in_order, log_f(z) - log_q, -np.inf)
        if not np.isfinite(lw).any():
            return -np.inf, 0.0
        w = np.exp(lw - lw.max())
        share = float(1.0 / np.sum((w / w.sum()) ** 2) / N_PER_POINT)
        lm = log_dfact - np.log(len(group)) + scipy.special.logsumexp(lw) - np.log(N_PER_POINT)
        return float(lm), share

    def kernel_log_marginal(self, model: Model, x: np.ndarray, rng: np.random.Generator, *,
                            kernel: str = "full") -> tuple[np.ndarray, np.ndarray]:
        """Superseded (OQ-14): the first per-point estimate, kept for the thin-states figure
        (`diagrams/002-foreign-q-prediction-thin-states.py`). Its centres come from the cloud,
        so at thin states it misses the posterior. `log m(x)` and each point's ESS share.

        The cloud weighted by the likelihood gives posterior draws; the proposal is a Gaussian
        kernel density around up to `N_CENTRES` of them (`kernel="full"`: their covariance at
        Scott's bandwidth; `"diagonal"`: its diagonal, 1.5 times wider), with
        `1 - LOCAL_SHARE` of a kernel density of the whole cloud as the defensive part, which
        bounds the weights. `N_PROPOSAL` draws per point; draws outside `Theta` weigh 0."""
        x = np.atleast_2d(np.asarray(x, dtype=float))
        s = model.sigma_eff
        Yc = model.y(self.atoms)
        D = self.atoms.shape[1]
        out, ess = np.empty(len(x)), np.empty(len(x))
        for i in range(len(x)):
            l0 = np.log(np.maximum(self.weights, 1e-300)) + log_normal_iso(x[i], Yc, s)
            w0 = np.exp(l0 - l0.max())
            w0 /= w0.sum()
            n0 = 1.0 / np.sum(w0**2)
            top, counts = np.unique(rng.choice(len(w0), size=N_CENTRES, p=w0), return_counts=True)
            wt = counts / counts.sum()
            C = np.cov(self.atoms.T, aweights=w0) if n0 > 2 else np.diag(self._kde_bw**2)
            C = np.atleast_2d(C)
            h = n0 ** (-1.0 / (D + 4)) * (1.0 if kernel == "full" else 1.5)
            K = (C if kernel == "full" else np.diag(np.diag(C))) * h**2 + 1e-12 * np.eye(D)
            L = np.linalg.cholesky(K)
            n_loc = rng.binomial(N_PROPOSAL, LOCAL_SHARE)
            z = np.concatenate([
                self.atoms[top[rng.choice(len(top), n_loc, p=wt)]] + rng.standard_normal((n_loc, D)) @ L.T,
                self._kde_atoms[rng.integers(0, len(self._kde_atoms), N_PROPOSAL - n_loc)]
                + self._kde_bw * rng.standard_normal((N_PROPOSAL - n_loc, D)),
            ])
            Kinv, ldK = np.linalg.inv(K), np.linalg.slogdet(K)[1]
            d = z[:, None, :] - self.atoms[top][None]
            l_loc = (scipy.special.logsumexp(np.log(wt)[None] - 0.5 * np.einsum("nkd,de,nke->nk", d, Kinv, d), axis=1)
                     - 0.5 * D * np.log(2 * np.pi) - 0.5 * ldK)
            log_q = np.logaddexp(np.log(LOCAL_SHARE) + l_loc, np.log1p(-LOCAL_SHARE) + self._kde_logpdf(z))
            lt = np.full(len(z), -np.inf)
            ok = self._in_box(z)
            if ok.any():
                with np.errstate(divide="ignore", invalid="ignore"):
                    lt[ok] = self.log_density(z[ok]) + log_normal_iso(x[i], model.y(z[ok]), s)
            lw = lt - log_q
            lw[~np.isfinite(lw)] = -np.inf
            out[i] = scipy.special.logsumexp(lw) - np.log(len(z))
            w = np.exp(lw - lw.max())
            w /= w.sum()
            ess[i] = 1.0 / np.sum(w**2) / len(z)
        return out, ess


def _log_sqrt_det_g(model: Model, xi: np.ndarray) -> np.ndarray:
    """`log sqrt(det g(xi))` at `sigma_eff`, `-inf` where `g` is singular."""
    with np.errstate(divide="ignore", invalid="ignore"):
        J = model.jacobian(xi)
        sign, ld = np.linalg.slogdet(np.swapaxes(J, -1, -2) @ J / model.sigma_eff**2)
    out = 0.5 * ld
    out[(sign <= 0) | ~np.isfinite(out)] = -np.inf
    return out


def _kde_logpdf(x: np.ndarray, centres: np.ndarray, w: np.ndarray, bw: np.ndarray, chunk: int = 1000) -> np.ndarray:
    D = x.shape[1]
    out = np.empty(len(x))
    lw = np.log(w)
    norm = -0.5 * D * np.log(2 * np.pi) - np.sum(np.log(bw))
    for a in range(0, len(x), chunk):
        z = (x[a:a + chunk, None, :] - centres[None]) / bw
        out[a:a + chunk] = scipy.special.logsumexp(lw[None] - 0.5 * np.sum(z * z, -1), axis=1) + norm
    return out


def build_sampled_jeffreys(model: Model) -> SampledPrior:
    """Exp-decay Jeffreys by adaptive importance sampling (§4.2): a cloud of `N_CLOUD`
    weighted draws in ordered `xi`, its normaliser over ordered `xi` and that estimate's
    standard error."""
    if model.family != "exp_decay":
        raise ValueError("the sampled Jeffreys path is exp-decay's (§4.2)")
    D = model.D
    rng = np.random.default_rng(SAMPLED_SEED + D)
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    mu0, sd0 = 0.8, 1.5
    log_q0 = lambda th: np.sum(scipy.stats.t.logpdf(th, T_DF, mu0, sd0), axis=-1)  # noqa: E731

    def draw_q0(n):
        return mu0 + sd0 * rng.standard_t(T_DF, size=(n, D))

    def xi_of(th):
        return np.exp(-np.exp(-th))

    def log_target(th):
        xi = np.sort(xi_of(th), axis=-1)
        out = _log_sqrt_det_g(model, xi) + np.sum(-np.exp(-th) - th, axis=-1)
        out[~np.all((xi >= lo) & (xi <= hi), axis=1)] = -np.inf
        return out

    def one_round(n, cloud, w):
        if cloud is None:
            th = draw_q0(n)
            return th, log_q0(th)
        sd = np.sqrt(w @ (cloud - w @ cloud) ** 2)
        bw = np.maximum(sd * (1.0 / np.sum(w**2)) ** (-1.0 / (D + 4)), 1e-6)
        th = cloud[rng.choice(len(cloud), size=n, p=w)] + bw * rng.standard_normal((n, D))
        base = rng.uniform(size=n) < ALPHA
        th[base] = draw_q0(int(base.sum()))
        keep = w > 1e-12
        log_q = np.logaddexp(np.log1p(-ALPHA) + _kde_logpdf(th, cloud[keep], w[keep] / w[keep].sum(), bw),
                             np.log(ALPHA) + log_q0(th))
        return th, log_q

    def weigh(th, log_q):
        lw = log_target(th) - log_q
        lw[~np.isfinite(lw)] = -np.inf
        top = lw.max()
        r = np.exp(lw - top)
        log_z = top + np.log(r.mean())
        se = r.std() / (r.mean() * np.sqrt(len(r)))
        return lw, log_z, se

    cloud, w, hist, ess_hist = None, None, [], []
    for rnd in range(MAX_ROUNDS):
        th, log_q = one_round(N_ROUND, cloud, w)
        lw, log_z, _ = weigh(th, log_q)
        w = np.exp(lw - lw.max())
        w /= w.sum()
        cloud = th
        hist.append(log_z)
        ess_hist.append(1.0 / np.sum(w**2) / len(w))
        if rnd >= 3 and np.std(hist[-3:]) < LOGZ_TOL:
            break
    floor = FINAL_ESS_SHARE * float(np.median(ess_hist[-3:]))
    for _ in range(FINAL_REDRAWS + 1):
        th, log_q = one_round(N_CLOUD, cloud, w)
        lw, log_z, se = weigh(th, log_q)
        wf = np.exp(lw - lw.max())
        wf /= wf.sum()
        share = 1.0 / np.sum(wf**2) / len(wf)
        if share >= floor:
            break
    else:
        raise RuntimeError(
            f"sampled Jeffreys at D = {D}: the last round's effective sample share {share:.2%} stayed "
            f"below {floor:.2%} over {FINAL_REDRAWS} redraws"
        )
    keep = wf > 0
    atoms = np.sort(xi_of(th[keep]), axis=-1)
    log_z_ordered = log_z - lgamma(D + 1)

    def log_density(xi):
        out = _log_sqrt_det_g(model, xi) - log_z_ordered
        out[~(np.all((xi >= lo) & (xi <= hi), axis=1) & np.all(np.diff(xi, axis=1) >= 0, axis=1))] = -np.inf
        return out

    return SampledPrior("p_J", model, atoms, wf[keep], log_density, log_normaliser=log_z_ordered, log_normaliser_se=se)


def sampled_from(prior, model: Model, name: str) -> SampledPrior:
    """A continuous prior with a direct sampler and a normalised density (`p_U`, `p_LN`)
    carried as an equal-weight cloud of `N_CLOUD` of its draws (§4.4)."""
    rng = np.random.default_rng(SAMPLED_SEED + 100 + model.D)
    atoms = prior.sample(N_CLOUD, rng)
    return SampledPrior(name, model, atoms, np.full(len(atoms), 1.0 / len(atoms)), prior.log_density,
                        log_normaliser=getattr(prior, "log_normaliser", 0.0))
