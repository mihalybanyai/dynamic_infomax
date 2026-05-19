# Handoff — 2026-05-19

## Where we left off

Today closed the implementation red-team loop on spec 001 and built
out the surrounding workflow infrastructure in parallel. The
implementation red-team report has been processed end-to-end:
annotated, decided, code/docs/spec edits made, eye test re-run and
re-approved, full test suite re-run with per-test commit hashes
logged. The result red-team report is now generated and awaiting
review — processing it tomorrow finishes the first full experiment
cycle.

In parallel with processing the impl red-team, the day's chat
session produced a substantial expansion of the workflow
infrastructure: the impl red-team skill was extracted, the
implement-spec workflow was formalised as a sibling to the three
red-team workflows, the spec-skill gained an Eye test convention,
the codegen log gained a per-file status with the
`pending-tests ↔ done` flip on red-team-driven edits, and the
`meta/` directory gained both a detail diagram for the impl phase
and an abstract structural-vocabulary document.

## Recent decisions worth remembering

- **Impl red-team skill extracted:** `skills/red-team-implementation.md`
  codifies the durable shape from yesterday's one-shot prompt. Five
  finding categories survived (bugs / latent risks / inefficiencies
  / doc inaccuracies / doc omissions), as did the `[test-gap]` and
  `[spec-implication]` upstream-routing tags, the
  read-docs-before-code convention, and the test-failure branch
  with its three-way uncertainty (edit was wrong / new finding /
  test is wrong). Severity calibration was deliberately left to
  the per-instance prompt.
- **Implement-spec workflow:** `workflows/implement-spec.md`
  formalises the four-stage shape (codegen → eye test → full
  suite → doc finalisation) that had been improvised so far. Each
  stage has a paste-ready Claude Code prompt. Eye-test rejection
  has two branches: localised debugging (default) and the active
  opt-in to "run the full suite as a debugging aid." Test-failure
  triage is the heaviest section; significant decisions route to
  the doc's Testing notes section.
- **Eye test convention promoted to the spec phase:**
  `skills/write-math-spec.md` gained an Eye test section spec. From
  spec 002 onward, the eye test is decided during spec writing
  rather than improvised at implementation time. The migration
  fallback in `implement-spec.md` stage 2 covers older specs that
  pre-date the convention.
- **Codegen log per-file status:** files modified during impl
  red-team edits flip to `pending-tests` in `CODEGEN_LOG.md` and
  flip back to `done` after the post-edit test rerun. Same
  direction-asymmetry rule as spec sections: Claude flips
  backwards on revision, forwards on verification.
- **Documentation lifecycle codified:** design decisions
  accumulate from codegen onward, testing notes from test-failure
  resolution, call graph and data flow are stage-4 additions. The
  call graph is generated via `code2flow` and embedded as
  mermaid; `_make_call_graph.py` is the helper script that
  regenerates it.
- **Workflow detail diagram:** `meta/workflow-overview.md` was
  rewritten from the original swimlane version (rejected as
  visually busy and not answering the right question) to an
  accumulation-pipeline diagram showing artifact states between
  transformations. Eight states, seven transformations, one
  back-edge (eye-test rejection) and one off-ramp (upstream
  routing). Reading the boxes tells the reader what exists in
  the repo at each point.
- **Workflow structural vocabulary:** `meta/workflow-structure.md`
  is the new abstract companion to `workflow-overview.md`. Four
  pieces: the four-phase pipeline, the generic
  `inputs → generate → review → resolve` cycle with three
  resolutions (apply / dismiss / route upstream), the red-team
  variant of the same cycle (entry shifted from generate to
  review, sub-agent reviewer), and a Rosetta-stone table
  mapping the abstract verbs onto each phase's concrete
  artifacts. The result phase rows are placeholders, anchoring
  the design space for the upcoming result-phase workflow.
- **Workflow primitive abstraction question, answered partially:**
  yesterday's open thread asked whether the three-step
  decide/update-upstream/regenerate-downstream shape deserves a
  shared workflow primitive. Today's answer: the abstract shape
  is real and now documented (in `workflow-structure.md`'s
  diagram 2), but the per-phase prompts still benefit from
  living in separate workflow files because they differ on
  artifact specifics. The structural diagram does the
  abstraction work; the workflow files do the calibration work.

## Open threads

- **Result red-team report is the immediate next step.**
  Processing it finishes the first experiment cycle. Run the
  standard annotate / decide / apply loop following the
  workflow shape; this is the fourth instance of the pattern
  (after spec, tests, impl), so it's worth paying attention to
  what feels durable vs. what feels phase-specific.
- **Result phase workflow:** the result phase has placeholder
  rows in the `workflow-structure.md` table but no actual
  workflow file yet. Once the result red-team is processed, the
  durable shape of "what does the result phase actually look
  like" should be extractable into
  `workflows/produce-result.md` (or whatever the right name
  turns out to be). The structural diagram constrains the
  design — inputs, generate, review, resolve all need concrete
  instantiation.
- **Result red-team skill extraction:** parallel to today's impl
  red-team skill extraction. After the report is processed,
  extract into `skills/red-team-result.md`. The fifth and last
  red-team skill, completing the set.
