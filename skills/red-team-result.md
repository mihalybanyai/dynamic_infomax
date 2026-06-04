# Skill: red-team-result

> Use this skill after an experiment in `experiments/NNN-*/` has been run,
> its figures and report (`REPORT.md`) have been written, and the relevant
> spec, tests, and implementation are all already at their post-red-team
> states. The goal is to find alternative explanations for the result
> before claiming it supports the hypothesis.

## Why this exists

This is the failure mode that bites scientists worst: a real experiment
produced a real number that looks like a real success, but the number is
explained by something other than the hypothesis. Common sources:

- A bug that happens to produce hypothesis-consistent results.
- A confound in the experimental design.
- A trivial baseline that would explain the result without the proposed
  mechanism.
- A statistical artifact from how the metric is computed.
- Overfitting to the specific seed / dataset / configuration.
- A figure that, read as a hostile reviewer would read it, says something
  weaker (or different) than the report claims.

A red-team sub-agent reading only the spec, the experiment plan, the
code, the figures, and the report — without the development context —
is well-placed to ask "what else could explain this?"

This is also the *last* red-team in the pipeline. All upstream artifacts
(spec, tests, implementation) have already been red-teamed and the
implementation passes the post-red-team test suite. So this red-team
faces a particular routing question that the earlier ones do not: a
finding can, in principle, send the workflow back to any earlier stage.
The skill names the four destinations and the workflow handles the
dispatch.

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
template. Substitute `<EXPERIMENT_DIR>` with the path (e.g.,
`experiments/000-static-fig1`).

