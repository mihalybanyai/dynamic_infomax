"""Map of notes/ in time: which note grew out of what, and where it went.

One row per document, grouped by thread. A dot is a day with a commit to that file;
the bar joins the first and last. Arrows: grey = led to (the target was written
because of the source), black = merged into a spec, dotted = cited as support. The
summer, when nothing was committed, is squeezed. The table in notes/README.md holds
the same rows in words; update both together.

Run:    uv run python diagrams/notes-map.py
Output: diagrams/notes-map.svg
"""

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#9a9893"
LANE = "#f0efec"
# Categorical slots 1-3 of the dataviz reference palette, one per thread.
THREAD_1 = "#2a78d6"
THREAD_2 = "#eb6834"
THREAD_3 = "#1baf7a"
NEUTRAL = INK_2

Y2026 = 2026


def d(month: int, day: int) -> date:
    return date(Y2026, month, day)


# Time axis: May and June at 1.5 units per day, the summer squeezed to GAP units,
# autumn at 1.1 units per day.
A0, A1 = d(5, 14), d(6, 13)
B0, B1 = d(9, 20), d(11, 6)
GAP = 5.0
SA, SB = 1.5, 1.1


def X(t: date) -> float:
    if t <= A1:
        return (t - A0).days * SA
    if t < B0:
        raise ValueError(f"{t} falls in the squeezed summer")
    return (A1 - A0).days * SA + GAP + (t - B0).days * SB


# Groups top to bottom: (heading, colour of the group's marks, rows).
# Row: (key, title, file, commit days, status).
GROUPS = [
    (
        "Sources",
        NEUTRAL,
        [
            ("res", "resources/", "papers and prior drafts", [], ""),
            ("lit", "literature/", "map of the field", [d(10, 5)], ""),
        ],
    ),
    (
        "Specs",
        INK,
        [
            ("s000", "000  Static p* (Mattingly Fig 1)", "specs/000-static-infomax-fig1.md",
             [d(5, 16), d(5, 17), d(5, 18), d(5, 19), d(5, 20)], "reviewed"),
            ("s001", "001  Does p* win at Kelly betting?", "specs/001-infomax-betting.md",
             [d(5, 25), d(5, 29), d(5, 30)], "reviewed"),
            ("s002", "002  Does p* predict a foreign q?", "specs/002-foreign-q-prediction.md",
             [d(6, 1), d(6, 3), d(6, 4), d(6, 5), d(6, 6), d(10, 1), d(10, 4), d(10, 5),
              d(10, 6), d(10, 25), d(10, 26)], "draft, in review"),
        ],
    ),
    (
        "Thread 1 · Is p* a good prior?",
        THREAD_1,
        [
            ("read", "Reading summary of the sources", "000-reading-summary.md",
             [d(5, 16)], "historical"),
            ("bet", "Betting-game maths for p*", "infomax_betting_experiment.md",
             [d(5, 25)], "became spec 001"),
            ("hats", "Two hats: design object vs belief", "infomax_two_hats_and_directions.md",
             [d(5, 31), d(6, 3), d(10, 4)], "background to 002"),
            ("pred", "Held-out log-loss as the score", "prediction_objective_for_priors.md",
             [d(5, 31), d(6, 1)], "merged into 002"),
            ("qfam", "Picturing the natures q", "q-family-visualisation.md",
             [d(6, 6), d(10, 5)], "open: 002 OQ-2"),
            ("budg", "What knowing the budget is worth", "budget-value-of-information.md",
             [d(10, 25), d(10, 26)], "in 002; threads open"),
            # parked_ideas.md was created empty on 4 Oct; its entries come from the budget note.
            ("park", "Parked ideas", "parked_ideas.md",
             [d(10, 4), d(10, 25), d(10, 26)], "running list"),
        ],
    ),
    (
        "Thread 2 · Daisy chain",
        THREAD_2,
        [
            ("dcd", "Daisy chain: state and derivation gap", "daisy_chain_derivation.md",
             [d(5, 25), d(6, 3), d(10, 20), d(10, 29)], "active, no spec"),
            ("dcc", "Daisy chain as self-made tasks", "daisy_chain_causal_discovery.md",
             [d(5, 28), d(10, 20)], "speculative, no spec"),
        ],
    ),
    (
        "Thread 3 · AP–RV experiment",
        THREAD_3,
        [
            ("aps", "AP–RV: maths seed", "infomax_aprv_seed.md", [d(5, 24)], "dormant"),
            ("apt", "AP–RV: thinking state", "aprv_thinking_state.md", [d(5, 24)], "dormant"),
        ],
    ),
    (
        "empirics/",
        NEUTRAL,
        [
            ("rwa", "Real-world betting analogues", "real_world_analogues.md",
             [d(5, 25), d(10, 4)], "historical"),
            ("ssp", "Slow-speed prior", "slow_speed_prior.md", [d(10, 4)], "lead"),
            ("ant", "Anticipated exposure", "anticipated_exposure.md", [d(10, 29)], "lead"),
        ],
    ),
]

