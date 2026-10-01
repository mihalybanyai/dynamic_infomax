# Skill: red-team (shared core)

> The core shared by every red-team skill. A stage skill says *what* to attack in its
> artefact; this file says how every red-team is configured, spawned, reported and
> resolved. Change a rule here once; change a stage skill only for what is specific to
> its stage.

## Why red-team

An artefact checked by the agent that produced it inherits that agent's anchoring: the
reasoning behind it is in context, so the check tends to confirm rather than challenge.
A red-team breaks the anchor with a fresh sub-agent under adversarial framing.

## The stages

| Stage | Skill | Runs after | Report |
|---|---|---|---|
| Spec | `red-team-spec.md` | a spec is written or substantially revised | `specs/NNN-*-redteam.md` |
| Spec, conceptual | `red-team-spec-conceptual.md` | a spec's conceptual and maths sections are written, before its algorithm and tests | `specs/NNN-*-redteam-conc.md` |
| Tests | `red-team-tests.md` | a test suite is derived from a spec | `tests/test_NNN_*-redteam.md` |
| Implementation | `red-team-implementation.md` | the implementation passes the red-teamed tests and its docs exist | `<doc dir>/redteam-impl.md` |
| Result | `red-team-result.md` | an experiment has run and been written up | `experiments/NNN-*/redteam-result.md` |

Each stage skill has the same parts: when to use it; a short prompt template; a
**sub-agent brief** (reading order and scope, checklist, stage-specific finding rules,
report details); and stage-specific notes on resolving. The stage workflows in
`workflows/invoke-red-team-on-*.md` orchestrate a whole pass.

## 1. The spawn-configuration gate (main agent, before spawning)

The sub-agent inherits this session's model and effort tier. Effort is not
machine-checkable from inside the agent, and the model *version* cannot be selected at
spawn, so the only guard is to put the configuration in front of the human and get
explicit ratification. Before spawning, the main agent MUST:

1. **Print the roster.** Reproduce the "Red-team reviewer roster" table from
   `AGENTS.md`, with its **Last verified** date, and print this session's declared model
   identity.
2. **Print the inheritance caveats and ask to proceed:**

   > Red-team spawn check:
   > - Model: this session is `<declared identity>`; the sub-agent inherits it. For the
   >   diversity pass on the *other* approved model, stop now and re-run this trigger
   >   from a session set to that model (a separate thread).
   > - Effort: the sub-agent inherits this session's effort tier. Policy is the highest
   >   available tier; this is NOT machine-checkable. If this session is not at the
   >   highest tier, stop now, raise it, and re-run this trigger.
   > - Replying "go" both spawns the red team **and** ratifies the roster above as
   >   current: its Last verified date will be set to today. If the roster is stale (a
   >   newer model shipped, a tier changed), fix the table first, then reply "go".

3. **Wait for an explicit "go".** Do not call the `Task` tool until the human replies.
   Conversational acknowledgement is not "go".
