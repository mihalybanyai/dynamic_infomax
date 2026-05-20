# Result red-team — spec 000

Reviewer: result red-team sub-agent
Date: 2026-05-19
Spec version reviewed: 447bbee
Report reviewed: experiments/000-static-fig1/REPORT.md
Code reviewed: experiments/000-static-fig1/run.py

## Summary

Broadly healthy: the experiment driver is short, the JSON dumps line up
with the report's headline table, and the figures faithfully visualise
what the spec asks for. The dominant kind of finding is reporting /
presentational, not bugs: the figure panels do not match the panel
m-values of the paper they claim to sit "side-by-side" with, the
within-panel y-axis units mix nats (axis ticks) with bits (title and
text), and several spec items (the grid-refinement re-runs at
`N_θ ∈ {200, 500, 2000}` from §3.1, the test-results headline for T3,
T3b, T8, T9, T10, T11) are not surfaced in the report. There is one
genuine code-level inefficiency (KS computation in a Python for-loop
over the 4001-point query, and recomputed a second time in the m=100
figure) — measurable but not load-bearing at the current sweep.
No category was empty in the end, though there are no high-severity
arithmetic bugs.

## Findings

### F1: Reproduction panel m-values do not match Mattingly Fig 1's panels [severity: medium] [paper-inconsistency] [doc-inaccuracy]

**Location**: `experiments/000-static-fig1/run.py:46` (`PANELS_M = (1, 5, 20, 100)`); `REPORT.md` §1 ("Our version (four representative panels plus the analytic m → ∞ Jeffreys density) sits side-by-side with the paper's original below.")

**Concern**: Mattingly Fig 1 displays panels at m = 1, 10, 100, and m → ∞ (verified by reading `figures/mattingly_fig1.png`). Our reproduction shows m = 1, 5, 20, 100, plus m → ∞. The report explicitly puts the two figures side-by-side and tells the reader the panels match the paper, but they do not: m = 10 (the middle panel of the paper, with 5 atoms and the visible mid-shoulder f_KL shape) is absent from our panels figure, while m = 5 and m = 20 in our reproduction have no counterpart in the paper. A lab-meeting attendee scanning the two figures will look for the m = 10 comparison and not find it. The full m = 10 result is in `results_table.json` (K = 5, MI* = 1.76 bits), so this is a panel-selection bug, not a data bug.

**What would resolve it**: Either set `PANELS_M = (1, 10, 100)` so the panels actually align with the paper (preferred — the m → ∞ analytic panel then closes the 2×2), or rewrite the §1 prose to say "a representative subset of our sweep" and stop claiming side-by-side correspondence.

**Touches**: both

> M: I actually like that the reproduction is not 1-to-1. it makes it more obvious that the implementation is general. so leave this as is

---

### F2: f_KL right-axis units (nats) inconsistent with title's MI* (bits) within each panel [severity: medium] [doc-inaccuracy]

**Location**: `experiments/000-static-fig1/run.py:139–146` (`make_panels_figure`)

**Concern**: Each Fig 1 panel labels the right axis `f_KL(θ)` (nats — that is what `compute_f_kl` returns) and draws a horizontal dashed line at `mi` in nats. The panel title is "$m = {m}$ ($K = {K}$, $MI^* = {mi_bits:.3f}$ bits)" — bits. So the dashed line at ~0.69 for m=1 and the title saying "MI* = 0.994 bits" appear inconsistent unless the reader recognises the right axis is nats. The KKT condition "f_KL = MI* on support" — the very thing the figure is meant to illustrate — therefore looks broken at a glance. A reader who trusts the title's units number will not be able to verify the diagnostic visually.

**What would resolve it**: Either plot `f_kl / log(2)` and the dashed line at `mi / log(2)` so the axis matches the title, or relabel the right axis "$f_{KL}(θ)$ (nats)" and add a parenthetical to the title like "$MI^* = 0.994$ bits = $0.689$ nats". The former is cleaner.

**Touches**: code

> M: it seems to me that we could just have every informational quantity in nats, and this ivolves just changing labels. true?

---

### F3: KS query for the atom step CDF is computed in a Python for-loop (and twice) [severity: low] [perf]

