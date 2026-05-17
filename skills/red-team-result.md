# Skill: red-team-result

> Use this skill after an experiment in `experiments/NNN-*/` has been run
> and its `README.md` has been written. The goal is to find alternative
> explanations for the result before claiming the result supports the
> hypothesis.

## Why this exists

This is the failure mode that bites scientists worst: a real experiment
produced a real number that looks like a real success, but the number is
explained by something other than the hypothesis. Common sources:

- A bug that happens to produce hypothesis-consistent results.
- A confound in the experimental design.
- A trivial baseline that explains the result without the proposed
  mechanism.
- A statistical artifact from how the metric is computed.
- Overfitting to the specific seed / dataset / configuration.

A red-team sub-agent reading only the spec, the experiment plan, and the
result — without the development context — is well-placed to ask "what
else could explain this?"

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<EXPERIMENT_DIR>` with the path.

```
You are reviewing the experimental result documented in
<EXPERIMENT_DIR>/README.md. The plan is in <EXPERIMENT_DIR>/PLAN.md.
Relevant specs and code are referenced from the plan. Provenance (the
exact git commits, seed, and package versions used) is in
<EXPERIMENT_DIR>/output/provenance.json — consult it if the question
of "what version of the spec/code was this run against" matters for a
finding.

The plan states a hypothesis and the README claims a result that
supports or refutes it. Your job is to challenge that interpretation.

## Alternative-explanation checklist

For each result claim, ask:

1. **Bug-as-feature**: could the result be produced by a specific bug?
   What is the simplest wrong implementation that would produce this
   exact result? Is there a test that would distinguish?

2. **Trivial baseline**: what does the simplest possible baseline produce
   on this task? If the baseline is not reported, that is a finding.
   Common skipped baselines: random predictor, constant predictor,
   nearest-neighbor with no learning, the input passed through unchanged.

3. **Confound**: is there a feature of the data or the protocol that
   could produce this result without the mechanism the hypothesis claims?
   Common confounds: class imbalance, leakage between train and test, a
   correlated nuisance variable, an unintended ordering in the data.

4. **Statistical artifact**: how does the metric behave under the null?
   If the result is a correlation, what is the correlation expected from
   noise alone given the sample size? If the result is an accuracy, what
   is the accuracy expected from chance, and is the gap large compared
   to the standard error?

5. **Seed / configuration sensitivity**: was the experiment run with a
   single seed? Single dataset split? Single hyperparameter? If yes, the
   result has unknown variance. Flag this and recommend the minimum
   robustness check (e.g., 3-5 seeds at a minimum).

6. **Cherry-picking risk**: how many configurations were tried before
   this one was reported? Is there a paper trail (in the experiment
   directory or elsewhere) of the failed configurations? If not, flag
   the multiple-comparisons risk.

7. **Plot artifacts**: if a figure is the main result, examine it as a
   hostile reviewer would. Are axes truncated? Is the y-axis log-scale
   when linear would tell a different story (or vice versa)? Are error
   bars present and do they reflect what they appear to reflect (within-
   run variance vs. between-run variance vs. confidence interval)?

8. **Sanity checks not run**: list checks the experiment did not run but
   should have. Common missing checks: does the model overfit a small
   dataset (basic capacity check)? Does the loss go down (basic training
   check)? Does the model behave reasonably on a held-out example you
   manually understand?

## Format

For each finding:
- **Concern**: a specific alternative explanation or risk.
- **Severity**: high (the result might not support the hypothesis at all),
  medium (the result needs an additional control to support the
  hypothesis cleanly), low (a check that should be added for
  defensibility, even if you do not expect it to change the conclusion).
- **What would resolve it**: a specific additional experiment, baseline,
  control, or analysis.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order by the checklist
category above (bug-as-feature first, then trivial baseline, then
confound, etc.). Number findings F1, F2, F3, ... *after* ordering.

Write to `<EXPERIMENT_DIR>/result-redteam.md`. Do not include counts of
findings by severity in the summary.

# Red-team review of experiment <EXPERIMENT_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Experiment commit: <git commit hash from provenance.json if available>
Spec commit(s) reviewed against: <as recorded in provenance.json>

## Summary

<one paragraph: qualitative impression — how strongly does the result
support the hypothesis as currently presented, what alternative
explanations are most concerning, what would change the picture. No
counts.>

## Findings

### F1: <short title> [severity: high]

**Concern**: <specific alternative explanation>

**What would resolve it**: <specific additional experiment / analysis>

---

### F2: ...

## What the experiment gets right

<one paragraph, briefly.>

End the report with one paragraph: **If after addressing all your
concerns the hypothesis would still be supported, state that. If your
concerns are severe enough that the current result should not be taken
as evidence for the hypothesis, state that, in plain language.**
```

## Annotation conventions in the redteam file

Same as `skills/red-team-spec.md`: `> M:` for the human's response,
`> C:` for the confirmation of action taken, two newlines between each.

For result findings specifically, the `> C:` annotation often references
a *follow-up experiment* directory rather than a code commit, since the
typical resolution is to run a control or additional baseline rather
than to edit existing code.

Example:

```markdown
### F2: No random-prior baseline reported [severity: medium]

**Concern**: The result shows the MI-maximising prior produces a
particular figure shape, but the README does not show what a random
prior produces. Without a baseline, the apparent specificity of the
result could just be a generic property of the BA solver on this
likelihood.

**What would resolve it**: Add an experiment that runs BA with a
random initial prior (averaged over several seeds) and compare the
resulting figure to the MI-maximising one.

> M: Apply. Run with three random initial priors as a sanity-check
> baseline. Should not change the BA result since BA converges, but
> it's the kind of thing reviewers will ask about.

> C: Follow-up experiment created at experiments/001-random-prior-baseline/.
> PLAN.md drafted, run pending. Original experiment README updated to
> note this follow-up is in flight.
```

## After the report exists

The author either:

- **Runs additional experiments** to address findings. Each follow-up
  experiment gets its own `experiments/NNN-*/` directory with its own
  PLAN and README. The original experiment's README links to the
  follow-ups. The `> C:` annotation references the follow-up
  directory.
- **Documents acceptance of the limitation** in the `> M:` response
  and in the experiment's README, explaining why the limitation does
  not undermine the use being made of the result. The `> C:`
  annotation confirms the README was updated.

For the project as a whole, a useful convention: a result is *not*
considered established until at least the high-severity findings from its
redteam are addressed. The experiment README should explicitly state
the high-severity findings' resolution status and link to follow-up
experiments where relevant.

## Caveat

This is the red-team skill most prone to producing speculative concerns
that are not really problems. Treat findings as questions to investigate,
not verdicts. The point is to make sure these questions were asked, not
to manufacture an answer of "the result is wrong."