4. **On "go":** set the roster's **Last verified** date in `AGENTS.md` to today and
   commit it with the red-team artefacts (the human's "go" *is* the verification), then
   spawn (§2).

The gate is the sole guard for effort and the cross-session guard for model version;
the sub-agent's identity check (§3, rule 1) is the agent-verifiable backstop.

## 2. Spawning (main agent)

Use the `Task` tool with the stage skill's prompt template. Substitute the stage's
placeholders and the gate's: the **approved roster** (`<APPROVED_ROSTER>`), the
human-ratified **effort tier** (`<EFFORT_TIER>`) and the roster's **Last verified** date
(`<ROSTER_VERIFIED_DATE>`). Every template tells the sub-agent to read §3 below and the
stage's sub-agent brief; do not paste their contents into the prompt instead, so each
rule keeps one home.

## 3. Sub-agent rules (every red-team sub-agent follows these)

1. **Identity check first.** Print your declared model identity. If it is not among the
   approved red-teamers named in your prompt, STOP: write nothing to the report file and
   reply only "Model mismatch: I am <identity>, not an approved red-teamer. Aborting."
2. **Environment.** Run Python via `uv run python` (or `uv run <script.py>`); the
   environment already ships numpy, scipy, matplotlib, pypdf, pypdfium2 and daft-pgm.
   Install nothing (no `pip install`, no `uv add`); `uv pip list` shows what is there.
3. **Independence.** Do not read any other red-team report (`*-redteam*.md`, prior or
   concurrent) for this artefact.
4. **Be hostile and specific.** You have no investment in the artefact being right; your
   reputation depends on finding real flaws that other reviewers would also find. Name
   the location and the concrete failure. Useless: "the proof in §3 might not work."
   Useful: "the inequality in (3.7) needs `f` convex, but §2 defines `f` as a difference
   of convex functions, which is not convex in general."
5. **Do not invent concerns.** A short report with three real flaws beats a long one
   with twenty fake ones. If you find nothing substantial in a category, say so.
6. **Document checks** (when your brief asks for them). Also flag:
   - *hidden load-bearing content*: a claim the argument depends on that appears only in
     an appendix, a footnote or a sibling file;
   - *unmarked provenance*: a claim neither shown in the document nor checked by code
     that carries no `[read: …]`, `[recalled]` or `[guess]` tag, or a `[read: …]` tag
     whose source does not say what is claimed (`AGENTS.md`, *Epistemic tags*);
   - *linear-reader breaks*: a symbol, acronym, label or coined term used before it is
     defined, linked to `GLOSSARY.md` or pointed to (`AGENTS.md`, *Readable top to
     bottom*).
7. **Routing tags** (when your brief allows them). A finding that points upstream of
   your artefact gets a tag instead of an in-place fix. At most one per finding: if it
   implies several levels, pick the highest-leverage one and name the others in the
   concern.
   - `[spec-implication]`: the spec is wrong, incomplete or ambiguous in a way that
     matters here.
   - `[test-gap]`: the test suite would not catch a class of bug it should.
   - `[code-implication]`: a code bug that the tests missed, scoped to the code.
8. **Findings.** Each states at least **Location**, **Concern**, **Severity** and **What
   would resolve it**. Severity is high, medium or low, calibrated by your brief (or by
   the invoking prompt if the brief leaves it open).
9. **Ordering.** Descending severity, then your brief's ordering key, unless the brief
   says otherwise. Number findings F1, F2, … *after* ordering.
10. **Minor findings.** Low-severity findings get no F-block: list them under `## Minor`,
    after the F-blocks, one line each (`m1 — <location> — <concern> — <fix>`).
11. **Report.** Write it to the path your brief gives, in this shape (your brief adds
    header lines, finding fields and closing sections where needed):

    ```
    # Red-team review of <ARTEFACT_NAME>

    Reviewer: red-team sub-agent
    Reviewer model (declared identity): <the identity printed under rule 1>
    Effort tier: <EFFORT_TIER> (human-set; not machine-verified)
    Roster verified: <ROSTER_VERIFIED_DATE>
    Date: <YYYY-MM-DD>
    Spec version: <git commit hash if available>

    ## Summary

    <One paragraph: overall impression, where the work is thinnest, whether it is ready
    for downstream work (your brief says what to focus on). No counts of findings by
    severity: the list is the source of truth, and separately produced counts drift.>

    ## Findings

    ### F1: <short title> [severity: high] [<routing tag, if any>]

    **Location**: <…>

    **Concern**: <…>

    **What would resolve it**: <…>

    ---

    ### F2: ...

    ## Minor

    - m1 — <location> — <concern> — <fix>

    ## What the <artefact> gets right

    <One short paragraph, not flattery: what the author must not break while fixing.>
    ```

## 4. Annotating the report (human and main agent)

The report is a living document. Annotated in place, it becomes the audit trail of what
was flagged, what the human decided and what was done. Annotations go two newlines below
what they answer.

- **`> M:`** (the human's initial): *apply* (with any wording specifics), *dismiss*
  (with the reason) or *uncertain* (with the question). One `> M:` may answer the whole
  Minor list, e.g. "apply all except m3".
- **`> M?:`**: the human cannot evaluate the finding yet; the question itself needs
  unpacking, not just its answer. It is discussed in chat before any `> C:`: Claude gives
  an explainer calibrated to what the evaluation needs, and the human upgrades to `> M:`
  once able to judge. Recurring concepts are promoted to `tutorials/` (see the stage
  workflow).
- **`> C:`**: what was actually done: the commit, the artefacts touched, status flips and
  revision-log entries, or that the finding was dismissed or routed upstream.

```markdown
### F3: Differentiability assumption unstated [severity: medium]

**Location**: §1.4

**Concern**: The optimisation step differentiates `f`, but §1.2 defines `f` as a max of
two functions, which is not differentiable everywhere.

**What would resolve it**: State the assumption, or replace the step with a subgradient
version.

> M: Apply; use subgradients. The max is over a finite set, so the subgradient is well
> defined.

> C: Applied in commit a3f4d12. §1.4 now uses subgradient notation; its status flipped
> to draft; revision-log entry added as Clarification.
```

## 5. Resolving (main agent)

Each finding ends in one of three ways, recorded in its `> C:`:

- **Fix** it in the right artefact, citing the commit and any status changes.
- **Dismiss** it, with the human's justification in the `> M:`.
- **Route** it upstream (findings with a routing tag): the `> C:` records the routing;
  the workflow handles re-running or scheduling the upstream red-team.

Status flips follow the project's direction asymmetry: Claude flips backwards on
revision, the human flips forwards on review. The report is committed together with the
changes it caused. Stage-by-stage processing is in `workflows/invoke-red-team-on-*.md`.

## 6. When to skip

- A trivial revision (typo, notation, rename, behaviour-preserving refactor) of an
  artefact that has already been red-teamed: note the prior report's commit and move on.
- An artefact explicitly marked as a working draft: red-team only stabilised artefacts.

Stage skills may add prerequisites.
