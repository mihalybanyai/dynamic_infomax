# Implementation red-team — spec 000

Reviewer: implementation red-team sub-agent
Date: 2026-05-18
Spec version reviewed against: 1bc185932bdc17d24a4f1550f6844ce11a5a3509
Implementation reviewed: 1105a056cb8c539773df9692b4fb77ac5711fccb

## Summary

The implementation is small, readable, and the math lines up with the spec
where it counts. The weak surface is documentation drift around the BA
parameters and convergence criterion: the spec's stated defaults
(`α = 1.5`, `|ΔI|` criterion) no longer match what the code does
(`α = 2.0`, Csiszár gap), the `eps_i` docstring still describes the
spec-style criterion, and a handful of inline annotations are off by one.
A second class of risk lives at the boundary of the public API: `init=`
is taken on trust (no positivity / normalisation check), and
`GridPrior.__init__` is similarly permissive — a labmate handing in a
sloppy init can land in `log(0)` or in a state that silently violates the
sums-to-1 invariant the protocol promises. The most concrete inefficiency
is that the precomputed likelihood matrix is `exp()`-ed inside
`_f_kl_from_masses` on every BA iteration (and twice per iteration when the
line-search is active), which roughly doubles per-iteration cost at the
spec's headline `tau_max = 500_000` budget. Nothing in the report rises to
"the BA result is wrong"; the findings are about behaviour under inputs
the tests do not exercise, and about doc claims that have aged.

## Findings

### F1: `init=` is taken on trust — no validation of positivity or normalisation [severity: medium]

**Location**: `src/infomax/ba.py:96-104`, `src/infomax/prior.py:55-63`

**Concern**: Spec §3.4 specifies the `init=` argument as "a
strictly-positive probability vector". Neither `blahut_arimoto` nor
`GridPrior.__init__` enforce either condition. An `init` with a zero
entry passes through, `log_p = np.log(p)` produces `-inf` at that
index, and BA proceeds with that cell pinned at zero for the rest of
the run — which is exactly the bug §1.4's "we initialise uniform rather
than e.g. on a random subset" note warns about. An unnormalised `init`
silently changes the meaning of `mi_history[0]` and shifts every later
MI value by `log(Σ init)` until the first `logsumexp` normalisation.
Neither failure is currently caught by any test (the tests only feed in
clean inits), and neither would surface loudly — both produce numbers
that look plausible.

**What would resolve it**: a one-line check in `blahut_arimoto` (and
optionally in `GridPrior.__init__`) that `init` is finite, strictly
positive, and sums to 1 within a small tolerance; raise `ValueError`
otherwise. Mention the contract in the docstring.

**Touches**: code

> M: easy and doesn't modify existing code. should do it.

> C: Adding positivity, finiteness, and normalisation checks to `blahut_arimoto`'s `init` arg (strictly positive + normalised, since user-supplied inits must be valid priors). Adding non-negativity, finiteness, and normalisation checks to `GridPrior.__init__` (non-negative rather than strictly positive — BA legitimately produces `exp(log_p) = 0.0` via float64 underflow for cells far from atoms). Both raise `ValueError`. Updating the `init` arg docstring to state the contract. F10's `GridPrior.__init__` validation is handled jointly here.

---

### F2: `BAResult.n_iters` and the `mi_history` length comment are off-by-one on `tau_max` exhaustion [severity: low]

**Location**: `src/infomax/ba.py:25`, `src/infomax/ba.py:141-148`

**Concern**: The loop is `for tau in range(tau_max + 1)`, so the
exhaustion path actually runs `tau_max + 1` iterations and appends
`tau_max + 1` entries to `history` inside the loop; the `for/else`
branch then appends one more recompute, giving `len(history) ==
tau_max + 2`. `n_iters` is set to `tau_max`, and the field comment on
`mi_history` describes it as `I_τ for τ = 0, 1, …, n_iters` (length
`n_iters + 1`). The two don't reconcile in the exhaustion case. Tests
(T6 monotonicity, T10 self-consistency) pass because they only consume
`history[0]`, `history[-1]`, and pairwise differences, none of which
require the length to match `n_iters + 1`. A future test or report
script that does `assert len(mi_history) == result.n_iters + 1` would
fire spuriously.

**What would resolve it**: either set `n_iters = tau_max + 1` in the
exhaustion branch and tighten the loop bound to `range(tau_max)`, or
drop the extra recompute-append from the `else` and rely on the
trailing iteration that already appended. Either way, update the
field comment to match.

**Touches**: code

