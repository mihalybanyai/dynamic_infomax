# Red-team review of the spec 002 implementation (`src/infomax/`) and its documentation

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 5.5
Effort tier: max (set at spawn by the main agent; not verifiable here)
Roster verified: 2026-11-27
Date: 2026-11-27
Spec version: 8d933e3
Code version: 88a8b84 (`src/` and `tests/` unchanged at 8d933e3)
Measurements: run at 8d933e3 by uncommitted scratch scripts; each footnote names the calls.

## Summary

At tier 0's cells (`experiments/002-foreign-q-prediction/PLAN.md`), the code does what spec §4 asks. `score_cell` follows §4.4, `C_N` agrees with direct Monte Carlo, and the exp-decay `p*` builds converge. The one defect in tier 0's own output is the beyond-the-cap label (F1). It fires on `p*` itself, and on nested rows its theorem does not cover, so §4.5's definition needs a decision before tier 0's labels are read.

The code is most fragile off tier 0's path. The capacity solver stops at a hard round cap without saying so (F2). Five further pieces are wrong, noisy or infeasible in cells §5.4 calls for, and none warns: the matched box's sampled Jeffreys (F3), the stiffest-first ranking on that box (F4), the per-state losses of sampled priors (F5), `p_LN^*` above `D = 5` (F6), and the curvature cells outside `2 ≤ D ≤ 4` (F7). I found no load-bearing inefficiency at tier 0's scale; cost notes for tier 2 are in F7 and m14.

The documentation mostly tracks the code: both call graphs regenerate edge for edge, and the README's node and candidate counts reproduce. Three places do not. The README's DD-C2 describes an atom merge the code does not do (F8), `mixture.py` misdescribes its own estimator (F9), and several README passages are stale (Minor). Tier 0's numbers can be read once F1 is settled; tier 1 also needs F2, and tier 2 also needs F3–F7.

## Findings

### F1: The beyond-the-cap label fires on `p*` itself and on rows its theorem does not cover [severity: high] [spec-implication]

**Location**: `src/infomax/diagnostics.py:59–73` (`beyond_cap`, `capacity_gap`), applied to every prior of every row at `experiments/002-foreign-q-prediction/run.py:148, 172`; spec §3.7 (*Beyond the cap*), §4.5.

**Touches**: code

**Concern**: The label asks only that `R − C_N` exceed one Monte-Carlo standard error plus the capacity gap. So it fires on `p*` itself, which by (3.1.1) cannot exceed its own cap. That happened in 3 of the 28 rows of PLAN's cost-model outputs, two of them `p*`'s own world[^1]; there, 40 reseeded repeats average `R(p*) − C_N = +0.002 ± 0.006`, and a quarter of them exceed one standard error[^2]. The label also marks `p_J` in the cone's nested rows. Their states lie outside the agent's `Θ`, where §3.2 says `R_N^q(p*) ≤ C_N` does not hold. Finally, `capacity_gap` draws its 256 states uniformly in the interior and misses the faces: at exp-decay `D = 3, 4` it records −0.0007 and −0.0037 nats, while face states reach +0.025 and +0.022[^3].

**What would resolve it**: Never label `p*`; record `R(p*) − C_N` per row instead, as a check on the gap. Leave the label off rows whose nature lies outside the agent's `Θ`. Use a several-σ margin (the suite's `MC_SIGMAS = 4`). Take the gap's maximum over face states (`pstar._random_face_states`) as well as interior ones. The first three need §4.5's and §3.7's wording changed.


> M: apply the suggested solution, with keeping the label everywhere as a purely descriptive one about the theorem (only when nature is inside theta), not something about the actual MC result. And set the tolerance to 4 sigmas.

