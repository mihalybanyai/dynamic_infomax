"""Eye test for spec 002: the manual gate before the full suite (spec §5.3).

Two figures for human review, against published shapes:

1. A&M (2023) Fig. 5: against `D` in exp-decay (`m = 26` times in [1, 5], `sigma = 0.1`),
   the mutual information `I/log 2` and the worst-case bias pressure `max b / log 2`, for
   `p*`, Jeffreys and the log-normal, with A&M's own points overlaid as open markers.
   The bias-pressure panel draws, per prior, a band between the maximum of `b` over 2000
   draws from the prior and the maximum over all of `Theta` (§5.3; A&M do not say over
   which states their maximum runs).
   Accept, at every `D`: `I_{p*} >= I_{p_J}`, `I_{p*} >= I_{p_LN}` and
   `B(p*) ≈ 0 <= B(p_J)`. On the extended `D in {5, 7, 11}` only: `I_{p*}` flat while
   `I_{p_J}` falls, and `B(p_J)` rising; the computed lines follow the overlaid points.
2. Komaki (2011) Fig. 1: latent information priors of the binomial model on the 11-point
   `Theta = {0, 0.1, ..., 1}`, for `N` in {0, 1, 10, 100} and `M` in {1, 10, 100, 1000},
   built by `build_plat` itself on the binomial model. Accept: nearly uniform at
   (0, 1000); close to the Jeffreys histogram at (0, 100); mass on few points when `N` and
   `M` are both small; mass moving toward 1/2 as `N` grows.

This is not a pytest test (no `test_` prefix; no assertions). Run it directly:

    uv run python tests/eye_test_002_foreign_q_prediction.py [--extended]

The default run, `D <= 4` on the candidate-set path, is the quick smoke check. Approval
needs one run with `--extended`, which adds A&M's `D in {5, 7, 11}` through AtomicPriors.jl
(OQ-1) and saves those numbers to `eyetest_am_fig5_extended.json` beside the figure; later
runs redraw from that file without recomputing. A&M's `D = 26` is left out so the eye
test stays cheap. Figures go to `tests/figures/002_foreign_q_prediction/`. The approval is
recorded in `experiments/002-foreign-q-prediction/CODEGEN_LOG.md`; the full suite runs only
after it. Regenerated after the test red-team (F2, F3, F16).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from infomax.diagnostics import worst_case_bias_pressure
from infomax.jeffreys import build_jeffreys
from infomax.models import binomial_model, build_model
from infomax.plat import build_plat
from infomax.plognormal import build_pln
from infomax.pstar import build_pstar
from infomax.score import mutual_information

SEED = 20260601
D_GRID = (1, 2, 3, 4)
D_EXTENDED = (5, 7, 11)
KOMAKI_N = (0, 1, 10, 100)
KOMAKI_M = (1, 10, 100, 1000)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "tests" / "figures" / "002_foreign_q_prediction"
EXTENDED_CACHE = FIG_DIR / "eyetest_am_fig5_extended.json"

AM_FIG5 = {
    "D": (1, 2, 3, 5, 7, 11),
    "I": {
        "p*": (3.85, 4.47, 4.65, 4.76, 4.86, 4.91),
        "p_J": (3.79, 3.86, 3.20, 2.29, 1.71, 1.19),
        "p_LN": (2.95, 3.12, 2.92, 2.53, 2.25, 1.87),
    },
    "B_lower": {
        "p*": (0.11, 0.21, 0.22, 0.22, 0.25, 0.25),
        "p_J": (0.15, 2.4, 10.0, 32.0, 65.0, 250.0),
        "p_LN": (4.5, 11.3, 17.9, 33.0, 45.0, 80.0),
    },
    "B_upper": {
        "p_J": (0.16, 6.3, 16.0, 43.0, 94.0, 280.0),
        "p_LN": (9.7, 17.5, 24.4, 38.0, 50.0, 91.0),
    },
}
"""A&M's Fig. 5 in bits, read off the published figure by eye at a 3.2x render of the PDF
[read: A&M Fig. 5, digitised by eye; about ±0.05 bits in `I` and ±0.05 decades in `B`].
For the other priors A&M plot lower and upper bounds on `B` (Bennett's method)."""

PRIORS = ("p*", "p_J", "p_LN")
STYLE = {"p*": ("o-", "C0"), "p_J": ("s--", "C3"), "p_LN": ("^-.", "C2")}


def _scores_at(D: int, rng: np.random.Generator) -> dict:
    """`I` in nats for each prior, and the band `[B_interior, B_all]` of `max_theta b` over
    `p*`'s candidate set (§5.3.1)."""
    model = build_model("exp_decay", D, m=26, sigma=0.1, N=1)
    pstar = build_pstar(model)
    priors = {"p*": pstar.prior, "p_J": build_jeffreys(model), "p_LN": build_pln(model)}
    states = pstar.candidates
    out = {"I": {}, "B": {}}
    for name, prior in priors.items():
        out["I"][name] = pstar.capacity if name == "p*" else mutual_information(prior, model, rng=rng)
        out["B"][name] = list(worst_case_bias_pressure(prior, model, states, rng))
    return out


def am_fig5(rng: np.random.Generator, extended: bool) -> Path:
    """Panel pair of A&M Fig. 5: information and worst-case bias pressure against `D`."""
    rows = {D: _scores_at(D, rng) for D in D_GRID}
    if extended:
        start = time.perf_counter()
        ext = {D: _scores_at(D, rng) for D in D_EXTENDED}
        EXTENDED_CACHE.write_text(
            json.dumps({"seconds": time.perf_counter() - start, "rows": {str(D): r for D, r in ext.items()}}, indent=1)
        )
        print(f"extended run took {time.perf_counter() - start:.0f} s; record it in spec §5.3")
        rows.update(ext)
    elif EXTENDED_CACHE.exists():
        rows.update({int(D): r for D, r in json.loads(EXTENDED_CACHE.read_text())["rows"].items()})
    Ds = sorted(rows)
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(5.5, 6.5), sharex=True)
    for name in PRIORS:
        marker, colour = STYLE[name]
        top.plot(Ds, [rows[D]["I"][name] / np.log(2) for D in Ds], marker, color=colour, label=name)
        band = np.array([rows[D]["B"][name] for D in Ds]) / np.log(2)
        bottom.fill_between(Ds, np.maximum(band[:, 0], 1e-3), np.maximum(band[:, 1], 1e-3), color=colour, alpha=0.25)
        bottom.plot(Ds, np.maximum(band[:, 1], 1e-3), marker, color=colour, label=name)
        bottom.plot(Ds, np.maximum(band[:, 0], 1e-3), marker, color=colour, alpha=0.5)
        top.plot(AM_FIG5["D"], AM_FIG5["I"][name], "o", mfc="none", color=colour, ms=9)
        bottom.plot(AM_FIG5["D"], AM_FIG5["B_lower"][name], "o", mfc="none", color=colour, ms=9)
        if name in AM_FIG5["B_upper"]:
            bottom.plot(AM_FIG5["D"], AM_FIG5["B_upper"][name], "v", mfc="none", color=colour, ms=7)
    top.plot([], [], "o", mfc="none", color="k", label="A&M Fig. 5 (open)")
    top.set_ylabel("I(X; Θ) / log 2  (bits)")
    top.legend(fontsize=8)
    bottom.set_yscale("log")
    bottom.set_ylabel("max b(θ) / log 2  (bits)\nband: own draws ↔ all of Θ")
    bottom.set_xlabel("D")
    fig.suptitle("Eye test: A&M Fig. 5 (exp-decay, σ = 0.1)" + ("" if max(Ds) > 4 else " — default run only"))
    path = FIG_DIR / "eyetest_am_fig5.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def komaki_fig1() -> Path:
    """The 16 panels of Komaki Fig. 1: `p_lat` of the binomial model at `(N, M)`, built by
    `build_plat` on `binomial_model(N, M)`, the same update as the Gaussian build."""
    grid = np.linspace(0.0, 1.0, 11)
    fig, axes = plt.subplots(len(KOMAKI_N), len(KOMAKI_M), figsize=(10, 9), sharex=True, sharey=True)
    for i, N in enumerate(KOMAKI_N):
        for j, M in enumerate(KOMAKI_M):
            res = build_plat(binomial_model(N, M), M=M, candidates=grid[:, None])
            ax = axes[i, j]
            ax.bar(res.prior.atoms[:, 0], res.prior.weights, width=0.06)
            ax.set_title(f"N={N}, M={M}", fontsize=9)
    fig.suptitle("Eye test: Komaki (2011) Fig. 1, latent information priors (binomial)")
    path = FIG_DIR / "eyetest_komaki_fig1.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    rng = np.random.default_rng(SEED)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    extended = "--extended" in sys.argv
    paths = [am_fig5(rng, extended=extended), komaki_fig1()]
    for path in paths:
        print(f"figure written to {path}")
    if not (extended or EXTENDED_CACHE.exists()):
        print("Approval needs the extended run: rerun with --extended (spec §5.3).")
    print("Human approval of these figures is required before the full spec 002 suite runs (spec §5.3).")


if __name__ == "__main__":
    main()
