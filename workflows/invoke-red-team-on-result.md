# Workflow: invoke-red-team-on-result

> Red-team an experimental result, then decide, return upstream if needed, apply the
> in-experiment changes and re-read the report. Shared stages are in
> `workflows/invoke-red-team.md`; this file holds only what is specific to results.

## When to use

When an experiment in `experiments/NNN-*/` has run and its figures and `REPORT.md` are
written: the gate between "ran cleanly and produced a report" and "established, citable
by downstream work". Run it only against a fully stabilised upstream chain. Findings
against a still-moving spec or implementation conflate "the result is wrong" with "what
it was produced against has since changed".

## Prerequisites

- The spec is `reviewed` in all relevant sections and has been through
  `invoke-red-team-on-spec.md`.
- The test suite, the implementation and its docs (`docs/<spec-id>/`) are at their
  post-red-team states, and the implementation passes the full suite at HEAD.
- `output/provenance.json` records the commits, seed and package versions of the run.

## Stage 1 — Invoke

```
Red-team the result in [[EXPERIMENT_DIR]]/REPORT.md with skills/red-team-result.md,
following workflows/invoke-red-team.md Stage 1.
```

## Stage 2 — Annotate

As in `workflows/invoke-red-team.md`. Routing tags here can point at any earlier stage,
so check each. This red-team is also the most prone to speculative concerns
(`skills/red-team-result.md`, *Caveat*): expect pushback on applies you have not waived
it for.

## Stage 3a — Decide

As in `workflows/invoke-red-team.md`, upstream check first. Each `> C:` names what it
touches: the report, the experiment code, a figure (regenerated), an upstream artefact
via a routing tag, or nothing (dismissed, or accepted as a limitation).

## Stage 3b — Return upstream (if needed)

If 3a found that the pass must return to an earlier stage, or accepted a routed finding,
run the upstream workflows now (*Routing upstream* in `workflows/invoke-red-team.md`)
and come back once upstream is stable again; the remaining stages run against the new
upstream state. Otherwise skip to 3c.

## Stage 3c — Apply

```
Make the edits the `> C:` annotations in [[EXPERIMENT_DIR]]/redteam-result.md call
for. Re-run the experiment if code or seed changed, regenerate the affected figures and
edit REPORT.md, marking each change red. Update [[EXPERIMENT_DIR]]/output/provenance.json
with the new commit and package versions. Commit each finding's edits separately, with
messages naming the finding ("F3: add constant-predictor baseline"). Leave the red
marking in place.
```

Per-finding commits make each `> C:` point at exactly one change.

## Stage 3d — Re-read and finalise

The human re-reads the report with the red marking in place. This is the gate: if a
marked change does not say what the human wanted, return to 3c with specific edits.
Then:

```
Looks good. Remove the red marking from the report and commit the cleanup. Record in
REPORT.md how each high-severity finding was resolved, or that it is outstanding, with
a pointer to the follow-up.
```

A finding accepted as a limitation is stated as one in the report, with its
justification: the record that it was considered, not missed. The result counts as
established once no high-severity finding is unresolved (`skills/red-team-result.md`).