> C: To apply, reading (B) (MB, chat): the label exists only where (3.1.1) holds, on rows whose
> nature lies inside the agent's `Θ`. There `beyond_cap[π]` holds when `R − C_N` exceeds 4 MCSE
> plus the capacity gap, and `p*` wins the cell by theorem. The hypercone's nested rows keep their
> numbers, `R − C_N` included, and carry no label. `p*` is never labelled: its `R(p*) − C_N` is
> recorded per row as a check. The gap is the largest excess over interior and face states
> (`pstar._random_face_states`), floored at 0. Spec (3b): §3.7 (*Beyond the cap*), §4.5, §2.4's
> sentence on the label, and §6.3 (the definition, and a column for the check). Code (3c):
> `diagnostics.beyond_cap` (4 MCSE, inside `Θ` only, never `p*`), `capacity_gap` (face states,
> floor at 0), `run.py` (the check column). Routed `[test-gap]` to `invoke-red-team-on-tests.md`:
> T22(b)'s cases encode the one-MCSE margin, and `(4.31, 0.1, 4.0, 0.2)` flips under four.

---

### F2: The capacity solver stops at a hard 12-round cap without saying so [severity: medium] [test-gap]

**Location**: `src/infomax/capacity.py:22` (docstring), `:363` (`max_outer = min(max_outer, 12)` beyond 1-D), `:431` (at most 32 entrants per round), `:437–440` (no convergence flag); `src/infomax/mixture.py:512–520, 450` (neighbour lists, `f = inf`); `pstar.py:379–397`; `plat.py:106–109`; README DD-S1 (lines 276–279); `tests/test_002_priors.py:525` (T16(b) only in 1-D and at the cheap cell).

**Touches**: both

**Concern**: Beyond one-dimensional data, `solve_capacity` returns after 12 outer rounds whatever remains, though its docstring promises a Csiszár gap below `add_tol`. Nothing checks or records the outcome, on the candidate path or for `p_lat`. Three of five instrumented builds stopped there with violators left[^4]:

- the tier-0 cone `D = 4` `p*`;
- the cheap cell's `p*_{10N}`, with a support of 794 atoms rather than DD-S1's 1669;
- T8's cone `p_lat`, whose two-sided bound stayed open at 5.8 times the 1e-3 rule.

That `p_lat` solve also lost a round to a NaN. `KernelTable` takes each state's neighbours among all support atoms, zero-weight entrants included, so an entrant whose neighbours all weigh zero gets `f = +inf`, and then `λ = w·f = 0·inf`. At 32 entrants per round, the cap also limits the support's growth to 384 atoms beyond its starting set of at most 1500. `p*_{10N}` at exp-decay `D = 4`, whose net holds 135,416 candidates[^5], may need more [guess].

**What would resolve it**: Return a `converged` flag and the final largest violation from `solve_capacity`, record both in `PStarResult` and `PLatResult` on every path, and warn when the cap is reached. Let the round budget follow the remaining violators instead of a constant. Build `KernelTable`'s neighbour lists from positive-weight atoms. Extend T16(b) to T8's cone cell. Then redo DD-S1's timing comparison (340 s against 795 s) on converged solves.

> M: let's definitely report if a cap was hit. let's use 24 as a compromise though

> C: To apply, with MB's fixed cap instead of a round budget that follows the violators. Code
> (3c): `solve_capacity`'s cap beyond 1-D goes from 12 to 24 rounds; it returns `converged` and
> the final largest violation `δ`, which `PStarResult` and `PLatResult` store on every path, and it
> warns when the cap is reached. `KernelTable`'s neighbour lists take positive-weight atoms only
> (the NaN). Spec (3b): §4.2's DD-S1 sentence states the 24-round cap and that a build stopped there
> is recorded as unconverged with its `δ`; §6.1's provenance line ("for every cell on the atomic
> path, its rounds and the largest violation") covers candidate-set builds too. Docs: DD-S1 (the cap,
> the reporting, the per-round trace of 2026-11-27: the three capped builds converged by rounds 15,
> 14 and 24; the 32-entrant timing comparison redone on converged solves). Routed `[test-gap]` to
> `invoke-red-team-on-tests.md`: T16(b) at T8's cone cell, and a check that the suite's solves
> converge.

