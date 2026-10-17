# Workflow: invoke-red-team (shared core)

> The stages every red-team pass shares: invoke, annotate, decide, and the spec-edit
> step. A stage workflow (`invoke-red-team-on-<stage>.md`) holds only what differs: when
> to run it, what a decision can touch, and how changes are applied. Change a shared
> stage here once.

What the sub-agent does is in the skills (`skills/red-team.md` and its stage skills).
The workflows cover what the human pastes and what the main agent does around the
sub-agent.

## The stage workflows

| Stage | Workflow | Skill | A `> C:` may touch | Stage-specific stages |
|---|---|---|---|---|
| Spec | `invoke-red-team-on-spec.md` | `red-team-spec.md`, `red-team-spec-conceptual.md` | spec | 3b spec edits |
| Tests | `invoke-red-team-on-tests.md` | `red-team-tests.md` | spec, tests | 3b spec edits; 3c regenerate tests |
| Implementation | `invoke-red-team-on-impl.md` | `red-team-implementation.md` | spec, code, docs, doc helper scripts; or routed | 3b spec edits; 3c regenerate code and docs; 3d re-run tests |
| Result | `invoke-red-team-on-result.md` | `red-team-result.md` | report, experiment code, figures; or routed | 3b return upstream; 3c apply; 3d re-read |

Every pass runs Stages 1, 2 and 3a below, then its stage workflow's later stages. Common
prerequisites: the session is oriented (`workflows/wake-up-claude-code.md`) and the
artefact is stable (`skills/red-team.md` §6); stage workflows add their own.

## Stage 1 — Invoke the sub-agent

The human pastes the stage workflow's one-line prompt. The main agent then:

1. Runs the spawn-configuration gate (`skills/red-team.md` §1). At the gate the human
   checks the model and that the roster is current, then replies "go". Effort needs no
   check: the main agent sets it at spawn.
2. Spawns as in `skills/red-team.md` §2.
3. Does not read or pre-filter the findings, and commits the report when the sub-agent
   is done. If the main agent dropped findings it judged spurious, the fresh-context
   value of the red-team would be lost: findings land raw, and the human triages.

## Stage 2 — Annotate (human only)

Annotate each finding in the report per `skills/red-team.md` §4: `> M:` to apply,
dismiss or ask, `> M?:` when you cannot yet evaluate it. A confident `> M:` is open to
pushback in Stage 3a; write "no pushback" to waive that for a finding. For a finding
with a routing tag, say in the `> M:` if you think the routing is wrong ("this is a
`[spec-implication]`, not a `[test-gap]`, because …").

## Stage 3a — Decide

```
Process the annotated red-team report at [[REDTEAM_PATH]]: decide, per
workflows/invoke-red-team.md Stage 3a. Edit no artefact yet.
```

The main agent:

1. **Checks upstream first** (implementation and result only, whose findings can carry
   routing tags): does any finding, alone or with others, force a return to an earlier
   stage, such as redrafting the spec or regenerating tests, code or docs? If so, it
   raises this in chat before walking the findings.
2. **Walks the findings.** For each:
   - a confident `> M:` it agrees with: a `> C:` under it (two newlines before), saying
     what will change and in which artefacts (the table above lists each stage's);
   - a confident `> M:` it disagrees with: push back in chat, and no `> C:` until
     resolved. A fresh sub-agent over-suggests and a human apply can be wrong;
     recording a decision it thinks is wrong would be waving it through;
   - an uncertain `> M:`: its opinion in chat, numbered by finding ID so the human can
     answer by ID;
   - a `> M?:`: no proposed action. It explains in chat what the human needs to
     evaluate *this* finding, not a generic tutorial, so the human can write a `> M:`
     in good conscience; the decision stays the human's (see *`> M?:` explanations*);
   - an accepted finding with a routing tag: a `> C:` recording the routing, not an
     in-place edit (see *Routing upstream*). The tag decides the routing, not the main
     agent's judgement.
3. **Writes chat resolutions back** as `> C:`, so the report is a complete record
   without the chat.

Once every finding has a `> C:`, the stage workflow's later stages apply them.

## Spec edits (stage 3b of the spec, tests and implementation workflows)

```
Make the spec edits in [[SPEC_PATH]] that the `> C:` annotations in [[REDTEAM_PATH]]
call for, per workflows/invoke-red-team.md "Spec edits".
```

The main agent marks each edit red (see *Red marking*), flips each affected section's
status to `draft`, adds a revision-log entry per `skills/write-math-spec.md`, adds the
commit to each `> C:` and commits. It touches nothing downstream of the spec: the human
re-reviews the affected sections first and flips them `draft → reviewed` (`AGENTS.md`,
*Spec status changes*). The red marking is removed after that re-review.

## Red marking

Revised text in a spec or report is marked so the human sees each change on re-read:
`<span style="color: red">…</span>` inline by default (renders in most markdown viewers
and diffs cleanly), a `> [!warning]` callout for a large revision, a caption note or red
border on a regenerated figure. The marking is removed once the human approves; the
revision log and the `> C:` annotations keep the audit trail.

## `> M?:` explanations

The first explanation of a concept lives in chat; the human's `> M:` can cite it
("after the chat explanation of Lagrangian duality, apply"), so the decision stays on
record. The second time the same concept comes up, across findings or passes, the main
agent says so and the explanation is promoted to `tutorials/<concept>.md`: one page,
calibrated to this project's derivations, naming at the top the findings that prompted
it. The trigger is "came up twice", which is data, not "seems important", which is
forecasting.

## Routing upstream

| Tag | Goes to |
|---|---|
| `[spec-implication]` | the spec: *Spec edits* above for a contained change; a full `invoke-red-team-on-spec.md` pass for a substantial one, with downstream regeneration per `skills/write-math-spec.md` |
| `[test-gap]` | `invoke-red-team-on-tests.md` |
| `[code-implication]` | `invoke-red-team-on-impl.md`, or a failing-test-first fix for a small, scoped bug |

Routing schedules the upstream work; only the result workflow waits for it (its stage
3b). Upstream work not done in this session goes in a GitHub issue or the handoff
(`AGENTS.md`, *Session types*).

## Re-runs

One red-team per artefact per pipeline pass, run once the artefact is stable. A second
pass after a substantial revision is a judgement call; the workflows do not prescribe
one.

## Related

- `skills/red-team.md`: the gate, spawning, sub-agent rules, report shape, annotation
  (§4) and resolution (§5).
- `skills/write-math-spec.md`: the status table, revision log and downstream-approval
  rules.
- `AGENTS.md`: the reviewer roster; spec status changes.