**Location**: `experiments/000-static-fig1/run.py:73–74` and again at `run.py:172–175`

**Concern**: The atom step CDF on the 4001-point query grid is built with `for i, q in enumerate(query): atom_cdf_query[i] = atom_masses_sorted[atom_thetas_sorted <= q].sum()` — O(K · 4001) work, in Python, and redone inside `make_m100_cdf_figure`. The natural vectorised form is `atom_cdf_query = np.cumsum(atom_masses_sorted)[np.searchsorted(atom_thetas_sorted, query, side='right') - 1]` with a zero fallback for the empty prefix. Not load-bearing at the current sweep (9 m-values × K ≤ 13), but it scales with K and the query length and is duplicated work; the report's narrative about "the discreteness floor" relies on this CDF being right, so we want the code that produces it readable.

**What would resolve it**: Replace the for-loop with `np.searchsorted` + `np.cumsum`. Factor the KS computation into a single helper used by both `run_one` and `make_m100_cdf_figure`.

**Touches**: code

> M: not sure if this a genuine perf issue, as this is just the experiment code. If it saves less than 10s wall clock time in this experiment, leave it

---

### F4: m=1 atom-CDF KS-to-Jeffreys value (0.486) is reported as a data point but never explained [severity: low] [doc-omission]

**Location**: `REPORT.md` §3 (KS-vs-m figure narrative); `results_table.json` row m=1 (`ks_to_jeffreys = 0.4858`)

**Concern**: The KS-vs-m plot shows the m=1 KS at 0.486, almost twice the discreteness floor for K=2 (`1/(2·2) = 0.25`). That's the right behaviour — two boundary atoms cannot approximate the Jeffreys CDF, whose mass is mostly in (0, 0.05) ∪ (0.95, 1). But the report's narrative ("Both shrink monotonically with m, but neither is fully eliminated…") implies the gap is just BA-convergence slack at all m. At m=1 the gap is structural: BA has converged exactly to the closed-form ½/½ optimum (T1 passes), and 0.486 ≈ F_J(0.0005)^c + F_J(0.0005) bounding gives the true KS distance from the two-atom prior to the continuous Jeffreys. A reader scanning the curve might infer "BA hasn't converged at m=1 either", which is the opposite of what the table tells them. One sentence in §3 to acknowledge that the m=1 (and small-m) KS values reflect the fundamental finite-K shortfall, not BA-residual, would close this.

**What would resolve it**: One added sentence in §3 contrasting m=1 (BA converged, KS reflects K=2 being far from the continuum) with m=100 (BA not at strict-tolerance convergence, KS reflects super-atom + positioning).

**Touches**: docs

> M: add the explanation

---

### F5: Grid-refinement re-runs at N_θ ∈ {200, 500, 2000} (spec §3.1) are not run by the driver [severity: low] [doc-omission] [spec-implication]

**Location**: `experiments/000-static-fig1/run.py:41` (`N_THETA = 1000` only); spec §3.1 ("We also re-run at `N_θ ∈ {200, 500, 2000}` to check that the qualitative results are stable under grid refinement (Mattingly's Fig 2 makes the same check).")

**Concern**: The spec calls for the experiment driver to re-run the sweep at three additional grid resolutions and report stability. The driver runs only N_θ = 1000. Grid invariance *is* exercised in the test suite (T5, at N_θ ∈ {200, 1000, 2000} for m ∈ {2, 5, 10}), so the property is checked — but the report should either show the multi-grid figure or explicitly note that the spec's §3.1 multi-grid re-run is delegated to T5 rather than reproduced in the experiment artefacts. The report claims "the script sweeps `m ∈ {…}` at `N_θ = 1000`" and stops; a labmate cold-reading will not know the §3.1 check happened anywhere.

**What would resolve it**: Add one line under §1 or §4 of the report ("Grid-refinement check (spec §3.1) is exercised by test T5 at N_θ ∈ {200, 1000, 2000}; see CODEGEN_LOG Run 4"), or actually run the multi-grid sweep in `run.py` and add the figure.

**Touches**: both

> M: yeah just make a note of this in the report and that's it

---

