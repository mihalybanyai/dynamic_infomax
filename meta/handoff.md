# Handoff — 2026-11-27 (early morning)

Science session: spec 002 stages 3 and 4 of `workflows/implement-spec.md`, with a memory fix
along the way. No meta-science branch. Stage 5, the implementation red team, is next after
MB re-reviews §4 and §5. (The previous handoff is in git history, `3067fee`.)

## Where we left off

- **Stage 3 passed at `88a8b84`.** Fast suite: 217 passed in 53 min with three workers. Slow
  suite: 28 passed in 57 min with two. Every test's row in the codegen log carries
  `88a8b84`, and every code file is `done` (`7e557f0`). Run logs are in
  `experiments/002-foreign-q-prediction/runs/` (gitignored).
- **Stage 4 is committed** (`1e40113`). `docs/002-foreign-q-prediction/README.md` now has a
  module-level call graph from `_make_call_graph.py` (code2flow; the function-level graph is
  in `call_graph_functions.md`), a data-flow diagram through `score_cell`, and `sampled.py`
  in the Modules table. The diagrams are not render-checked.
- **MB's decisions before the suites** (`09181eb`, `de7ba08`): §4, §5, §7 reviewed; T21(a)'s
  hypercone cases at `D = 11, 26` left out; DD-S1's stopping rule is the code's; the values
  Claude chose are accepted (T2's 1e-6, T12(b)'s 0.05, T12(f)'s 0.01, §5.5's tolerances, the
  routing at 300 and 50 effective draws, the annealing settings). The new text is red, so §4
  and §5 are draft again. T10's `R`-alone test is now listed in §5 (`591acc1`).
- **DD-K4, a memory fix** (`88a8b84`). §3.3's split runs in every `score_cell`, tier 0
  included, and formed its posterior weights for all data at once: about 7 GB at tier 0's 500
  draws on `p_U`'s 280,800 nodes at exp-decay `D = 4`. It now works in batches (304 MB) and
  reuses cached node predictions. Bit-identical outputs; off the eye test's path (the eye
  test's computation at `D = 1`–4 completes with the changed methods made to raise), so the
  approval stands.

## Open threads (decisions for MB)

1. **Re-review §4 and §5**: two red sentences from `de7ba08` (DD-S1 after §4.2's pseudocode;
   T21(a) in §5.4). Then stage 5.
2. **A NaN in `p_lat`'s solve on the cone cell**: T8's cone case warned at
   `capacity.py:124` (`DifferenceObjective`, probably `inf − inf`). T8 passed; whether the
   build is affected is not checked (docs, Testing notes, *Stage 3*).
3. **Skip the split in tier 0?** It is not part of §3.7's verdict, but `run.py` records it.
   Skipping it saves its time as well as its memory.
4. **`r_N`'s tier**: `PLAN.md` puts it in tier 1; you kept both families in tier 0.
5. **OQ-14 above `D = 5`**: Jeffreys' annealed estimates at `D = 11` are adequate for the eye
   test only; tier 2's `D ≥ 5` needs more.
6. **Untested**: `p_lat` beyond `D_switch`; `p_proj` above `D = 4`.
7. **Not implemented**: `run.py`'s tiers 1–2, figures and report; the persistent build cache;
   exp-decay `p_ref` at `D ≥ 3` (DD-A2).
8. **Small**: spec lines 1643–1644 still describe `transtrum`'s walkers and burn-in, which
   OQ-6 replaced; a `[CITATION NEEDED]` in §5.5's footnote; `ruff` is not installed.

## Next session — start here

1. **Speed-ups and memory** (MB wants these next), measured before changed (IR-2):
   - T1(e) went from 0.7 s (`762eae0`) to 501 s; find what changed.
   - T8 on every row (1962 s cone, 942 s cheap), T22(a) on every row (961 s) and on the
     diagonal (698 s): profile one each. The split's per-datum loop (2.3 of 4.2 s per 100
     data at `D = 4`) is a candidate.
   - Re-measure tier 0's cell peaks after DD-K4: `run.py`'s scheduler budgets from peaks
     recorded before it. Python's allocation tracer saw 1.43 GB where the OS reported 1.09 GB
     resident at one point, so macOS may compress memory and recorded peaks may understate it
     [guess].
   - Not done: smaller chunks in `mixture_logpdf` (32·10⁶ entries, 256 MB per temporary), and a
     conftest hook recording each test's peak memory so heavy tests can get their own pass.
2. **Stage 5**: `workflows/invoke-red-team-on-impl.md`, after thread 1.
