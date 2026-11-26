# Handoff — 2026-11-26

Science session: spec 002 stage 3, testing the implementation per
`workflows/implement-spec.md`. One meta-science branch: IR-2 in `AGENTS.md` ("hours of
compute: look for minutes first"), its own commit `e620ff0`. (The previous handoff, 2026-11-25,
is in git history.)

## Where we left off

Everything is committed (through `1394f7c`, plus the eye-test figure commit after it). Julia
1.13.4 is installed through juliaup; the fixtures have their own pinned environment in
`tests/fixtures/atomicpriors/` (DD-J1).

- **Fast suite** (`0483d5b` plus the `p_proj` sampler; T12(e) run apart): 149 passed, 6
  failed (`experiments/002-foreign-q-prediction/runs/fast_suite_0483d5b-pproj.log`,
  untracked). T7(a) has since been fixed, so four failures remain: T14(a) for the two
  log-normals, T21(a) `mass_near`, and T16(b) at the cheap cell. All are test-side.
- **Slow tests run this session:** T7b, T12(f) and T4's two sampled tests pass. The slow
  suite as a whole has not run.
- **Eye test:** MB approved `D ≤ 5` on the old Jeffreys grid. That grid turned out to lose 5%
  of Jeffreys' mass at `D = 4` and 24% at `D = 5`, so the figure was redrawn with sampled
  `p_J` from `D = 4`, and `D = 7` was added (`--extended=5,7`). The redraw took 37 min. Through `D = 5` it matches A&M as before (`I(p_J)` 2.28
  bits at `D = 5`, against 2.29). At `D = 7`, `I(p*)` = 4.86 and `I(p_LN)` = 2.25 bits match
  A&M, but `I(p_J)` = 1.52 bits sits 0.19 bits below A&M's 1.71, while the D = 7 prototype's
  resampled cloud gave 1.69 ± 0.04. `p_LN`'s `B` band also reaches 416 bits at its upper end,
  against A&M's 45–50. Both point at the weak sampling at `D ≥ 7` (thread 5); not yet
  reviewed by MB. `D = 11` has
  not run.

## Recent decisions worth remembering

- **`p_proj`** is sampled by adaptive importance sampling (OQ-6, DD-P3), not `transtrum`'s
  chain, which did not mix. Fits are polished tightly and snapped onto faces (DD-P1). The
  `transtrum` fixture is re-fitted.
- **The atomic path** (`p*` above `D_switch`) is an adaptive pool on our own solver (OQ-1,
  DD-A1). AtomicPriors.jl fell 0.027 nats short at `D = 5` by direct Monte Carlo and is now a
  one-sided reference (T12(f)). Julia is development-time only (OQ-7).
- **Continuous priors beyond the grids** (OQ-13, DD-Q4): exp-decay `p_J` is sampled from
  `D = 4`; `p_U` and `p_LN` become clouds above `D = 5`. `B`'s maximum is refined per point.
- **Test changes, all decided with MB:** T12(b) uses the cross-equalizer; T12(c) runs at
  reduced noise; T13(d) checks only inside the warped ball; T7(a)'s reference uses exact
  cell masses.

## Open threads (decisions for MB)

1. **Test-side issues:** T14(a)'s log-normal midpoint grid, probably the same fix as T7(a);
   T21(a) `mass_near`'s own precondition; T16(b)'s `1e-6` bound.
2. **DD-S1:** the solver stops beyond 1-D at violations of 1e-3 nats and a support residual
   of 2e-3, against the spec's `1e-8`. The atomic path inherits this.
3. **Unconfirmed values:** §5.4's sweep design and §5.5's T12 tolerances. Two were chosen by
   Claude: T12(b)'s 0.05, after seeing the data, and T12(f)'s 0.01 floor.
4. **Scope above `D = 4`:** which cells run there. IR-2 asks for a cost estimate before
   `run.py`.
5. **Sampling at `D ≥ 7`:** `p_J`'s sampler levels off at about 8% effective sample size,
   and the per-point marginal's two versions differ by up to 0.9 nats at face states. In
   the eye test at `D = 7`, `I(p_J)` came out 0.19 bits below A&M, and `p_LN`'s `B` upper end
   reached 416 bits. A better proposal is the likely fix; `D = 11` waits on it.
6. **Untested:** the pool in the hypercone (T21(a) at `D = 11, 26`); `p_lat` beyond
   `D_switch`; `p_proj` above `D = 4`, where a Jeffreys start loses about 10× effective
   sample size per added `D`.
7. **Not implemented:** `run.py`, and exp-decay `p_ref` at `D ≥ 3` (DD-A2).
8. **Small:** a `[CITATION NEEDED]` in spec §5.5's unique-mixture footnote; `ruff` is not
   installed; LineSearches 7.5.1's mis-declared compatibility could be reported upstream
   (optional).

## Next session — start here

1. Look at the redrawn eye test, `tests/figures/002_foreign_q_prediction/eyetest_am_fig5.png`:
   `D = 4, 5` with sampled `p_J`, and `D = 7`.
2. Decide threads 1–3. If agreed, fix T14(a) as T7(a) was.
3. Estimate, then run, the slow suite (`pytest -m slow tests/test_002_*.py`), leaving out
   T21(a) at `D = 11, 26`; then the fast suite once more.
4. Stage-3 bookkeeping: per-test commit hashes in the codegen log.