---

### F3: The matched box's sampled Jeffreys collapses from `D = 6`, silently [severity: medium]

**Location**: `src/infomax/sampled.py:626–631` (the first law: Student-t log decay times at location 0.8 and scale 1.5), `:726–730` (`_anneal_jeffreys` keeps only the first-law draws inside `Θ`).

**Touches**: code

**Concern**: The first law is fitted to the whole manifold, and on the matched box (`θ ∈ [0, log 5]`) almost none of its draws land in `Θ`. Importance sampling collapses, and the annealed build runs on the few that do land: 59 of 20,000 at `D = 6`, and 21 at `D = 7`[^6]. Its `log Z` comes out 6.0 and 7.5 nats too high. `log_density`, the bell-shaped per-point marginal and the own-world sampler all inherit the error, and nothing warns. At `D = 4, 5` the build agrees with brute force within 1.3 standard errors, but §5.4 runs the box knob across the `D`-sweep, and §6.1 plots both boxes.

**What would resolve it**: Fit the first law to `Θ`, either each log time's t truncated to the box or uniform in `ξ` on the box. Raise an error when fewer than a set number of particles start inside `Θ`. Add T4's brute-force normaliser check on the matched box at `D = 4`–7.

> M: apply these suggestions, including the new test. Treat this as a high-priority issue, because despite only touching tier 2, it's at the core of the spec

> C: To apply; high priority (MB): before tier 2 runs the matched box. Code (3c): in
> `build_sampled_jeffreys`, each log time's Student-t first law is truncated to `Θ` where the box is
> finite; on the whole manifold the law and its draws are unchanged. The build and
> `_anneal_jeffreys` raise when too few first-law draws start inside `Θ` (1000 of 20,000 proposed,
> a design decision for DD-Q4). Spec (3b): §4.2's description of the first law says it is truncated
> to `Θ`. Docs: DD-Q4. The new test, T4's brute-force normaliser on the matched box at `D = 4`–7,
> is routed `[test-gap]` to `invoke-red-team-on-tests.md`: this workflow does not edit tests.

---

### F4: The stiffest-first `p_ref` ignores the box [severity: medium]

**Location**: `src/infomax/pref.py:116–118` (`THETA_RANGE`), `:207–258` (`_curve_fields`, `_StiffestField`), `:311–319`.

**Touches**: code

**Concern**: `_StiffestField` traces the sloppy eigenvector's curves over the fixed log-time range `(−4, 9)`, and normalises each by its whole Fisher length `L` and geometric mean `G`. It never reads `model.box`, so on the matched box the field is the whole manifold's: the largest difference over 2000 box states is 0.0[^7]. `p_ref[stiffest]` there weights each curve by lengths taken mostly outside `Θ`. It is therefore not the box model's Berger–Bernardo prior, unlike the coordinate rankings, which take their nuisance ranges from the box (`pref.py:78`). The matched-box cell at `D = 2` would report `gap_pi` and `delta_R_pref` against it (§2.4, §6.4 item 7).

**What would resolve it**: Clip each curve to `Θ` in log decay time before computing `L` and `G`, and run T15(d) and T15(e) on the matched box too.

> M: the suggestion sounds reasonable to me

> C: To apply. Code (3c): `_StiffestField` clips each curve to `Θ` in log decay time before
> computing `L` and `G` (`pref.py`). Docs: the `p_ref` design entry. Routed `[test-gap]` to
> `invoke-red-team-on-tests.md`: T15(d) and T15(e) on the matched box.

---

### F5: Per-state losses of sampled priors bypass the routed marginal [severity: medium]

**Location**: `src/infomax/score.py:231–233` (`isinstance(prior, DiscretePrior)` also catches a `SampledPrior`), reached from `diagnostics.covered_fraction` (`:106`), `score.bias_pressure` (`:280–282`) and T21's mass bound.

