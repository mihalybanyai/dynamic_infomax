"""Vertex figure for spec 002-foreign-q-prediction (§1.2, "The vertex and its noise halo").

What the curvature knob acts on, drawn at D = 2, where the square hypercone is a triangle
in prediction space and the figure is exact rather than schematic.

  (a) The hypercone's boundary: the base face (theta_1 = W), the lateral edge along the
      theta_1-axis (theta_2 = 0), the top edge (theta_2 = 1), and the vertices: the tip and
      the two base corners. The knob's vertex v = y(W, 0) is the base corner on the
      theta_1-axis. The maximum-likelihood estimate of an observation is its nearest
      manifold point (Gaussian noise of one scale), so observations in the shaded
      quarter-plane all have their estimate at v: v's noise halo. W = 5 for display; the
      spec uses W = 50.
  (b) Zoom on v with the knob off (kappa = 1): data of a nature at v, at noise
      sigma/sqrt(N) = 0.1, and the halo computed as the set of outside points whose
      nearest manifold point is v. A quarter of the estimates land on v.
  (c) The same with kappa = 1/2: inside the ball of radius rho = 5 sigma/sqrt(N) the
      corner narrows to kappa*pi/2 = 45 degrees and the halo widens to pi - kappa*pi/2 = 135
      degrees, so 3/8 of the estimates land on v. Outside the ball nothing changes.
  (d) The warp's angle factor kappa(u): kappa up to rho/2, the smoothstep
      S(s) = 3s^2 - 2s^3 of s = 2u/rho - 1 up to rho, 1 beyond (spec §4.1).

The warp is re-implemented here from §4.1's pseudocode, for drawing only;
src/infomax/models.py holds the implementation the tests check.

Run:    uv run python diagrams/002-foreign-q-prediction-vertex.py
Output: diagrams/002-foreign-q-prediction-vertex.svg
"""

import matplotlib

matplotlib.use("Agg")  # headless: write SVG, no display
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Polygon
from matplotlib.path import Path

# ---- shared style (as the geometry figure) ---------------------------------
RELEVANT = "#1f4e79"   # manifold edges, labels
IRREL = "#c0c0c0"      # manifold fill
HALO = "#d08c2b"       # v's noise halo, estimates at v
ACCENT = "#2e7d32"     # the warp's ball and ramp
GREY = "#555555"

plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

W = 5.0                # display value; the spec uses W = 50
SIGMA_EFF = 0.1        # noise of the data mean, sigma/sqrt(N), at a curvature cell
RHO = 5 * SIGMA_EFF    # the warp's ball (spec §4.1)


# ---- the warp, from spec §4.1 (v at the origin of the relative coordinates) -
def smoothstep(s):
    """S(s) = 3s^2 - 2s^3: 0 to 1 with zero slope at both ends."""
    return s * s * (3 - 2 * s)


def kappa_of_u(u, kappa, rho):
    """The warp's angle factor: kappa inside rho/2, 1 beyond rho, smoothstep between."""
    return kappa + (1 - kappa) * smoothstep(np.clip(2 * u / rho - 1, 0, 1))


def warp_vertex(d, kappa, rho):
    """Warp points d = y - v (shape (n, 2)): the angle beta from the lateral edge
    (direction -e_1) becomes kappa(u) * beta; the distance u from v is kept."""
    u = np.linalg.norm(d, axis=-1)
    a, perp = -d[:, 0], d[:, 1]
    beta = np.arctan2(np.abs(perp), a)
    k = kappa_of_u(u, kappa, rho)
    out = np.stack([-u * np.cos(k * beta), u * np.sin(k * beta) * np.sign(perp)], axis=-1)
    return np.where((u < rho)[:, None], out, d)


def boundary(kappa):
    """The (warped) triangle's boundary in coordinates relative to v, as a closed polyline:
    tip -> lateral edge -> v -> base face -> top base corner -> top edge -> tip."""
    x = np.concatenate([np.linspace(-W, -1.0, 40), np.linspace(-1.0, 0.0, 1500)[1:]])
    lateral = np.stack([x, np.zeros_like(x)], axis=-1)
    s = np.concatenate([np.linspace(0.0, 1.2 * RHO, 1500), np.linspace(1.2 * RHO, 1.0, 100)[1:]])
    base = warp_vertex(np.stack([np.zeros_like(s), s], axis=-1), kappa, RHO)
    top = np.stack([np.linspace(0.0, -W, 60), np.linspace(1.0, 0.0, 60)], axis=-1)
    return np.concatenate([lateral, base[1:], top[1:]])