```
You are reviewing the experimental result documented in
<EXPERIMENT_DIR>/REPORT.md. The plan is in <EXPERIMENT_DIR>/PLAN.md.
The experiment code is at <EXPERIMENT_DIR>/run.py (or as named in the
plan). Relevant specs and code modules are referenced from the plan.
Provenance — the exact git commits, seed, and package versions used —
is in <EXPERIMENT_DIR>/output/provenance.json. Consult it whenever
"what version of the spec/code/tests was this run against?" matters
for a finding; the spec, code, or tests may have moved on since the
result was produced.

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

Context: the spec is at status `reviewed` across all relevant
sections, the test suite has been red-teamed, the implementation
passes the red-teamed test suite, and the implementation has itself
been red-teamed. So you are NOT auditing the math (settled), NOT
auditing test coverage against the spec (settled), and NOT auditing
the implementation against the spec (settled). Your job is the gap
between "the code ran cleanly and produced numbers/figures" and "the
result, as written up in the report, actually supports the claim the
report makes." Read the spec and the plan first, then the report
(including its figures), and only then the code. The "report first,
code second" order is deliberate — if you form a code-first picture
you will unconsciously correct for report inaccuracies and miss them.

## Alternative-explanation checklist

For each result claim, ask:

1. **Bug-as-feature**: could the result be produced by a specific bug?
   What is the simplest wrong implementation that would produce this
   exact result? Is there a test that would distinguish?

2. **Trivial baseline**: what does the simplest possible baseline
   produce on this task? If the baseline is not reported, that is a
   finding. Common skipped baselines: random predictor, constant
   predictor, nearest-neighbor with no learning, the input passed
   through unchanged.

3. **Confound**: is there a feature of the data or the protocol that
   could produce this result without the mechanism the hypothesis
   claims? Common confounds: class imbalance, leakage between train
   and test, a correlated nuisance variable, an unintended ordering
   in the data.

4. **Statistical artifact**: how does the metric behave under the
   null? If the result is a correlation, what is the correlation
   expected from noise alone given the sample size? If the result is
   an accuracy, what is the accuracy expected from chance, and is the
   gap large compared to the standard error?

5. **Seed / configuration sensitivity**: was the experiment run with
   a single seed? Single dataset split? Single hyperparameter? If
   yes, the result has unknown variance. Flag this and recommend the
   minimum robustness check (e.g., 3–5 seeds at a minimum).

6. **Cherry-picking risk**: how many configurations were tried before
   this one was reported? Is there a paper trail (in the experiment
   directory, the codegen log, or elsewhere) of the failed
   configurations? If not, flag the multiple-comparisons risk.

7. **Plot artifacts**: if a figure is the main result, examine it as
   a hostile reviewer would. Are axes truncated? Is the y-axis
   log-scale when linear would tell a different story (or vice
   versa)? Are error bars present and do they reflect what they
   appear to reflect (within-run variance vs. between-run variance
   vs. confidence interval)? Does the legend/caption say something
   the data does not support?

8. **Report-vs-result mismatch**: does the prose in the report claim
   more than the figures and numbers actually show? Common drifts:
   "X improves over Y" when the improvement is within noise,
   "robust" when only one or two conditions were tested, "scales"
   from two data points, qualitative reads of figures that the
   figures do not support.

9. **Sanity checks not run**: list checks the experiment did not run
   but should have. Common missing checks: does the model overfit a
   small dataset (basic capacity check)? Does the loss go down
   (basic training check)? Does the model behave reasonably on a
   held-out example you manually understand?

NOT in scope for the sub-agent:

- Style/formatting issues in the report (the human owns those).
- Suggestions for the next experiment unconnected to defending this
  one. Wishlist items are out of scope; only flag follow-up
  experiments that would resolve a specific concern about *this*
  result.
- Re-auditing the math, the test coverage, or the implementation
  against the spec. If a finding actually points at a problem in one
  of those upstream artifacts, tag it (see "Routing tags" below)
  rather than acting on it.

## Routing tags

The result red-team is the last in the pipeline, so a finding can in
principle imply that an earlier artifact was wrong. Tag findings
accordingly so the routing happens at discovery time, not on read:

- `[spec-implication]` — the result reveals that the spec is wrong,
  incomplete, or ambiguous in a way that mattered for the result.
  Routes to the spec red-team workflow rather than being acted on
  here.
- `[test-gap]` — the result reveals a class of bug that the test
  suite, even at its post-red-team state, would not catch. Routes
  to the test red-team workflow.
- `[code-implication]` — the result reveals a bug or mis-implementation
  in the code that the test suite happened to miss but that is
  scoped to the code, not the spec or tests. Routes back to the
  implementation red-team workflow (or directly to a code edit,
  per the human's judgement).
- (Untagged) — the finding is scoped to this experiment: a report
  edit, a code edit in the experiment's own `run.py`, a regenerated
  figure, an additional baseline run, or an acceptance note in the
  report.

A finding can carry at most one routing tag; if it implies issues at
multiple levels, pick the highest-leverage one and note the others
in the concern paragraph.

## Format

For each finding:
- **Concern**: a specific alternative explanation or risk.
- **Severity**: high (the result might not support the hypothesis at
  all), medium (the result needs an additional control to support
  the hypothesis cleanly), low (a check that should be added for
  defensibility, even if you do not expect it to change the
  conclusion).
- **Routing tag**: one of the above, or none.
- **What would resolve it**: a specific additional experiment,
  baseline, control, analysis, code edit, or report edit. If
  resolution requires touching an upstream artifact (spec, tests,
  implementation), say so.

**Ordering**: list findings in order of descending severity (high
first, then medium, then low). Within a severity level, order by
the checklist category above (bug-as-feature first, then trivial
baseline, then confound, etc.). Number findings F1, F2, F3, …
*after* ordering. Do not include counts of findings by severity in
the summary — the list below is the source of truth, and counts
produced separately tend to drift from the actual list.

Write the report to `<EXPERIMENT_DIR>/redteam-result.md`. Suggested
top-level structure:

# Red-team review of experiment <EXPERIMENT_NAME>

Reviewer: red-team sub-agent
Reviewer model (declared identity): <the identity you printed as your first action>
Effort tier: <EFFORT_TIER> (human-set; not machine-verified)
Roster verified: <ROSTER_VERIFIED_DATE>
Date: <YYYY-MM-DD>
Spec version: <git commit hash if available>
Experiment commit: <git commit hash from provenance.json>
Spec commit(s) reviewed against: <as recorded in provenance.json>

## Summary

<one paragraph: qualitative impression — how strongly does the
result support the hypothesis as currently presented, what
alternative explanations are most concerning, what would change the
picture. No counts.>

## Findings

### F1: <short title> [severity: high] [routing: none | spec-implication | test-gap | code-implication]

**Concern**: <specific alternative explanation>

**What would resolve it**: <specific additional experiment / edit
/ analysis>

---

### F2: ...

## What the experiment gets right

<one paragraph, briefly.>

End the report with one paragraph: **If after addressing all your
concerns the hypothesis would still be supported, state that. If
your concerns are severe enough that the current result should not
be taken as evidence for the hypothesis, state that, in plain
language.**
```

## Annotation conventions in the redteam file

The redteam file is a living document, not a one-time report. After
the sub-agent writes it, the human and Claude Code annotate it in
place, so that the file at the end of the workflow is a complete
audit trail of which findings were applied, dismissed, or routed,
and why. The conventions match the other red-team skills:

- The human's first-pass reaction goes on a blank line two newlines
  below each finding, prefixed `> M:` (initial-of-author colon).
- A `> M:` annotation can be a confident *apply* instruction, a
  confident *dismiss* explanation, or an explicit *uncertain*
  question. The same prefix covers all three; the content
  disambiguates.
