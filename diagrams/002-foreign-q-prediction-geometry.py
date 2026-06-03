"""Model-geometry figure for spec 002-foreign-q-prediction (§1.2).

Unlike the PGM (which draws *nature's* sampling process), this figure draws the
*geometry of the model manifold* that the conceptual claims of §0/§2/§3 ride on:
the hyperribbon structure, the hypercone caricature, and the constant-cross-
section null. It is the visual companion to the "model geometry" block of §1.2.

Three panels, left to right:

  (a) Hyperribbon Fisher-width spectrum. The model manifold {y(theta)} is long
      and thin: its Fisher widths W_mu (square-roots of the FIM eigenvalues, in
      noise units sigma) fall off roughly geometrically over many orders. A few
      directions are RELEVANT (W>1: resolvable at this budget, "stiff"); the
      many others are IRRELEVANT (W<1: unresolvable, "sloppy"). The co-volume is
      the product of the irrelevant widths -- extent the data cannot pin down but
      a parameter-space measure (Jeffreys) still weights.

  (b) Square hypercone (taper r = theta_1/L). The analytic caricature that
      isolates the single feature driving the co-volume pathology: a co-volume
      GRADIENT. One relevant axis theta_1 (Fisher length ~ L) with d-1 irrelevant
      directions whose extent r(theta_1)=theta_1/L tapers linearly to the tip, so
      the cross-sectional (co-)volume element sqrt(det g) ∝ theta_1^{d-1} grows
      toward the thick base. Jeffreys piles its mass at the base (a vanishing
      fraction of distinguishable predictions as d grows) and its posterior is
      pulled there -- the closed-form bias Delta=(d-1)/x, largest at the thin end.
      p* instead places atoms ≈1 Fisher length apart along the relevant axis and
      collapses the irrelevant ones onto the boundary.

  (c) Constant cross-section cone (taper 0, the negative control of §2.4). Same
      family with r(theta_1)=r0 constant: no co-volume gradient, sqrt(det g)
      constant, b(theta)≡0, Jeffreys = uniform on the relevant coordinate. With
      no pathology to avoid, every prior must tie -- the falsification screen T2.

The exp-decay model (§4.1.1) is the realistic curved instance of the panel-(a)
ribbon; the hypercone (b) is its exactly-solvable caricature; (c) is (b) with the
taper switched off. Exact maps and FIM are in §4.1 / §9.

Run:    python diagrams/002-foreign-q-prediction-geometry.py
Output: diagrams/002-foreign-q-prediction-geometry.svg
"""

import matplotlib

matplotlib.use("Agg")  # headless: write SVG, no display
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

# ---- shared style ---------------------------------------------------------
RELEVANT = "#1f4e79"   # stiff / resolvable
IRREL = "#c0c0c0"      # sloppy / unresolvable
JEFF = "#c1432e"       # Jeffreys mass / bias
PSTAR = "#1f4e79"      # p* atoms
ACCENT = "#2e7d32"     # annotations

plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(13.5, 4.4))


# ---- panel (a): hyperribbon Fisher-width spectrum -------------------------
d = 8
mu = np.arange(1, d + 1)
# Fisher lengths (= manifold widths) falling geometrically: the sloppy spectrum
L = 30.0 * (0.30 ** (mu - 1))
relevant = L > 1.0

axA.bar(mu[relevant], L[relevant], color=RELEVANT, width=0.7,
        label="relevant ($L_\\mu>1$, stiff)")
axA.bar(mu[~relevant], L[~relevant], color=IRREL, width=0.7,
        label="irrelevant ($L_\\mu<1$, sloppy)")
axA.axhline(1.0, color=JEFF, ls="--", lw=1.3)
axA.text(d + 0.35, 1.0, r"$L_\mu=1$" "\n(resolution)", color=JEFF,
         va="center", ha="left", fontsize=8.5)
axA.set_yscale("log")
axA.set_xlabel(r"parameter direction $\mu$  (FIM eigen-index)")
axA.set_ylabel(r"Fisher length $L_\mu$ = width  (units of $\sigma$)")
axA.set_title("(a) hyperribbon: a sloppy width spectrum", fontsize=10.5)
axA.set_xticks(mu)
axA.set_xlim(0.4, d + 1.9)
axA.legend(loc="upper right", fontsize=8, frameon=False)
axA.annotate(r"co-volume $V_\perp$" "\n" r"$=\prod_{L_\mu<1} L_\mu$",
             xy=(6.0, L[5]), xytext=(4.55, 0.016),
             fontsize=8.5, color="#555555", ha="center",
             arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8))


