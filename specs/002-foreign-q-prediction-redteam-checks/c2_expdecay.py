"""Exp-decay (spec 002 sec 4.1): Fisher lengths vs grid cells; distance from the wide box's faces to the true edges."""
import numpy as np
times = np.linspace(1.0, 5.0, 26)

def y(theta):
    k = np.exp(-np.asarray(theta, float))
    return np.mean(np.exp(-k[:, None] * times), axis=0)

def J(theta):
    theta = np.asarray(theta, float); D = len(theta); k = np.exp(-theta)
    return (times[:, None] * k[None, :] * np.exp(-k[None, :] * times[:, None])) / D   # (m, D)

for sigma in (0.05, 0.1, 0.4):
    # D = 1: Fisher length of the box [-1, 3] and per-cell length at G = 50
    th = np.linspace(-1, 3, 4001)
    speed = np.array([np.linalg.norm(J([t])[:, 0]) / sigma for t in th])
    L = np.trapezoid(speed, th)
    print(f"sigma={sigma}: D=1 Fisher length of [-1,3] = {L:.1f}; max speed {speed.max():.1f}/unit theta;"
          f" G=50 cell = {4/50*speed.max():.2f} Fisher lengths at steepest")

sigma = 0.1
# stiffest eigen-direction speed at sample points for D = 2, 3, 4 and the cell size at the spec's G
rng = np.random.default_rng(1)
for D, G in ((2, 50), (3, 30), (4, 20)):
    sp = []
    for _ in range(2000):
        t = np.sort(rng.uniform(-1, 3, D))
        g = J(t).T @ J(t) / sigma**2
        sp.append(np.sqrt(np.linalg.eigvalsh(g)[-1]))
    sp = np.array(sp)
    cell = 4.0 / G
    print(f"D={D}, G={G}: cell {cell:.3f} in theta; stiffest speed median {np.median(sp):.1f}, 90% {np.quantile(sp,0.9):.1f}"
          f" -> cell spans {cell*np.median(sp):.2f} (median) / {cell*np.quantile(sp,0.9):.2f} (90%) Fisher lengths at sigma=0.1;"
          f" at sigma=0.05: {2*cell*np.quantile(sp,0.9):.2f}")

# distance (noise units, N=1, sigma=0.1) from the wide box's slow face theta=3 to theta=+inf (component constant 1),
# and from the fast face theta=-1 to theta=-inf (component 0), with the other D-1 components fixed
for D in (1, 2, 4, 8, 26):
    d_slow = np.linalg.norm((1.0 - np.exp(-np.exp(-3.0) * times)) / D) / 0.1
    d_fast = np.linalg.norm(np.exp(-np.exp(1.0) * times) / D) / 0.1
    print(f"D={D:2d}: face theta=3 is {d_slow:.2f} noise units from the slow edge; face theta=-1 is {d_fast:.2f} from the fast edge")
