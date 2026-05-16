# Handoff — 2026-05-17

## Where we left off

Repo bootstrapped at https://github.com/mihalybanyai/dynamic_infomax,
GitHub remote configured (with `http.version HTTP/1.1` workaround for
the Mac/HTTP-2 stall — see workflow-issues), `AGENTS.md` and starter
skills in place. Claude Code generated `specs/001-mattingly-fig1.md`
as a first spec, but it predates the new conventions in the updated
`skills/write-math-spec.md` (per-section status table, daft
generative-model diagram, revision log section). The spec has not been
reviewed yet — human reviewer was tired and explicitly chose not to
rubber-stamp. That instinct was the right one.

## Recent decisions worth remembering

- **Spec format:** per-section status table at top, no justification
  line on status changes. The deliberate edit *is* the act of review.
- **Downstream gating from status table:** Setup + Objective `reviewed`
  → test scaffolding; Derivation `reviewed` → property tests; Algorithm
  `reviewed` → implementation; all `reviewed` → red-team pass.
- **Diagrams:** daft for plate notation (Python, fast iteration),
  Mermaid for algorithm/dataflow (inline in markdown). Both source and
  rendered output committed in `diagrams/`.
- **Spec revisions:** every non-trivial change after first review gets
  a revision log entry, categorized as Correction / Clarification /
  Refinement. When unsure, escalate (prefer Correction).
- **Red-team skills** for spec, tests, implementation, result exist in
  the repo but are not yet in `bootstrap.py` (workflow-issues entry).
- Multiple workflow-issues entries opened for "evaluate after N specs"
  reviews — deliberately deferring premature codification of
  conventions whose value isn't yet pressure-tested.

## Open threads

- The first spec needs to be migrated to the new `skills/write-math-spec.md`
  format. This is a format change, not a content change.
- After migration: actual human review of the spec, section by section.
  Reproducing Mattingly Fig 1 (qualitatively) is the test case.
- After review: red-team pass on the spec, then test scaffolding,
  property tests, implementation.
- Transcript capture for today's two sessions (this chat + Claude Code)
  still TBD — see workflow-issues entry.
- Editor setup (VSCode + Obsidian) suggested but untried.
- Per-section approval rules and status-table convention should be
  pressure-tested over the next two specs. The workflow-issues
  entries name the review moment.

## Next session — start here

1. Skim `meta/workflow-issues.md` for any open items relevant to
   today's work.
2. Have Claude Code migrate `specs/001-mattingly-fig1.md` to the
   updated `skills/write-math-spec.md` format:
   - Add per-section status table at top, all sections at `draft`.
   - Add a daft plate-notation diagram if the spec has probabilistic
     structure (it should — Mattingly is Bayesian/information-bottleneck).
   - Add an empty Revision log section at the bottom.
   - Do not change spec content; this is a format migration.
3. Then begin actual section-by-section human review. Status flips
   from `draft` to `reviewed` happen by direct edit of the status
   table, with the spec section actually read at the time of the flip.
4. Once Setup + Objective are `reviewed`, Claude Code can sketch test
   scaffolding. Don't skip ahead — that's the whole point of the
   per-section gating.

## Notes to self

- The big risk tomorrow is the same as tonight: tiredness plus
  rubber-stamping. The status-table convention should help by making
  the review a deliberate edit rather than a "looks good" handwave.
  Watch whether it actually does, and note the observation (in
  `meta/what-worked.md` or `what-didnt.md`) for the post-three-specs
  review.
- The chat-Claude session that produced this handoff isn't in the
  repo yet. Once a transcript-capture convention is settled, today's
  chat should be saved to `transcripts/000-initial-planning.md` or
  similar — it has design rationale that isn't in the skills or
  AGENTS.md.

## Prompt for the next chat-Claude session

Paste this at the start of tomorrow's conversation with Claude on
claude.ai (not Claude Code — Claude Code reads the repo automatically):

> Continuing yesterday's work on dynamic_infomax. Repo is at
> https://github.com/mihalybanyai/dynamic_infomax. Please read
> AGENTS.md, meta/workflow-issues.md, meta/handoff.md, and the current
> spec specs/001-mattingly-fig1.md, then we'll start with the spec
> migration and review.
