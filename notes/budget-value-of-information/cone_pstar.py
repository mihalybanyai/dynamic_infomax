"""Reduced p* for the square hypercone (sigma=1, N=1, L=50).

Given theta_1, the D-1 habit channels are independent parallel amplitude-constrained
Gaussian channels with range [0, r], r = theta_1/L, so their conditional capacity is
exactly (D-1)*c(r), achieved by a product of two-endpoint inputs (r <= 1 < 3.3).
Ignoring what the habit data say about theta_1 (A&M's O(D/L^2) correction),
I(Theta;X) = I(theta_1;x_1) + E[(D-1) c(r)], maximised by BA with a bonus term.
"""
import numpy as np

L, sig = 50.0, 1.0
th = np.linspace(0, L, 501)
x = np.linspace(-7, L + 7, 1281); dx = x[1] - x[0]
lik = np.exp(-(x[None, :] - th[:, None])**2 / 2) / np.sqrt(2*np.pi)          # p(x|th)

z = np.linspace(-10, 11, 20001); dz = z[1]-z[0]
phi = lambda u: np.exp(-u**2/2)/np.sqrt(2*np.pi)
def c(a):   # MI of equiprobable binary input {0,a} through N(.,1), nats
    m = 0.5*phi(z) + 0.5*phi(z-a)
    f = lambda p: np.sum(p*np.log(np.maximum(p,1e-300)/np.maximum(m,1e-300)))*dz
    return 0.5*f(phi(z)) + 0.5*f(phi(z-a))
cr = np.array([c(t/L) for t in th])

negH = np.sum(lik*np.log(np.maximum(lik,1e-300)), axis=1)*dx
def ba(bonus, iters=6000):
    w = np.ones_like(th)/len(th)
    for _ in range(iters):
        m = w @ lik
        d = negH - (lik @ np.log(np.maximum(m,1e-300)))*dx
        w = w*np.exp(d + bonus); w /= w.sum()
    return w, d

def post_dev(w, x0):   # posterior mean of theta_1 minus x0 (1-D reduction)
    p = w*np.exp(-(x0-th)**2/2); p /= p.sum(); return p @ th - x0

def kl_marg(qw, w):    # D(m_q || m_w) on x_1
    mq, mw = qw @ lik, w @ lik
    return np.sum(mq*np.log(np.maximum(mq,1e-300)/np.maximum(mw,1e-300)))*dx

qU = np.ones_like(th)/len(th)                 # nature uniform in theta_1 (t=0 marginal)
print(f"c(1) = {cr[-1]:.3f} nats = {cr[-1]/np.log(2):.3f} bits;  c(0.5) = {c(0.5):.4f}")
print(" D | p* tip/base wt ratio | p* Dev at x=3,10,25,40     | Jeff Dev at x=3,10,25,40   | D(mU||m_p*)  D(mU||m_J)")
for D in [1, 5, 10, 26, 50, 100]:
    w, _ = ba((D-1)*cr)
    lo, hi = w[th < 5].sum(), w[th > 45].sum()
    J = th**(D-1); J = J/J.sum()
    dp = [post_dev(w, x0) for x0 in (3, 10, 25, 40)]
    dj = [post_dev(J, x0) for x0 in (3, 10, 25, 40)]
    print(f"{D:3d} | {lo/hi:9.3g}            | " + " ".join(f"{v:6.2f}" for v in dp)
          + " | " + " ".join(f"{v:6.2f}" for v in dj)
          + f" | {kl_marg(qU,w):8.2f}  {kl_marg(qU,J):9.2f}")
