"""Test of the criterion: value of knowing N ~ spread of dC(th1) = C_perp_M(th1) - C_perp_N(th1).
Reduced square hypercone (sigma=1, L=50): th1 in [0,L] seen at noise 1/sqrt(N);
D-1 habits of width r*sqrt(N) Fisher lengths, r = th1/L (taper) or r = r0 (constant
cross-section control). Conditional habit capacity (D-1)*c(r sqrt M) is exact (parallel
channels); the information habit data carry about th1 is ignored (A&M's O(D/L^2)).
p*_M = BA on th1 with that bonus. Score at budget N on x1: D(m_q^N || m_{p*_M}^N) for
nature q on th1, as excess over p*_N. Prediction (prior level): log E_{w_N} e^{dC} - E_q dC."""
import numpy as np
L = 50.0
th = np.linspace(0, L, 1001)

# c(a): capacity (nats) of amplitude-constrained Gaussian channel, input [0,a], unit noise
def cap(a):
    if a < 1e-6: return 0.0
    u = np.linspace(0, a, 161); z = np.linspace(-7, a + 7, 1200); dz = z[1]-z[0]
    lk = np.exp(-(z[None,:]-u[:,None])**2/2)/np.sqrt(2*np.pi)
    nH = np.sum(lk*np.log(np.maximum(lk,1e-300)),axis=1)*dz
    w = np.ones_like(u)/len(u)
    for _ in range(3000):
        d = nH - (lk @ np.log(np.maximum(w @ lk,1e-300)))*dz
        w = w*np.exp(d); w /= w.sum()
    return float(np.max(nH - (lk @ np.log(np.maximum(w @ lk,1e-300)))*dz))
agrid = np.linspace(0, 4.0, 41)
cvals = np.array([cap(a) for a in agrid])
c = lambda a: np.interp(a, agrid, cvals)

def chan(N):
    s = 1/np.sqrt(N)
    x = np.linspace(-6*s, L + 6*s, 1400); dx = x[1]-x[0]
    lk = np.exp(-(x[None,:]-th[:,None])**2/(2*s*s))/np.sqrt(2*np.pi*s*s)
    nH = np.sum(lk*np.log(np.maximum(lk,1e-300)),axis=1)*dx
    return lk, nH, dx
budgets = [1, 4, 16]
ch = {N: chan(N) for N in budgets}

def ba(bonus, chN, iters=4000):
    lk, nH, dx = chN
    w = np.ones_like(th)/len(th)
    for _ in range(iters):
        d = nH - (lk @ np.log(np.maximum(w @ lk,1e-300)))*dx
        w = w*np.exp(d + bonus - bonus.max()); w /= w.sum()
    return w
def mism(qw, w, chN):
    lk, _, dx = chN
    mq, mw = qw @ lk, w @ lk
    return float(np.sum(mq*np.log(np.maximum(mq,1e-300)/np.maximum(mw,1e-300)))*dx)

natures = {"uniform": np.ones_like(th), "thin end (th1<L/5)": (th < L/5).astype(float)}
for k in natures: natures[k] /= natures[k].sum()
print("c(a) at a=0.5,1,2,4:", [round(float(c(a)),3) for a in (0.5,1,2,4)])
for geom, rfun in [("taper", lambda t: t/L), ("constant cross-section", lambda t: np.ones_like(t))]:
    for D in [10, 26]:
        bon = {M: (D-1)*c(rfun(th)*np.sqrt(M)) for M in budgets}
        w = {M: ba(bon[M], ch[M]) for M in budgets}
        print(f"\n== {geom}, D={D}: excess D(m_q||m_p*M) - D(m_q||m_p*N) on x1, nats  [criterion prediction]")
        for qn, q in natures.items():
            print(f"  nature {qn}:")
            for N in budgets:
                cells = []
                for M in budgets:
                    ex = mism(q, w[M], ch[N]) - mism(q, w[N], ch[N])
                    dC = bon[M] - bon[N]
                    pred = np.log(np.sum(w[N]*np.exp(dC - dC.max()))) + dC.max() - q @ dC
                    cells.append(f"M={M:<2d} {ex:7.2f} [{pred:6.2f}]")
                print(f"    N={N:<2d} " + "  ".join(cells))