def nearest_on_polyline(points, poly, chunk=4000):
    """Nearest point of the closed polyline `poly` to each of `points` (Euclidean)."""
    A, B = poly[:-1], poly[1:]
    AB = B - A
    L2 = np.maximum((AB**2).sum(-1), 1e-300)
    out = np.empty_like(points)
    for i in range(0, len(points), chunk):
        P = points[i:i + chunk, None, :]
        t = np.clip(((P - A) * AB).sum(-1) / L2, 0.0, 1.0)
        Q = A + t[..., None] * AB
        j = ((P - Q) ** 2).sum(-1).argmin(axis=1)
        out[i:i + chunk] = Q[np.arange(len(j)), j]
    return out


def mle_at_v(points, kappa):
    """True where the maximum-likelihood estimate of an observation is v itself: the point
    lies outside the manifold and its nearest manifold point is v."""
    poly = boundary(kappa)
    inside = Path(poly).contains_points(points)
    near = nearest_on_polyline(points, poly)
    return (~inside) & (np.linalg.norm(near, axis=-1) < 1e-9)


fig, ((axA, axB), (axC, axD)) = plt.subplots(2, 2, figsize=(11.5, 9.6))


# ---- panel (a): the hypercone at D = 2, its faces and vertices --------------
tri = np.array([[0.0, 0.0], [W, 0.0], [W, 1.0]])
axA.add_patch(Polygon(tri, closed=True, facecolor=IRREL, edgecolor="none", alpha=0.55))
axA.add_patch(Polygon([[W, 0], [W + 2, 0], [W + 2, -2], [W, -2]], closed=True,
                      facecolor=HALO, edgecolor="none", alpha=0.30))
axA.plot([0, W], [0, 0], color=RELEVANT, lw=2.4)            # lateral edge
axA.plot([W, W], [0, 1], color=RELEVANT, lw=2.4)            # base face
axA.plot([0, W], [0, 1], color="#7a7a7a", lw=1.2)           # top edge
for (x, y) in tri:
    axA.plot(x, y, "o", color=RELEVANT, ms=5, zorder=5)
axA.plot(W, 0, "o", color=HALO, ms=9, mec="k", zorder=6)
axA.text(W - 0.12, -0.13, r"$v = y(W, 0)$", ha="right", va="top", fontsize=10, color="k")
axA.text(-0.1, 0.06, "tip\n" r"($\theta_1 = 0$)", ha="left", va="bottom", fontsize=8.5,
         color=GREY)
axA.text(2.3, -0.06, r"lateral edge: the $\theta_1$-axis ($\theta_2 = 0$)", ha="center",
         va="top", fontsize=9, color=RELEVANT)
axA.text(W + 0.08, 0.62, "base face\n" r"($\theta_1 = W$)", ha="left", va="center",
         fontsize=9, color=RELEVANT)
axA.text(2.25, 0.56, r"top edge ($\theta_2 = 1$)", ha="center", va="bottom", fontsize=8.5,
         color=GREY, rotation=9)
axA.text(W + 0.08, 1.0, "base corner", ha="left", va="center", fontsize=8.5, color=GREY)
axA.text(W + 0.55, -0.75, "halo of $v$:\nestimate\nat $v$", ha="center", va="center",
         fontsize=9, color=HALO)
# three observations and their estimates (nearest manifold points)
for (x, y), (ex, ey) in [((5.55, -0.28), (W, 0.0)), ((3.4, -0.42), (3.4, 0.0)),
                         ((5.55, 0.45), (W, 0.45))]:
    axA.plot(x, y, "x", color="k", ms=6, mew=1.4)
    axA.annotate("", xy=(ex, ey), xytext=(x, y),
                 arrowprops=dict(arrowstyle="->", color="k", lw=1.0, shrinkA=3, shrinkB=2))
axA.text(0.0, -0.62, "observation $\\times$ $\\to$ its estimate:\nthe nearest manifold point",
         ha="left", va="top", fontsize=8.5, color=GREY)
axA.set_xlim(-0.3, W + 1.1)
axA.set_ylim(-1.0, 1.3)
axA.set_xlabel(r"$y_1$")
axA.set_ylabel(r"$y_2$")
axA.set_title(r"(a) the hypercone at $D = 2$: faces, edges, vertices", fontsize=10.5)


# ---- panels (b), (c): zoom on v, knob off and on ----------------------------
rng = np.random.default_rng(20261124)
X = rng.normal(0.0, SIGMA_EFF, size=(600, 2))            # data means of a nature at v
X_MC = rng.normal(0.0, SIGMA_EFF, size=(40000, 2))       # for the fraction quoted
XL, YL = (-0.75, 0.45), (-0.45, 0.75)
gx, gy = np.meshgrid(np.linspace(*XL, 241), np.linspace(*YL, 241))
grid = np.stack([gx.ravel(), gy.ravel()], axis=-1)