# Labelled points on the sources row:
# (day, label, hollow = outside the repo, label offset in points, alignment).
SOURCES = [
    (d(5, 16), "Overleaf draft, Notion, Mattingly '18", False, (-4, 8), "right"),
    (d(5, 24), "AP–RV manuscript (not in repo)", True, (0, -13), "center"),
    (d(5, 31), "Abbott & Machta '23", False, (0, 8), "center"),
]

# Commits that only moved a file: (row, day, label).
MOVES = [("rwa", d(10, 4), "moved from notes/")]

# Red-team reports, by the day each was added.
REDTEAMS = {
    "s000": [d(5, 17)],
    "s001": [d(5, 30)],
    "s002": [d(6, 2), d(6, 4), d(6, 11)],
}

# The budget note's chat thread ran before the note was committed.
CHAT = ("budg", d(10, 8), d(10, 24))

# (from (row, day), to (row, day), kind, arc radius)
LED, INTO, CITES = "led", "into", "cites"
LINKS = [
    (("res", d(5, 16)), ("read", d(5, 16)), LED, 0.25),
    (("read", d(5, 16)), ("s000", d(5, 16)), LED, -0.35),
    (("res", d(5, 16)), ("dcd", d(5, 25)), LED, 0.12),
    (("res", d(5, 24)), ("aps", d(5, 24)), LED, 0.08),
    (("aps", d(5, 24)), ("apt", d(5, 24)), LED, -0.6),
    (("s000", d(5, 20)), ("bet", d(5, 25)), LED, -0.15),
    (("bet", d(5, 25)), ("s001", d(5, 25)), INTO, -0.25),
    (("bet", d(5, 25)), ("rwa", d(5, 25)), LED, 0.1),
    (("bet", d(5, 25)), ("dcc", d(5, 28)), CITES, -0.15),
    (("dcd", d(5, 25)), ("dcc", d(5, 28)), LED, -0.4),
    (("s001", d(5, 30)), ("hats", d(5, 31)), LED, 0.2),
    (("res", d(5, 31)), ("pred", d(5, 31)), LED, -0.12),
    (("hats", d(5, 31)), ("pred", d(5, 31)), LED, -0.5),
    (("pred", d(6, 1)), ("s002", d(6, 1)), INTO, 0.25),
    (("hats", d(6, 3)), ("s002", d(6, 3)), CITES, 0.2),
    (("s002", d(6, 5)), ("qfam", d(6, 6)), LED, -0.15),
    (("s002", d(10, 4)), ("ssp", d(10, 4)), LED, 0.08),
    (("lit", d(10, 5)), ("s002", d(10, 5)), CITES, -0.2),
    (("qfam", d(10, 5)), ("s002", d(10, 5)), CITES, 0.25),
    (("budg", d(10, 20)), ("dcd", d(10, 20)), LED, -0.25),
    (("budg", d(10, 25)), ("park", d(10, 25)), LED, -0.5),
    (("budg", d(10, 26)), ("s002", d(10, 26)), INTO, 0.15),
    (("budg", d(10, 26)), ("ant", d(10, 29)), LED, -0.12),
    (("dcd", d(10, 29)), ("ant", d(10, 29)), LED, 0.2),
]

ROW_H = 1.0
HEAD_H = 0.85


def layout() -> tuple[dict[str, float], list[tuple[str, str, float]]]:
    """Y position per row key, and (heading, colour, y) per group heading."""
    ys: dict[str, float] = {}
    heads = []
    y = 0.0
    for heading, colour, rows in GROUPS:
        y -= HEAD_H
        heads.append((heading, colour, y))
        for key, *_ in rows:
            y -= ROW_H
            ys[key] = y
    return ys, heads


