"""1-D bounded Gaussian channel, theta in [0,1], noise s0/sqrt(N), Fisher length L0*sqrt(N).
p*_M = capacity-achieving prior at budget M (BA). Score each prior at budget N:
R_N^q = E_{theta~q} KL(N(theta, s_N^2) || m_pi) on the sufficient statistic xbar,
for q uniform (smooth nature) and worst case over theta. Jeffreys = uniform here."""
import numpy as np
L0 = 3.0; s0 = 1.0/L0
budgets = [1, 4, 16, 64, 256]
th = np.linspace(0, 1, 1201)
def chan(N):
    s = s0/np.sqrt(N)
    x = np.linspace(-6*s, 1+6*s, 2400); dx = x[1]-x[0]
    lik = np.exp(-(x[None,:]-th[:,None])**2/(2*s*s))/np.sqrt(2*np.pi*s*s)
    negH = np.sum(lik*np.log(np.maximum(lik,1e-300)),axis=1)*dx
    return lik, negH, dx
def per_theta(w, ch):
    lik, negH, dx = ch
    m = w @ lik
    return negH - (lik @ np.log(np.maximum(m,1e-300)))*dx     # KL(p_theta || m_w) per theta
def ba(ch, iters=5000):
    w = np.ones_like(th)/len(th)
    for _ in range(iters):
        w = w*np.exp(per_theta(w, ch)); w /= w.sum()
    return w
chans = {N: chan(N) for N in budgets}
pstar = {M: ba(chans[M]) for M in budgets}
U = np.ones_like(th)/len(th)
print("atoms (mass>1e-3) per p*_M:", {M: int(np.sum(pstar[M] > 1e-3)) for M in budgets})
print("C_N:", {N: round(float(np.max(per_theta(pstar[N], chans[N]))),3) for N in budgets})
for label, agg in [("uniform nature", lambda d: U @ d), ("worst case", np.max)]:
    print(f"\nExcess R_N over p*_N, {label} (rows: scored at budget N; cols: prior p*_M, then Jeffreys=uniform)")
    print("   N | " + " ".join(f"M={M:<5d}" for M in budgets) + " | Jeffreys")
    for N in budgets:
        ref = agg(per_theta(pstar[N], chans[N]))
        row = [agg(per_theta(pstar[M], chans[N])) - ref for M in budgets]
        j = agg(per_theta(U, chans[N])) - ref
        print(f"{N:4d} | " + " ".join(f"{v:7.2f}" for v in row) + f" | {j:7.2f}")
