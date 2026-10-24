"""Budget-relative prior vs p*_N in the reduced square hypercone (D=26, L=50, sigma=1).
The budget-relative prior equalises regret against an oracle that knows what N observations
resolve (here th1). In the reduced model that regret is -log w(th1) + const, so its th1
marginal is the 1-D p*_N of th1's own channel (no hidden-detail bonus); the hidden
directions keep p*'s conditional input, so their score is the same as p*_N's.
Reports the x1 mismatch D(m_q||m_pi) (nats) per nature; lower is better."""
import numpy as np
exec(open("cone_misbudget.py").read().split("natures = {")[0])   # grids, c(a), chan, ba, mism
D = 26
natures = {"uniform": np.ones_like(th), "thin end (th1<L/5)": (th < L/5).astype(float),
           "thick end (th1>4L/5)": (th > 4*L/5).astype(float)}
for k in natures: natures[k] /= natures[k].sum()
zero = np.zeros_like(th)
for N in budgets:
    pN  = ba((D-1)*c(th/L*np.sqrt(N)), ch[N])     # p*_N (taper)
    p1  = ba((D-1)*c(th/L*np.sqrt(1)), ch[1])     # p*_1, the coarsest
    rel = ba(zero, ch[N])                          # budget-relative prior
    print(f"N={N:<2d} " + " | ".join(
        f"{qn}: p*_N {mism(q,pN,ch[N]):5.2f}, p*_1 {mism(q,p1,ch[N]):5.2f}, budget-relative {mism(q,rel,ch[N]):5.2f}"
        for qn, q in natures.items()))
    lk, nH, dx = ch[N]
    worst = lambda w: np.max(nH - (lk @ np.log(np.maximum(w @ lk,1e-300)))*dx + (D-1)*c(th/L*np.sqrt(N)))
    print(f"      worst-case per-theta redundancy incl. hidden cost: p*_N {worst(pN):.2f}, budget-relative {worst(rel):.2f}")
