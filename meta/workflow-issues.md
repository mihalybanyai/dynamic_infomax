# Workflow issues and improvements

Tracks meta-level issues with the project's workflow itself — things to
fix, reconsider, or add to the conventions. For research and code issues,
use GitHub Issues on the repo.

## Conventions

- Every entry has: a short title, status, date opened, category, and a
  paragraph of context.
- Status: `open` / `in-progress` / `resolved` / `dismissed`.
- Categories: `bootstrap`, `skills`, `conventions`, `tooling`, `meta`.
- Resolved and dismissed entries stay in the file with a resolution
  note — they are the project's institutional memory.

## Review cadence

Skim this file at the start of each significant session, particularly
before starting a new spec or experiment. Quick scan of open items;
address what's cheap, file what's not.

---

## Open

### Wire experiment commit hashes through to the report automatically [conventions]

*Opened 2026-05-20*

The result red-team (F14 in `experiments/000-static-fig1/redteam-result.md`)
flagged that REPORT.md's commit-hash claim drifts: the hash named in the
header (`1f8339e`) identified the test-suite-passing implementation, but
the report itself was regenerated at a later HEAD. We resolved the
specific instance by relabelling the header to distinguish "code under
test" (`src/infomax` hash) from "report regenerated at" (current HEAD).
The general fix is to have `run.py` record both `git rev-parse HEAD` and
`git rev-parse HEAD:src/infomax` into `results_table.json` metadata at
run time, and have REPORT.md cite the JSON-recorded values rather than a
hand-edited hash. Worth applying to spec 002's experiment driver from
the start rather than retrofitting.

### Revise write-math-spec skill after first 3 specs [skills]

*Opened 2026-05-17*

The current `skills/write-math-spec.md` is a reasonable first guess at
spec structure but is not yet informed by use. After three specs have
been written and used (tested against, red-teamed, possibly implemented),
review observations tagged `[spec-format]` in `meta/what-worked.md` and
`meta/what-didnt.md`, then decide what to revise. Do not revise piecemeal
in the meantime.

### Evaluate status-table convention after a few specs [conventions]

*Opened 2026-05-17*

The status table in `skills/write-math-spec.md` requires the human to
flip per-section status by direct table edit. After three specs have
been reviewed under this convention, evaluate: does it actually slow
down rubber-stamping? Or has it become an empty ritual? If the former,
keep. If the latter, redesign.

### Evaluate downstream-approval gating after a few specs [conventions]

*Opened 2026-05-17*

The rules in `skills/write-math-spec.md` gate test scaffolding behind
Setup+Objective approval, property tests behind Derivation approval, and
implementation behind Algorithm approval. These are conservative
guesses. After three specs reach implementation, evaluate whether the
gates were appropriate, too strict (causing workarounds), or too loose
(letting unreviewed math drive code). Revise the skill accordingly.

### Test traceability to spec sections [conventions]

*Opened 2026-05-17*

When a spec revision is a Correction, the affected tests need to be
identified and marked stale. Right now this is manual. Candidate
conventions: test docstrings that name the spec section they verify,
or a separate `tests/SPEC_MAPPING.md`. Decide based on what actually
hurts during the first Correction cycle, not in advance.

### Experiment-to-spec-commit traceability [conventions]

*Opened 2026-05-17*

When a spec is revised after experiments have been run against it,
identifying affected experiments is currently manual. Candidate
convention: experiment READMEs record the git commit hash of each spec
they depend on. Add this to `skills/document-experiment.md` if needed,
based on first-cycle experience.

### Settle on transcript-capture conventions [conventions]

*Opened 2026-05-17*

Today's sessions need to be captured to `transcripts/` but the right
mechanism hasn't been chosen. Candidates: (a) browser extension export
to Markdown for chat.claude.ai sessions, (b) raw JSONL from
~/.claude/projects/ for Claude Code, (c) Claude Code self-summarizing
the previous session at the start of the next. Pick after a few
sessions of seeing which captures actually get read back.

### Codify session-end routine after a few cycles [skills]

*Opened 2026-05-17*

Today established a rough session-end routine: dump transcript to
`transcripts/`, write `meta/handoff.md`, commit and push, skim
workflow-issues for open items. After this routine has been used
several times, consider codifying as `skills/close-session.md`. Hold
off on writing the skill until the routine has stabilized.