- For findings where the human cannot evaluate the suggestion well
  enough to apply or dismiss in good conscience — because the
  finding turns on statistical reasoning, mathematics, or
  experimental-design concepts the human does not yet command —
  use `> M?:` (note the question mark) rather than `> M:`. This is
  distinct from "uncertain" (`> M:` with a question): `> M?:` means
  "I'm not sure I understand the question." Findings annotated
  `> M?:` will be discussed in chat before any `> C:` resolution
  is recorded; Claude responds with a calibrated math/stats
  explainer, and the human upgrades the annotation to `> M:` once
  they can evaluate the finding. See
  `workflows/invoke-red-team-on-result.md` stage 3a for the
  promotion-to-tutorial rule.
- Claude Code's resolution goes on a blank line two newlines below
  the `> M:` annotation, prefixed `> C:`. Each `> C:` records
  *which artifact(s)* the change touches — the report, the
  experiment code, a figure (regenerated), an upstream artifact via
  a routing tag, or none (dismissed / accepted as limitation). When
  multiple artifacts are touched, list them all.

Example:

```
### F3: No constant-predictor baseline reported [severity: medium] [routing: none]

**Concern**: The reported accuracy of 0.62 is treated as evidence the
model has learned the structure, but the class distribution is
imbalanced (0.55 majority class). The gap to the constant predictor
is therefore 0.07, not 0.62, and the report does not make this
gap explicit.

**What would resolve it**: Run the constant-predictor baseline,
report the gap, and rewrite the relevant paragraph in REPORT.md.

> M: Confirmed, this is a real omission. Add the constant baseline
> to run.py, rerun, and reword the "Results" paragraph to lead with
> the gap-to-baseline rather than the raw accuracy.

> C: Applied. Added `_constant_baseline()` to run.py (touches
> experiment code), reran the experiment, regenerated Fig 2
> (touches figure), and rewrote the "Results" paragraph in
> REPORT.md (touches report). Commit <hash>.
```

For a routed finding the `> C:` records the routing rather than an
in-place edit:

```
> C: Routed. This is a [test-gap]: the test suite would not catch
> the off-by-one in the windowing function that produced the
> spurious correlation. Filed under the test red-team queue; no
> changes to this experiment until the test gap is resolved
> upstream.
```

For a finding that forces a return to an earlier stage of the
workflow, the `> C:` says so explicitly, and the in-experiment
processing pauses until the upstream artifact has been re-stabilised.
See the workflow file's stage 3a for the discussion convention.

## After the report exists

The redteam file is processed via `workflows/invoke-red-team-on-result.md`.
The workflow's stage 3 has four sub-stages, in order:

1. **Stage 3a — Decide.** First, ask the global question: do *any*
   findings, in aggregate or individually, force a return to an
   earlier stage of the workflow (spec / tests / implementation /
   docs)? If yes, surface that in chat before per-finding processing.
   If no, walk each finding top-down by severity, propose a `> C:`
   for confident `> M:` items, push back where you disagree, ask
   the human where they were uncertain, and respond with a
   calibrated explainer for `> M?:` items.
2. **Stage 3b — Update upstream artifacts (if applicable).** For
   findings tagged `[spec-implication]`, `[test-gap]`, or
   `[code-implication]` that were accepted, hand off to the
   corresponding upstream workflow rather than acting in place. In
   the simplest case (stage 3a determined no upstream return is
   needed and all routing tags were rejected) this stage is empty.
3. **Stage 3c — Apply.** Make the in-experiment edits to `run.py`,
   regenerate the affected figures by re-running the experiment,
   and edit the report text. As with the other red-team workflows,
   apply red colouring to changed regions of the report so the
   human can see the diff visually on re-read.
4. **Stage 3d — Finalise.** After the human has re-read the report
   and approved, remove the red colouring and commit the revision
   as a single commit.

If no high-severity findings remain unresolved (either applied or
explicitly accepted with a documented justification in the report),
the result is considered established. Per project convention, the
report should explicitly state the high-severity findings' resolution
status and link to follow-up experiments where any apply.

## Caveat

This is the red-team skill most prone to producing speculative
concerns that are not really problems — the broader the question,
the more space for hypothetical alternatives. Treat findings as
questions to investigate, not verdicts. The point is to make sure
these questions were asked, not to manufacture an answer of "the
result is wrong." Use the pushback license on `> M:` confident
applies liberally if a finding is genuinely a wishlist item dressed
as a concern.

## Provenance

The annotation conventions, the routing tags
(`[spec-implication]` / `[test-gap]` / `[code-implication]`), the
"return to earlier stage" first-pass check, and the four-sub-stage
processing shape were all decided during the first result red-team
session (experiment `000-static-fig1`); see the corresponding
transcript in `transcripts/` for the original reasoning. This skill
codifies them so subsequent result red-teams don't rediscover the
shape.