**Touches**: code

**Concern**: `per_state_redundancy` sends a `SampledPrior` to `KernelTable` over its plain cloud, which is the very estimate that §4.4 and OQ-14 replace at thin states. For `p_J` at exp-decay `D = 4`, it overstates the loss near the no-decay corner by 0.28 ± 0.03 nats, and by less than 0.01 nats elsewhere[^8]. The README's own measurements put the plain cloud's error for `p_LN` at up to 54 nats at `D = 3` and 188 at `D = 5`, and `p_U` and `p_LN` become clouds from `D = 6`. So §4.5's per-state losses, `covered_J`, `mass_bound_gap` and `bias_pressure` are biased exactly at the thin states that (3.2.1) and the insurance reading depend on. Tier 0 leaves those fields null, so no reported number is affected yet.

**What would resolve it**: Route a `SampledPrior` in `per_state_redundancy` through `log_marginal` with `n_x` draws of `x̄`, as `worst_case_bias_pressure`'s refinement already does, and run T21(a) once with a sampled prior.

> M: yes, let's certainly use the more up-to-date solution everywhere

> C: To apply. Code (3c): `per_state_redundancy` sends a `SampledPrior` through its routed
> `log_marginal` with `n_x` draws of `x̄`, as `worst_case_bias_pressure`'s refinement does; every
> caller (`covered_fraction`, `bias_pressure`, the mass bound) then uses the routed marginal. Docs:
> the per-state redundancy entry. Routed `[test-gap]` to `invoke-red-team-on-tests.md`: T21(a)
> with a sampled prior.

---

### F6: `p_LN^*`'s search above `D = 5` runs on a noisy objective [severity: medium]