### F6: Headline test results in §5 list only T1, T2, T4, T5, T6, T7 — six of twelve [severity: low] [doc-omission]

**Location**: `REPORT.md` §5 ("Test results")

**Concern**: The spec's §5 item 5 says "Test results: pass/fail status of T1–T7 with the numerical tolerances actually achieved." Since the spec was revised that list has grown to T1–T11 (plus T2b, T2c, T3b, T4b, T7b, T8, T9, T10, T11). The report headlines only T1, T2, T4, T5, T6, T7 — T3 (capacity bound), T3b (output-alphabet bound), T8 (reflection symmetry), T9 (continuum scaling), T10 (MI/f_KL self-consistency), and T11 (likelihood vs. scipy) are not mentioned, despite being the substantive defences added in the test red-team. The line "All 53 tests in tests/test_000_static_infomax_fig1.py pass" covers them, but the spec asked for *headline tolerances*. T10 in particular is the load-bearing self-consistency check the report's "MI* is reliable" claim leans on; it should be cited.

**What would resolve it**: Add rows to §5 for T3/T3b (capacity bounds at every m, tolerance), T8 (symmetry tolerance achieved), T10 (MI/f_KL self-consistency tolerance achieved). T9 and T11 can be one line each.

**Touches**: docs

> M: we don't actually need to recapitualte the test suite in the report. so only the ones that have very direct relevance to something here should be mentioned. do you think the existing section should be modified in either positive or negative direction in this light?

---

### F7: Report's "csiszar_gap" column in §4 table is taken from `compute_f_kl(result.prior, log_lik)`, not from BA's own convergence test [severity: low] [doc-inaccuracy]

**Location**: `experiments/000-static-fig1/run.py:59,83` (`f_kl = compute_f_kl(result.prior, log_lik); … "csiszar_gap": float(np.max(f_kl) - result.mi)`); `REPORT.md` §4 table column "Csiszár gap"

**Concern**: The value reported in `results_table.json` (e.g. 4.94e-07 at m=100) is a post-hoc Csiszár gap recomputed from the returned prior, not the gap at the last BA iteration. For the spec's purposes these should agree to within float64 slack — but the BA loop's `converged` flag (`csiszar_gap < eps_i = 1e-12` per ba.py:137) and the reported gap (5e-7) are six orders of magnitude apart at m ≥ 2. The report tries to resolve this by saying "the gap *did* fall to ~5e-7" — but this number is the recomputed-from-prior gap, not the gap BA itself was tracking. If `compute_f_kl` and BA's internal f_KL ever drift (e.g. a refactor changes `log_p_x` from `logsumexp(log_lik + log_p)` to something subtly different), the report's gap and BA's convergence test would diverge silently. The fact that `converged=False` while csiszar_gap=5e-7 is presented as evidence of correctness, not as the curiosity it is — they are answering slightly different questions.

**What would resolve it**: Either pull the gap from BA's last iteration (return it as a field on `BAResult`), or add a note in §4 clarifying that the table's "Csiszár gap" is independently recomputed from the returned prior and that this gap agreeing with BA's internal gap is itself a self-consistency check (in spirit, T10). One sentence.

**Touches**: both

> M: clarify this in the doc

---

### F8: m=1 row in the §4 table has K=2 but the report's panel commentary says "two atoms at the grid boundary, masses 0.5 each" — actually masses are 0.49999999992816 each [severity: low] [doc-omission]

**Location**: `REPORT.md` §1 ("masses 0.5 each"); `results_table.json` m=1 row

**Concern**: A minor but verifiable mismatch. The achieved masses are 0.4999999999281627 each, differing from 0.5 by 7.2e-11. Within the T1 tolerance (1e-6) — fine — but the prose says "masses 0.5 each" as if exact. A careful reader who opens results_table.json will see the discrepancy and wonder whether the boundary mass leaked or the BA stalled. Mentioning "to 1e-10" or quoting the achieved tolerance would close the gap; the report already does this for the KS distance and the Csiszár gap.

**What would resolve it**: Either round-trip the prose ("masses ≈ 0.5 each, within 1e-10") or leave it but reference the T1 tolerance in §5 as the formal claim.

**Touches**: docs

