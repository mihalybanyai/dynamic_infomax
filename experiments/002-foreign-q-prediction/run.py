"""Experiment 002 runner: spec 002 (`specs/002-foreign-q-prediction.md`) §5.4 and §6, in the
priority tiers of `PLAN.md`. Tier 0 only, so far.

Tier 0 is §3.7's verdict on `R_N`. Its cast is `p*`, `p_J`, `p_U` and, in exp-decay, `p_LN`.
Its cells are the base cells of both families (exp-decay at `sigma = 0.1`, `N = 1`, the whole
manifold; the hypercone at `sigma = 1`, `N = 1`, `W = 50`, taper on, `phi = 1`, `kappa = 1`) and
the submodel agents of the `D_max = 26` cone at fall-off 0.5, which see the nested natures,
each at `D = 1`-4. Every row of a cell (`qfamily.cell_rows`) is scored on `R_N` alone.

Cells run in worker processes, a fresh one per cell, each with a fixed number of numba and BLAS threads
(`--threads`, recorded), so that the workers share the cores and the summation order does not
change with the number of workers. Each worker builds its own cast; no prior crosses a process
boundary. Determinism: the experiment seed `20260601` is split into one child stream per
cell, in the fixed order of `tier0_cells`, and each cell splits its stream into a cast stream,
a capacity-gap stream and one stream per row. The builders use fixed seeds and the per-point
marginals are seeded by the point, so results do not depend on the number of workers or the
order in which cells finish.

Output, under `--out` (default `experiments/002-foreign-q-prediction/output/tier0`):
`cells/<cell>.json`, written as each cell finishes, so a run resumes; `results_table.json`,
one row per cell and nature with §6.3's fields for tier 0 (fields needing later tiers or
extra computation are null: the `r_N` scores, `covered_J`, `mass_bound_gap`, `joint_width2`,
the failure-map fields and the prior side other than `I_pstar`); `provenance.json`.

Usage:
    uv run python experiments/002-foreign-q-prediction/run.py [--workers 2] [--S_q 500]
        [--threads 2] [--cells exp_decay/base/D2,hypercone/base/D4] [--out DIR] [--force]
"""
from __future__ import annotations

import os
import sys

# Thread counts must be set before numpy and numba load, in this process and so in the
# spawned workers, which inherit the environment.


def _argv_int(argv: list[str], flag: str, default: int) -> int:
    for i, a in enumerate(argv):
        if a.startswith(flag + "="):
            return int(a.split("=", 1)[1])
        if a == flag and i + 1 < len(argv):
            return int(argv[i + 1])
    return default


THREADS_DEFAULT = 2
"""Threads per worker, fixed whatever the number of workers. Parallel sums (numba's `prange`,
BLAS) add in an order that depends on the thread count, and a change from 8 to 4 threads
moved `C_N` by 4.5e-11 and the gaps to Jeffreys by up to 7.7e-4 relative (2026-11-26). With
the count fixed and recorded, results do not depend on how the cells are scheduled."""
_WORKERS = _argv_int(sys.argv[1:], "--workers", 2)
_THREADS = _argv_int(sys.argv[1:], "--threads", THREADS_DEFAULT)
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_var] = str(_THREADS)

import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import resource  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from importlib import metadata  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SEED = 20260601
"""The experiment seed (spec §5.4)."""
S_Q = 500
"""Draws per cell and nature (spec §5.4); raised to 2000 where a gap's sign is unresolved, in
a later tier."""
D_TIER0 = (1, 2, 3, 4)


@dataclass(frozen=True)
class Cell:
    family: str
    variant: str  # "base", or "nested" for the submodel agents of the D_max cone
    D: int

    @property
    def name(self) -> str:
        return f"{self.family}/{self.variant}/D{self.D}"


def tier0_cells() -> list[Cell]:
    """Tier 0's cells in their fixed (lexicographic) order, which fixes their seed streams."""
    cells = [Cell("exp_decay", "base", D) for D in D_TIER0]
    cells += [Cell("hypercone", "base", D) for D in D_TIER0]
    cells += [Cell("hypercone", "nested", D) for D in D_TIER0]
    return sorted(cells, key=lambda c: (c.family, c.variant, c.D))