def build() -> plt.Figure:
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    ys, heads = layout()
    colour_of = {key: c for _, c, rows in GROUPS for key, *_ in rows}
    x_end = X(B1)
    x_status = x_end + 3

    fig, ax = plt.subplots(figsize=(16, 11.5))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # Group bands, alternately shaded, and headings.
    for i, (heading, colour, yh) in enumerate(heads):
        rows = GROUPS[i][2]
        top, bottom = yh + HEAD_H / 2, ys[rows[-1][0]] - ROW_H / 2
        if i % 2 == 1:
            ax.axhspan(bottom, top, color=LANE, lw=0, zorder=0)
        ax.plot(-40.5, yh, "s", ms=8, color=colour, zorder=4, clip_on=False)
        ax.text(-39, yh, heading, ha="left", va="center", fontsize=10.5,
                fontweight="bold", color=INK)

    # The squeezed summer.
    xa, xb = X(A1), X(B0)
    ax.axvspan(xa, xb, color=SURFACE, lw=0, zorder=1)
    for x in (xa, xb):
        ax.axvline(x, color=INK_3, lw=0.6, ls=(0, (2, 2)), zorder=1)
    ax.text((xa + xb) / 2, 0.15, "summer:\nno commits\n12 Jun–22 Sep", ha="center",
            va="top", fontsize=7, color=INK_2, zorder=6)

    # Rows: label, bar, commit dots, status.
    for _, _, rows in GROUPS:
        for key, title, path, days, status in rows:
            y, c = ys[key], colour_of[key]
            ax.text(-39, y + 0.13, title, ha="left", va="center", fontsize=9, color=INK)
            ax.text(-39, y - 0.25, path, ha="left", va="center", fontsize=7, color=INK_2,
                    family="DejaVu Sans Mono")
            if days:
                ax.plot([X(min(days)), X(max(days))], [y, y], color=c, lw=2.5,
                        alpha=0.35, solid_capstyle="round", zorder=2)
                for t in days:
                    ax.plot(X(t), y, "o", ms=7, color=c, mec=SURFACE, mew=1.5, zorder=5)
            for t in REDTEAMS.get(key, []):
                ax.plot(X(t), y + 0.32, "v", ms=6, mfc=SURFACE, mec=INK, mew=1.1, zorder=5)
            if status:
                ax.text(x_status, y, status, ha="left", va="center", fontsize=8.5, color=INK_2)

    ax.text(x_status, heads[0][2], "status", ha="left", va="center", fontsize=9,
            fontweight="bold", color=INK)

    for t, label, hollow, offset, ha in SOURCES:
        y = ys["res"]
        if hollow:
            ax.plot(X(t), y, "o", ms=7, mfc=SURFACE, mec=NEUTRAL, mew=1.4, zorder=5)
        else:
            ax.plot(X(t), y, "o", ms=7, color=NEUTRAL, mec=SURFACE, mew=1.5, zorder=5)
        ax.annotate(label, (X(t), y), xytext=offset, textcoords="offset points",
                    ha=ha, va="center", fontsize=7, color=INK_2, zorder=6)

    for key, t, label in MOVES:
        ax.annotate(label, (X(t), ys[key]), xytext=(-6, 8), textcoords="offset points",
                    ha="right", fontsize=7, color=INK_2, zorder=6)

    key, t0, t1 = CHAT
    ax.plot([X(t0), X(t1)], [ys[key], ys[key]], color=colour_of[key], lw=1.6,
            ls=(0, (3, 2)), zorder=2)
    ax.annotate("chat thread", (X(t0), ys[key]), xytext=(0, 7), textcoords="offset points",
                ha="left", fontsize=7, color=INK_2)

    style = {
        LED: dict(color=INK_3, lw=1.1, ls="-"),
        INTO: dict(color=INK, lw=1.6, ls="-"),
        CITES: dict(color=INK_3, lw=1.1, ls=(0, (1, 2))),
    }
    for (ka, ta), (kb, tb), kind, rad in LINKS:
        ax.annotate(
            "",
            xy=(X(tb), ys[kb]),
            xytext=(X(ta), ys[ka]),
            arrowprops=dict(arrowstyle="-|>", mutation_scale=9, shrinkA=5, shrinkB=5,
                            connectionstyle=f"arc3,rad={rad}", **style[kind]),
            zorder=3,
        )

    y_min = min(ys.values()) - ROW_H / 2
    ax.set_xlim(-41.5, x_status + 18)
    ax.set_ylim(y_min - 0.1, 0.3)
    ticks = [d(5, 16), d(6, 1), d(10, 1), d(10, 15), d(11, 1)]
    ax.set_xticks([X(t) for t in ticks], [t.strftime("%-d %b") for t in ticks])
    ax.tick_params(axis="x", colors=INK_2, labelsize=8, length=3)
    ax.set_yticks([])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK_2)
    ax.spines["bottom"].set_bounds(0, x_end)

    handles = [
        plt.Line2D([], [], ls="", marker="o", ms=7, color=INK_2, label="day with a commit"),
        plt.Line2D([], [], ls="", marker="v", ms=6, mfc=SURFACE, mec=INK,
                   label="red-team report added"),
        plt.Line2D([], [], color=INK_3, lw=1.1, label="led to"),
        plt.Line2D([], [], color=INK, lw=1.6, label="merged into a spec"),
        plt.Line2D([], [], color=INK_3, lw=1.1, ls=(0, (1, 2)), label="cited as support"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=5,
              frameon=False, fontsize=8.5, labelcolor=INK)

    fig.tight_layout()
    return fig


def main() -> None:
    out = Path(__file__).with_suffix(".svg")
    build().savefig(out, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
