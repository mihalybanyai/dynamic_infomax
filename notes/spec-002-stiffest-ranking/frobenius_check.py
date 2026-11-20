"""Does exp-decay's stiffest Fisher direction integrate to a coordinate? (spec 002 §4.2, [^4-stiff])

A ranking "stiffest direction first" needs a coordinate psi(theta) whose Fisher gradient is the
stiffest eigenvector v(theta) of g, i.e. d psi proportional to omega = g v, which is proportional
to v. By Frobenius, such a psi exists locally iff omega ^ d omega = 0. In D = 2 this holds
identically; this script measures it at D = 3 and D = 4.

Model (A&M Eq. 6; spec 002 §4.1): y_t = (1/D) sum_mu exp(-k_mu t), k_mu = exp(-theta_mu),
m = 26 times in [1, 5]. sigma only scales g, so it is left out. Points: theta drawn uniformly in
the ordered box [-1, 3]^D, kept when adjacent rates differ by at least 0.3 and the top two
eigenvalues by a factor of at least 2, so that v is well defined. Derivatives of the unit
eigenvector field are central differences with step h; the sign of v is aligned with its value
at the centre.

Reported per point: the twist |omega ^ d omega| / (|omega| |d omega|), which is 0 for an
integrable field and at most 1 (in D = 3 it is |cos| of the angle between v and curl v).
Controls: a normalised gradient field (integrable: twist ~ finite-difference error) and the
contact form (-x2, x1, 1) (not integrable: twist of order one).

Run:    uv run python notes/spec-002-stiffest-ranking/frobenius_check.py
Output: notes/spec-002-stiffest-ranking/frobenius_check.out (stdout; a few seconds)
"""

from datetime import date
from itertools import combinations

import numpy as np

T = np.linspace(1.0, 5.0, 26)
LO, HI = -1.0, 3.0
H = 1e-4
SEED = 20261120


def jac(theta):
    k = np.exp(-theta)
    return (T[:, None] * k[None, :] * np.exp(-k[None, :] * T[:, None])) / len(theta)


def stiffest(theta):
    J = jac(theta)
    w, V = np.linalg.eigh(J.T @ J)
    return V[:, -1], w[-1] / w[-2]


def twist(field, x):
    """|omega ^ d omega| / (|omega| |d omega|) at x, for a unit covector field."""
    D = len(x)
    w0 = field(x)
    dw = np.zeros((D, D))  # dw[j] = d omega / d x_j
    for j in range(D):
        e = np.zeros(D)
        e[j] = H
        wp, wm = field(x + e), field(x - e)
        wp *= np.sign(wp @ w0)
        wm *= np.sign(wm @ w0)
        dw[j] = (wp - wm) / (2 * H)
    F = dw - dw.T  # F[j, k] = d_j omega_k - d_k omega_j
    norm_F = np.sqrt(sum(F[j, k] ** 2 for j, k in combinations(range(D), 2)))
    T3 = [w0[i] * F[j, k] + w0[j] * F[k, i] + w0[k] * F[i, j] for i, j, k in combinations(range(D), 3)]
    return np.sqrt(np.sum(np.square(T3))) / (np.linalg.norm(w0) * norm_F)


def unit(f):
    return lambda x: f(x) / np.linalg.norm(f(x))


def sample_points(D, n, rng):
    out = []
    while len(out) < n:
        th = np.sort(rng.uniform(LO, HI, D))
        if np.min(np.diff(th)) < 0.3:
            continue
        if stiffest(th)[1] < 2.0:
            continue
        out.append(th)
    return out


def summarise(label, values):
    v = np.array(values)
    q = np.quantile(v, [0.1, 0.5, 0.9])
    print(f"  {label:<34} n={len(v):3d}  twist 10/50/90%: {q[0]:.2e} {q[1]:.2e} {q[2]:.2e}"
          f"  share > 1e-3: {np.mean(v > 1e-3):.2f}")


def main():
    rng = np.random.default_rng(SEED)
    print(f"frobenius_check.py  {date.today()}  seed {SEED}  h = {H}")
    print("Controls (D = 3, 100 random points in [-1, 3]^3):")
    grad = unit(lambda x: np.array([2 * x[0] + x[1] * x[2], 2 * x[1] + x[0] * x[2], 2 * x[2] + x[0] * x[1]]))
    contact = unit(lambda x: np.array([-x[1], x[0], 1.0]))
    pts = [rng.uniform(LO, HI, 3) for _ in range(100)]
    summarise("normalised gradient (integrable)", [twist(grad, p) for p in pts])
    summarise("contact form (not integrable)", [twist(contact, p) for p in pts])
    print("Exp-decay, stiffest eigenvector of g:")
    for D in (3, 4):
        pts = sample_points(D, 200, rng)
        summarise(f"D = {D}", [twist(lambda th: stiffest(th)[0], p) for p in pts])


if __name__ == "__main__":
    main()
