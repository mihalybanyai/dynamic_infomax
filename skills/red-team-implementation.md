# Skill: red-team-implementation

> Use this skill after an implementation in `src/` has been written from a
> reviewed spec, the test suite (itself red-teamed) passes, and the
> documentation files for the implementation are in place. The goal is to
> find what "passes the tests" misses — bugs the tests didn't catch,
> latent correctness risks, load-bearing inefficiencies, and inaccuracies
> or load-bearing omissions in the documentation.

## Why this exists

A passing test suite is necessary but not sufficient evidence that an
implementation is correct. Tests only exercise the cases the test author
imagined. The implementation can:

1. Be wrong on cases the tests don't exercise.
2. Be right on the tested regime but rely on assumptions that won't hold
   for the next spec or the next scaling regime.
3. Be slow enough that the spec's intended scale is unreachable.
4. Be documented in a way that misleads a future reader — wrong shape
   annotations, stale design-decision rationale, comments that
   contradict the code.

A fresh sub-agent reading the spec, then the docs, then the code is
positioned to catch all four. The reading order is deliberate: if the
docs claim X and the code does Y, a docs-first reader notices the
mismatch as a mismatch, where a code-first reader would form an
opinion of what the code does and the docs would then have to fight it.

## Before invoking — the spawn-configuration gate

The sub-agent inherits this session's model and effort tier. Effort is not
machine-checkable from inside the agent, and the specific model *version* is
not selectable from the spawn — so the only guard is to put the configuration
in front of the human and get explicit ratification. Before spawning, the main
agent MUST:

1. **Print the roster.** Reproduce the "Red-team reviewer roster" table from
   `AGENTS.md`, including its **Last verified** date, and print this session's
   declared model identity.

2. **Print the inheritance caveats and ask to proceed:**

   > Red-team spawn check:
   > - Model: this session is `<declared identity>`; the sub-agent inherits it.
   >   For the diversity pass on the *other* approved model, stop now and re-run
   >   this trigger from a session set to that model (a separate thread).
   > - Effort: the sub-agent inherits this session's effort tier. Policy is the
   >   highest available tier; this is NOT machine-checkable. If this session is
   >   not at the highest tier, stop now, raise it, and re-run this trigger.
   > - Replying "go" both spawns the red team **and** ratifies the roster above
   >   as current — its Last verified date will be set to today. If the roster
   >   is stale (a newer model shipped, a tier changed), fix the table first,
   >   then reply "go".

3. **Wait for an explicit "go".** Do not call the `Task` tool until the human
   replies. Conversational acknowledgement is not "go".

4. **On "go":**
   - Set the roster's **Last verified** date in `AGENTS.md` to today and commit
     it alongside the red-team artifacts — the human's "go" *is* the
     verification (they saw the table and did not flag it stale).
   - Spawn the sub-agent, substituting into its prompt template: the spec path,
     the **approved roster** (`<APPROVED_ROSTER>`), the human-ratified **effort
     tier** (`<EFFORT_TIER>`), and the roster **Last verified** date
     (`<ROSTER_VERIFIED_DATE>`), so the sub-agent can run its model failsafe and
     stamp all three into the report header.

This gate is the sole guard for effort and the cross-session guard for model
version; the in-prompt model failsafe (step 1 of the prompt below) is the
agent-verifiable backstop.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt
template. Substitute `<SPEC_PATH>`, `<CODE_DIR>`, and `<DOC_PATH>` with
the actual paths.

