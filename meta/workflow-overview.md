# Workflow overview

> Bird's-eye view of how artifacts flow through this project, and
> which agent (human, Claude Code, sub-agent) is responsible at each
> stage. Read this if you're new to the project, returning after a
> break, or wondering where a given task fits in the larger shape.

The workflow is **under construction.** Sections shown with dashed
borders below are forthcoming; they reflect structural intent, not
implemented procedure.

## The diagram

```mermaid
flowchart TD

    subgraph HUMAN["Human"]
        direction TB
        H_write[Write/refine spec<br/>section by section]
        H_review_spec[Review spec sections<br/>flip draft → reviewed]
        H_annotate_spec_rt["Annotate spec redteam<br/>> M: / > M?: / dismiss"]
        H_review_tests[Review derived tests<br/>+ property-to-test table]
        H_annotate_tests_rt["Annotate tests redteam<br/>> M: / > M?: / dismiss"]
        H_eye_test[Inspect eye-test figure<br/>approve or reject]
        H_review_impl[Review implementation]
        H_annotate_impl_rt[/"Annotate impl redteam<br/>(forthcoming)"/]
        H_annotate_result_rt[/"Annotate result redteam<br/>(forthcoming)"/]
    end

    subgraph CODE["Claude Code (main)"]
        direction TB
        C_draft_spec[Draft spec sections<br/>flip back to draft on revision]
        C_derive_tests[Derive test suite<br/>+ eye-test file]
        C_apply_spec_fixes["Apply spec redteam fixes<br/>(stage 3 of workflow)"]
        C_apply_test_fixes["Apply test redteam fixes<br/>regenerate tests, update spec"]
        C_implement[Write implementation]
        C_apply_impl_fixes[/"Apply impl redteam fixes<br/>(forthcoming)"/]
        C_run_full_suite[Run full test suite]
    end

    subgraph SUB["Claude sub-agent (fresh context)"]
        direction TB
        S_redteam_spec[Red-team spec<br/>find math errors, drift, gaps]
        S_redteam_tests[Red-team tests<br/>find coverage gaps, vacuous tests]
        S_redteam_impl[/"Red-team impl<br/>(forthcoming)"/]
        S_redteam_result[/"Red-team result<br/>(forthcoming)"/]
        S_explain_math[Calibrated math explainer<br/>triggered by > M?:]
    end

    H_write --> C_draft_spec
    C_draft_spec --> H_review_spec
    H_review_spec -->|all sections reviewed| S_redteam_spec
    S_redteam_spec --> H_annotate_spec_rt
    H_annotate_spec_rt --> C_apply_spec_fixes
    C_apply_spec_fixes --> H_review_spec

    H_review_spec -->|spec stable<br/>post red-team| C_derive_tests
    C_derive_tests --> H_review_tests
    H_review_tests -->|tests complete| S_redteam_tests
    S_redteam_tests --> H_annotate_tests_rt
    H_annotate_tests_rt --> C_apply_test_fixes
    C_apply_test_fixes --> H_review_tests

    H_review_tests -->|tests stable<br/>post red-team| C_implement
    C_implement --> H_review_impl
    H_review_impl -->|impl drafted| S_redteam_impl
    S_redteam_impl --> H_annotate_impl_rt
    H_annotate_impl_rt --> C_apply_impl_fixes
    C_apply_impl_fixes --> H_eye_test

    H_eye_test -->|approved| C_run_full_suite
    H_eye_test -->|rejected| C_implement
    C_run_full_suite --> S_redteam_result
    S_redteam_result --> H_annotate_result_rt

    H_annotate_spec_rt -.->|"> M?: raised"| S_explain_math
    H_annotate_tests_rt -.->|"> M?: raised"| S_explain_math
    H_annotate_impl_rt -.->|"> M?: raised"| S_explain_math
    S_explain_math -.->|resolves to > M:| H_annotate_spec_rt
    S_explain_math -.->|resolves to > M:| H_annotate_tests_rt
    S_explain_math -.->|resolves to > M:| H_annotate_impl_rt

    classDef forthcoming stroke-dasharray: 5 5,opacity:0.7
    class H_annotate_impl_rt,H_annotate_result_rt,C_apply_impl_fixes,S_redteam_impl,S_redteam_result forthcoming

    classDef humanNode fill:#fef3c7,stroke:#b45309,color:#000
    class H_write,H_review_spec,H_annotate_spec_rt,H_review_tests,H_annotate_tests_rt,H_eye_test,H_review_impl,H_annotate_impl_rt,H_annotate_result_rt humanNode

    classDef codeNode fill:#dbeafe,stroke:#1e40af,color:#000
    class C_draft_spec,C_derive_tests,C_apply_spec_fixes,C_apply_test_fixes,C_implement,C_apply_impl_fixes,C_run_full_suite codeNode

    classDef subNode fill:#ede9fe,stroke:#6d28d9,color:#000
    class S_redteam_spec,S_redteam_tests,S_redteam_impl,S_redteam_result,S_explain_math subNode

    linkStyle default stroke-width:2px
```