> M: certainly don't drop the recompute-append. I'm not sure we want to make any change to the code here, sounds like it would break something. The comment should change though.

> C: Agreed — no code change. Fixing the `mi_history` field comment in `BAResult` to state `len = n_iters+1` normally, `n_iters+2` on `tau_max` exhaustion, cross-referencing DD6. `converged` field comment updated in lockstep to name the Csiszár gap rather than `|ΔI|`.

---

### F3: `np.exp(log_likelihood)` is recomputed on every BA iteration [severity: low]

**Location**: `src/infomax/ba.py:46` (called from `:121` and `:135`)

**Concern**: `_f_kl_from_masses` materialises `P = np.exp(log_likelihood)`
on every call, and the BA loop calls it once for the current prior and
again for the trial prior in the line-search recheck. With
`tau_max = 500_000`, `N_θ = 1000`, `n_x ≤ 101` that is up to ~10⁶
allocations and `exp` evaluations of a `(1000, 101)` matrix even though
`log_likelihood` is fixed for the lifetime of the call. On the
laptop-runtime envelope §0 calls out and the codegen log records
(Run 3 already at 8 min/run with α=1, faster but not by orders of
magnitude with α=2), this is the single largest constant factor
sitting on the BA hot path. Not a correctness issue and not a
showstopper at the current scale; flagging because spec 000 explicitly
sets `tau_max = 500_000` as a default and spec 001/002 are expected to
inherit this loop.

**What would resolve it**: precompute `P = np.exp(log_likelihood)` once
inside `blahut_arimoto` and pass it into `_f_kl_from_masses` alongside
`log_likelihood`; or cache it on a closure. Keep the public
`compute_f_kl` signature.

**Touches**: code

> M: this seems like a major performance sink. We should certainly change it according to the suggestion if you don't think it will break something.

> C: Won't break anything — purely internal. Precomputing `P = np.exp(log_likelihood)` once in `blahut_arimoto` and threading it into `_f_kl_from_masses` as a third parameter. Private signature change only; public `compute_f_kl` interface unchanged (it computes P before the single call).

---

### F4: spec default `α = 1.5` no longer matches code default `α = 2.0` [severity: medium] [tag: spec-implication]

**Location**: `src/infomax/ba.py:59`, vs spec §3.4 line 354 and the
data-flow caption in `docs/000-static-infomax-fig1/README.md` line 44

**Concern**: Spec §3.4 states "Defaults: `α = 1.5`, …". The implementation
defaults to `alpha: float = 2.0`. The codegen log (Run 3, 2026-05-18)
records a deliberate choice of `α = 2` after empirical testing, and the
T4 caption in the README mentions `α = 2`, but the spec text was never
updated. A reader who treats the spec as the source of truth for
default parameters will be wrong; a reader who reads the README's
design-decisions section will not even see this choice listed (no DD
entry pins the α default). The spec is marked `reviewed` at §3.4, so
the divergence currently has no in-band owner.

**What would resolve it**: pick one — either change the code default to
`1.5`, or amend spec §3.4 to read `α = 2` and add a DD entry in the
README pointing at Run 3 in the codegen log. The README data-flow
prose already implies α > 1; one of the two has to give.

**Touches**: both

> M: this sounds like the thing to update is the spec. 

> C: Updating spec §3.4 defaults line from `α = 1.5` to `α = 2.0` (changed text marked red), adding a revision log entry dated 2026-05-19, and flipping §3 status to `draft`. DD8 added to README (see F6 below).

---

### F5: `eps_i` docstring describes the spec criterion, not the implemented Csiszár-gap criterion [severity: low]

**Location**: `src/infomax/ba.py:83`

**Concern**: The docstring reads
`eps_i: convergence tolerance on |I_{tau+1} - I_tau| in nats.` The
actual check (line 124) is `csiszar_gap = max(f_kl) - mi < eps_i`,
which DD3 in the README explicitly flags as a deliberate departure
from the spec. A caller reading the docstring will set `eps_i` against
the wrong mental model — Csiszár's gap is tighter than `|ΔI|`, so a
tolerance set "for `|ΔI|`" will over-tighten convergence and waste
iterations (or under-tighten and over-converge, depending on which
direction the caller errs). The inline comment immediately below the
docstring contradicts the docstring, which is the worst of both
worlds.

**What would resolve it**: rewrite the `eps_i` parameter docstring to
describe Csiszár's gap, and cross-reference DD3 in the README.

**Touches**: code (docstring)

> M: yes update the docstring

