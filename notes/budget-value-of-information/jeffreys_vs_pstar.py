"""Betting performance (x1 mismatch = excess cumulative log-loss, nats; lower is better) of
Jeffreys vs p*_N in the reduced square hypercone, D=26, L=50, sigma=1, on four natures."""
import numpy as np
exec(open("cone_misbudget.py").read().split("natures = {")[0])   # grids, c(a), chan, ba, mism
D = 26
nat = {"uniform": th >= 0, "thin end (<10)": th < 10, "thick end (>40)": th > 40,
       "very base (>48)": th > 48}
for N in [1, 16]:
    pN = ba((D-1)*c(th/L*np.sqrt(N)), ch[N])
    J = np.maximum(th, 1e-12)**(D-1); J /= J.sum()
    print(f"N={N:<2d} " + " | ".join(
        f"{k}: J {mism(m/m.sum(), J, ch[N]):6.2f}, p*_N {mism(m/m.sum(), pN, ch[N]):5.2f}"
        for k, m in ((k, v.astype(float)) for k, v in nat.items())))