def _models(cell: Cell):
    from infomax.models import build_model, submodel
    from infomax.qfamily import D_MAX

    if cell.family == "exp_decay":
        return build_model("exp_decay", cell.D, m=26, sigma=0.1, N=1), None
    if cell.variant == "base":
        return build_model("hypercone", cell.D, m=26, sigma=1.0, N=1, W=50.0), None
    model_max = build_model("hypercone", D_MAX, m=26, sigma=1.0, N=1, W=50.0, falloff=0.5)
    return submodel(model_max, cell.D), model_max


def _tier0_cast(model) -> tuple[dict, object]:
    from infomax.jeffreys import build_jeffreys
    from infomax.plognormal import build_pln
    from infomax.pref import build_uniform
    from infomax.pstar import build_pstar

    pstar = build_pstar(model)
    cast = {"p*": pstar.prior, "p_J": build_jeffreys(model), "p_U": build_uniform(model)}
    if model.family == "exp_decay":
        cast["p_LN"] = build_pln(model)
    return cast, pstar


def _pairs(d: dict) -> dict:
    """JSON-ready: tuple values to lists, tuple keys to 'a|b'."""
    out = {}
    for k, v in d.items():
        key = "|".join(k) if isinstance(k, tuple) else k
        out[key] = _pairs(v) if isinstance(v, dict) else (list(v) if isinstance(v, tuple) else v)
    return out


