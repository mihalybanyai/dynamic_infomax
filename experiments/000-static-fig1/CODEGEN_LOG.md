# Code generation log — spec 000

Started: 2026-05-18.

Tracks file-by-file implementation of spec 000's algorithm against the
test suite in `tests/test_000_static_infomax_fig1.py`. One commit per
file lands implementation + this log update, so an interrupted run
leaves the repo in a clean state.

## Status

| File | State | Targeted tests |
|---|---|---|
| `src/infomax/likelihood.py` | **done** (T11 passing) | T1, T11 directly; foundation for all others |
| `src/infomax/jeffreys.py` | **done** (CDF smoke-test passes) | T4 |
| `src/infomax/prior.py` | pending | all (GridPrior is the backbone) |
| `src/infomax/atoms.py` | pending | T1, T4, T4b, T5 |
| `src/infomax/ba.py` | pending | T1, T2, T2b, T2c, T3, T3b, T4, T4b, T5, T6, T7, T7b, T8, T9, T10 |

## Test-suite result log

(Populated after the full suite is implemented and run end-to-end.)
</content>