### Handle parallel work tracks via separate handoffs [conventions]

*Opened 2026-05-18*

The project will have at least two concurrent threads: (a) the
implementation track (currently spec 000), and (b) a more
mathematical/conceptual sub-project (TBD which spec or note files).
Convention: one handoff file per active track (`meta/handoff-<track>.md`),
updated only by sessions working on that track. Start of a session
loads the relevant handoff. Don't mix tracks within a single
conversation — switch tracks by closing the session and opening a new
one with the other handoff. Revisit if a third track appears or if
this becomes cumbersome.

### Randomness/reproducibility conventions [conventions]

*Opened 2026-05-18, in-progress*

Skill `skills/manage-randomness.md` written in v1 form before first use,
because the conventions govern every code-touching action and
retrofitting would be expensive. Pending: revise after first experiment
actually runs against the conventions. Known v1 gaps documented at the
bottom of the skill (CUDA non-determinism, parallelism, caching).

### Reference handling: PDFs vs annotated bibliography [conventions]

*Opened 2026-05-18*

Two-tier convention adopted: (a) primary sources for active specs go
into `resources/` as PDFs; (b) background/secondary references live
in `resources/references.md` as an annotated bibliography with DOIs
and links, not as PDFs. Reduces repo bloat and copyright exposure
without sacrificing what red-teaming and review actually need.
Revisit if the project grows large enough that `resources/`
itself becomes unwieldy — git LFS or external paper storage may then
be appropriate.

### Skills vs. workflows: maintain the boundary [conventions]

*Opened 2026-05-18*

`skills/` contains procedures (what to do for a task). `workflows/`
contains reusable prompts that orchestrate skills and conventions
(how to trigger a session of work). Boundary signal: if a prompt to
Claude Code or chat-Claude contains substantive content beyond "follow
skill X on artifact Y", that content is either (a) a candidate for
absorption into the relevant skill (preferred when the content is
about *how* to do the procedure) or (b) a candidate for a workflow file
(when the content is about *when* and *in what context* to invoke the
procedure).

When drafting new prompts, ask: is this prompt's content really
something the skill should specify? If yes, fix the skill. Only after
that, add a workflow file if the orchestration itself is reusable.

Review the boundary after 5+ workflow files exist, or if any workflow
file grows beyond ~50 lines of prompt content (suggesting it's
absorbing what should be in skills).

### Naming convention is inconsistent across the repo [conventions]

*Opened 2026-05-20*

Hyphens vs underscores vary across filenames, directory names, and
path elements with no apparent rule, and the same basename appears
under different paths in some cases (e.g. `experiments/000-static-fig1/run.py`
will collide once a second experiment lands). Cross-references already
drift — spec 000 §6 Layout lists `tests/test_static_infomax.py` while
the actual file is `tests/test_000_static_infomax_fig1.py`. The cost
is that filename references in specs, codegen logs, and revision logs
are not stable permalinks and have to be checked by humans.

A draft `AGENTS.md` section was sketched with three rules — `snake_case`
everywhere except externally-fixed names, globally-unique basenames
enforced by a CI check, path-prefix for files whose role isn't clear
from the basename alone — plus a "new and touched files only" migration
policy to avoid a flag-day rename pass. Deferred because the carve-outs
(kebab for diagrams? for URL-facing markdown?), the migration cadence
(reactive on touch vs scheduled passes), and the question of whether
to rename `run.py` proactively before experiment 001 lands all need
more thought than the rest of the session allowed. Draft text and the
discussion live in the chat of 2026-05-20.

Action: revisit when the second experiment is about to land (the
`run.py` collision forces a decision), when any unrelated `AGENTS.md`
revision is in flight (chance to land the section in the same edit),
or when a cross-reference breakage is found that basename uniqueness
would have caught.

### Bootstrap still ships pre-evolution copies of three procedural skills [bootstrap]

*Opened 2026-05-24*

