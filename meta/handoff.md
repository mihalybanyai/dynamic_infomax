# Handoff — 2026-11-25

Science session: implementing spec 002 (`specs/002-foreign-q-prediction.md`) per
`workflows/implement-spec.md`. (The previous handoff, 2026-05-19, is in git history.)

## Where we left off

Stage 1 (codegen) is done and committed, one commit per file; stage 2 (eye test) is
approved for the default run. The fast suite (`pytest tests/test_002_*.py`, slow tests
excluded) was started at `762eae0` and writes to
`experiments/002-foreign-q-prediction/runs/fast_suite_762eae0.log` (untracked). Read it
first: it ends with an `elapsed` line, and `-ra` lists every failure. Expected runtime 15–20
min. Per-test status and the known failures are in
`experiments/002-foreign-q-prediction/CODEGEN_LOG.md`; every design choice the spec does
not fix is in `docs/002-foreign-q-prediction/README.md` (DD-*, and *Testing notes*).

## Recent decisions worth remembering

- **The divergence estimator is deterministic** (DD-K1, DD-K3): Gauss–Hermite on the 1–3
  leading directions of the neighbours' span plus a second-order term, compiled with numba
  (new dependency). Error ≤ 3.4e-4 nats. Explainer: `tutorials/math/quadrature.md`.
- **The capacity solver** (DD-S1): spec 000's BA as warm start, then projected Newton
  ascent with an active set. Beyond 1-D it stops at violations of 1e-3 nats and a support
  residual of 2e-3, not at the spec's `tol = 1e-8`: needs MB's review. Damping floor 1e-5
  for `p*`, 1e-10 for `p_lat`.
- **`p*` is the unmerged candidate-set solution** (DD-C2): merging adjacent candidates broke
  the equalizer by up to 0.05 nats.
- **Eye test** (spec §5.3 red text, DD-E1): `B` is drawn as a band, from the maximum over
  the prior's own 2000 draws to the maximum over all of `Theta`, because A&M do not say
  over which states their `B` runs. Information matches A&M within 0.05 bits.
  `B(p*)` ≈ 0 against A&M's 0.2 bits, which their caption attributes to solver error.
- **Speed:** a full cheap-cell cast now takes about 5 min (was over 40); builds of `p*` and
  `p_lat` are memoised within a process. A persistent cache is deferred until the code is
  stable (MB).

## Open threads (decisions for MB, all in *Testing notes* or the codegen log)

1. **Test-side issues:** T13(d) requires `det g > 0` at the cone tip, where it is 0;
   T7(a)'s reference grid is less accurate than the code (`p_U`, `p_LN`); T21(a)
   `mass_near`'s own precondition fails on its jittered states; T16(b)'s `1e-6` two-sided
   bound at the cheap cell is unreachable with a quadrature estimator (gap ≈ 1e-3).
2. **Infeasible on candidate sets:** T21(a) in the cone at `D = 11, 26` (atoms on every
   cross-section corner, `3^D` faces). Needs the atomic path or a smaller `D`.
3. **Julia:** T12 (fixtures), T7b, the extended eye test and the atomic path all need it.
4. **Not implemented:** exp-decay `p_ref` at `D >= 3` (DD-A2); `run.py` and
   `tests/fixtures/atomicpriors/generate.jl`.
5. **Suspect:** T11 `p_proj` information vs capacity at `D = 3, 4` failed in an early run;
   probably Monte-Carlo noise (SE ~0.02 nats) against a 1e-3 slack. Not re-checked.

## Next session — start here

1. Read the fast-suite log; triage failures into code bugs (fix) and test or spec issues
   (report, do not edit tests without MB).
2. Run the slow suite (`pytest -m slow tests/test_002_*.py`, about 40 min), excluding
   T21(a) at `D = 11, 26`.
3. Stage 3 bookkeeping: per-test commit hashes in the codegen log once tests pass.
