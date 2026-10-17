# Workflow: invoke-red-team-on-spec

> Red-team a spec, then decide and apply each finding. Shared stages are in
> `workflows/invoke-red-team.md`; this file holds only what is specific to specs.

## When to use

When every section of a spec in `specs/` is `reviewed`: the gate between
"human-reviewed" and "approved for downstream work that depends on the whole spec". Not
while any section is `draft` or `needs-revision`.

The conceptual variant (`skills/red-team-spec-conceptual.md`) runs earlier, once the
conceptual and maths sections are `reviewed` and before the algorithm and tests are
written. Everything below applies to it too, with its own Stage 1 prompt.

## Prerequisites

The sources the spec cites are reachable: PDFs in `resources/`, other references mapped
in `literature/`. How the sub-agent uses them is in the skill's brief.

## Stage 1 — Invoke

```
Red-team [[SPEC_PATH]] with skills/red-team-spec.md, following
workflows/invoke-red-team.md Stage 1.
```

Conceptual variant:

```
Red-team Sections [[FIRST_SEC]]–[[LAST_SEC]] of [[SPEC_PATH]] with
skills/red-team-spec-conceptual.md, following workflows/invoke-red-team.md Stage 1.
```

## Stages 2 and 3a — Annotate and decide

As in `workflows/invoke-red-team.md`. Every `> C:` touches the spec; nothing is upstream
of a spec, so nothing is routed.

## Stage 3b — Apply

*Spec edits* in `workflows/invoke-red-team.md`. The human then re-reviews the affected
sections; when a section flips back to `reviewed`, its red marking is removed in the same
edit. Downstream work resumes against the revised sections per the downstream-approval
rules in `skills/write-math-spec.md`.