## How to read it

Three lanes for the three agents: **human** (amber), **Claude Code
main agent** (blue), **Claude sub-agent with fresh context**
(purple). An artifact's home lane is the agent responsible for it
at that stage; arrows cross lanes when responsibility shifts.

Solid arrows are the primary flow. Dashed arrows show the
math-explainer side-cycle: when the human raises a `> M?:`
annotation on a red-team finding (meaning "I don't yet command this
math well enough to evaluate the finding"), the sub-agent produces
a calibrated explanation, and the cycle resolves when the human can
annotate `> M:` (a substantive decision) in good conscience.

Dashed-bordered nodes are forthcoming. The implementation and
result red-team passes follow the same structural pattern as the
spec and test red-teams but haven't been exercised yet.

## What's load-bearing

Three structural choices worth naming, since they're not obvious
from the diagram alone:

**Status flows asymmetrically.** Only Claude Code flips section
status *backwards* (`reviewed → draft`) on revision; only the human
flips it *forwards* (`draft → reviewed`) on re-review. This
prevents the obvious failure mode where Code self-certifies that
its own edits are reviewed.

**Sub-agent context isolation is the point.** The red-team passes
exist because a fresh sub-agent without the main agent's anchoring
will see things the main agent won't. Collapsing the sub-agent
lane into the Code lane would erase the reason red-team works.

**The human is on every closure.** Every loop in the diagram routes
through the human lane. This is intentional, not vestigial: the
project's value proposition is auditable scientific work, and
auditability requires that judgement-bearing transitions are made
by a person who can be questioned about them.

## What's not in the diagram

- **Chat-Claude.** Design conversations (including the one that
  produced this document) happen alongside the workflow but aren't
  part of the artifact flow. The audit trail of those conversations
  lives in `transcripts/`.
- **Git operations.** Commits happen at sensible boundaries; the
  diagram is silent on this because git is everywhere and showing
  it would dilute the workflow-specific content.
- **The eye test specification step.** The eye test is *specified*
  in the spec (where it lives as a subsection) and *executed* in
  the diagram (the `Inspect eye-test figure` node). The specifying
  is folded into "Draft spec sections" rather than getting its own
  node.

## Related documents

- `AGENTS.md` — the project handbook, including the test-gates
  convention this diagram visualises.
- `skills/` — the procedures the agents follow at each stage.
- `workflows/` — the orchestration prompts that trigger sessions
  of the workflow.
- `meta/workflow-issues.md` — the open and resolved questions
  about how the workflow itself should evolve.

## Maintenance

The diagram is revised when the workflow changes structurally —
new artifact type, new gate, new lane, removed step. Stylistic
edits to skill files don't trigger a diagram revision. The trigger
is "the diagram now misrepresents the workflow," judged by reading
it cold.
