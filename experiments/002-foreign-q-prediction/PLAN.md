# Experiment 002 — Foreign-`q` prediction: plan

Runs spec 002 ([`specs/002-foreign-q-prediction.md`](../../specs/002-foreign-q-prediction.md))
in three tiers, core first. Tier 0 gives preliminary results in a few hours on a laptop; the
rest waits for parallelism, a build cache or a larger machine. The spec is the contract; this
file sets only the order of the runs and what each tier needs.

## Question

Does the infomax prior `p*` predict held-out data from a foreign
[nature](../../GLOSSARY.md#nature) better than Jeffreys, on its home score `R_N`, in
high-dimensional sloppy models? Secondarily, do the budget-conscious priors as a family?
(Spec §0.2, §3.7.)

## Hypothesis

`p*` beats Jeffreys away from home on `R_N`, and on the nested natures its loss grows more
slowly with `D` than Jeffreys' does (spec §3.7, §3.2). The sign is open; the spec fixes how it
is measured (§2.4).

## Method

Algorithm in spec §4, sweep design in §5.4, report in §6. Seed `20260601`, one child stream
per cell, cells in a fixed lexicographic order (§5.4). Entry point `run.py`, not yet written.

### Priority tiers

Each tier adds to the one before. The report states which tier each claim rests on.

| Tier | Answers | Cast | Score | Natures | Cells |
|---|---|---|---|---|---|
| **0** | §3.7's verdict: `p*` against Jeffreys away from home; the trend in `D` on the nested natures | `p*`, `p_J`, `p_U`; `p_LN` in exp-decay | `R_N` | the round robin of this cast; the nested natures; few rates | the base cells of both families (MB, 2026-11-26), and the cone at fall-off `φ = 0.5` for the nested natures, each at `D = 1`–4: 12 cells |
| **1** | Whether a lead is `p*`'s own or the budget principle's; what knowing `N` is worth; the second score | + `p_lat`, `p_proj`, `p_LN^*`, `p*_{N/10}`, `p*_{10N}` | + `r_N` (proposed here; please confirm) | + their own worlds; the stress natures | + the twin cells at `N = 4`, where `r_N` differs from `R_N`'s budget; the curvature cells, for the vertex nature |
| **2** | Whether the verdict survives the knobs | + `p_ref`, once per ranking | both | every row on tier 0's cells; the round robin of tier 0's cast on the others | the rest of §5.4's one-knob variations (`σ`, `N`, box, taper, fall-off); `D ≥ 5` on the atomic path; more draws where a gap's sign is unresolved |

The diagnostics of §6.1 (decomposition, calibration, mass bound, insurance) are computed on
whatever cells a tier builds; they need no cells of their own.

### Cost and run order

Measured on the development laptop (8 cores, 8 GB), 2026-11-26, sharing the machine with
other runs, so slightly high: one tier-0 cell per kind at `D = 2` and `D = 4`, 500 draws, 2
threads.

| Cell | `D = 2` | `D = 4` | Peak memory at `D = 4` |
|---|---|---|---|
| exp-decay base | 41 s | 380 s | 2.9 GB (0.7 GB at `D = 2`) |
| hypercone base | 31 s | 108 s | 0.2 GB |
| hypercone, nested natures | 125 s | 177 s | 0.3 GB |

- **Tier 0:** 12 cells, about 22 min serially (`D = 1, 3` interpolated), and about 7–10 min with
  the memory scheduler at its defaults (4 cells at once within 6 GB) [estimate]. The first
  guess was 1–3 h.
- **Tier 1:** not measured. It adds the heaviest builds (`p*_{10N}` took 340 s at the cheap cell,
  `p_lat` about 50 s) and the twin cells for `r_N`; measure one cell before planning it.
- **Tier 2:** about 70 cells, and `D ≥ 5`: the atomic-path `p*` (5–9 min at `D = 5`) and, for
  Jeffreys at `D ≥ 9`, annealed per-point estimates of about 10 s per thin point. Measure first.

### Savings, by expected impact

1. **Parallel cells**: in `run.py` for tier 0, a fresh worker process per cell, each with a
   fixed number of threads (`--threads`, recorded), so results do not depend on the
   scheduling: serial and parallel runs agree bit for bit. Cells are scheduled under a memory
   budget (75% of physical memory by default), largest expected peak first, from the peaks
   earlier runs recorded; an unmeasured cell counts as the heaviest measured one. Thin points
   within a cell are not split across workers.
2. **A persistent build cache keyed by `σ/√N`**, which twin cells and the mis-budgeted `p*`
   share: not implemented (deferred until the code is stable; MB).
3. **Robustness cells score a subset of rows**: in tier 2 above.
4. **Draws raised only where a gap's sign is unresolved**: §5.4's 500 → 2000 rule.
5. **Scoring `R_N` alone** where a tier needs only it, and a memo of thin points' marginals:
   done; tier 0 had paid about three times its cost at thin points.
6. **Cheaper thin points**: the bell-shaped per-point estimate costs 1.8–3.5 s at `D = 7`;
   not yet profiled.

## Success criteria

§3.7's verdict, per group of rows and per budget-conscious prior, `p*` first: *supported* where
`Δ^J_{R_N}(π) < 0` beyond Monte-Carlo error, *refuted* where `π` ties with or loses to
Jeffreys. No average over rows decides it, and no cell is set aside; own worlds, relatives'
worlds and cells beyond the cap are labelled, not excluded.

## Failure modes to watch for

- **Self-sampling**: a lead only in a prior's own or relatives' worlds (§2.5).
- **Sampled priors at thin states** (OQ-14): the routed marginal is validated to `D = 5` (T7(a));
  a result at `D ≥ 6` against a sampled prior needs its annealed bracket.
- **Monte-Carlo error against a gap's size**: §5.4's escalation rule.
- **`p*`'s capacity gap and the solver's 1e-3-nat stopping rule** (DD-S1), which the beyond-the-cap
  label already allows for.
- **A cast that thins with `D`**: trends are read twice, with the full cast and with the cast
  present at every `D` (§2.4).
- **Jeffreys' `I` at `D = 11`** sits 0.11 bits below A&M's, not explained (spec §4.2).