**Location**: `src/infomax/plognormal.py:77–80, 94–119`; `src/infomax/sampled.py:289–291` (per-point seeds from each datum's bytes); README DD-L1 (lines 430–434).

**Touches**: both

**Concern**: Above `GRID_MAX_D = 5`, `build_pln` returns a cloud, so the objective's marginal is the routed one. Its per-point estimates are seeded by each datum's bytes: moving `(θ̄, τ)` moves the data and reseeds them, which breaks the common random numbers DD-L1 relies on at thin points. At `D = 6`, a step of 1e-6 in `τ` moved the objective by 1.2e-3 nats[^9], against Nelder–Mead's `fatol = 1e-5`, so the search stops on noise. DD-L1's "the marginal by quadrature" and "a smooth function of the parameters" hold only up to `D = 5`, and T23 runs only at the cheap cell.

**What would resolve it**: Above `D = 5`, search on the plain cloud's mixture, which is deterministic and uses the same draws in every trial, and evaluate the final `I` through the routed marginal. Or stop `p_LN^*` at `D = 5` and say so in the coverage table and DD-L1. Either way, run T23(b) at `D = 6`.

> M: the suggestion sounds reasonable. I wouldn't stop at D=5 if not necessary. running the test for D=6 seems good too.

> C: To apply the first option; no stop at `D = 5`. Code (3c): above `GRID_MAX_D`, `p_LN^*`'s
> search runs on the plain cloud's mixture, deterministic and on the same draws in every trial,
> and the final `I` comes from the routed marginal. Spec (3b): §4.2's `p_LN^*` paragraph says so,
> replacing its stale clause "above `D_switch`, from AtomicPriors.jl's `mutual` of a weighted
> sample", which OQ-1 and OQ-7 already ruled out. Docs: DD-L1. Routed `[test-gap]` to
> `invoke-red-team-on-tests.md`: T23(b) at `D = 6`.

---

### F7: The curvature cells work only at `2 ≤ D ≤ 4`, and fail instead of refusing outside that range [severity: medium]

**Location**: `src/infomax/qfamily.py:168–197` (`VertexNature.nodes`), `src/infomax/jeffreys.py:86–94`, `src/infomax/pref.py:374–383` (`_cone_pref_with_curvature`); spec §4.2, coverage table.

**Touches**: both

**Concern**: Three things fail, and no document states the limit, although §5.4 varies the knob across the whole `D`-sweep:

- The vertex nature puts 80 nodes on every free axis of every face, so `80^(D−1)` nodes per face before the `ρ` filter: 5.1e5 at `D = 4` and 4.1e7 at `D = 5`. At `D = 5` that is about 5 GB per face, more than the 8 GB laptop can hold, and the run dies instead of refusing.
- With curvature on, `p_J` is a box grid, not the coverage table's "closed form, every D". By `box_grid`'s own sizing it has about 2e6 nodes at `D = 6` and 3e7 at `D = 8`, and above `D = 8` it raises with a stale message about AtomicPriors.jl.
- With curvature on, `build_pref` crashes at `D = 1` (`need at least one array to stack`, measured), where the warp is the identity.

**What would resolve it**: State `2 ≤ D ≤ 4` for the curvature cells in the coverage table and the README, and raise a clear error outside that range. Alternatively, size the vertex quadrature by each axis's Fisher width, as `box_grid` does, and build curvature-on Jeffreys as the closed form outside the ball plus quadrature inside it.

> M: yeah iirc this is about the curvature param that aims to delineate p* and p_proj. seems reasonable to only use it up to 4 dims

> C: To apply the first option (the knob is §3.4's case adversarial to `p_proj` and benign for
> `p*`, as MB recalls). Spec (3b): §4.2's coverage table and §5.4's curvature knob state
> `2 ≤ D ≤ 4` for the curvature cells. Code (3c): `VertexNature`, curvature-on `build_jeffreys` and
> `_cone_pref_with_curvature` raise a clear error outside `2 ≤ D ≤ 4`, replacing the stale
> AtomicPriors.jl message. Docs: the README's coverage statement and the curvature entries.

---

### F8: DD-C2 describes a merge the code does not do [severity: medium]

**Location**: README DD-C2 (lines 247–253), against `src/infomax/pstar.py:263–293` (`merge_atoms`) and `:388–397`; `experiments/002-foreign-q-prediction/run.py:180` (`pstar_n_atoms`).

**Touches**: docs

**Concern**: DD-C2 says that supported candidates within 1 noise unit merge at their mass-weighted centroid, that the weights are re-solved on the merged atoms, and that `C_N` is that prior's information. In the code the prior is the unmerged candidate-set solution and `C_N` is the solver's value. `merge_atoms` merges at 0.75 noise units onto the heaviest member, and nothing calls it. So a reader misreads what `p*` and `C_N` are. Meanwhile `pstar_n_atoms` (§6.3) counts supported candidates: 104 at the cheap cell, against 84 atoms merged at 0.75 and 64 at DD-C2's radius[^10].

**What would resolve it**: Rewrite DD-C2 to match the code: the prior is the candidate-set solution, and merging, at its stated radius, is for reporting only. Define `pstar_n_atoms` as one of the two counts.

> M: merging is vestigial. let's delete it, and redefine everything as non-merged. if we need it later it's in the revision history.

> C: To apply. Code (3c): `pstar.merge_atoms` and the comment pointing to it are deleted; `p*`
> stays the unmerged candidate-set solution, and `run.py`'s `pstar_n_atoms` its supported
> candidates. Spec (3b): §4.2's pseudocode returns the candidate-set solution (no
> `extract_atoms`), and §6.3 defines `pstar_n_atoms` as the number of supported candidates,
> unmerged. Docs: DD-C2 rewritten (no merging, and why: it moved mass by up to a net spacing and
> broke the equalizer by several `1e-2` nats). Spec 000's `atoms.extract_atoms` is untouched.

---

### F9: `mixture.py` misdescribes its own estimator [severity: medium]

**Location**: `src/infomax/mixture.py:12–21` (module docstring), `:297–299` (comment in `SobolKernelTable`).

**Touches**: code