```
You are a hostile reviewer of an implementation. Your job is to find
the gap between "passes the tests" and "is actually a good
implementation of the reviewed spec, well-documented."

Before anything else, print your declared model identity (the model version
you are running as). The approved red-teamers for this project are:
<APPROVED_ROSTER>. If your declared identity is not among them, STOP: write
nothing to the report file and reply only with "Model mismatch: I am
<identity>, not an approved red-teamer. Aborting." Do not review.

The project's Python environment is managed by `uv` and already ships the
scientific stack — currently numpy, scipy, matplotlib, pypdf, pypdfium2, and
daft-pgm. Run Python via `uv run python` (or `uv run <script.py>`); do NOT
install anything (no `pip install`, no `uv add`) — run `uv pip list` if you need
to confirm what is available. Also do NOT read any other red-team report
(`*-redteam*.md`, prior or concurrent) for this artefact — review it
independently, on its own merits.

Context you should take as given:
- The spec at <SPEC_PATH> has been red-teamed and is at status
  `reviewed` across all relevant sections. You are NOT auditing the
  math.
- The test suite has been red-teamed and the implementation passes
  all tests. You are NOT auditing test coverage against the spec.
- The implementation lives at <CODE_DIR>. The documentation lives at
  <DOC_PATH>.

Read the spec first to load the contract. Then read the documentation
(design decisions, data flow, call graph, inline conventions). Then
read the code. This order is deliberate: form your picture of what
the implementation *should* do from spec+docs, and let the code be
checked against that picture rather than the other way round.

Audit for the following, in this order of priority:

1. **Bugs the tests didn't catch.** Cases where the code produces
   wrong output for inputs the tests don't exercise. Off-by-one
   errors at boundaries, wrong behaviour for degenerate inputs not
   covered by tests, silent incorrect handling of edge cases the
   spec implicitly requires but the tests don't probe.

   **Meta-rule**: if a bug you find would have been caught by a test
   that already exists and passed, that's not a bug-finding, that's
   a *test* finding — the test is wrong or vacuous. Mark with
   `[test-gap]` in the finding header; it retroactively belongs to
   the test red-team's territory and will be routed there during
   triage.

2. **Latent correctness risks.** Code that produces correct output
   for the spec's exercised cases but contains assumptions that
   would fail under plausible extensions. Examples: assumes a
   specific axis order that the next spec might transpose; relies
   on a numerical regime (small N, large temperature, full-rank
   covariance) that won't hold for the next spec; has undefined
   behaviour on edge cases the current spec doesn't explicitly
   forbid but the next one might exercise.

3. **Load-bearing inefficiencies.** Performance issues that would
   prevent running the experiment at the scale the spec calls for,
   or that scale poorly with parameters the spec varies. NOT
   stylistic optimisations ("you could use np.einsum here"); only
   inefficiencies that block the spec's intended use. If unsure,
   err on the side of not flagging.

4. **Documentation inaccuracies.** For each documentation type:
   - **Design-decisions log**: claims that don't match the code
     (e.g. "we vectorise X" but the code loops), reasoning that
     elides a real alternative, decisions that have silently
     changed in the code without a log entry.
   - **Data-flow / shape documentation**: shape annotations or flow
     descriptions that don't match what the code actually does.
   - **Call graph or structural docs**: stale entries, missing
     edges, edges that no longer exist.
   - **Inline comments**: comments that contradict the code. Always
     flag — a wrong comment is worse than no comment, because it
     misleads.

5. **Documentation omissions.** Things load-bearing for understanding
   the code that aren't documented anywhere — not in the spec, not
   in the doc files, not in comments. A "load-bearing" omission is
   one where a labmate reading the code cold would predictably get
   stuck or make a wrong inference. Random unexplained constants,
   unstated invariants, non-obvious convention choices.

**Not in scope for you:**

- Style or formatting issues (linters cover this).
- Suggestions to add tests (the test red-team owns this).
- Suggestions to revise the spec (the spec red-team owns this). If
  you think a finding actually points at a spec problem rather than
  an implementation problem, flag it as `[spec-implication]` in the
  finding header; the triage will route it.
- Documentation that "would be nice to have" without a load-bearing
  reason. Wishlist items are out of scope.

For each finding, state:
- **Header**: short title with severity in brackets and any
  category tag (e.g. `[test-gap]`, `[spec-implication]`).
- **Location**: file + line range, or doc section.
- **Concern**: 2–4 sentences on what's wrong and why.
- **What would resolve it**: specific suggestion.
- **Touches**: code, docs, or both.

Be specific. Useless: "this function might be slow on large inputs."
Useful: "this function computes the m×n×n covariance tensor by a
triple Python loop over the batch dimension at lines 142–149; for the
m=1024 batch size the spec specifies in §3.2, this is approximately
~10⁶ Python-level operations per training step. Vectorise via the
batched outer product over axis 0."

**Ordering**: findings ordered by descending severity within each of
the five categories above, with the categories themselves in the
priority order listed (bugs first, then latent risks, then
inefficiencies, then doc inaccuracies, then doc omissions). Number
findings F1, F2, F3, ... *after* ordering, so F1 is the
highest-severity finding in the highest-priority category.

If you cannot find substantial issues in a category, say so directly.
Do not invent concerns to seem thorough.

Write your findings to `<DOC_PATH_DIR>/redteam-impl.md` in the
following format:

# Red-team review of <IMPL_NAME>

Reviewer: red-team sub-agent
Reviewer model (declared identity): <the identity you printed as your first action>
Effort tier: <EFFORT_TIER> (human-set; not machine-verified)
Roster verified: <ROSTER_VERIFIED_DATE>
Date: <YYYY-MM-DD>
Spec version: <git commit hash if available>

## Summary

<one paragraph: qualitative impression of the implementation and its
documentation — does the code plausibly do what the spec calls for,
where is it most fragile, does the documentation track the code. No
counts of findings by severity; the list is the source of truth.>

## Findings

### F1: <short title> [severity: high] [<optional tag>]

**Location**: <file:lines or doc section>

**Concern**: <2–4 sentences>

**What would resolve it**: <specific suggestion>

**Touches**: <code | docs | both>

---

### F2: ...

## What the implementation gets right

<one paragraph, briefly. So the author knows what not to inadvertently
break when addressing the findings.>
```

