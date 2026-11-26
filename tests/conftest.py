"""Shared pytest configuration.

Parallel runs (`uv run pytest -n 3 --dist loadfile`, pytest-xdist) give each worker process a
fixed number of numba and BLAS threads, the cores divided by the workers and at least 1, so
that the workers share the cores instead of each starting one thread per core. A value already
set in the environment wins. The variables are set in the controller before any worker starts,
and the workers inherit them; numpy and numba read them when they first load, in the workers.
`--dist loadfile` keeps each file's tests in one worker, where builds are memoised in-process.
Serial runs are untouched.

The tests do not depend on the thread count: their tolerances lie far above the summation-order
noise it causes (at most 7.7e-4 relative on gaps, experiment 002's runner, 2026-11-26), and the
one bit-identity check (T10) compares runs within one process.
"""
from __future__ import annotations

import os

THREAD_VARS: tuple[str, ...] = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS",
)


def pytest_configure(config) -> None:
    workers = getattr(config.option, "numprocesses", None)
    if not workers or os.environ.get("PYTEST_XDIST_WORKER"):
        return
    cores = os.cpu_count() or 1
    n = cores if isinstance(workers, str) else int(workers)
    threads = max(1, cores // max(1, n))
    for var in THREAD_VARS:
        os.environ.setdefault(var, str(threads))
