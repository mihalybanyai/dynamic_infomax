"""Active learning with an investment: does knowing the horizon N pay?
Target theta ~ N(0,1); unknown offset beta ~ N(0, b^2). Each round the agent bets on a
fresh target outcome y = theta + e (log-loss, excess over the oracle = 0.5 log(1+Var theta))
and then makes one measurement: A: theta + beta + e (direct but confounded), or
C: beta + e (calibration, says nothing about theta by itself). Noise variance 1.
Score: cumulative excess log-loss of the N bets. Linear-Gaussian, so the posterior depends
only on the counts (nA, nC); the order of measurements matters through the bets made
along the way. Informed: DP-optimal schedule for the known N. Uninformed: one schedule
for every N (best of three families, chosen by minimax ratio over the N range)."""
import numpy as np
b2 = 100.0
def var_theta(nA, nC):
    P11, P12, P22 = 1 + nA, nA, 1/b2 + nA + nC
    return P22/(P11*P22 - P12**2)
cost = lambda nA, nC: 0.5*np.log(1 + var_theta(nA, nC))
T = 400
Ns = [2, 5, 10, 20, 50, 100, 200, 400]

# informed: g[t][c] = min cumulative cost of bets 0..t along paths reaching (t-c, c)
g = np.full((T, T), np.inf); g[0][0] = cost(0, 0)
for t in range(1, T):
    for c in range(t + 1):
        prev = min(g[t-1][c] if c <= t-1 else np.inf, g[t-1][c-1] if c >= 1 else np.inf)
        g[t][c] = cost(t - c, c) + prev
informed = {N: g[N-1][:N].min() for N in Ns}
c_opt = {N: int(np.argmin(g[N-1][:N])) for N in Ns}   # calibration count at the last bet

def path_cost(choose):          # choose(nA, nC, t) -> 'A' or 'C'; returns cumulative cost per N
    nA = nC = 0; tot = 0.0; out = {}
    for t in range(T):
        tot += cost(nA, nC)
        if t + 1 in Ns: out[t + 1] = tot
        if choose(nA, nC, t) == 'C': nC += 1
        else: nA += 1
    return out
families = {}
for c0 in [0, 2, 5, 10, 20, 40]:
    families[f"C-block {c0} first"] = path_cost(lambda nA, nC, t, c0=c0: 'C' if nC < c0 else 'A')
for k in [0.5, 1, 2, 4]:
    families[f"keep nC ~ {k}*sqrt(nA)"] = path_cost(lambda nA, nC, t, k=k: 'C' if nC < k*np.sqrt(nA + 1) else 'A')
families["greedy (myopic)"] = path_cost(
    lambda nA, nC, t: 'C' if var_theta(nA, nC + 1) < var_theta(nA + 1, nC) else 'A')
ratio = {name: max(p[N]/informed[N] for N in Ns) for name, p in families.items()}
best = min(ratio, key=ratio.get)
print("informed calibration count by N:", c_opt)
print(f"{'N':>4} | informed | best uninformed ({best}) | greedy | never calibrate")
for N in Ns:
    print(f"{N:4d} | {informed[N]:8.2f} | {families[best][N]:8.2f} (x{families[best][N]/informed[N]:.2f})"
          f" | {families['greedy (myopic)'][N]:8.2f} | {families['C-block 0 first'][N]:8.2f}")
print("worst-case ratio over N per schedule:", {k: round(v, 2) for k, v in ratio.items()})
