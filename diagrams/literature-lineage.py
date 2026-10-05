"""Lineage of the clusters in literature/ (the map of the field).

One horizontal lane per cluster, key works placed by year, a few links between
clusters, and a matrix on the right showing which spec each cluster feeds. The
full lists live in literature/*.md; this figure shows only the works that carry
the links. Update both together.

Links: grey solid = builds on or cites; blue dashed = the same object under
another name. A filled dot in the matrix = feeds a claim of that spec; a hollow
dot = feeds spec 002's open score choice.

Run:    uv run python diagrams/literature-lineage.py
Output: diagrams/literature-lineage.svg
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
LANE = "#f0efec"
SAME = "#2a78d6"

LANES = [
    "Scoring and betting",
    "Capacity and rate–distortion",
    "Universal coding",
    "Learning curves",
    "MDL and NML",
    "Bernardo's circle",
    "Machta group",
    "Komaki school",
    "Feder group",
]
Y = {name: len(LANES) - 1 - i for i, name in enumerate(LANES)}

# (lane, year, label, label offset in points (dx, dy))
U1, U2, D1, D2 = 6, 17, -13, -24
WORKS = [
    ("Scoring and betting", 1956, "Kelly '56", (0, U1)),
    ("Scoring and betting", 1984, "Dawid '84", (0, U1)),
    ("Scoring and betting", 2007, "Gneiting & Raftery '07", (0, U1)),
    ("Capacity and rate–distortion", 1948, "Shannon '48", (0, U1)),
    ("Capacity and rate–distortion", 1959, "Shannon '59", (0, U1)),
    ("Capacity and rate–distortion", 1971, "Smith '71", (-14, U1)),
    ("Capacity and rate–distortion", 1972, "Blahut, Arimoto '72", (14, D1)),
    ("Capacity and rate–distortion", 1980, "Witsenhausen '80", (14, U1)),
    ("Capacity and rate–distortion", 2005, "Chan et al. '05", (0, U1)),
    ("Universal coding", 1969, "Sibson '69", (-8, D1)),
    ("Universal coding", 1973, "Davisson '73, Kemperman '74", (6, U1)),
    ("Universal coding", 1974, "", (0, 0)),
    ("Universal coding", 1979, "Gallager, Ryabko, Topsøe '79; Davisson & Leon-Garcia '80", (40, D2)),
    ("Universal coding", 1980, "", (0, 0)),
    ("Universal coding", 1990, "Clarke & Barron '90, '94", (14, D1)),
    ("Universal coding", 1994, "", (0, 0)),
    ("Universal coding", 1997, "Haussler '97", (10, U1)),
    ("Learning curves", 1994, "Haussler, Kearns & Schapire '94", (-50, U1)),
    ("Learning curves", 1997, "Haussler & Opper '97", (6, D1)),
    ("Learning curves", 2001, "Bialek, Nemenman & Tishby '01", (62, U1)),
    ("MDL and NML", 1987, "Shtarkov '87", (0, U1)),
    ("MDL and NML", 1996, "Rissanen '96", (-6, D1)),
    ("MDL and NML", 1997, "Balasubramanian '97", (16, U1)),
    ("MDL and NML", 2007, "Grünwald '07", (0, D1)),
    ("MDL and NML", 2013, "Watanabe et al. '13", (0, U1)),
    ("MDL and NML", 2021, "Suzuki & Yamanishi '21", (0, D1)),
    ("MDL and NML", 2024, "α-NML '24", (8, U1)),
    ("Bernardo's circle", 1946, "Jeffreys '46", (0, U1)),
    ("Bernardo's circle", 1959, "Stein '59", (0, U1)),
    ("Bernardo's circle", 1977, "Zellner '77", (-10, U1)),
    ("Bernardo's circle", 1979, "Bernardo, Geisser '79", (6, D1)),
    ("Bernardo's circle", 1989, "Berger, Bernardo & Mendoza '89", (14, U1)),
    ("Bernardo's circle", 1996, "Kass & Wasserman '96", (10, D1)),
    ("Bernardo's circle", 2005, "Bernardo '05", (0, U1)),
    ("Bernardo's circle", 2009, "Berger, Bernardo & Sun '09", (14, D1)),
    ("Machta group", 2010, "Transtrum et al. '10, '11", (-20, U1)),
    ("Machta group", 2011, "", (0, 0)),
    ("Machta group", 2016, "Chis et al. '16", (-10, U1)),
    ("Machta group", 2018, "Mattingly et al. '18", (-4, D1)),
    ("Machta group", 2019, "Abbott & Machta '19", (18, D2)),
    ("Machta group", 2023, "Abbott & Machta '23, Quinn et al. '23", (-10, U2)),
    ("Komaki school", 2001, "Komaki '01", (0, U1)),
    ("Komaki school", 2011, "Komaki '11", (-12, D1)),
    ("Komaki school", 2012, "Komaki '12", (10, U1)),
    ("Komaki school", 2014, "Tanaka '14", (14, D1)),
    ("Komaki school", 2016, "Kojima & Komaki '16", (30, U1)),
    ("Feder group", 1998, "Merhav & Feder '98", (0, U1)),
    ("Feder group", 2018, "Fogel & Feder '18", (-14, D1)),
    ("Feder group", 2023, "Goldstein '23", (-16, U1)),
    ("Feder group", 2024, "Fogel & Feder '24, Vituri & Feder '24", (-30, D2)),
]


def X(year: float) -> float:
    """Time axis: one unit per year to 2000, 2.2 units per year after."""
    return year - 1940 if year <= 2000 else 60 + (year - 2000) * 2.2


# (from (lane, year), to (lane, year), kind, arc radius)
LINKS = [
    (("Capacity and rate–distortion", 1972), ("Machta group", 2018), "builds", -0.25),
    (("Universal coding", 1980), ("Komaki school", 2011), "builds", 0.2),
    (("MDL and NML", 1996), ("Machta group", 2023), "builds", -0.2),
    (("Bernardo's circle", 1979), ("Komaki school", 2011), "builds", 0.25),
    (("Feder group", 2024), ("Machta group", 2018), "builds", 0.35),
    (("Bernardo's circle", 1989), ("Machta group", 2018), "same", -0.15),
    (("Bernardo's circle", 1989), ("Komaki school", 2011), "same", 0.2),
    (("Komaki school", 2011), ("Feder group", 2018), "same", -0.3),
    (("Learning curves", 2001), ("Machta group", 2018), "same", 0.15),
]

SPECS = ["000", "001", "002"]
# 1 = feeds a claim, 0.5 = feeds 002's open score choice
FEEDS = {
    "Scoring and betting": {"001": 1, "002": 1},
    "Capacity and rate–distortion": {"000": 1, "002": 1},
    "Universal coding": {"000": 1, "002": 1},
    "Learning curves": {"002": 0.5},
    "MDL and NML": {"002": 1},
    "Bernardo's circle": {"000": 1, "001": 1, "002": 1},
    "Machta group": {"000": 1, "001": 1, "002": 1},
    "Komaki school": {"002": 0.5},
    "Feder group": {"002": 0.5},
}

XM = X(2026) + 12  # first matrix column
DXM = 7


def build() -> plt.Figure:
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(16, 7.8))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for name, y in Y.items():
        if y % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, xmin=0, xmax=1, color=LANE, lw=0, zorder=0)
        ax.text(-2, y, name, ha="right", va="center", fontsize=9.5, color=INK)

    for lane, year, label, (dx, dy) in WORKS:
        y = Y[lane]
        ax.plot(X(year), y, "o", ms=6, mfc=INK, mec=SURFACE, mew=1.5, zorder=4)
        if label:
            ax.annotate(
                label,
                (X(year), y),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="center",
                fontsize=7.2,
                color=INK_2,
                zorder=5,
            )

    for (la, ya), (lb, yb), kind, rad in LINKS:
        same = kind == "same"
        ax.annotate(
            "",
            xy=(X(yb), Y[lb]),
            xytext=(X(ya), Y[la]),
            arrowprops=dict(
                arrowstyle="<->" if same else "->",
                color=SAME if same else INK_2,
                lw=1.3,
                ls=(0, (4, 3)) if same else "-",
                connectionstyle=f"arc3,rad={rad}",
                shrinkA=5,
                shrinkB=5,
            ),
            zorder=3,
        )

    for j, spec in enumerate(SPECS):
        x = XM + j * DXM
        ax.text(x, len(LANES) - 0.45, spec, ha="center", fontsize=8.5, color=INK)
        for name, y in Y.items():
            v = FEEDS[name].get(spec)
            if v == 1:
                ax.plot(x, y, "o", ms=7, color=INK, zorder=4)
            elif v == 0.5:
                ax.plot(x, y, "o", ms=7, mfc=SURFACE, mec=INK, mew=1.3, zorder=4)
    ax.text(XM + DXM, len(LANES) - 0.2, "feeds spec", ha="center", fontsize=8.5, color=INK)
    ax.axvline(XM - 6, color=INK_2, lw=0.6, ymin=0.02, ymax=0.98)

    ax.set_xlim(-1, XM + DXM * (len(SPECS) - 1) + 4)
    ax.set_ylim(-0.7, len(LANES) + 0.05)
    years = [1940, 1960, 1980, 2000, 2010, 2020]
    ax.set_xticks([X(y) for y in years], [str(y) for y in years])
    ax.text(X(2026), -1.08, "time runs 2.2 times faster after 2000", ha="right",
            fontsize=7.5, color=INK_2)
    ax.tick_params(axis="x", colors=INK_2, labelsize=8, length=3)
    ax.set_yticks([])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK_2)
    ax.spines["bottom"].set_bounds(0, X(2026))

    handles = [
        plt.Line2D([], [], color=INK_2, lw=1.3, label="builds on or cites"),
        plt.Line2D([], [], color=SAME, lw=1.3, ls=(0, (4, 3)), label="same object, another name"),
        plt.Line2D([], [], ls="", marker="o", ms=7, color=INK, label="feeds a claim of the spec"),
        plt.Line2D(
            [], [], ls="", marker="o", ms=7, mfc=SURFACE, mec=INK, label="feeds 002's open score choice"
        ),
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=4,
        frameon=False,
        fontsize=8,
        labelcolor=INK,
    )

    fig.tight_layout()
    return fig


def main() -> None:
    out = Path(__file__).with_suffix(".svg")
    build().savefig(out, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