# ---- hypercone drawing helper ---------------------------------------------
def draw_cone(ax, r_of_theta, title, *, taper):
    """Side view of the (square) hypercone manifold along the relevant axis.

    The filled envelope shows one representative irrelevant direction's extent
    +/- r(theta_1)/2; the co-volume is the product over all d-1 such directions.
    For d=2 there is exactly one irrelevant direction, so this panel IS the full
    model manifold (drawn centred about the spine rather than the one-sided
    [0, r] of the literal map; same triangle).
    """
    L = 5.0
    th = np.linspace(0.0, L, 200)
    half = r_of_theta(th) / 2.0

    # manifold envelope (one irrelevant direction)
    upper = list(zip(th, half))
    lower = list(zip(th[::-1], -half[::-1]))
    ax.add_patch(Polygon(upper + lower, closed=True,
                         facecolor=IRREL, edgecolor="#7a7a7a", lw=1.2, alpha=0.55))
    # relevant axis (the spine)
    ax.plot([0, L], [0, 0], color="#7a7a7a", lw=0.8, ls=":")

    # a few cross-sections, to read off how the (co-)volume changes along theta_1
    for tc in [1.0, 2.5, 4.0]:
        hc = r_of_theta(np.array([tc]))[0] / 2.0
        ax.plot([tc, tc], [-hc, hc], color="#5a5a5a", lw=1.4)

    # p* atoms: tile the relevant axis (≈1 Fisher length apart, g_rel ≈ 1) AND
    # collapse each irrelevant direction onto its TWO endpoints -> the two cone
    # edges, a pair per relevant tile, merging at the tip as r -> 0. (Not on the
    # spine: a single interior atom would resolve nothing.)
    tiles = np.arange(0.5, L, 1.0)
    edge = r_of_theta(tiles) / 2.0
    ax.plot(tiles, edge, "o", color=PSTAR, ms=6.0, zorder=5)
    ax.plot(tiles, -edge, "o", color=PSTAR, ms=6.0, zorder=5)

    # Jeffreys co-volume density sqrt(det g) on a twin axis
    ax2 = ax.twinx()
    if taper:
        sdg = (th / L) ** (d - 1)          # ∝ theta_1^{d-1}
    else:
        sdg = np.ones_like(th)             # constant cross-section
    ax2.plot(th, sdg, color=JEFF, lw=2.0)
    ax2.set_ylim(-0.05, 1.15)
    ax2.set_yticks([])

    ax.set_xlim(-0.25, L + 0.25)
    ax.set_ylim(-0.95, 0.95)
    ax.set_xlabel(r"relevant coordinate $\theta_1$ (tip $0 \to$ base $L$)")
    ax.set_title(title, fontsize=10.5)
    ax.set_yticks([])
    return ax2


# ---- panel (b): tapering hypercone (co-volume gradient) -------------------
ax2b = draw_cone(axB, lambda t: t / 5.0, "(b) hypercone (taper): co-volume gradient",
                 taper=True)
ax2b.text(5.15, 1.0, r"$\sqrt{\det g}\propto\theta_1^{\,d-1}$",
          color=JEFF, fontsize=9, va="center", ha="left", rotation=90)
axB.annotate("Jeffreys mass\n& posterior pull", xy=(4.55, 0.0), xytext=(2.5, 0.62),
             fontsize=8.5, color=JEFF, ha="center",
             arrowprops=dict(arrowstyle="->", color=JEFF, lw=1.4))
axB.text(2.55, -0.8,
         r"$p^\star$: relevant tiling $\times$ irrelevant endpoints (cone edges)",
         color=PSTAR, fontsize=8.0, ha="center")
axB.text(0.15, 0.78, "thin end\n(irrelevant\nextent $\\to 0$)", fontsize=7.8,
         color="#555555", ha="left", va="top")


# ---- panel (c): constant cross-section (negative control) -----------------
ax2c = draw_cone(axC, lambda t: 0.7 * np.ones_like(t),
                 "(c) constant cross-section: the null", taper=False)
ax2c.text(5.15, 1.0, r"$\sqrt{\det g}=$ const", color=JEFF, fontsize=9,
          va="center", ha="left", rotation=90)
axC.text(2.5, 0.62, r"no co-volume gradient $\Rightarrow b(\theta)\equiv 0$",
         color=ACCENT, fontsize=9, ha="center")
axC.text(2.5, -0.74, "every prior ties (control T2, §2.4)",
         color=ACCENT, fontsize=8.5, ha="center")


fig.suptitle(
    "Model geometry for spec 002: hyperribbon structure, the hypercone caricature, "
    "and the no-gradient null",
    fontsize=11.5,
)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig("diagrams/002-foreign-q-prediction-geometry.svg")
print("wrote diagrams/002-foreign-q-prediction-geometry.svg")