**Concern**: The module docstring says that a span of more than one dimension is integrated with a scrambled Sobol set and antithetic pairs. The default `KernelTable` (DD-K1) instead uses a Gauss–Hermite tensor rule on at most three leading directions, plus an exact second-order term for the rest; Sobol is only the `method="sobol"` reference. This is the estimator behind `C_N`, the equalizer and the capacity gap, and DD-K1 measures the two methods' errors at 3.4e-4 and 2e-3 nats. The comment that dropped directions "move each exponent by under `RES_REL * CUTOFF`" also fails once a state has many neighbours. A dropped component can reach `RES_REL · sv_0`, and `sv_0` grows like the square root of the neighbour count times `CUTOFF`.

**What would resolve it**: State DD-K1's rule in the docstring, and give the comment the bound `RES_REL · sv_0`.

> M: make the edits

> C: To apply. Code comments only (3c): `mixture.py`'s module docstring states DD-K1's rule
> (Gauss–Hermite on the leading one to three directions plus the exact second-order term; Sobol
> only as `method="sobol"`), and the comment at `:297` gives the bound `RES_REL · sv_0`.


## Minor

- m1 — `qfamily.QbarPrior._row_objects`, `.sample` (`qfamily.py:213–233`) — in a nested cone cell `q̄` builds its nested rows on the agent's submodel, with the ignored coordinates pinned at ½ instead of uniform. That moves `log m_q̄` by at most 1.7e-3 nats on average (`φ ∈ {0.5, 0.1}`, `D ∈ {1, 2, 4}`, measured), and `q̄.sample(..., model=<the D_max cone>)` raises a shape error, since own rows have `D` columns and nested rows 26 — build nested rows on the nature's model.
- m2 — `diagnostics.covered_fraction` (`:99–107`), `mass_near` (`:93–96`) — neither takes a nature model, so a nested cone nature is drawn on the agent's submodel, and `p_J` is rebuilt on every call (20–75 s when sampled) — pass `nature_model` and an already built `p_J`.
- m3 — `jeffreys.build_jeffreys` (`:89–94`) [test-gap] — exp-decay `p_J` at `D ≤ 3` uses the direct `slogdet(model.fim)`, not the Newton form that T4's 80-digit test checks. At `D = 3` it is within 1e-3 nats except at a triple near-coincidence (`−inf` where the truth is −39.70) and at (0.999, 0.9995, 0.9999) (9.1e-3 off), both measured — use `sampled._log_sqrt_det_g` there too.
- m4 — README *Testing notes*, "Sampled priors at thin states" (lines 685–691) [spec-implication] — "The scores … use the plain cloud everywhere" and "It fails for both priors until OQ-14 is resolved" are stale: `SampledPrior._lmn` routes, and the test passes. Spec OQ-14 (§7.1) repeats the first — mark both as superseded.
- m5 — `pref.py:6`, `plognormal.py:5–6` — the module docstrings still say "Stubs until the implementation stage." — delete the sentence.
- m6 — `sampled.py:54–59` — the docstring that describes `JEFFREYS_SAMPLED_FROM_D` sits under `JEFFREYS_ANNEAL_BELOW`'s, attached to no constant — move it.
- m7 — README DD-Q1 (line 295) — "0.6 beyond" holds only for `D = 3, 4` (`ARC_CELL_BY_D`); `D = 5` starts at 0.3 and is coarsened to the 2e6-node cap — say so.
- m8 — README DD-Q4 (lines 328, 353–354) — "varies by less than 0.02 nats" is in fact a standard deviation below 0.02 over three rounds, and no warning "when fewer than 20 draws are effective" exists in `sampled.py` — correct both.
- m9 — README DD-SC2 (line 452) — every `CloudPrior` takes the Monte-Carlo branch whatever its size (`score.py:269`), not only large clouds — reword.
- m10 — README DD-E1 (line 461), `worst_case_bias_pressure` — for discrete priors and clouds the 64 and 512 draws are ignored, because DD-K1 is deterministic, so the refinement recomputes the screen's values — say so.
- m11 — README data flow (line 121) — in nested cone cells `m` is `D_max = 26`, not `D` — add that case.
- m12 — README module list (line 25) — `priors002.py` is a fifth module new beyond spec §4.6, and §4.6's edits to `prior.py`, `atoms.py` and `likelihood.py` were not made (they are spec 000's code, unchanged) — state the deviation.
- m13 — `_make_call_graph.py:11–17`, `call_graph_functions.md` — "they were the only false ones" holds for cross-module edges only. The function graph keeps five false self-loops (`DifferenceObjective.cheap_f`, `.f`, `.f_S`, `.f_and_jac`, `KernelTable.__new__`) and lacks the edges `DifferenceObjective → GaussianObjective, BinomialObjective` — say so. Both graphs regenerate edge for edge at 8d933e3 (measured).
- m14 — README DD-A1, `pstar.build_pstar(method="auto")` — `D_switch` is not documented. Exp-decay nets hold 3632, 4634 and 5871 candidates at `D = 3, 4, 5`. At `D = 5` the default path gave `C_N = 3.3250` (direct MC 3.3237 ± 0.0026) in 17 s, while PLAN's tier-2 costing assumes the atomic path's 4–9 minutes. Cone nets hold 4046, 13,347 and 67,033 candidates at `D = 4, 5, 6` (measured), so from about `D = 8` each build would grow a doomed 1e6-point net before falling back [guess] — state `D_switch` per family, and estimate a net's size before growing it.

