# Skill: red-team-result

> Use after an experiment in `experiments/NNN-*/` has been run and written up in
> `REPORT.md`, with its spec, tests and implementation all at their post-red-team
> states. The goal is to find alternative explanations for the result before claiming
> it supports the hypothesis. Shared rules are in `skills/red-team.md`; this file holds
> only what is specific to results.

## Why this stage

The failure that bites scientists worst: a real experiment produced a real number that
looks like success, but something other than the hypothesis explains it, such as a bug,
a confound, a trivial baseline, a statistical artifact, overfitting to one
configuration, or a figure that says less than the report claims. A sub-agent reading
only the spec, plan, code, figures and report, without the development context, is well
placed to ask what else could explain the result.

This is the last red-team in the pipeline, so a finding can send the workflow back to
any earlier stage; the routing tags name where.

## Prompt template

Run the spawn-configuration gate (`skills/red-team.md` §1), then spawn with:

```
You are reviewing the experimental result documented in <EXPERIMENT_DIR>/REPORT.md.
Before anything else, read `skills/red-team.md` §3 (sub-agent rules) and the "Sub-agent
brief" section of `skills/red-team-result.md`, and follow both throughout, with
<EXPERIMENT_DIR> as the experiment directory. Approved red-teamers: <APPROVED_ROSTER>.
Effort tier: <EFFORT_TIER>. Roster verified: <ROSTER_VERIFIED_DATE>.
```

## Sub-agent brief

### Reading order and scope

Inputs: `<EXPERIMENT_DIR>/REPORT.md`, the plan `<EXPERIMENT_DIR>/PLAN.md`, the code
`<EXPERIMENT_DIR>/run.py` (or as the plan names it), and the specs and modules the plan
references. Provenance (git commits, seed, package versions) is in
`<EXPERIMENT_DIR>/output/provenance.json`; consult it whenever it matters which version
of the spec, code or tests the run used, since they may have moved on.

Take as settled: the math (spec `reviewed`), test coverage (tests red-teamed), and the
implementation against the spec (implementation red-teamed, tests passing). Your job is
the gap between "the code ran and produced numbers and figures" and "the result, as
written up, supports the claim the report makes".

Read the spec and plan first, then the report with its figures, and only then the code.
A code-first picture makes you unconsciously correct for inaccuracies in the report.

Out of scope: style of the report; follow-up experiments unconnected to defending this
result; re-auditing math, coverage or implementation (tag such findings instead).

### Checklist

For each result claim, ask:

1. **Bug-as-feature**: could a specific bug produce this result? What is the simplest
   wrong implementation that would, and would any test distinguish it?
2. **Trivial baseline**: what does the simplest baseline produce (random or constant
   predictor, nearest neighbour without learning, input passed through)? An unreported
   baseline is a finding.
3. **Confound**: could a feature of the data or protocol produce the result without the
   claimed mechanism (class imbalance, train–test leakage, a correlated nuisance
   variable, an unintended ordering)?
4. **Statistical artifact**: how does the metric behave under the null? Is the effect
   large against its standard error and the chance level?
5. **Seed and configuration sensitivity**: single seed, split or hyperparameter? Then
   the variance is unknown; recommend the minimum robustness check (3–5 seeds at least).
6. **Cherry-picking risk**: how many configurations were tried before this one, and is
   there a paper trail of the failures? If not, flag the multiple-comparisons risk.
7. **Plot artifacts**: truncated axes; a log scale hiding a different linear story (or
   the reverse); error bars that are missing or not what they appear to be; a caption or
   legend claiming what the data do not show.
8. **Report-versus-result mismatch**: prose claiming more than the numbers show: "X
   improves over Y" within noise, "robust" from two conditions, "scales" from two points.
9. **Sanity checks not run**: e.g. overfitting a small dataset, loss going down,
   behaviour on a held-out example you understand by hand.
10. **Document checks** (`skills/red-team.md` §3, rule 6), applied to the report.

### Findings

**Location** is the claim, figure or report section concerned. Severity: **high** if
the result might not support the hypothesis at all; **medium** if it needs an additional
control to support it cleanly; **low** for a check worth adding for defensibility even
if it would not change the conclusion. All three routing tags are allowed, shown in the
header as `[routing: …]`; an untagged finding is scoped to this experiment (a report
edit, a change to its own `run.py`, a regenerated figure, a new baseline run, or an
accepted limitation). What would resolve it may be an experiment, baseline, control,
analysis or edit; say if it touches an upstream artefact. Within a severity level, order
by checklist category.

### Report

Write to `<EXPERIMENT_DIR>/redteam-result.md`, titled "Red-team review of experiment
<EXPERIMENT_NAME>". Add two header lines after "Spec version": `Experiment commit:` and
`Spec commit(s) reviewed against:`, both from `provenance.json`. Summary focus: how
strongly the result supports the hypothesis as presented, which alternative
explanations are most concerning, what would change the picture. The artefact in "What
the … gets right" is the experiment.

End with one plain-language paragraph: if, after all your concerns were addressed, the
hypothesis would still be supported, say so; if the concerns are severe enough that the
current result should not count as evidence for it, say that.

## After the report

Processing follows `workflows/invoke-red-team-on-result.md`. It begins with one global
question: does any finding, alone or with others, force a return to an earlier stage?
If so, raise it in chat before processing findings one by one, and pause in-experiment
edits until the upstream artefact is stable again. Each `> C:` lists every artefact it
touched (report, experiment code, regenerated figures, an upstream artefact via a
routing tag), or none if dismissed or accepted as a limitation.

The result counts as established once no high-severity finding is unresolved, meaning
each is applied or explicitly accepted with a justification in the report. The report
states how each high-severity finding was resolved and links any follow-up experiments.

**Caveat.** This is the red-team most prone to speculative concerns: the broader the
question, the more room for hypothetical alternatives. Treat findings as questions to
investigate, not verdicts, and push back on a confident `> M:` apply when a finding is a
wishlist item dressed as a concern.

Extracted from the first result red-team (experiment `000-static-fig1`); the original
reasoning is in `transcripts/`.