> C: Rewriting the `eps_i` parameter docstring in `blahut_arimoto` to describe the Csiszár gap criterion and cross-reference DD3. Also updating the `eps_i` line in the Args section to add the default value (F11 covers all kwarg defaults jointly).

---

### F6: README design decisions list does not document the `α = 2.0` choice [severity: low]

**Location**: `docs/000-static-infomax-fig1/README.md` §"Design decisions"
(DD1–DD7)

**Concern**: The list is the canonical place for "the implementation
made a choice the spec didn't pin down" (DD3 is exactly such a case,
for the convergence criterion). The α default disagrees with the spec
in the same way and for similar reasons (empirical convergence
behaviour from Run 3 in the codegen log), but there is no DD entry for
it. A future maintainer reconciling spec ↔ code on parameters will
notice DD3 and assume α has not been similarly overridden.

**What would resolve it**: add a `DD8 — Default α = 2.0 (overrelaxation)`
entry citing the Run 3 trial and the line-search fallback. Pairs with
F4.

**Touches**: docs

> M: add this

> C: Adding DD8 — "Default α = 2.0 (overrelaxation)" — to the README design decisions list, citing Run 3 in the codegen log and the line-search fallback. Paired with the spec update in F4.

---

### F7: README design decisions claim `mi_history` is `I_τ` per iteration; on exhaustion it has one extra entry [severity: low]

**Location**: `docs/000-static-infomax-fig1/README.md` DD4 (lines 132-138);
related to F2

**Concern**: DD4 says `mi_history` is "the inner-loop snapshot of `I_τ`
per iteration". DD6 then says the exhaustion branch *appends an extra
`history` entry* for the advanced prior so that `history[-1] ==
result.mi`. Both are true, but DD4 reads as if `len(mi_history) ==
n_iters + 1` always — which it isn't on the exhaustion path. T6's
endpoint-pin test is robust to this, but the doc claim and the inline
field comment are in tension.

**What would resolve it**: amend DD4 to say "with one extra entry
appended in the `tau_max`-exhaustion branch (see DD6)". Fix the inline
field comment in `BAResult` in lockstep.

**Touches**: docs (and the inline field comment in `ba.py`)

> M: make the doc and comment consistent with what the code does

> C: Amending DD4 in README to note the extra `mi_history` entry on `tau_max` exhaustion (cross-referencing DD6). `BAResult.mi_history` field comment fixed in lockstep (covered under F2 above).

---

### F8: call graph omits `atoms.extract_atoms` and `atoms.count_support` entirely [severity: low]

**Location**: `docs/000-static-infomax-fig1/README.md` §"Call graph"
mermaid block (lines 22-42)

**Concern**: The mermaid call graph shows three subgraphs (`ba`,
`likelihood`, `prior`) but no `atoms` subgraph, even though
`extract_atoms` and `count_support` are the canonical post-BA
consumers and are referenced in the testing notes and §3.5 of the
spec. They take a `GridPrior` and call `prior.support()` /
`prior.masses()`, so code2flow won't trace those instance-method
edges (the doc already disclaims that), but the *nodes* themselves
exist as free functions and would normally appear regardless. A
labmate reading the call graph cold would conclude `atoms.py` is
dead code or not part of the spec-000 surface.

**What would resolve it**: re-run `_make_call_graph.py` with `atoms` in
scope (or manually add a stub `atoms` subgraph if code2flow drops
isolated nodes), and add a one-line note that nodes with no
intra-package edges still appear.

**Touches**: docs

> M: yeah the call graph was kinda fishy, I waved it through as a placeholder mostly, but I shouldn't have, it should have real information. Let's try to make it more complete

> C: Extending `_make_call_graph.py` with an AST-based symbol-discovery pass: modules that code2flow produces zero nodes for (like `atoms.py`, whose functions have only instance-method calls to `prior.support()`/`prior.masses()`) still appear as subgraphs with their public top-level functions as nodes. Adding a note to the README call-graph preamble about this. Regenerating the call graph block after both this change and the F9 removal of `GridPrior.updated`.

---

### F9: `GridPrior.updated` is part of the documented `Prior` protocol but the BA loop never calls it [severity: low]

**Location**: `src/infomax/prior.py:81-91`, `src/infomax/ba.py:120-140`

