"""Adds the habit coordinates' own score to cone_misbudget.py (same reduced cone, taper).
Given th1 (well resolved at L=50), each habit is an amplitude-constrained channel of width
a_N = r sqrt(N); p*_M uses the capacity-achieving input for width a_M = r sqrt(M), which at
budget N sits at positions scaled by sqrt(N/M). Habit nature: u ~ U[0,1] per habit.
Excess habit score of p*_M over p*_N at budget N:
  (D-1) E_{th1~q} [ h(r;M,N) - h(r;N,N) ],  h = E_u KL(N(a_N u,1) || mixture of N(a_N v_j,1)).
Prints it next to the x1-part excess from cone_misbudget.out."""
import numpy as np
L = 50.0
def cap_input(a, n=161, iters=3000):
    u = np.linspace(0, max(a,1e-9), n); z = np.linspace(-7, a+7, 1200); dz = z[1]-z[0]
    lk = np.exp(-(z[None,:]-u[:,None])**2/2)/np.sqrt(2*np.pi)
    nH = np.sum(lk*np.log(np.maximum(lk,1e-300)),axis=1)*dz
    w = np.ones(n)/n
    for _ in range(iters):
        d = nH - (lk @ np.log(np.maximum(w @ lk,1e-300)))*dz
        w = w*np.exp(d); w /= w.sum()
    return u/max(a,1e-9), w          # input positions as fractions of the width, weights
def h(frac, w, aN, nu=101):
    """E_{u~U[0,1]} KL(N(aN u,1) || sum_j w_j N(aN frac_j, 1))"""
    z = np.linspace(-7, aN+7, 1500); dz = z[1]-z[0]
    phi = lambda m: np.exp(-(z-m)**2/2)/np.sqrt(2*np.pi)
    mix = sum(wj*phi(aN*fj) for fj, wj in zip(frac, w) if wj > 1e-8)
    us = np.linspace(0, 1, nu); out = 0.0
    for uu in us:
        p = phi(aN*uu); out += np.sum(p*np.log(np.maximum(p,1e-300)/np.maximum(mix,1e-300)))*dz
    return out/nu
budgets = [1, 4, 16]
rs = np.linspace(0.02, 1, 25)
inputs = {(r, M): cap_input(r*np.sqrt(M)) for r in rs for M in budgets}
H = {(M, N): np.array([h(*inputs[(r, M)], r*np.sqrt(N)) for r in rs]) for M in budgets for N in budgets}
th = rs*L
natures = {"uniform": np.ones_like(rs), "thin end (th1<L/5)": (th < L/5).astype(float)}
for k in natures: natures[k] /= natures[k].sum()
for D in [10, 26]:
    print(f"\n== taper, D={D}: habit-part excess of p*_M over p*_N at budget N, nats")
    for qn, q in natures.items():
        print(f"  nature {qn}:")
        for N in budgets:
            print(f"    N={N:<2d} " + "  ".join(f"M={M:<2d} {(D-1)*(q @ (H[(M,N)]-H[(N,N)])):8.2f}" for M in budgets))