> M: dude c'mon. Ok, let's make note of the approximate equality using the curly equation sign

---

### F9: `run.py` ignores `result.mi_history` so the report has no monotonicity trace [severity: low] [doc-omission]

**Location**: `experiments/000-static-fig1/run.py` (no use of `mi_history`)

**Concern**: Not strictly a spec violation (§5 doesn't itemise a monotonicity figure), but the report's T6 line ("BA monotonicity holds at every step") is asserted without a single visible iterate. The codegen log presumably has it; the report does not. For a lab-meeting audience this is the one figure that visually confirms BA is doing its thing, and it costs ~10 lines to produce. Optional; flagging because it is "in the spirit of" §5 even if not literally enumerated.

**What would resolve it**: Add one small figure plotting `mi_history` for m=100 (or all m, log-x), even if just embedded in §5 or §6.

**Touches**: both

> M: good idea, let's do this

---

### F10: `K_upper` (T3) and `K` (extracted) are not both reported, so the report's K column is the extractor's K only [severity: low] [doc-omission]

**Location**: `REPORT.md` §4 (K column); spec §4 T3

**Concern**: The spec carefully decoupled the capacity bound (T3) from the §3.5 atom-extraction heuristic by introducing `K_upper = #{p*_i > 1e-12}`. The report's K column is the extractor's K, which is the right thing for the figure but is *not* what bounds MI*. At m=100, K=13 and `MI* = 3.07 bits = 2.13 nats`; `log(13) = 2.56 nats` so the bound holds with slack. But a curious reader who reads the spec first and then asks "where is K_upper and does the bound hold?" will not find K_upper in the dumps. Including it as a column (cheap, one np.sum) would close the gap and make the §4 table self-contained against the spec's tightest claim.

**What would resolve it**: Add a `K_upper` column to `results_table.json` and the §4 table; cite it once in §5 alongside T3.

**Touches**: both

> M: let's include this

---

### F11: KS computation uses `query = np.linspace(0.0, 1.0, 4001)` but a step CDF's worst case is achieved between jump points; sampling at fixed query points underestimates KS [severity: low] [latent-risk]

**Location**: `experiments/000-static-fig1/run.py:71` (`query = np.linspace(0.0, 1.0, 4001)`)

**Concern**: The spec T4 mandates "a dense θ-grid (10⁴ points)" precisely because the worst case of a step CDF against a smooth one sits between jumps. 4001 ≈ 4 × 10³ is a quarter of the spec's recommended density. At the m=100 atom spacing (smallest gap between two adjacent atoms is ~0.026 between the m=100 super-atom-flank atoms), the query grid resolves each gap with ~100 points, which is fine for now. As the experiment is extended (smaller atom spacings at larger m, or to `AtomicPrior` later), `n=4001` will start to *miss* the worst-case midpoint between adjacent atoms whose spacing approaches `1/4000`. Cheap fix; flagging because the spec asked for 10⁴ explicitly.

**What would resolve it**: `query = np.linspace(0.0, 1.0, 10001)`. Or, better: union the query grid with the set of atom centroids ± a small epsilon, so the maximum gap is sampled exactly.

**Touches**: code

> M: how much of a computational burden would this be? in either case there shouldn't be a mismatch between the spec and the code

---

### F12: `n` shadowing / off-by-one risk in `make_panels_figure` for `n_panels = len(panel_ms) + 1` vs. axes flattening [severity: low] [latent-risk]

**Location**: `experiments/000-static-fig1/run.py:112–162`

**Concern**: With `PANELS_M = (1, 5, 20, 100)` we get `n = 5`, `cols = 3`, `rows = 2`, six axes flattened, one hidden. If a future caller sets `PANELS_M = (1, 10, 100)` (e.g. fixing F1), `n = 4`, `cols = 3`, `rows = 2`, two axes hidden — fine. But if `PANELS_M` is set to a length-divisible-by-`cols` value like `(1, 2, 5, 10, 20)`, then `n = 6`, `rows = 2`, exactly 6 axes; the unused-axes loop `axes[n:]` is empty and works. So no current bug — but `axes = np.atleast_2d(axes).ravel()` only does the right thing when `rows >= 2`. With `rows == 1` (`PANELS_M = (1, 100)`, n=3, cols=3), `axes` from `plt.subplots(1, 3)` is 1-D, `np.atleast_2d` then makes it a (1, 3) row, `.ravel()` gives length 3 — works, but the path is implicit. A labmate setting `PANELS_M = (1,)` plus the Jeffreys panel (n=2, cols=3, rows=1) would still get `axes` of length 3, two hidden — also fine. So no actual bug; just brittle. Flagging because the spec leaves `PANELS_M` open for future revision and the failure mode (silent zip-truncation if `len(panel_ms) > rows*cols`) would not raise.

**What would resolve it**: `assert len(panel_ms) + 1 <= rows * cols` after the geometry is decided, or compute geometry as `cols = min(3, n); rows = int(np.ceil(n / cols))`.

**Touches**: code

> M: this is patently unreadable for me. does it has something to do with plot panel layouts?

---

### F13: §1 panel commentary for m=1 says "f_KL(θ) is U-shaped, equal to MI* = 1 bit exactly at the two atom locations" — the achieved MI* is 0.994 bits, not 1 bit [severity: low] [doc-inaccuracy]

**Location**: `REPORT.md` §1 first bullet ("`MI* = 1 bit`")

**Concern**: The continuum optimum is `log 2` nats = 1 bit, achieved by `½δ(0) + ½δ(1)`. Our cell-centred grid achieves `MI_ref(1000) = log 2 − H(1/2000) ≈ 0.68885 nats = 0.99380 bits`, exactly as the table reports. The §1 bullet states `MI* = 1 bit` flatly, with no caveat. The DC-1 caveat is referenced in §6, but inside the m=1 bullet itself a reader sees "MI* = 1 bit" next to a panel labelled "MI* = 0.994 bits" and is left to reconcile. Minor; one parenthetical fixes it.

**What would resolve it**: Replace "equal to `MI* = 1 bit` exactly" with "equal to `MI*` (0.994 bits on the cell-centred grid; the continuum optimum is 1 bit — see DC-1)".

**Touches**: docs

> M: yes, let's differentiate between the cell-centered and continuum options explicitly in text, and fix the lables

---

### F14: Status header references commit `1f8339e` but the current HEAD is `447bbee` [severity: low] [doc-inaccuracy]

**Location**: `REPORT.md` header and §5 and §7 ("based on the test-suite-passing implementation at commit `1f8339e`")

**Concern**: HEAD is at `447bbee` ("first experiment report generated"), and the report was generated by that commit. The hash `1f8339e` is from an earlier implementation-pass commit. If a labmate `git checkout 1f8339e`, they will not see the experiment driver (it was added in 447bbee). The hash should either point to the commit that *generated* the report, or be removed in favour of "current HEAD". This becomes more confusing once the report is re-generated again; the next regeneration should update the hash.

**What would resolve it**: Update the hash to `447bbee` (or generalise the wording to "the current HEAD" with a `git rev-parse HEAD` footnote). Better: have `run.py` write the current commit into `results_table.json`'s metadata and have the report read it.

**Touches**: docs

> M: ok so usually there will be legitimately multiple commits between the last test-passing code and the report. I don't think this is much of an issue, the commit hash is to identify the version of _the code_ that was used, regardless of version changes in any other file. what do you think would be the most informative?

---

## What the experiment + report get right

The driver is short, single-file, and the JSON dumps are the source of
truth for the report's numbers — every figure cited in the table (K,
MI*, KS, Csiszár gap) is traceable back to `results_table.json`. The
qualitative reproduction of Mattingly's headline features (boundary
atoms at m=1, growing K, U-shaped envelope at m=100) is visible in our
panels and the report calls out the super-atom shortfall honestly
rather than papering over it. The KS-vs-m curve plus discreteness
floor is exactly the convergence diagnostic the spec asks for in §5
item 3, and the m=100 atom-CDF-vs-Jeffreys overlay matches the spec's
§5 item 2. The notes section flags DC-1 and DC-2 caveats and the
deliberate scope limit ("what we deliberately did not do"), which is
the load-bearing context the lab-meeting audience needs.