def run_cell(cell: Cell, seed: np.random.SeedSequence, S_q: int) -> dict:
    """One cell: build tier 0's cast, score every row on `R_N`, return its rows and timings."""
    warnings.simplefilter("ignore")
    from infomax.diagnostics import beyond_cap, capacity_gap, row_summaries
    from infomax.qfamily import cell_rows
    from infomax.score import score_cell

    start = time.perf_counter()
    cast_seed, gap_seed, rows_seed = seed.spawn(3)
    model, model_max = _models(cell)
    cast, pstar = _tier0_cast(model)  # tier 0's builders take no generator (fixed seeds)
    t_build = time.perf_counter() - start
    gap = capacity_gap(pstar, model, np.random.default_rng(gap_seed))
    names = {id(p): n for n, p in cast.items()}
    rows = cell_rows(model, cast)
    row_seeds = rows_seed.spawn(len(rows))
    out = []
    for k, row in enumerate(rows):
        nested = row[0] == "nested" and model.family == "hypercone"
        sc = score_cell(model, cast, row, S_q=S_q, rng=np.random.default_rng(row_seeds[k]), scores=("R",),
                        nature_model=model_max if nested else None)
        own = names[id(row[1])] if row[0] == "own" else None
        summ = row_summaries(sc.draws_R, {}, own_prior=own)
        out.append({
            # key (§6.3)
            "model": model.family, "D": cell.D, "sigma": float(model.sigma), "N": int(model.N),
            "box": "full" if model.family == "exp_decay" else None,
            "W": float(model.W) if model.family == "hypercone" else None,
            "taper": float(model.taper), "falloff": float(model.falloff), "curvature": float(model.curvature),
            "nature": own if own is not None else f"{row[0]}:{row[1]}",
            "D_max": int(model_max.D) if nested else None,
            # scores
            "R_mean": sc.R_mean, "R_mcse": sc.R_mcse, "r_mean": None, "r_mcse": None,
            # mismatches and marks
            "floor_R": sc.floor_R, "floor_r": None, "mismatch_R": sc.mismatch_R, "mismatch_R_mcse": sc.mismatch_R_mcse,
            "mismatch_r": None, "C_N": float(pstar.capacity), "capacity_gap": gap,
            "beyond_cap": {n: beyond_cap(sc.R_mean[n], sc.R_mcse[n], pstar.capacity, gap) for n in cast},
            "relatives_world": summ.relatives_world, "floor_sub": sc.floor_sub,
            # row summaries (R only in tier 0)
            "gap_J": _pairs(summ.gap_J), "gap_pi": _pairs(summ.gap_pi), "gap_pair": _pairs(summ.gap_pair),
            # diagnostics computed with the scores; the rest later
            "mean_shift": sc.mean_shift, "spread_mismatch": sc.spread_mismatch, "covered_J": None,
            "mass_bound_gap": None, "joint_width2": None, "breadth": None, "best_rival": None, "gap_rival": None,
            # prior side
            "I_pstar": float(pstar.capacity / np.log(2)), "pstar_n_atoms": int(np.sum(pstar.prior.weights > 0)),
            "pstar_method": getattr(pstar, "method", None),
            # provenance
            "S_q": S_q, "seed_stream": {"cell": cell.name, "row": k}, "tier": 0,
        })
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    return {"cell": cell.name, "rows": out, "seconds": time.perf_counter() - start, "build_seconds": t_build,
            "peak_rss_mb": rss / 2**20 if sys.platform == "darwin" else rss / 2**10, "pid": os.getpid()}


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def provenance(args, timings: dict, wall: float) -> dict:
    """§6.1's provenance (`skills/manage-randomness.md`, rule 4)."""
    pkgs = {}
    for name in ("numpy", "scipy", "numba"):
        try:
            pkgs[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pkgs[name] = None
    return {
        "git_head": _git("rev-parse", "HEAD"), "git_dirty": bool(_git("status", "--porcelain", "--", "src", "experiments")),
        "src_tree": _git("rev-parse", "HEAD:src/infomax"),
        "spec_commit": _git("log", "-1", "--format=%H", "--", "specs/002-foreign-q-prediction.md"),
        "packages": pkgs, "python": platform.python_version(), "platform": platform.platform(),
        "cpu_count": os.cpu_count(), "workers": args.workers, "threads_per_worker": _THREADS,
        "seed": SEED, "S_q": args.S_q, "tier": 0, "wall_seconds": wall, "cells": timings,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--threads", type=int, default=THREADS_DEFAULT, help="threads per worker (recorded)")
    ap.add_argument("--S_q", type=int, default=S_Q)
    ap.add_argument("--cells", default="", help="comma-separated cell names; default: all of tier 0")
    ap.add_argument("--out", default=str(ROOT / "experiments/002-foreign-q-prediction/output/tier0"))
    ap.add_argument("--force", action="store_true", help="recompute cells whose output exists")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "cells").mkdir(parents=True, exist_ok=True)

    cells = tier0_cells()
    seeds = dict(zip((c.name for c in cells), np.random.SeedSequence(SEED).spawn(len(cells))))
    chosen = [c for c in cells if not args.cells or c.name in set(args.cells.split(","))]
    todo = [c for c in chosen if args.force or not (out / "cells" / f"{c.name.replace('/', '__')}.json").exists()]
    print(f"tier 0: {len(chosen)} cells chosen, {len(todo)} to run, {args.workers} workers x {_THREADS} threads", flush=True)

    start = time.perf_counter()
    import multiprocessing as mp

    # one fresh process per cell: a cell's peak memory is its own (a reused worker reports the
    # peak of its whole life), and no state carries from one cell to the next
    pool = ProcessPoolExecutor(max_workers=max(1, args.workers), mp_context=mp.get_context("spawn"), max_tasks_per_child=1)
    futures = [pool.submit(run_cell, c, seeds[c.name], args.S_q) for c in todo]
    results = (f.result() for f in as_completed(futures))
    for res in results:
        (out / "cells" / f"{res['cell'].replace('/', '__')}.json").write_text(json.dumps(res, indent=1, default=float))
        print(f"{res['cell']}: {res['seconds']:.0f} s (build {res['build_seconds']:.0f} s), "
              f"{len(res['rows'])} rows, peak {res['peak_rss_mb']:.0f} MB", flush=True)
    wall = time.perf_counter() - start

    rows, timings = [], {}
    for c in chosen:
        path = out / "cells" / f"{c.name.replace('/', '__')}.json"
        if path.exists():
            res = json.loads(path.read_text())
            rows += res["rows"]
            timings[c.name] = {k: res[k] for k in ("seconds", "build_seconds", "peak_rss_mb")}
    (out / "results_table.json").write_text(json.dumps(rows, indent=1, default=float))
    (out / "provenance.json").write_text(json.dumps(provenance(args, timings, wall), indent=1))
    print(f"wrote {len(rows)} rows to {out / 'results_table.json'} in {wall:.0f} s", flush=True)


if __name__ == "__main__":
    main()
