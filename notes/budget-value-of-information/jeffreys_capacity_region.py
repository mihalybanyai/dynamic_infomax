"""Where the sufficient condition settles p* against Jeffreys in the reduced hypercone
(L=50, sigma=1, N=1). R^q(p*) <= C for every nature, so p* beats Jeffreys on every nature
supported where Jeffreys' per-state redundancy exceeds C. Jeffreys' redundancy on x1 alone
is a lower bound on its full per-state redundancy, so the region found is conservative.
C is the reduced capacity, hidden-direction information included."""
import numpy as np
exec(open("cone_misbudget.py").read().split("natures = {")[0])   # grids, c(a), chan, ba
lk, nH, dx = ch[1]
for D in [26, 100]:
    bonus = (D-1)*c(th/L)
    w = ba(bonus, ch[1])
    d = nH - (lk @ np.log(np.maximum(w @ lk, 1e-300)))*dx
    C = float(np.max(d + bonus))
    J = np.maximum(th, 1e-12)**(D-1); J /= J.sum()
    dJ = nH - (lk @ np.log(np.maximum(J @ lk, 1e-300)))*dx
    edge = th[np.argmax(dJ < C)]
    print(f"D={D}: C={C:.2f} nats; Jeffreys' per-state redundancy on x1 exceeds C for th1 < {edge:.1f} (of {L:.0f})")