The v2 bootstrap pass landed updated AGENTS.md, the four red-team
skills, manage-randomness, the tutorials, uv setup, and the macOS
git fix — but the three original procedural skills
(`write-math-spec.md`, `derive-test-suite.md`,
`document-experiment.md`) were carried over verbatim from the v1
bootstrap because they were not part of the regeneration pass and
have plausibly evolved in the live repo since. A labmate running
`bootstrap.py` today gets these three at their original v1 content,
which is likely behind the live versions (the AGENTS.md test-gates
section already implies a richer derive-test-suite that mentions
property-to-test tables and eye-test files, neither of which is in
the seeded copy).

Action: compare the live `skills/{write-math-spec,derive-test-suite,document-experiment}.md`
against the strings `ORIG_SKILL_WRITE_MATH_SPEC`,
`ORIG_SKILL_DERIVE_TEST_SUITE`, `ORIG_SKILL_DOCUMENT_EXPERIMENT` in
`bootstrap.py`. For each one that has drifted, update the embedded
string. Wait until the existing workflow-issues entry on revising
`write-math-spec` after three specs has resolved before doing the
write-math-spec one, so the revision and the bootstrap pickup land
together.

---

## Resolved / dismissed

<!-- Entries move here when closed, with a one-line resolution note. -->

### Default to lightweight PDF tools in skills [skills]

*Opened 2026-05-16, dismissed 2026-05-24* 

Deemed unimportant by the human.

### Session-resume rhythm and wake-up cost [conventions]

*Opened 2026-05-18, dismissed 2026-05-24*

Other issues basically cover this.

### Codify Claude Code session-start prompt [skills]

*Opened 2026-05-18, resolved 2026-05-24*

This has been done in a worflow file.

### Clarify red-team resolution workflow in skills [skills]

*Opened 2026-05-18, resolved 2026-05-24*

This has been done.

### Add red-team skills to bootstrap.py [bootstrap]

*Opened 2026-05-16, resolved 2026-05-24*

Resolved in the v2 bootstrap pass on 2026-05-24. All four red-team
skills (`red-team-spec`, `red-team-tests`, `red-team-implementation`,
`red-team-result`) are now seeded by `bootstrap.py`. The originally
proposed `## Red-teaming` section in `AGENTS.md` was not added as a
separate section; the test-gates section and the explicit references
to red-team skills throughout the conventions and reproducibility
sections cover the same ground.

### Add macOS git HTTP/1.1 fix to bootstrap.py [bootstrap]

*Opened 2026-05-16, resolved 2026-05-24*

Resolved in the v2 bootstrap pass on 2026-05-24. `bootstrap.py` now
calls `git config http.version HTTP/1.1` on Darwin after `git init`,
with a printed note explaining the workaround on macOS and a
shorter explanatory note on other platforms.

### Bootstrap should set up uv + pyproject.toml [bootstrap]

*Opened 2026-05-18, resolved 2026-05-24*

Resolved in the v2 bootstrap pass on 2026-05-24. `bootstrap.py` now
seeds a minimal `pyproject.toml` (project name, `requires-python =
">=3.11"`, empty `dependencies`, `dev` dependency group with `pytest`
and `ruff`) and invokes `uv sync` at the end of bootstrap. If `uv` is
not on PATH the script prints an install pointer and continues; if
`uv sync` fails (e.g. no Python 3.11 available) the script reports
the error and continues, leaving the labmate to fix the issue and
re-run `uv sync` themselves. Specific Python version pinning remains
at `>=3.11`; tighter pinning can wait for a concrete reason.

### Next bootstrap revision: skills, tutorials, uv, macOS fix [bootstrap]

*Updated 2026-05-18, resolved 2026-05-24*

Resolved in the v2 bootstrap pass on 2026-05-24. All bundled items
landed: red-team skills, macOS git fix, uv setup, the
`manage-randomness.md` skill, the `tutorials/` directory (`README.md`,
`uv.md`, `gh.md`, `rng-passing.md`, and the `math/kkt.md` math
explainer), and the current `AGENTS.md` seed content (which already
includes the reproducibility section, the iron-rules section, the
test-gates section, the dependencies/uv section, and the
status-transition direction asymmetry). The original three procedural
skills (`write-math-spec`, `derive-test-suite`, `document-experiment`)
were not refreshed in this pass and have been split off into their
own follow-up entry; see "Bootstrap still ships pre-evolution copies
of three procedural skills" under Open.