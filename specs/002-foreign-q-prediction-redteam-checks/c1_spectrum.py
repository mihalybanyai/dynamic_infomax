"""Fixed-spectrum nature of spec 002 sec 4.3: clipping fraction and D-dependence of its data law."""
import numpy as np
from scipy.stats import norm
rng = np.random.default_rng(0)
times = np.linspace(1.0, 5.0, 26)
sigma = 0.1

def theta_spec(c, w, D, box):
    q = (np.arange(1, D + 1) - 0.5) / D
    th = c + w * norm.ppf(q)
    return np.clip(th, *box)

def y(theta):
    k = np.exp(-theta)
    return np.mean(np.exp(-k[:, None] * times), axis=0)

boxes = {"wide": (-1.0, 3.0), "matched": (0.0, np.log(5.0))}
# 1) fraction of rates clipped onto a box face, averaged over the nature's (c, w)
for name, box in boxes.items():
    for D in (4, 26):
        fr = []
        frw = {0.25: [], 0.5: [], 1.0: [], 2.0: []}
        for _ in range(4000):
            c = rng.uniform(0, np.log(5)); w = np.exp(rng.uniform(np.log(0.1), np.log(2)))
            q = (np.arange(1, D + 1) - 0.5) / D
            th = c + w * norm.ppf(q)
            fr.append(np.mean((th <= box[0]) | (th >= box[1])))
        for wf in frw:
            vals = []
            for c in np.linspace(0, np.log(5), 41):
                th = c + wf * norm.ppf((np.arange(1, D + 1) - 0.5) / D)
                vals.append(np.mean((th <= box[0]) | (th >= box[1])))
            frw[wf] = np.mean(vals)
        print(f"box={name:7s} D={D:2d}: mean clipped fraction over nature = {np.mean(fr):.2f}; "
              + ", ".join(f"w={k}: {v:.2f}" for k, v in frw.items()))
# 2) D-dependence of the data law at fixed (c, w): distance in noise units between y at D and at D=26
print("Distance |y_D - y_26|/sigma (single observation, N=1), wide box:")
for c, w in [(0.8, 0.3), (0.8, 1.0), (0.8, 2.0), (0.3, 0.5)]:
    yref = y(theta_spec(c, w, 26, boxes["wide"]))
    out = []
    for D in (2, 3, 4, 8, 12):
        out.append(np.linalg.norm(y(theta_spec(c, w, D, boxes["wide"])) - yref) / sigma)
    print(f"  c={c}, w={w}: " + ", ".join(f"D={D}: {d:.2f}" for D, d in zip((2, 3, 4, 8, 12), out)))
