"""Continuous priors beyond the quadrature grids (spec 002 §4.2, §4.4, OQ-13; DD-Q4).

Exp-decay's tensor grids in `xi` grow combinatorially with `D`, and Jeffreys' grid loses mass
where rates nearly coincide from `D = 4` (2026-11-26). There a continuous prior is a weighted
cloud of its own draws (`SampledPrior`, a `CloudPrior`): its marginal is the mixture over the
cloud, and where the prior is thin near `x`, `refined_log_marginal` estimates `log m(x)`
per point by importance sampling.

Jeffreys is sampled by adaptive importance sampling in unordered log decay times
`theta = -log(-log xi)`, where its density is `sqrt(det g)` times the Jacobian of `xi`
(Jeffreys is invariant) and symmetric under swapping rates. The first round draws independent
normal log times; each later round draws from a Gaussian kernel density of the previous
weighted cloud, with `ALPHA` of the first law as the defensive part. Rounds stop once `log Z`
has varied by less than `LOGZ_TOL` over three rounds; a last round of `N_CLOUD` draws gives the
cloud and the normaliser. Builds are deterministic (`SAMPLED_SEED`), since the builders take no
generator (`skills/manage-randomness.md`, rule 7).
"""
from __future__ import annotations

from math import lgamma

import numpy as np
import scipy.special
import scipy.stats

from infomax.mixture import log_normal_iso
from infomax.models import Model
from infomax.priors002 import CloudPrior

SAMPLED_SEED: int = 20261126
N_CLOUD: int = 20000
N_ROUND: int = 8000
ALPHA: float = 0.1
LOGZ_TOL: float = 0.02
MAX_ROUNDS: int = 15
JEFFREYS_SAMPLED_FROM_D: int = 4
"""Exp-decay `p_J` is sampled from this `D` (its grid misses 5% of the mass at `D = 4`)."""
GRID_MAX_D: int = 5
"""Exp-decay product laws (`p_U`, `p_LN`) keep their grids up to this `D` (843k nodes at `D = 5`)."""
N_PROPOSAL: int = 1000
N_CENTRES: int = 200
LOCAL_SHARE: float = 0.8


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

    def refined_log_marginal(self, model: Model, x: np.ndarray, rng: np.random.Generator, *,
                             kernel: str = "full") -> tuple[np.ndarray, np.ndarray]:
        """`log m(x)` per point by importance sampling, and each point's ESS share (§4.4).

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
    log_q0 = lambda th: np.sum(scipy.stats.norm.logpdf(th, mu0, sd0), axis=-1)  # noqa: E731

    def xi_of(th):
        return np.exp(-np.exp(-th))

    def log_target(th):
        xi = np.sort(xi_of(th), axis=-1)
        out = _log_sqrt_det_g(model, xi) + np.sum(-np.exp(-th) - th, axis=-1)
        out[~np.all((xi >= lo) & (xi <= hi), axis=1)] = -np.inf
        return out

    def one_round(n, cloud, w):
        if cloud is None:
            th = rng.normal(mu0, sd0, size=(n, D))
            return th, log_q0(th)
        sd = np.sqrt(w @ (cloud - w @ cloud) ** 2)
        bw = np.maximum(sd * (1.0 / np.sum(w**2)) ** (-1.0 / (D + 4)), 1e-6)
        th = cloud[rng.choice(len(cloud), size=n, p=w)] + bw * rng.standard_normal((n, D))
        base = rng.uniform(size=n) < ALPHA
        th[base] = rng.normal(mu0, sd0, size=(int(base.sum()), D))
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

    cloud, w, hist = None, None, []
    for rnd in range(MAX_ROUNDS):
        th, log_q = one_round(N_ROUND, cloud, w)
        lw, log_z, _ = weigh(th, log_q)
        w = np.exp(lw - lw.max())
        w /= w.sum()
        cloud = th
        hist.append(log_z)
        if rnd >= 3 and np.std(hist[-3:]) < LOGZ_TOL:
            break
    th, log_q = one_round(N_CLOUD, cloud, w)
    lw, log_z, se = weigh(th, log_q)
    wf = np.exp(lw - lw.max())
    wf /= wf.sum()
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
