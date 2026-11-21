"""Eye test for spec 002: the manual gate before the full suite (spec §5.3).

Two figures for human review, against published shapes:

1. A&M (2023) Fig. 5: against `D` in exp-decay (`m = 26` times in [1, 5], `sigma = 0.1`),
   the mutual information `I/log 2` and the worst-case bias pressure `max b / log 2`, for
   `p*` and Jeffreys. Accept, at every `D`: `I_{p*} >= I_{p_J}` and `B(p*) ≈ 0 <= B(p_J)`.
   Only on the range extended toward `D = 26`: `I_{p*}` flat while `I_{p_J}` falls, and
   `B(p_J)` rising (A&M find `p*` flat only once `d > 3`).
2. Komaki (2011) Fig. 1: latent information priors of the binomial model on the 11-point
   `Theta = {0, 0.1, ..., 1}`, for `N` in {0, 1, 10, 100} and `M` in {1, 10, 100, 1000}.
   Accept: nearly uniform at (0, 1000); close to the Jeffreys histogram at (0, 100); mass on
   few points when `N` and `M` are both small; mass moving toward 1/2 as `N` grows.

This is not a pytest test (no `test_` prefix; no assertions). Run it directly:

    uv run python tests/eye_test_002_foreign_q_prediction.py [--extended]

`--extended` adds `D` beyond the candidate-set path through AtomicPriors.jl (OQ-1).
Figures go to `tests/figures/002_foreign_q_prediction/`. The approval is recorded in
`experiments/002-foreign-q-prediction/CODEGEN_LOG.md`; the full suite runs only after it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from infomax.jeffreys import build_jeffreys
from infomax.models import build_model
from infomax.plat import build_plat_binomial
from infomax.pstar import build_pstar
from infomax.score import bias_pressure, mutual_information

SEED = 20260601
D_GRID = (1, 2, 3, 4)
D_EXTENDED = (6, 11, 16, 26)
KOMAKI_N = (0, 1, 10, 100)
KOMAKI_M = (1, 10, 100, 1000)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "tests" / "figures" / "002_foreign_q_prediction"


def am_fig5(rng: np.random.Generator, extended: bool) -> Path:
    """Panel pair of A&M Fig. 5: information and worst-case bias pressure against `D`."""
    Ds = D_GRID + (D_EXTENDED if extended else ())
    rows = []
    for D in Ds:
        model = build_model("exp_decay", D, m=26, sigma=0.1, N=1)
        pstar = build_pstar(model)
        p_J = build_jeffreys(model)
        states = pstar.candidates
        rows.append(
            (
                D,
                pstar.capacity,
                mutual_information(p_J, model, rng=rng),
                np.max(bias_pressure(pstar.prior, model, states, rng=rng)),
                np.max(bias_pressure(p_J, model, states, rng=rng)),
            )
        )
    D_arr, I_star, I_J, B_star, B_J = map(np.array, zip(*rows))
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(5, 6), sharex=True)
    top.plot(D_arr, I_star / np.log(2), "o-", label="p*")
    top.plot(D_arr, I_J / np.log(2), "s--", label="Jeffreys")
    top.set_ylabel("I(X; Θ) / log 2  (bits)")
    top.legend()
    bottom.plot(D_arr, B_star / np.log(2), "o-", label="p*")
    bottom.plot(D_arr, B_J / np.log(2), "s--", label="Jeffreys")
    bottom.set_ylabel("max b(θ) / log 2  (bits)")
    bottom.set_xlabel("D")
    fig.suptitle("Eye test: A&M Fig. 5 (exp-decay, σ = 0.1)")
    path = FIG_DIR / "eyetest_am_fig5.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def komaki_fig1() -> Path:
    """The 16 panels of Komaki Fig. 1: `p_lat` of the binomial model at `(N, M)`."""
    grid = np.linspace(0.0, 1.0, 11)
    fig, axes = plt.subplots(len(KOMAKI_N), len(KOMAKI_M), figsize=(10, 9), sharex=True, sharey=True)
    for i, N in enumerate(KOMAKI_N):
        for j, M in enumerate(KOMAKI_M):
            res = build_plat_binomial(grid, N=N, M=M)
            ax = axes[i, j]
            ax.bar(grid, res.weights, width=0.06)
            ax.set_title(f"N={N}, M={M}", fontsize=9)
    fig.suptitle("Eye test: Komaki (2011) Fig. 1, latent information priors (binomial)")
    path = FIG_DIR / "eyetest_komaki_fig1.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    rng = np.random.default_rng(SEED)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = [am_fig5(rng, extended="--extended" in sys.argv), komaki_fig1()]
    for path in paths:
        print(f"figure written to {path}")
    print("Human approval of these figures is required before the full spec 002 suite runs (spec §5.3).")


if __name__ == "__main__":
    main()