- **Post-three-specs review still upcoming.** The per-section
  approval rules, status-table convention, and now the
  per-file codegen-log status have all been pressure-tested on
  one spec. The original moment for systemic review was "after
  three specs"; we're still on the first. The current shape is
  holding up but the data point is single.
- **Workflow infrastructure churn slowing.** Today added two new
  workflow files, one new skill, two new meta docs, and an
  edit to the spec skill. The rate of new conventions should
  start dropping now that all four phases have either a
  workflow file or a clear design surface. Worth tracking in
  `meta/what-worked.md` whether the rate actually does fall
  through specs 002 and 003, or whether each new spec keeps
  surfacing infrastructure gaps.
- **Transcript capture is still TBD.** Today's chat session
  produced design rationale for the impl skill, the
  implement-spec workflow, the spec skill's Eye test addition,
  and both `meta/` documents. None of it is captured outside
  the chat. Yesterday's handoff named this as an open thread;
  it still is.
- **Documentation has now been red-teamed in conjunction with
  code but not in isolation.** Same status as yesterday — the
  question of whether docs without an implementation alongside
  need their own red-team workflow is unresolved. Probably
  worth deferring until a concrete case forces the issue.

## Next session — start here

1. Skim `meta/workflow-issues.md` for any items that the result
   red-team might touch or that were opened today.
2. Read the result red-team report at wherever Code put it
   (likely `experiments/000-static-fig1/redteam-result.md` or
   similar — check the experiment directory).
3. Annotate the report with `> M:` / `> M?:` / dismiss reactions,
   working top-down by severity. The
   `[test-gap]` / `[spec-implication]` / (and possibly new for
   this red-team type) `[code-implication]` tags would route
   findings to other workflows — flag in chat when you hit them.
4. Run the standard processing shape (decide / update upstream /
   regenerate downstream) for whatever the result-phase's
   downstream artifact is — probably the result figures and any
   accompanying narrative document.
5. After the report is processed and changes are committed,
   extract the durable shape into `skills/red-team-result.md`.
   Then fill in the result-phase placeholder rows in
   `meta/workflow-structure.md`'s table and consider whether a
   `workflows/produce-result.md` workflow file is warranted, or
   whether the result phase is simple enough that the
   structural diagram + the skill suffice.
6. With spec 001 fully closed, start spec 002 prep. The Eye test
   convention is now in the spec skill, so spec 002 should be
   the first spec written with a deliberate eye-test section
   from the start rather than retrofitted.

## Notes to self

- This finishes the first end-to-end pass on a spec, including
  the result phase. The candidates for `meta/what-worked.md` /
  `what-didnt.md` are: did the abstract
  `inputs → generate → review → resolve` cycle survive contact
  with the result phase, or did the result phase break the
  pattern? Was the impl red-team skill extraction (today's
  exercise) the right level of abstraction, or did the
  one-shot prompt carry calibration that the skill lost? Did
  the codegen-log per-file status flip catch anything that
  wasn't already obvious?
- The workflow-structure document was a late addition today and
  it's the kind of artifact that's easy to over-invest in. If a
  labmate (or future-me) ends up referring to it more than the
  concrete workflow files, that's a sign the abstraction is
  earning its place. If it gets read once and ignored, that's a
  sign it was decorative. Worth checking in on this in a few
  weeks.
- The result red-team is the third new red-team type since spec
  and tests, and the second new one this week. Pay attention
  to which parts of the impl red-team shape carry over and
  which feel forced. The five-category structure in particular
  was opinionated for impl; the result-phase categories are
  probably different (claim-evidence mismatches? overclaiming?
  figure misreadings?).
- Resist the temptation to also formalise
  `workflows/produce-result.md` tomorrow if the shape isn't
  clear yet. The result phase has been improvised exactly once;
  one data point doesn't warrant a workflow file. Better to let
  spec 002's result phase pressure-test the shape before
  codifying.
- The handoff notes are themselves becoming a useful artifact
  pattern. Today's is the second; consider whether
  `meta/handoff.md` should always be the latest one or whether
  they should accumulate (probably the latter, into something
  like `meta/handoffs/2026-05-19.md` with a symlink or
  pointer-section in `meta/handoff.md`).

## Prompt for the next chat-Claude session

Paste this at the start of tomorrow's conversation with Claude on
claude.ai (not Claude Code — Claude Code reads the repo
automatically):

> Continuing work on dynamic_infomax. Repo is at
> https://github.com/mihalybanyai/dynamic_infomax. Please read
> AGENTS.md, meta/workflow-issues.md, meta/handoff.md, and the
> result red-team report (likely at
> experiments/000-static-fig1/redteam-result.md or similar —
> check the experiment directory). The immediate task is to
> process the report — annotate, decide, apply — following the
> shape of the impl red-team processing we did today, adapted
> for whatever the result phase's downstream artifacts turn out
> to be. After processing is complete, we'll extract the
> durable shape into skills/red-team-result.md, fill in the
> result-phase placeholder rows in meta/workflow-structure.md,
> and start prep for spec 002.