**Concern**: Spec §3.3 frames `Prior.updated()` as the one MI-improvement
step that the BA loop drives. The implementation instead inlines the
update inside `blahut_arimoto` (which constructs `GridPrior` from raw
`p` at return time) and `GridPrior.updated` is unused. The call graph
shows `GridPrior.updated → GridPrior.__init__` as a dangling edge.
This is not strictly wrong — the BA loop needs to do its own
log-space arithmetic and history bookkeeping that the abstract
`updated()` cannot express — but it means the prior-as-abstraction
story the spec tells is presently aspirational: the abstraction is
declared, not exercised. A future `AtomicPrior` plugging in by
implementing `updated()` will not actually plug into anything because
nothing calls it. The README's data-flow diagram does not show the
`updated()` edge either, so the doc is at least internally
consistent — but the gap between "spec architecture" and "code
architecture" is undocumented.

**What would resolve it**: either delete `GridPrior.updated` until
something calls it (with a note in the README that the BA loop owns
the update for `GridPrior` and the protocol is currently advisory),
or refactor `blahut_arimoto` to drive iteration via `prior.updated()`
and a `log_likelihood_fn` closure. Calling this low because the spec
explicitly defers the multi-prior plumbing to later specs; flagging
because the discrepancy is invisible to anyone reading the docs.

**Touches**: both

> M: this has the potential to bite into asses later. Can the specified prior abstraction be saved so that future implementation can plug into it coherently? If not, we should just remove the updated() function, and at least be clear about that having to happen in the BA loop instead

> C: Cannot be saved for `GridPrior` cheaply — the BA loop requires direct access to `log_p` arrays, line-search state, and history bookkeeping that do not fit through the `updated()` callable interface. Removing `updated()` from both the `Prior` protocol and `GridPrior`. Updating the `prior.py` module docstring to note that the BA update is owned by `blahut_arimoto`; `updated()` is reserved for future prior types (e.g. `AtomicPrior`) where the update step is self-contained and pluggable. Adding a note to the README that the `Prior` protocol no longer declares `updated()` and explaining the architectural reason.

---

### F10: `GridPrior.__init__` does not enforce the documented "sums to 1" invariant [severity: low]

**Location**: `src/infomax/prior.py:55-63`

**Concern**: The `Prior.masses()` docstring says "Probability masses,
summing to 1, aligned with `support()`." `GridPrior.__init__` only
checks shape compatibility — not non-negativity, not sums-to-1.
`extract_atoms` and the report scripts trust this invariant. The
invariant is currently maintained by construction (BA returns
normalised `exp(log_p)`), so this is latent rather than active, but
the gap means any future caller building a `GridPrior` by hand
(including future test fixtures and the `AtomicPrior` work) can
violate it silently. Flagged low because no current path triggers
it; flagged at all because the protocol promise is load-bearing for
downstream consumers.

**What would resolve it**: add a normalisation / positivity check in
`__init__`, gated by a `validate: bool = True` kwarg if perf is a
concern (it isn't, at `N_θ ≤ 10000`).

**Touches**: code

> M: this check should be added

> C: Handled jointly with F1 — positivity and normalisation validation added to `GridPrior.__init__`.

---

### F11: Default `α` is not documented in the BA docstring's "Args" section [severity: low]

**Location**: `src/infomax/ba.py:73-86`

**Concern**: The docstring lists each kwarg with its semantic but does
not state the default value of `alpha` (or, for that matter, of any
other kwarg). Combined with F4's spec-vs-code drift on this value, a
reader who lands on `blahut_arimoto` without the README open has no
way to know what `α` is being used. Trivially fixable by listing
defaults in the docstring (e.g. `alpha: overrelaxation step-size
(default 2.0) per spec §3.4.`).

**What would resolve it**: list the default for each kwarg in the
docstring, especially `alpha`, `tau_max`, and `eps_i`.

**Touches**: code (docstring)

> M: add this to the docstring

> C: Adding default values to all kwarg entries in the `blahut_arimoto` docstring Args section (`alpha`, `eps_i`, `tau_min`, `tau_max`).

---

## What the implementation gets right

The BA loop is in log-space where it needs to be, the line-search
fallback to α=1 is implemented exactly as the spec describes (it is
the single thing that keeps T6 sound under α>1), and the exhaustion
branch (DD6) is one of the more thoughtful pieces of the file —
without it the returned `BAResult` would silently fail T10. The
likelihood routes through `scipy.stats.binom.logpmf` (DD1) so T11 is
trivially tight. The `_f_kl_from_masses` arithmetic matches the
spec's per-iteration formulas line-for-line, which is what makes
T10's 1e-12 self-consistency check achievable. The atom-extraction
heuristic is short, edge-correct (pad-and-diff handles the
endpoints), and isolated from the `count_support` path that T3
consumes. None of the math is wrong.
