"""Active learning with an indivisible investment (ski-rental structure).
Same target and offset as active_calibration.py (theta ~ N(0,1), beta ~ N(0,b^2), noise 1),
same scoring: each round, bet on y = theta + e; cumulative excess log-loss.
Actions: measure A (theta + beta + e, confounded) or spend the round building an
instrument; after B building rounds every measurement is calibrated (theta + e).
Policy family: "start building at round k" (k = never included). Informed: best k for the
known N. Uninformed: one k for every N, chosen by minimax ratio over the N range."""
import numpy as np
import sys
b2, B, T = float(sys.argv[1]), int(sys.argv[2]), 1000
Ns = [2, 5, 10, 20, 40, 60, 100, 200, 400, 1000]
def var_theta(n1, n2):          # n1 confounded, n2 calibrated samples
    P11, P12, P22 = 1 + n1 + n2, n1, 1/b2 + n1
    return P22/(P11*P22 - P12**2)
def run(k):                      # cumulative cost for every horizon, building from round k
    n1 = n2 = 0; built_at = None; tot = 0.0; out = {}
    for t in range(T):
        tot += 0.5*np.log(1 + var_theta(n1, n2))
        if t + 1 in Ns: out[t + 1] = tot
        if k is not None and k <= t < k + B: continue          # building: no measurement
        if k is not None and t >= k + B: n2 += 1
        else: n1 += 1
    return out
ks = [None] + list(range(0, 601, 5))
runs = {k: run(k) for k in ks}
informed = {N: min(runs[k][N] for k in ks) for N in Ns}
best_k = {N: min(ks, key=lambda k: runs[k][N] if True else 0) for N in Ns}
ratio = {k: max(runs[k][N]/informed[N] for N in Ns) for k in ks}
kb = min(ratio, key=ratio.get)
print(f"b^2={b2}, B={B}");print("informed choice (build start) by N:", {N: best_k[N] for N in Ns})
print(f"best single schedule for all N: build at k={kb}, worst-case ratio {ratio[kb]:.2f}")
print(f"{'N':>4} | informed | uninformed k={kb} | never build | build at once")
for N in Ns:
    print(f"{N:4d} | {informed[N]:8.2f} | {runs[kb][N]:8.2f} (x{runs[kb][N]/informed[N]:.2f}) "
          f"| {runs[None][N]:8.2f} | {runs[0][N]:8.2f}")
