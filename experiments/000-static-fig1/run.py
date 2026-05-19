"""Spec 000 experiment: reproduce Mattingly Fig 1.

Sweeps m, runs BA at each, extracts atoms, and writes the figures and
results table consumed by `REPORT.md`. Re-run with:

    uv run python experiments/000-static-fig1/run.py

Outputs (under `experiments/000-static-fig1/`):
- `figures/fig1_panels.png` — multi-panel reproduction of Mattingly Fig 1:
  for each m in the sweep, atom stems for `p*(θ)` and `f_KL(θ)` overlay
  with the achieved `MI*` line.
- `figures/m100_atom_cdf_vs_jeffreys.png` — atom CDF at m=100 vs the
  analytic Jeffreys CDF.
- `figures/ks_vs_m.png` — KS distance to Jeffreys CDF as a function of m,
  with the discreteness floor `1/(2 K(m))` overlaid.
- `results_table.json` — per-m summary: K, MI* (bits), atom positions
  and weights. Loaded by `REPORT.md`'s embedded values.
- `convergence.json` — per-m convergence diagnostics (Csiszar gap,
  iterations, whether the convergence flag was set).

Spec §3.6 and §5.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from infomax.atoms import extract_atoms
from infomax.ba import blahut_arimoto, compute_f_kl
from infomax.jeffreys import jeffreys_bernoulli_cdf, jeffreys_bernoulli_pdf
from infomax.likelihood import binomial_log_likelihood, cell_centred_grid

EXPERIMENT_DIR = Path(__file__).resolve().parent
FIGURE_DIR = EXPERIMENT_DIR / "figures"
FIGURE_DIR.mkdir(exist_ok=True, parents=True)

M_SWEEP: tuple[int, ...] = (1, 2, 3, 4, 5, 10, 20, 50, 100)
N_THETA: int = 1000

# Panels to show in the Fig 1 reproduction (a representative subset of
# the full sweep — keeps the figure readable; full sweep still feeds the
# results table and the KS-vs-m curve).
PANELS_M: tuple[int, ...] = (1, 5, 20, 100)


def run_one(m: int) -> dict:
    """One BA run + atom extraction + Jeffreys KS distance.

    Returns a JSON-friendly dict with all per-m quantities the report
    consumes.
    """
    grid = cell_centred_grid(N_THETA)
    log_lik = binomial_log_likelihood(grid, m=m)
    result = blahut_arimoto(log_lik, grid)
    atoms = extract_atoms(result.prior)
    f_kl = compute_f_kl(result.prior, log_lik)

    # KS distance: atom step CDF vs analytic Jeffreys CDF, evaluated on
    # a fine grid. Atom CDF = cumulative sum of atom masses up to each
    # query θ.
    atom_thetas = np.asarray([a.theta for a in atoms], dtype=np.float64)
    atom_masses = np.asarray([a.mass for a in atoms], dtype=np.float64)
    sort_idx = np.argsort(atom_thetas)
    atom_thetas_sorted = atom_thetas[sort_idx]
    atom_masses_sorted = atom_masses[sort_idx]
    atom_cdf_at_atoms = np.cumsum(atom_masses_sorted)
    # Query at a dense set: atom positions ± a midpoint scheme.
    query = np.linspace(0.0, 1.0, 4001)
    atom_cdf_query = np.zeros_like(query)
    for i, q in enumerate(query):
        atom_cdf_query[i] = atom_masses_sorted[atom_thetas_sorted <= q].sum()
    jeffreys_cdf_query = jeffreys_bernoulli_cdf(query)
    ks = float(np.max(np.abs(atom_cdf_query - jeffreys_cdf_query)))

    return {
        "m": m,
        "K": len(atoms),
        "mi_nats": float(result.mi),
        "mi_bits": float(result.mi / np.log(2.0)),
        "csiszar_gap": float(np.max(f_kl) - result.mi),
        "n_iters": int(result.n_iters),
        "converged": bool(result.converged),
        "atom_theta": atom_thetas_sorted.tolist(),
        "atom_mass": atom_masses_sorted.tolist(),
        "ks_to_jeffreys": ks,
        # The discreteness floor: 1/(2K) is the best a K-atom step CDF
        # can do against a continuous reference (the worst point is
        # halfway between two atoms).
        "ks_floor": 1.0 / (2.0 * max(len(atoms), 1)),
        # Storing the prior masses and f_kl on the grid for the figure
        # generators. These are bulky (N_θ floats); kept here so the
        # plotting code is decoupled from re-running BA.
        "grid": grid.tolist(),
        "prior_masses": result.prior.masses().tolist(),
        "f_kl": f_kl.tolist(),
    }


def make_panels_figure(results: list[dict]) -> None:
    """Multi-panel figure mirroring Mattingly Fig 1.

    Each panel: prior stems (red) + f_KL(θ) overlay (grey, right axis)
    + horizontal MI* line. Layout matches the paper's 2×2 plus the
    m → ∞ analytic Jeffreys panel for direct comparison.
    """
    panel_ms = PANELS_M
    by_m = {r["m"]: r for r in results}

    n = len(panel_ms) + 1  # +1 for the Jeffreys analytic panel
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(11, 3.0 * rows), constrained_layout=True)
    axes = np.atleast_2d(axes).ravel()

    for ax, m in zip(axes, panel_ms):
        r = by_m[m]
        grid = np.asarray(r["grid"])
        masses = np.asarray(r["prior_masses"])
        f_kl = np.asarray(r["f_kl"])
        mi = r["mi_nats"]

        # Prior stems (left axis), only at atom centroids — not all grid
        # cells, because the figure becomes a forest at N_θ = 1000.
        atom_theta = np.asarray(r["atom_theta"])
        atom_mass = np.asarray(r["atom_mass"])
        markerline, stemlines, baseline = ax.stem(
            atom_theta, atom_mass, basefmt=" ", linefmt="C3-", markerfmt="C3o"
        )
        plt.setp(markerline, markersize=5)
        plt.setp(stemlines, linewidth=1.5)

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, max(atom_mass.max() * 1.15, 1e-3))
        ax.set_xlabel(r"$\theta$")
        ax.set_ylabel(r"$p_\star(\theta)$ (atom mass)")
        ax.set_title(f"$m = {m}$ ($K = {r['K']}$, $MI^* = {r['mi_bits']:.3f}$ bits)")

        # f_KL overlay on a right axis. Drawn at every grid cell.
        ax_r = ax.twinx()
        ax_r.plot(grid, f_kl, color="0.6", linewidth=1.2, label=r"$f_{KL}(\theta)$")
        ax_r.axhline(mi, color="0.4", linestyle="--", linewidth=0.9)
        ax_r.set_ylabel(r"$f_{KL}(\theta)$", color="0.4")
        ax_r.tick_params(axis="y", colors="0.5")

    # Final panel: analytic Jeffreys (the m → ∞ limit).
    ax = axes[len(panel_ms)]
    theta = np.linspace(1e-4, 1 - 1e-4, 1000)
    pdf = jeffreys_bernoulli_pdf(theta)
    ax.fill_between(theta, pdf, alpha=0.3, color="C3")
    ax.plot(theta, pdf, color="C3", linewidth=1.5)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, min(pdf.max() * 1.1, 8.0))
    ax.set_xlabel(r"$\theta$")
    ax.set_ylabel(r"$p_J(\theta)$ (Jeffreys density)")
    ax.set_title(r"$m \to \infty$ (Jeffreys, analytic)")

    # Hide any unused axes.
    for ax in axes[n:]:
        ax.set_visible(False)

    fig.savefig(FIGURE_DIR / "fig1_panels.png", dpi=140)
    plt.close(fig)


def make_m100_cdf_figure(result_100: dict) -> None:
    atom_theta = np.asarray(result_100["atom_theta"])
    atom_mass = np.asarray(result_100["atom_mass"])
    # Step CDF: cumsum, evaluated on a fine query grid.
    query = np.linspace(0.0, 1.0, 4001)
    atom_cdf_query = np.array(
        [atom_mass[atom_theta <= q].sum() for q in query]
    )
    jeffreys = jeffreys_bernoulli_cdf(query)

    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    ax.plot(query, atom_cdf_query, color="C3", linewidth=1.5, label=f"BA atom step CDF, m=100 (K={result_100['K']})")
    ax.plot(query, jeffreys, color="0.3", linewidth=1.5, linestyle="--", label="Jeffreys CDF (analytic)")
    ax.set_xlabel(r"$\theta$")
    ax.set_ylabel("CDF")
    ax.set_title(f"m=100 atom CDF vs Jeffreys CDF (KS = {result_100['ks_to_jeffreys']:.3f})")
    ax.legend(loc="lower right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.savefig(FIGURE_DIR / "m100_atom_cdf_vs_jeffreys.png", dpi=140)
    plt.close(fig)


def make_ks_vs_m_figure(results: list[dict]) -> None:
    ms = np.array([r["m"] for r in results])
    ks = np.array([r["ks_to_jeffreys"] for r in results])
    floor = np.array([r["ks_floor"] for r in results])

    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    ax.plot(ms, ks, "o-", color="C3", label="KS distance, BA atoms to Jeffreys")
    ax.plot(ms, floor, "x--", color="0.4", label=r"Discreteness floor $1/(2K(m))$")
    ax.set_xscale("log")
    ax.set_xlabel("m")
    ax.set_ylabel("KS distance to Jeffreys CDF")
    ax.set_title("Convergence of BA prior to Jeffreys as m grows")
    ax.legend()
    ax.grid(True, which="both", linewidth=0.3, alpha=0.5)
    fig.savefig(FIGURE_DIR / "ks_vs_m.png", dpi=140)
    plt.close(fig)


def main() -> None:
    print(f"Running BA at m ∈ {M_SWEEP}, N_θ = {N_THETA}")
    results: list[dict] = []
    for m in M_SWEEP:
        print(f"  m={m} ... ", end="", flush=True)
        r = run_one(m)
        print(
            f"K={r['K']}, MI*={r['mi_bits']:.4f} bits, "
            f"KS={r['ks_to_jeffreys']:.3f}, iter={r['n_iters']}, "
            f"conv={r['converged']}"
        )
        results.append(r)

    # Persist results. Drop the bulky grid arrays from the table file —
    # keep them only in the convergence dump.
    table_rows = []
    for r in results:
        row = {k: v for k, v in r.items() if k not in ("grid", "prior_masses", "f_kl")}
        table_rows.append(row)
    (EXPERIMENT_DIR / "results_table.json").write_text(json.dumps(table_rows, indent=2))
    (EXPERIMENT_DIR / "convergence.json").write_text(
        json.dumps(
            [
                {k: r[k] for k in ("m", "n_iters", "converged", "csiszar_gap")}
                for r in results
            ],
            indent=2,
        )
    )

    print("Generating figures...")
    make_panels_figure(results)
    make_m100_cdf_figure(next(r for r in results if r["m"] == 100))
    make_ks_vs_m_figure(results)
    print(f"Figures in {FIGURE_DIR}")


if __name__ == "__main__":
    main()
