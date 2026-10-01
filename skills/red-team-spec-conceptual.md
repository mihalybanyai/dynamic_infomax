# Skill: red-team-spec-conceptual

> Use after the first, conceptual and mathematical sections of a spec in `specs/` have
> been written or substantially modified, to find errors and weaknesses **before** the
> algorithm and tests are specified. A variant of `red-team-spec.md`; shared rules are
> in `skills/red-team.md`. This file holds only the differences.

## Prompt template

Run the spawn-configuration gate (`skills/red-team.md` §1), then spawn with this,
substituting `<FIRST_SEC>` and `<LAST_SEC>` with the section numbers bounding the
conceptual content:

```
You are a hostile reviewer of Sections <FIRST_SEC>–<LAST_SEC> of the conceptual and
mathematical specification at <SPEC_PATH>. Before anything else, read
`skills/red-team.md` §3 (sub-agent rules) and the "Sub-agent brief" section of
`skills/red-team-spec-conceptual.md`, and follow both throughout. Approved
red-teamers: <APPROVED_ROSTER>. Effort tier: <EFFORT_TIER>. Roster verified:
<ROSTER_VERIFIED_DATE>.
```

## Sub-agent brief

Follow the "Sub-agent brief" of `skills/red-team-spec.md`, with these changes:

- **Scope.** Read Sections `<FIRST_SEC>`–`<LAST_SEC>` and the files they reference;
  ignore the other sections of the spec.
- **Checklist.** Use these failure modes from the red-team-spec checklist, in this
  order: conceptual confusion (1), math errors (4), unstated assumptions (5), notation
  drift (7), vague claims (9), aims not achieved (2), inconsistency with the literature
  (3), document checks (11). Skip spec/algorithm mismatch, edge cases and test coverage:
  the sections they concern do not exist yet.
- **Report.** Write to `<SPEC_PATH_WITHOUT_EXTENSION>-redteam-conc.md`, titled
  "Conceptual red-team review of <SPEC_NAME>".
