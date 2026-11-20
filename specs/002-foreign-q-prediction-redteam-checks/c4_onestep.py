"""Reduced square hypercone, relevant datum only (W=50, sigma=1, D=26), as in notes/budget-value-of-information.
Cumulative mismatch KL(m_q||m_pi) at budget N depends on s=sigma/sqrt(N); one-step mismatch r_N = M(N+1) - M(N)."""
import numpy as np
from scipy.special import logsumexp
W, D = 50.0, 26
th = np.linspace(1e-6, W, 20001); dth = th[1] - th[0]
x = np.linspace(-8, W + 8, 6001); dx = x[1] - x[0]
logJ = (D - 1) * np.log(th); logJ -= logsumexp(logJ) + np.log(dth)          # Jeffreys theta_1 marginal density
def marg(logprior, s):
    # m(x) = int N(x; t, s^2) p(t) dt, in logs
    lp = logprior[None, :] + np.log(dth) - 0.5 * ((x[:, None] - th[None, :]) / s) ** 2 - np.log(np.sqrt(2 * np.pi) * s)
    return logsumexp(lp, axis=1)
def kl(lq, lp):
    q = np.exp(lq); return np.sum(q * (lq - lp)) * dx
natures = {
    "uniform": np.where(th <= W, 0.0, -np.inf) - np.log(W),
    "thin end (<10)": np.where(th < 10, -np.log(10.0), -np.inf),
    "thick half (>25)": np.where(th > 25, -np.log(25.0), -np.inf),
}
for name, lq_prior in natures.items():
    Ms = {}
    for N in (1, 2, 3, 4, 8, 9, 16, 17):
        s = 1 / np.sqrt(N)
        Ms[N] = kl(marg(lq_prior, s), marg(logJ, s))
    print(f"{name:16s}: cumulative M_N(J): " + ", ".join(f"N={N}: {Ms[N]:.2f}" for N in (1, 4, 8, 16))
          + " | one-step r_N mismatch: " + ", ".join(f"N={N}: {Ms[N+1]-Ms[N]:.3f}" for N in (1, 2, 3, 8, 16)))
