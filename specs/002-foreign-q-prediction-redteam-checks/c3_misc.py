import numpy as np
from scipy.stats import norm
from scipy.integrate import quad
from scipy.optimize import minimize

# --- T6: Jeffreys posterior-mean deviation in the hypercone, relevant datum only, sigma=1, W=50
W = 50.0
for D, x in ((6, 10.0), (11, 10.0), (26, 10.0)):
    f = lambda t: np.exp((D - 1) * np.log(t) - 0.5 * (t - x) ** 2 - ((D - 1) * np.log(x + 5)))
    Z = quad(f, 1e-12, W, limit=200)[0]
    mean = quad(lambda t: t * f(t), 1e-12, W, limit=200)[0] / Z
    dev = mean - x
    lead = (D - 1) / x
    print(f"T6 D={D}: mean dev {dev:.3f}, (D-1)/x {lead:.3f}, |diff| {abs(dev-lead):.3f}, "
          f"3(D-1)^2/x^3 = {3*(D-1)**2/x**3:.3f}, (D-1)^2/x^3 = {(D-1)**2/x**3:.3f}")

# --- T18: latent information prior for one Bernoulli observation, one to predict
def cmi(w, thetas):
    w = np.asarray(w); th = np.asarray(thetas)
    P = {}
    for a in (0, 1):
        for b in (0, 1):
            P[(a, b)] = np.sum(w * th ** (a + b) * (1 - th) ** (2 - a - b))
    HXY = -sum(p * np.log(p) for p in P.values() if p > 0)
    PX = [P[(0, 0)] + P[(0, 1)], P[(1, 0)] + P[(1, 1)]]
    HX = -sum(p * np.log(p) for p in PX if p > 0)
    h = lambda t: -(t * np.log(t) + (1 - t) * np.log(1 - t)) if 0 < t < 1 else 0.0
    HYgT = np.sum(w * np.array([h(t) for t in th]))
    return HXY - HX - HYgT
th3 = [0.0, 0.5, 1.0]; w3 = [0.3, 0.4, 0.3]
print("T18 CMI of stated prior:", cmi(w3, th3), "log(5/4) =", np.log(1.25))
# per-state conditional divergence f(theta) = E_theta[log p(X2|theta) - log m(X2|X1)] under the stated prior
def m_cond(w, th):
    P = {(a, b): np.sum(np.asarray(w) * np.asarray(th) ** (a + b) * (1 - np.asarray(th)) ** (2 - a - b)) for a in (0,1) for b in (0,1)}
    return {(a, b): P[(a, b)] / (P[(a, 0)] + P[(a, 1)]) for a in (0, 1) for b in (0, 1)}
mc = m_cond(w3, th3)
grid = np.linspace(0, 1, 1001); fs = []
for t in grid:
    val = 0.0
    for a in (0, 1):
        pa = t if a else 1 - t
        for b in (0, 1):
            pb = t if b else 1 - t
            if pa * pb > 0:
                val += pa * pb * (np.log(pb) - np.log(mc[(a, b)]))
    fs.append(val)
fs = np.array(fs)
print(f"T18 KKT: max_theta f = {fs.max():.4f} at theta={grid[fs.argmax()]:.3f}; f at 0, .5, 1 = {fs[0]:.4f}, {fs[500]:.4f}, {fs[-1]:.4f}")

# --- Rotation: p_U vs p_ref marginal on s=(Q theta)_1 in the box [0,W]x[0,1]^{D-1}, rotation in (theta1,theta2)
for alpha in (np.pi / 8, np.pi / 4):
    ca, sa = np.cos(alpha), np.sin(alpha)
    lo, hi = -sa, W * ca
    s = np.linspace(lo, hi, 200001)
    # p_U marginal on s: length of theta2 in [0,1] with theta1=(s+sa*theta2)/ca in [0,W], divided by ca*W
    t2lo = np.clip(-s / sa, 0, 1); t2hi = np.clip((W * ca - s) / sa, 0, 1)
    pU = np.clip(t2hi - t2lo, 0, None) / (ca * W)
    pU /= np.trapezoid(pU, s)
    pref = np.full_like(s, 1.0 / (hi - lo))
    mask = pU > 0
    kl = np.trapezoid(np.where(mask, pref * np.log(pref / np.where(mask, pU, 1)), 0), s)
    print(f"rotation alpha={alpha:.3f}: s-range [{lo:.2f},{hi:.2f}], ramps of width {sa:.2f}; KL(p_ref||p_U) on s = {kl:.4f} nats "
          f"(parameter space; data-space mismatch is smaller)")