> M: m1 and m2 are serious findings, nature's nested model should be used everywhere appropriate. this is a definite error to be corrected. The rest of the suggestions should be applied too.

> C: To apply; m1 and m2 treated as one serious finding (MB); m8 amended (MB, chat).
> - m1, m2 — code: `QbarPrior` builds its nested rows on the nature's model, and samples there;
>   `covered_fraction` and `mass_near` take the nature's model and an already built `p_J`; every
>   other place that builds a nature is checked for the same mistake. `nature_prior` raises when
>   given a hypercone nested row on the agent's submodel (`skills/write-implementation.md`, Rule 1).
> - m3 — code: exp-decay `p_J` at `D ≤ 3` uses `sampled._log_sqrt_det_g`. This is on the eye
>   test's path, so 3d's eye-test rerun covers it. Routed `[test-gap]`: T4's 80-digit test on the
>   grid path.
> - m4 — spec (3b): OQ-14's "The scores use the cloud everywhere" marked superseded. Docs: the two
>   stale Testing-notes sentences marked superseded.
> - m5, m6 — code docstrings. m7, m9, m10, m11, m12 — README edits as stated.
> - m8 — code: `build_sampled_jeffreys` warns when its final cloud keeps fewer than 20 effective
>   draws, so DD-Q4's claim becomes true (MB: no silent collapse). Docs: DD-Q4's "varies by less
>   than 0.02 nats" reworded as a standard deviation below 0.02 over three rounds.
> - m13 — helper script: `_make_call_graph.py`'s docstring scopes its claim to cross-module edges
>   and names the false self-loops and missing edges; rerun, `call_graph_functions.md` regenerated.
> - m14 — docs: DD-A1 states `D_switch` per family; code: the net's size is estimated before it is
>   grown, so a doomed net falls back to the atomic path at once. Routed to experiment 002:
>   `PLAN.md`'s tier-2 costing, which assumes the atomic path at `D = 5` (handoff).

## What the implementation gets right

