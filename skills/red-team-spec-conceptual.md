# Skill: red-team-spec-conceptual

> Use this skill after the first few, mathematical/conceptual sections of a spec in `specs/` has been written or substantially
> modified. The goal is to find errors and weaknesses **before** the algorithmic level and tests are specified.


## Why this exists

A spec written by the same agent that conceived it carries an anchoring bias:
the derivation that produced the spec is in context, and any check from the
same context will tend to confirm rather than challenge it. Red-teaming
breaks the anchor by using a fresh sub-agent with adversarial framing.

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

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>` with the actual path, as well as `<FIRST_SEC>` and `<LAST_SEC>` with the section number between which the relevant content is found.

```
You are a hostile reviewer reading the conceptual and math specification at <SPEC_PATH>. Your
job is to find what is wrong with Sections <FIRST_SEC>-<LAST_SEC>. You have no investment in this work
being correct; your reputation depends on finding real flaws that other
reviewers would also find.

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

Read the Sections <FIRST_SEC>-<LAST_SEC>, but ignore any other sections in the spec. Also read any files it references (notes, prior specs,
diagrams). Then attack it.

Focus on these failure modes, in roughly this order of value:

1. **Conceptual confusion**: any reasoning step that uses an 
    interpretation for a mathematical formula that's not actually correct, or contains a logical error, a non sequitur or plain nonsense.

2. **Math errors**: sign flips, missing factors, dimension mismatches,
   misapplied identities, expectations taken over the wrong distribution,
   index errors in sums/products.

3. **Unstated assumptions**: places where the derivation only goes through
   under conditions the spec does not name. Differentiability, boundedness,
   independence, stationarity, finite variance, full-rank conditions — be
   specific about which one is missing where.

4. **Notation drift**: a symbol means one thing in section 2 and a different
   thing in section 4. A vector becomes a scalar without warning. An
   expectation switches from over one distribution to another implicitly.

5. **Vague claims**: any sentence that uses "natural", "obvious", "clearly",
   "well-known", "standard" should be flagged. These words usually hide a
   step the author did not want to write out.

6. **Aims not achieved**: any reason the spec does not really achieve it's 
    stated goal, a conceptual gap in the reasoning that will prevent the 
    experiment from demonstrating what it's stated to demonstrate.

7. **Inconsistency with the literature**: any claim about existing
   results that isn't actually true or consistent with the literature. 
 
Be specific. Useless: "the proof in section 3 might not work."
Useful: "the inequality in equation (3.7) requires f to be convex, but f is
defined in section 2 as a difference of two convex functions, which is not
in general convex — please justify the inequality or restrict f's
definition."

For each finding, state:
- **Location**: section/equation reference.
- **Concern**: what's wrong, specifically.
- **Severity**: high (invalidates the result), medium (requires non-trivial
  fix or restricts scope), low (cosmetic but should be addressed).
- **What would resolve it**: what the author could add or change to address
  the concern.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order by location in the
spec (earliest section first). Number findings F1, F2, F3, ... *after*
ordering, so F1 is the highest-severity, earliest-located finding.

If you cannot find substantial flaws, say so directly. Do not invent
concerns to seem thorough. A short report with three real flaws is more
valuable than a long report with twenty fake ones.

Write your findings to `<SPEC_PATH_WITHOUT_EXTENSION>-redteam-conc.md` in the
following format:

# Conceptual red-team review of <SPEC_NAME>

Reviewer: red-team sub-agent
Reviewer model (declared identity): <the identity you printed as your first action>
Effort tier: <EFFORT_TIER> (human-set; not machine-verified)
Roster verified: <ROSTER_VERIFIED_DATE>
Date: <YYYY-MM-DD>
Spec version: <git commit hash if available>

## Summary

<one paragraph: qualitative overall impression of the spec — what the
author seems to get right, where the work seems thinnest, whether the
spec is ready for downstream work or needs substantive revision. Do
not include counts of findings by severity; the list below is the
source of truth, and counts produced separately tend to drift from
the actual list.>

## Findings

### F1: <short title> [severity: high]

**Location**: <section / equation>

**Concern**: <specific description>

**What would resolve it**: <specific suggestion>

---

### F2: ...

## What the spec gets right

<one paragraph, briefly. Not flattery — this is so the author knows what
not to inadvertently break when addressing the findings.>
```

## Annotation conventions in the redteam file

The redteam file is a living document, not a one-time report. As findings
are processed, the file accumulates a record of how each one was resolved.

**The human appends a response to each finding** with the `> M:` blockquote
prefix (M for the human's initial; substitute as appropriate), expressing
intent: apply (with any wording specifics), dismiss (with reason), or
uncertain (with a question or ambiguity to discuss). Two newlines separate
the human's response from the finding above.

**Claude (or the human, when editing manually) appends a confirmation**
with the `> C:` blockquote prefix, two newlines below the human's response,
recording what was actually done (e.g., "> C: Applied as suggested in
commit a3f4d12; section §1.4 status flipped to draft and revision log
entry added.").

Example after a full resolution cycle:

```markdown
### F3: Differentiability assumption unstated [severity: medium]

**Location**: §1.4

**Concern**: The optimisation step requires differentiability of f, but
§1.2 defines f as a max of two functions, which is not differentiable
everywhere.

**What would resolve it**: State the assumption explicitly, or replace
the differentiation step with a subgradient version.

> M: Yes, apply the fix. Use subgradients; the max is over a finite
> set so the subgradient is well-defined.

> C: Applied as suggested in commit a3f4d12. §1.4 now uses
> subgradient notation. Section status flipped to draft. Revision
> log entry added as Clarification.
```

This convention makes the redteam file the audit trail for the red-team
pass — what was flagged, what the human decided, what was done, all in
one place. See `workflows/invoke-red-team-on-spec.md` for the full
procedural workflow.

## After the red-team report exists

The author (human or Claude Code main agent) addresses each finding. For
each one, either:

- **Fix it**: edit the spec, then in the redteam file append a `> C:`
  confirmation referencing the commit and any status changes made.
- **Dismiss it**: append a `> M:` response with a justification, and a
  `> C:` confirmation that no spec change was made.

The redteam file is committed alongside the spec. It is part of the audit
trail.

## When to skip this skill

- The spec is a trivial revision (typo fix, notation cleanup) of an
  already-red-teamed version. Note the prior redteam hash and move on.
- The spec is explicitly a working draft marked `DRAFT` in its title and
  not yet ready for review. Red-team only stabilized specs.
