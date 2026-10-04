# Skill: red-team-spec

> Use after a spec in `specs/` has been written or substantially modified, to find
> errors and weaknesses **before** any code is written against it. Shared rules (the
> spawn gate, sub-agent rules, report shape, annotation, resolution) are in
> `skills/red-team.md`; this file holds only what is specific to specs.

## Prompt template

Run the spawn-configuration gate (`skills/red-team.md` §1), then spawn with:

```
You are a hostile reviewer of the specification at <SPEC_PATH>. Before anything else,
read `skills/red-team.md` §3 (sub-agent rules) and the "Sub-agent brief" section of
`skills/red-team-spec.md`, and follow both throughout. Approved red-teamers:
<APPROVED_ROSTER>. Effort tier: <EFFORT_TIER>. Roster verified: <ROSTER_VERIFIED_DATE>.
```

## Sub-agent brief

### Reading order and scope

Read the spec, and any files it references (notes, prior specs, diagrams). Then attack
it.

### Checklist

Failure modes, roughly in order of value:

1. **Conceptual confusion**: a reasoning step that gives a mathematical formula an
   interpretation it does not have, or contains a logical error, a non sequitur or plain
   nonsense.
2. **Aims not achieved**: any reason the spec does not really achieve its stated goal; a
   conceptual gap that will prevent the experiment from demonstrating what it is stated
   to demonstrate.
3. **Inconsistency with the literature**: a claim about existing results that is not
   true or not consistent with the literature.
4. **Math errors**: sign flips, missing factors, dimension mismatches, misapplied
   identities, expectations over the wrong distribution, index errors in sums and
   products.
5. **Unstated assumptions**: places where the derivation goes through only under
   conditions the spec does not name (differentiability, boundedness, independence,
   stationarity, finite variance, full rank). Say which is missing where.
6. **Spec/algorithm mismatch**: the pseudocode does not implement the math; the
   algorithm optimises something other than the stated objective; the properties to
   verify do not all follow from the math as written.
7. **Notation drift or clash**: a symbol changes meaning between sections; a vector
   silently becomes a scalar; an expectation switches distribution implicitly; a symbol
   breaks *Symbol choice* in `skills/write-math-spec.md`.
8. **Edge cases the spec ignores**: empty, degenerate, zero-variance, infinite-support or
   single-sample inputs.
9. **Vague claims**: any sentence using "natural", "obvious", "clearly", "well-known" or
   "standard". These words usually hide a step the author did not want to write out.
10. **Test coverage**: a capability the proposed test suite leaves uncertain.
11. **Document checks** (`skills/red-team.md` §3, rule 6).

### Findings

Severity: **high** invalidates the result; **medium** requires a non-trivial fix or
restricts scope; **low** is cosmetic but should be addressed. Within a severity level,
order by location in the spec, earliest first. No routing tags: a spec has nothing
upstream of it.

### Report

Write to `<SPEC_PATH_WITHOUT_EXTENSION>-redteam.md`. The artefact in "What the …
gets right" is the spec.

## Variants

`red-team-spec-conceptual.md` runs this brief on the conceptual and maths sections only,
before the algorithm and tests exist.