`score_cell` follows §4.4 to the letter: one draw of `θ`, `e1` and `e2` per row, every prior scored on it with its exact mixture, and every difference's error taken from per-draw differences. The cone's closed-form marginals carry the nested cells. The deterministic Gauss–Hermite divergence gives a `C_N` that direct Monte Carlo confirms: 2.6103 against 2.6093 ± 0.0014 at cone `D = 2`. At exp-decay `D = 5`, the default path reaches the atomic path's capacity. Routing a sampled prior's marginal by its likelihood-weighted effective sample size also removes the self-hit in its own world. At exp-decay `D = 4`, the generating atom raises `log m` by only 7e-4 nats on average at the points left on the cloud[^11]. The grid sampler's envelope holds: the largest `f / f_max` is 2.47, against `K = 4`, at `D = 3`. Keep all of these, and the fixed seeds, when fixing.

[^1]: `experiments/002-foreign-q-prediction/output/cost_model/cells/*.json`: PLAN's tier-0 cost measurements at `D = 2, 4` (6 cells, 28 rows). `beyond_cap["p*"]` is true in exp-decay `D = 2` few rates (`R(p*) − C_N = 0.057 ± 0.034`), and in `p*`'s own world in the cone base and nested cells at `D = 2` (0.070 ± 0.031 and 0.069 ± 0.027).
[^2]: `score_cell` with `p*` alone in its own world, at the cone base cell, `D = 2`, `S_q = 500`, over 40 seeds. Direct Monte Carlo puts `I_{p*}` at 2.6093 ± 0.0014, against `C_N = 2.6103`, so the solver is not the cause.
[^3]: `per_state_redundancy(p*, ...)` at 3000 `pstar._random_face_states`, against `capacity_gap`'s 256 uniform states. On the few-rates diagonal the excess stays below 6e-4 at `D = 2`–4, so the few-rates label in [^1] is noise.
[^4]: `solve_capacity` instrumented. Exp-decay `p*` converged in 7 rounds at `D = 3` and 8 at `D = 4`, and `p*_{N/10}` in 1. Cone `D = 4` `p*`: 12 rounds, 2 candidates above `C + 1e-3`, worst +1.19e-3. Cheap-cell `p*_{10N}`: 12 rounds, 15 above, worst +1.43e-3, 221 s. Cone `D = 4` `p_lat`: 12 rounds, bound `[0.54294, 0.54878]`, one NaN `λ` from an entrant with only zero-weight neighbours, 632 s.
[^5]: `candidate_set(model.at_budget(10))`: 15,150, 75,062 and 135,416 candidates at exp-decay `D = 2, 3, 4` (11, 59 and 123 s).
[^6]: `build_sampled_jeffreys(build_model("exp_decay", D, box="matched"))`, against `log mean √det g` over 1e6 uniform ordered draws in the box. `D = 6`: −24.04 ± 0.13 against −30.01 ± 0.004. `D = 7`: −39.43 against −46.95. `D = 4`: −6.911 ± 0.014 against −6.893 ± 0.002. `D = 5`: −16.70 ± 0.03 against −16.71 ± 0.003.
[^7]: `_StiffestField` built on both boxes at `D = 2`, and evaluated at 2000 uniform states of the matched box.
[^8]: At `ξ = (0.97, 0.98, 0.99, 1)`, `per_state_redundancy` gives 27.17. With 600 draws of `x̄`, the routed `log_marginal` gives 27.00 ± 0.10 and the plain cloud 27.28; the paired difference is 0.28 ± 0.03. At (0, 0, 0, 1) and (½, ½, ½, ½) the paired difference is 0.005–0.007.
[^9]: `mutual_information(build_pln(model, 0, τ), model, rng=default_rng(123), n=256)` at `τ = 1` and `τ = 1 + 1e-6`, exp-decay `D = 6`. There, 87 of the objective's 4096 draws (2.1%) are thin.
[^10]: `merge_atoms` on the cheap cell's `build_pstar` result, at `link = 0.75` and `link = 1.0`.
[^11]: Leave-one-out over 500 own-world draws of the sampled `p_J` at exp-decay `D = 4` (1.6% of them thin). The envelope figure comes from 4e5 of `grid_rejection_sample`'s own proposals per `D`; the largest ratio at `D = 2` is 1.68.