## Annotation conventions in the redteam file

Same convention as `skills/red-team-spec.md` and `skills/red-team-tests.md`:
the human appends responses with `> M:` (or appropriate initial) and
Claude or the human appends confirmations with `> C:`, two newlines
between each. The redteam file becomes the audit trail for the
implementation red-team pass.

`> M?:` (with the question mark) is used for findings the human is not
equipped to evaluate without further explanation — typically when the
finding touches a numerical-stability argument, a non-obvious algorithmic
identity, or a performance claim the human can't size without help.
Distinct from `> M:` with uncertainty (which means the question is
understood but the answer is unclear): `> M?:` means the question itself
needs unpacking. Findings annotated `> M?:` are discussed in chat before
any `> C:` resolution is recorded.

Example after a full resolution cycle:

```markdown
### F4: Covariance update reuses unwhitened input [severity: high]

**Location**: src/infomax/sufficient_stats.py:88–104

**Concern**: The running covariance is updated using `x` directly,
but `x` has already been whitened in-place at line 76. The update
therefore computes the covariance of the whitened residual rather
than the raw input. Tests pass because the test suite only checks
the whitened second moment.

**What would resolve it**: Either compute the update before
whitening, or store a copy of the pre-whitening input and use it in
the update.

**Touches**: code, docs

> M: Apply — store a copy of the pre-whitening input. Update the
> data-flow doc to mark the pre-whitening copy as a named
> intermediate.

> C: Applied in commit 7c9a01e. Added `x_raw = x.copy()` at line 75
> before whitening; covariance update now uses `x_raw`. Data-flow
> doc updated with the named intermediate. Spec untouched.
```

This convention makes the redteam file the audit trail for the red-team
pass — what was flagged, what the human decided, what was done, all in
one place. See `workflows/invoke-red-team-on-impl.md` for the full
procedural workflow, including the three category-routing tags and the
post-edit verification step.

## After the redteam report exists

The triage follows the four-stage process in
`workflows/invoke-red-team-on-impl.md`: decide → update spec (if any) →
regenerate code and docs (flipping the status of any modified code file
in `CODEGEN_LOG.md` to `pending-tests`) → re-run tests one-by-one,
logging per-test commit hashes in `CODEGEN_LOG.md` and flipping the
modified files' status back to `done` once all tests pass. The
four-stage shape exists because findings in this red-team can touch up
to three artifacts (spec, code, docs including helper scripts), and the
regenerated code needs to be verified against the test suite before the
pass is closed. The `pending-tests → done` status flip follows the same
direction-asymmetry rule used elsewhere in the project: Claude flips
backwards on revision, forwards on verification.

For each finding, the outcome is one of:

- **Fix it** in the appropriate artifact (code, docs, helper script, or
  spec), append a `> C:` confirmation referencing the commit and any
  status changes.
- **Dismiss it** with a `> M:` justification, append a `> C:` confirming
  no change was made.
- **Route upstream**: findings tagged `[test-gap]` go to the test
  red-team's territory (they reveal a test that should have caught the
  bug); findings tagged `[spec-implication]` go to the spec red-team's
  territory (they reveal an under-specified or wrong piece of spec).
  Routed findings get a `> C:` noting the routing rather than an
  in-place fix. The downstream effect — re-running the relevant
  upstream red-team or scheduling one — is handled by the workflow,
  not this skill.

The redteam file is committed alongside the implementation, the docs,
and any spec changes that resulted from `[spec-implication]` routing.

## On the test failure branch

After the edits, the workflow re-runs the test suite. If a test fails
on the rerun, the failure is reported back to the human and decided
jointly. The failure can mean three things and the workflow does not
pre-commit to which:

- The edit was wrong (return to the relevant `> C:` and re-decide).
- A new finding has emerged that the red-team missed (add it to the
  redteam file as F_n+1 and triage it like the others).
- A test is wrong (route upstream as `[test-gap]`, same as during the
  original red-team).

This skill flags the junction; the workflow handles the dispatch.

## When to skip this skill

- The implementation is a trivial revision (renaming, comment fix,
  pure refactor with no behavioural change) of an already-red-teamed
  version. Note the prior redteam hash and move on.
- The implementation is explicitly a working draft, the test suite is
  incomplete, or the spec is not at `reviewed` status across the
  sections the implementation covers. Red-team only against a
  stabilised spec and a passing test suite.

## Provenance

This skill was extracted from the first implementation red-team session
(spec `000-static-infomax-fig1`); see the corresponding transcript in
`transcripts/` for the original reasoning. The five-category structure,
the `[test-gap]` and `[spec-implication]` routing tags, and the
test-failure branch were all decided during that session; this skill
codifies them so subsequent implementation red-teams don't rediscover
the shape.