def draw_zoom(ax, kappa, title):
    poly = boundary(kappa)
    ax.add_patch(Polygon(poly, closed=True, facecolor=IRREL, edgecolor="none", alpha=0.55))
    halo = mle_at_v(grid, kappa).reshape(gx.shape)
    ax.contourf(gx, gy, halo.astype(float), levels=[0.5, 1.5], colors=[HALO], alpha=0.30)
    ax.plot(poly[:, 0], poly[:, 1], color=RELEVANT, lw=2.0)
    ax.add_patch(Circle((0, 0), RHO, fill=False, ls="--", lw=1.1, color=ACCENT))
    ax.add_patch(Circle((0, 0), RHO / 2, fill=False, ls=":", lw=1.1, color=ACCENT))
    hit = mle_at_v(X, kappa)
    ax.plot(X[~hit, 0], X[~hit, 1], ".", color=GREY, ms=2.5, alpha=0.6)
    ax.plot(X[hit, 0], X[hit, 1], ".", color=HALO, ms=3.5)
    ax.plot(0, 0, "o", color=HALO, ms=8, mec="k", zorder=6)
    corner = kappa * 90.0
    ax.add_patch(Arc((0, 0), 0.24, 0.24, theta1=180 - corner, theta2=180, color="k", lw=1.0))
    ax.text(-0.17 * np.cos(np.radians(corner / 2)), 0.17 * np.sin(np.radians(corner / 2)),
            f"{corner:.0f}°", ha="center", va="center", fontsize=8.5)
    frac_mc = mle_at_v(X_MC, kappa).mean()
    title += (f"\ncorner {corner:.0f}°, halo {180 - corner:.0f}°; P(estimate at $v$) = "
              rf"$\frac{{1}}{{2}} - \frac{{\kappa}}{{4}}$ = {0.5 - kappa / 4:.3f} (simulated {frac_mc:.3f})")
    ax.text(RHO * np.cos(np.radians(200)) - 0.02, RHO * np.sin(np.radians(200)) - 0.04,
            r"$\rho$", color=ACCENT, fontsize=9, ha="right")
    ax.text(RHO / 2 * np.cos(np.radians(215)) - 0.01, RHO / 2 * np.sin(np.radians(215)) - 0.03,
            r"$\rho/2$", color=ACCENT, fontsize=8.5, ha="right")
    ax.set_xlim(*XL)
    ax.set_ylim(*YL)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$y_1 - W$")
    ax.set_ylabel(r"$y_2$")
    ax.set_title(title, fontsize=9.5)


draw_zoom(axB, 1.0, r"(b) zoom on $v$, knob off ($\kappa = 1$)")
draw_zoom(axC, 0.5, r"(c) knob on ($\kappa = \frac{1}{2}$): the corner narrows inside $\rho$")
axB.text(-0.72, 0.55, "dots: data means of a nature at $v$\n(noise $\\sigma/\\sqrt{N} = 0.1$);\n"
         "orange: estimate at $v$", ha="left", va="center", fontsize=8, color=GREY)
axC.text(-0.72, 0.55, "manifold unchanged\nbeyond " r"$\rho$", ha="left", va="center",
         fontsize=8, color=ACCENT)


# ---- panel (d): the angle factor kappa(u) -----------------------------------
u = np.linspace(0.0, 1.3 * RHO, 400)
for kappa, ls in [(1.0, "-"), (0.5, "--"), (0.25, ":")]:
    axD.plot(u / RHO, kappa_of_u(u, kappa, RHO), color=ACCENT, ls=ls, lw=2.0,
             label=rf"$\kappa = {kappa:g}$")
axD.axvspan(0.5, 1.0, color=ACCENT, alpha=0.08)
axD.text(0.75, 0.08, r"$\kappa + (1-\kappa)\,S(2u/\rho - 1)$" "\n" r"$S(s) = 3s^2 - 2s^3$",
         ha="center", va="bottom", fontsize=9, color="k")
axD.text(0.25, 0.08, r"$\kappa$", ha="center", va="bottom", fontsize=9)
axD.text(1.15, 0.08, "1\n(identity)", ha="center", va="bottom", fontsize=9)
axD.set_xlim(0, 1.3)
axD.set_ylim(0, 1.1)
axD.set_xticks([0, 0.5, 1.0])
axD.set_xticklabels(["0", r"$\rho/2$", r"$\rho$"])
axD.set_xlabel(r"distance $u$ from $v$")
axD.set_ylabel(r"angle factor $\kappa(u)$: $\beta \mapsto \kappa(u)\,\beta$")
axD.legend(loc="center left", bbox_to_anchor=(0.0, 0.62), fontsize=8.5, frameon=False)
axD.set_title(r"(d) the warp: angle factor $\kappa(u)$ (spec §4.1)", fontsize=10.5)


fig.suptitle("Spec 002 §1.2 — the vertex $v$ and its noise halo, at $D = 2$", fontsize=11.5)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig("diagrams/002-foreign-q-prediction-vertex.svg")
