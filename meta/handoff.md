# Handoff — 2026-05-18

## Where we left off

The first spec has gone all the way through: spec written and
red-teamed, test suite derived and red-teamed (including the new
test red-team workflow we formalised today), implementation
written, eye test passed, full test suite passing, and documentation
written. The implementation red-team sub-agent has now run on the
code + docs and produced a report — that's the next thing to
process.

Today's session also produced a meaningful expansion of the
workflow infrastructure: the test red-team workflow file, the eye
test convention, the `> M?:` annotation for math gaps, a math
explainer for KKT, the workflow overview document with embedded
Mermaid diagram, and the README setup section gaining a VSCode
extension entry.

## Recent decisions worth remembering

- **Test red-team workflow:** `workflows/invoke-red-team-on-tests.md`
  formalises the three-step decide / update-spec / regenerate-tests
  pattern. Differs from spec red-team in three substantive ways:
  findings can touch spec, tests, or both; pushback on `> M:` is
  explicit; stage 3c bundles red-marking removal with first-time
  property-to-test table addition.
- **Eye test convention:** every spec from 002 onward includes an
  eye-test subsection (smallest run, expected qualitative features,
  human approval). Eye-test file is its own `tests/test_NNN_*_eyetest.py`,
  not picked up by pytest, runnable as a standalone script. Eye-test
  gate sits between implementation and full test suite.
- **`> M?:` annotation:** sibling to `> M:` for findings the human
  can't evaluate due to a math gap. Distinct from "uncertain"
  (`> M:` with a question) — `> M?:` means "I'm not sure I understand
  the question." Triggers a calibrated math explainer from Claude
  Code; promotes to `tutorials/math/` on the second occurrence of
  the same concept.
- **Math explainer pattern:** new third pattern in `tutorials/README.md`,
  living in `tutorials/math/` subfolder. Scope discipline: calibrated
  to the project's use, not the general theory. First example is
  `tutorials/math/kkt.md`, triggered by red-team findings on
  spec 001.
- **Workflow overview doc:** `meta/workflow-overview.md` contains
  the bird's-eye-view diagram (Mermaid swimlanes: human, Claude Code,
  sub-agent) plus minimal prose. Embedded mermaid block, no
  separate `.mermaid` source file — single source of truth.
- **Honest review commitment:** added as fourth commitment in
  `AGENTS.md` "How we work". States that reviewing what you don't
  understand is delegation in review's clothing; `> M?:` is the
  mechanism for flagging gaps explicitly. Premise: growing the
  human's command of the mathematics is itself a project goal.
- **Implementation red-team prompt:** one-shot prompt rather than a
  new skill file. Discover-under-load applied to skills themselves —
  the shape that worked will get extracted into
  `skills/red-team-implementation.md` after this first pass.

## Open threads

- **Implementation red-team report is the immediate next step.**
  Evaluate findings using the `> M:` / `> M?:` / dismiss annotation
  convention, then process per the test red-team workflow shape
  (decide / update upstream / regenerate downstream — though here
  "upstream" might be the spec or tests, and "downstream" is the
  implementation and docs).
- **Implementation red-team skill extraction.** After the report is
  fully processed, extract the durable shape into
  `skills/red-team-implementation.md`. Likely candidates for what
  transfers: five-category structure, doc-type-specific review
  criteria, `[test-gap]` and `[spec-implication]` cross-workflow
  routing tags, "read docs before code" convention. The exact
  severity calibration probably won't transfer.
- **Implementation-test workflow formalisation.** The three-step
  decide/update-upstream/regenerate-downstream shape will now have
  been used for spec, tests, and implementation red-teams. Worth
  considering whether the shape should be abstracted into a shared
  workflow primitive rather than three separate workflow files. The
  workflow-issues entry from the test workflow named this as the
  trigger ("third instance shows whether the abstraction is real").
- **Documentation we built has not been red-teamed in isolation.**
  The implementation red-team includes doc review, but if a future
  spec produces docs without an implementation alongside (unlikely
  but possible), the doc-review criteria might need their own home.
- Transcript capture is still TBD as of the last handoff; the chat
  session that produced today's workflow infrastructure has design
  rationale not captured anywhere else.
- Per-section approval rules and status-table convention have now
  been pressure-tested on one spec end-to-end. The post-three-specs
  review moment is still upcoming.

## Next session — start here

1. Skim `meta/workflow-issues.md` for any items opened today or
   that the implementation red-team might touch.
2. Read the implementation red-team report
   (`meta/redteam-impl-001.md` or wherever Code put it).
3. Annotate the report with `> M:` / `> M?:` / dismiss reactions
   for each finding, working top-down by severity. The `[test-gap]`
   and `[spec-implication]` tags from the prompt route findings to
   the other workflows — flag in chat when you hit them rather than
   acting on them here.
4. Once annotated, run the three-step processing (decide / update
   upstream / regenerate downstream) following the test red-team
   workflow shape, adapted for code + docs as the downstream
   artifacts.
5. After the report is fully processed and changes are committed,
   extract the durable shape into
   `skills/red-team-implementation.md`. Then formalise the
   implementation-test workflow: this is the "third instance" check
   on whether the three-step shape deserves abstraction into a
   shared primitive.

## Notes to self

- This is the first end-to-end pass on a spec. Worth a post-mortem
  entry in `meta/what-worked.md` or `what-didnt.md` once the
  implementation red-team is fully processed, ahead of the
  post-three-specs review. The candidates worth flagging now: the
  eye test catching anything the quantitative tests didn't, the
  `> M?:` annotation actually getting used (or not — its absence
  would also be a finding), and the doc red-team criteria turning
  up findings the doc author missed.
- The implementation red-team is the first new red-team type since
  spec and tests. Pay attention while processing to which parts of
  the prompt felt right and which felt awkward — that's the
  material the skill extraction will use. The five-category
  structure in particular is opinionated and might not survive
  contact.
- The temptation when extracting the skill will be to over-specify.
  Resist. The skills for spec and tests are short; this one should
  be too. Move durable structure into the skill, leave calibration
  to the per-instance workflow prompt.

## Prompt for the next chat-Claude session

Paste this at the start of tomorrow's conversation with Claude on
claude.ai (not Claude Code — Claude Code reads the repo
automatically):

> Continuing work on dynamic_infomax. Repo is at
> https://github.com/mihalybanyai/dynamic_infomax. Please read
> AGENTS.md, meta/workflow-issues.md, meta/handoff.md, and the
> implementation red-team report at meta/redteam-impl-001.md (or
> wherever Code put it). The immediate task is to process the
> report — annotate, decide, apply — following the shape of the
> test red-team workflow at workflows/invoke-red-team-on-tests.md,
> adapted for code + docs as the downstream artifacts. After
> processing is complete, we'll extract the durable shape into
> skills/red-team-implementation.md and consider formalising the
> implementation-test workflow.
