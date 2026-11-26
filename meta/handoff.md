# Handoff — 2026-11-27

Science session: spec 002 stage 2 (eye test), per `workflows/implement-spec.md`, with the
test-side fixes, a rebuilt Jeffreys path and experiment 002's tier-0 runner along the way. No
meta-science branch. (The earlier handoff of 2026-11-26 is in git history, `aad520b`.)

## Where we left off

- **The eye test passed (MB, 2026-11-27)**, stage 2's gate. The extended run at `D = 11` took
  3321 s and matches A&M: `I` = 4.90, 1.08, 1.93 bits for `p*`, `p_J`, `p_LN`, against 4.91,
  1.19, 1.87, and A&M's `B` bounds inside our bands (`0fc45e6`).
- **MB's parallel session (2026-11-27)** reviewed §4, §5 and §7 (`09181eb`) and settled, in
  `de7ba08`: T21(a)'s hypercone cases at `D = 11, 26` are left out; DD-S1's stopping rule is the
  code's; the values Claude chose are accepted (T2's 1e-6, the 300-draw routing threshold,
  §5.5's fixture tolerances). Its new text is red, so §4 and §5 are draft again.
- **`D ≤ 7`, redrawn the day before, also matches A&M.** At `D = 7`, `I` is 4.86, 1.68, 2.29 bits for `p*`,
  `p_J`, `p_LN`, against 4.86, 1.71, 2.25; A&M's `B` bounds lie inside our bands at `D = 5, 7`
  (`ddcae39`). `B` at `D = 11` is good to about 1% only: Jeffreys' annealed estimates differ by
  0.4–0.6 nats between runs there.
- **The suites have not run since today's changes.** The last full fast run was before them
  (`0483d5b` plus the `p_proj` sampler); the slow suite has never run as a whole. Run today
  and passing at the time: every slow T4 and T7(a) test, the fast T7(a) and T10 tests, T14(a)
  and T16 (before the Jeffreys changes), and in parallel the fast tests of
  `test_002_models.py`, `test_002_natures.py` and `test_002_diagnostics.py`.
- Everything else is committed, through this handoff.

## Recent decisions worth remembering

- **Jeffreys' density** is computed by a Newton-basis factorisation of its Vandermonde
  Jacobian. Double precision had been off by up to 43 nats at `D = 7` and 260 at `D = 11` at
  thin states (`143a620`). The new form is good to 6e-5 nats to `D = 11` and fails at `D = 13`.
- **Jeffreys' sampler** draws a Student-t first law (`edcd164`). It anneals to Jeffreys when
  importance sampling ends below 2% effective, as at `D = 9, 11` (`c9834ba`). Its `I(p_J)` at
  `D = 11` sits 0.11 bits below A&M's, not because of the build (two methods agree, more
  moves change nothing), and is recorded as unexplained.
- **Sampled priors' marginals are routed** (OQ-14, `613ed14`, `8ae89d5`). The cloud is used
  where 300 or more likelihood-weighted draws are effective. Elsewhere a bell-shaped
  per-point estimate in log decay times is used, and an annealed one where that keeps under
  50 effective draws. The annealed one also gives a forward–backward bracket. Validated
  against exact grids at `D = 3` and for `p_LN` at `D = 5`, and by cross-checks on Jeffreys'
  faces at `D = 5, 7`. It warns above `D = 5`.
- **Test-side fixes**, decided with MB: T14(a) checks the product laws against closed forms
  (`82d31de`); T21(a)'s precondition (`55bcf81`); T16(b) at DD-S1's `1e-3` beyond 1-D
  (`e675eab`).
- **Experiment 002** runs in three priority tiers, in
  `experiments/002-foreign-q-prediction/PLAN.md`. Tier 0, §3.7's verdict on `R_N`, takes about
  22 min serially on this laptop. `run.py` runs tier 0's cells in parallel under a memory
  budget, deterministic whatever the scheduling (`32980f5`, `cfe8762`). Tiers 1–2, the figures
  and the report are not written. Its runs come after the implementation red team [assumed
  from the workflow order, not checked].
- **Tests run in parallel** with `uv run pytest -n 3 --dist loadfile` (`73a6b16`); `tests/conftest.py`
  caps each worker's threads. On 8 GB, memory limits the workers: use 2 for the slow suite.

## Open threads (decisions for MB)

1. **Re-review §4 and §5**: draft again after `de7ba08`'s red text and this session's §5.3 run
   time.
2. **Values Claude chose, not yet confirmed**: the hand-over to annealing (50 effective draws);
   the annealing settings (2000 particles, 80% per step, 10 moves); the eye test's speed-ups
   (10 states with 16 draws for `B`, 2048 draws for `I`). T12(b)'s 0.05, chosen after seeing
   the data, if `de7ba08` did not cover it.
3. **`r_N`'s tier**: `PLAN.md` puts it in tier 1; you kept both families in tier 0.
4. **OQ-14 above `D = 5`**: at `D = 11` Jeffreys' annealed estimates are adequate for the eye
   test only. Tier 2's `D ≥ 5` needs more.
5. **Untested**: `p_lat` beyond `D_switch`; `p_proj` above `D = 4`.
6. **Not implemented**: `run.py`'s tiers 1–2, figures and report; the persistent build cache
   (tier 1); exp-decay `p_ref` at `D ≥ 3` (DD-A2).
7. **Small**: a `[CITATION NEEDED]` in §5.5's unique-mixture footnote; `ruff` is not installed;
   LineSearches 7.5.1's mis-declared compatibility could be reported upstream (optional).

## Next session — start here

1. **Stage 2** is done: the eye test passed (MB, 2026-11-27).
2. **Stage 3, the suites.** Fast first, then slow, in parallel:
   - `uv run pytest -n 3 --dist loadfile tests/ 2>&1 | tee experiments/002-foreign-q-prediction/runs/fast_suite_<commit>.log`
   - `uv run pytest -n 2 --dist loadfile -m slow tests/` (T21(a)'s hypercone cases run at `D = 6`
     only, since `de7ba08`)

   The workflow wants each passing test's commit in the codegen log. A run at one commit gives
   every passing test that commit. A failure is reported to MB, not fixed unilaterally, then
   rerun alone; finish with one end-to-end run and flip the File status table to `done`.
3. **Stage 4, documentation finalisation** (`workflows/implement-spec.md`): a call graph from
   code2flow (already a dev dependency) and a data-flow diagram, both as mermaid, in
   `docs/002-foreign-q-prediction/README.md`, in the workflow's section order.
4. **Stage 5**: hand off to the implementation red-team (`workflows/invoke-red-team-on-impl.md`),
   with §4 and §5 reviewed again.
