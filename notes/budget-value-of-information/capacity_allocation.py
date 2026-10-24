"""Hard-capacity test: does knowing N help an agent allocate K representational units?
Reduced square hypercone, L=50, sigma=1, D-1 habits (data x_1 = th1 + e/sqrt(N),
x_mu = r(th1) u_mu + e/sqrt(N), r = th1/L). Representation (additive capacity):
J atoms along th1 (cell centres, equal weights: neutral mass) plus one shared codebook of
n_u values of u per habit (cell centres, equal weights); K = J + (D-1)*n_u.
Allocation rule at an assumed budget N': choose n_u (hence J) minimising the worst-case
per-theta cost at N' (worst th1 gap + (D-1) * worst habit gap at the thick end, r=1).
Score at the true N: x1 mismatch D(m_q||m_pi) + (D-1) E_{th1~q} D(g_r||h_r), habit
values u ~ U[0,1] (habit part conditions on th1, which L=50 resolves at every N here).
Informed = rule at N'=N. Lower is better."""
import numpy as np, math
L = 50.0
erf = np.vectorize(math.erf)
Phi = lambda z: 0.5*(1 + erf(z/np.sqrt(2)))
phi = lambda z, s: np.exp(-z**2/(2*s*s))/np.sqrt(2*np.pi*s*s)
def kl(p, q, dx): return float(np.sum(p*np.log(np.maximum(p,1e-300)/np.maximum(q,1e-300)))*dx)

def th1_atoms(J): return (np.arange(J) + 0.5)*L/J
def u_code(n):    return (np.arange(n) + 0.5)/n

def worst_th1(J, s):            # max over th1 of KL(N(th1,s^2) || equal mixture of J atoms)
    at = th1_atoms(J); gap = L/J
    x = np.linspace(-6*s, L + 6*s, 3000); dx = x[1]-x[0]
    m = phi(x[:,None] - at[None,:], s).mean(axis=1)
    cands = np.concatenate([at[:2], at[:2] + gap/2, [0.0, L]])  # interior gaps repeat
    return max(kl(phi(x - t, s), m, dx) for t in cands)
def worst_habit(n, s, r=1.0):  # max over u of KL(N(r u,s^2) || codebook mixture), at r
    cu = u_code(n)*r
    x = np.linspace(-6*s, r + 6*s, 1500); dx = x[1]-x[0]
    m = phi(x[:,None] - cu[None,:], s).mean(axis=1)
    cands = np.concatenate([[0.0, r], cu[:1] + r/(2*n) if n > 1 else [r/2]])
    return max(kl(phi(x - t, s), m, dx) for t in cands)

def allocate(K, Dm1, Nass):
    s = 1/np.sqrt(Nass); best = None
    for n in range(1, (K - 1)//Dm1 + 1):
        J = K - Dm1*n
        c = worst_th1(J, s) + Dm1*worst_habit(n, s)
        if best is None or c < best[0]: best = (c, J, n)
    return best[1], best[2]

def score(J, n, N, q_lo, q_hi, Dm1):
    s = 1/np.sqrt(N)
    x = np.linspace(-6*s, L + 6*s, 4000); dx = x[1]-x[0]
    tg = np.linspace(q_lo, q_hi, 400)
    mq = phi(x[:,None] - tg[None,:], s).mean(axis=1)
    mp = phi(x[:,None] - th1_atoms(J)[None,:], s).mean(axis=1)
    s1 = kl(mq, mp, dx)
    hab = 0.0; rs = np.linspace(q_lo, q_hi, 41)/L
    for r in rs:
        if r < 1e-9: continue
        z = np.linspace(-6*s, r + 6*s, 1500); dz = z[1]-z[0]
        g = (Phi(z/s) - Phi((z - r)/s))/r                       # uniform u, smeared
        h = phi(z[:,None] - (u_code(n)*r)[None,:], s).mean(axis=1)
        hab += kl(g, h, dz)
    return s1 + Dm1*hab/len(rs)

budgets = [1, 4, 16, 64]
natures = {"uniform": (0, L), "thin end": (0, L/5), "thick end": (4*L/5, L)}
for Dm1, Ks in [(1, [20, 60, 150]), (25, [60, 150, 400])]:
    for K in Ks:
        alloc = {Na: allocate(K, Dm1, Na) for Na in budgets}
        print(f"\n== D={Dm1+1}, K={K}: allocation (J th1 atoms, n_u codebook) by assumed N': "
              + ", ".join(f"N'={Na}: {alloc[Na]}" for Na in budgets))
        for qn, (lo, hi) in natures.items():
            print(f"  nature {qn}: rows true N; cols assumed N' (score, nats)")
            for N in budgets:
                row = [score(*alloc[Na], N, lo, hi, Dm1) for Na in budgets]
                tag = "  informed best" if np.argmin(row) == budgets.index(N) or \
                      abs(row[budgets.index(N)] - min(row)) < 1e-9 else \
                      f"  best off-diagonal N'={budgets[int(np.argmin(row))]}"
                print(f"    N={N:<2d} " + " ".join(f"{v:8.2f}" for v in row) + tag)
