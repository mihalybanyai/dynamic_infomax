# Handoff — 2026-05-19

## Where we left off

The implementation red-team report (`docs/000-static-infomax-fig1/redteam-impl.md`)
has been fully processed. All 11 findings are annotated with `> M:` (your
responses) and `> C:` (what was done). Changes have been applied across
code, spec, and docs; the test suite is re-passing with 85 tests.

## Changes made this session

### redteam-impl.md
All 11 findings annotated with `> C:` notes directly under the `> M:` responses.
One nuance captured there: the F10 `GridPrior.__init__` check uses non-negative
(not strictly positive) because BA legitimately produces `exp(log_p) = 0.0` via
float64 underflow for cells far from atoms.

### src/infomax/ba.py
- **F1**: `init` validation added (strict positivity, finiteness, normalisation to 1±1e-8). Raises `ValueError`.
- **F2/F7**: `BAResult.mi_history` field comment updated (len = n_iters+1 normally, n_iters+2 on exhaustion). `converged` comment updated to name Csiszár gap.
- **F3**: `P = np.exp(log_likelihood)` precomputed once in `blahut_arimoto`, threaded into `_f_kl_from_masses` as third parameter. `compute_f_kl` computes P before its single call. Private API change only.
- **F5/F11**: `eps_i` docstring rewritten to describe Csiszár gap and cross-reference DD3. All kwarg defaults added to Args section.

### src/infomax/prior.py
- **F1/F10**: `GridPrior.__init__` validates non-negativity, finiteness, and normalisation (sum within 1e-8 of 1). Non-negative (not strict) because underflowed cells are legitimately 0.
- **F9**: `updated()` removed from both `Prior` protocol and `GridPrior`. Unused `FKLFn` type alias and `logsumexp` import removed. Module docstring updated to explain the architectural reason and reserve `updated()` for future self-contained prior types.

### specs/000-static-infomax-fig1.md
- **F4**: §3.4 defaults line updated from `α = 1.5` to `α = 2.0` (changed text marked red). Revision log entry added (2026-05-19). §3 status flipped to `draft`.

### docs/000-static-infomax-fig1/README.md
- **F4/F6**: DD8 added — "Default α = 2.0 (overrelaxation)", citing Run 3.
- **F7**: DD4 updated to note `mi_history` length is n_iters+2 on exhaustion.
- **F8**: Call graph preamble updated to mention AST supplementary pass.
- **F9**: DD9 added — documents that `Prior.updated()` is not declared and the BA update is owned by `blahut_arimoto`, with the architectural reason.
- Call graph mermaid block regenerated: atoms and jeffreys subgraphs now appear (AST pass), dangling `GridPrior.updated` edge removed.

### docs/000-static-infomax-fig1/_make_call_graph.py
- **F8**: Added `_ast_top_level_functions()` helper (AST-based), added `ast` and `hashlib` imports, and an AST merge step in `main()` that adds subgraphs for any module with zero code2flow nodes.

## Open threads

- **Implementation red-team skill extraction** is still pending. The shape
  that worked: `> C:` notes directly under `> M:` in the report; one-by-one
  resolution in chat for uncertain items before writing `> C:`; nuance
  captured inline in the `> C:` note (e.g. non-negative vs strictly positive).
  Extract to `skills/red-team-implementation.md`.
- **Implementation-test workflow formalisation.** This is now the third
  red-team instance (spec, tests, implementation). The three-step
  decide/update-upstream/regenerate-downstream shape holds for all three.
  Check `meta/workflow-issues.md` for the entry on this; it's the moment
  to consider abstracting the shape into a shared primitive.
- **Post-mortem for spec 000.** First end-to-end pass complete. Worth a
  short entry in `meta/what-worked.md`. Candidates: the eye test gate
  was effective; `> M?:` was not triggered (no math gaps, which is a
  finding in itself); the doc red-team found real issues the doc author
  missed (F4, F6, F7, F8 all doc findings that landed changes).
- Per-section approval rules and status-table convention have now been
  pressure-tested on one spec end-to-end. The post-three-specs
  review moment is still upcoming.
- Transcript capture is still TBD.

## Next session — start here

1. Skim `meta/workflow-issues.md` for open items.
2. Extract `skills/red-team-implementation.md` from the shape that worked
   in this session. Keep it short (spec and test skill files are short).
3. Decide on the implementation-test workflow abstraction: is the
   three-step shape ready to be a shared primitive?
4. Write the spec 000 post-mortem entry in `meta/what-worked.md`.
5. Begin spec 001.

## Recent decisions worth remembering (carried forward)

- **Test red-team workflow:** `workflows/invoke-red-team-on-tests.md`.
- **Eye test convention:** standalone `tests/test_NNN_*_eyetest.py`, gate between implementation and full suite.
- **`> M?:` annotation:** for math gaps the human can't evaluate.
- **Math explainer pattern:** `tutorials/math/`, calibrated to project use.
- **Workflow overview doc:** `meta/workflow-overview.md`.
- **Honest review commitment:** fourth commitment in `AGENTS.md`.
- **Implementation red-team `> C:` pattern:** write `> C:` note directly under `> M:` in the report, with nuance captured inline. Resolve uncertain items in chat before writing the note.
- **`GridPrior` validation nuance:** uses non-negative (not strict positivity) because BA underflows cells far from atoms to 0.0 legitimately.
- **`Prior.updated()` removed:** BA update is owned by `blahut_arimoto`; `updated()` reserved for future self-contained prior types. DD9 in README documents this.
