# Plumbing spec — repo → web layer

> **Not a spec in the `specs/` sense.** No math contract, no test suite, no
> red-team gate. This is the description of how repo content becomes the
> published web object, and it is the render's source of truth: when the
> render changes, this file changes first. Naming follows MB's coinage
> ("plumbing spec") so it stays findable.
>
> **Status:** draft. Nothing here has been built yet.
> **Maintained by:** MB writes §2–§4 decisions; Claude may propose edits and
> implement §7–§8. Changes to §1 (invariants) are MB-only.

---

## 0. What the web object is for

One page-set that lets a technically-apt stranger learn (a) what the project
claims, (b) how sure we are of each claim and why, (c) what is unresolved, and
(d) what has been built and run — without reading a paper that hides the
first three.

Second, equal purpose: it is MB's own working view of the project. If it is
not the thing MB looks at to decide what to do next, it will not be
maintained, and every design decision below is subordinate to that.

---

## 1. Invariants

Constraints on what is allowed to happen at all. A convenience that conflicts
with one of these loses.

**I-1 — One home per fact.** Every fact lives in exactly one place in the
repo. Every other appearance of it is generated. Two hand-maintained copies
of the same fact are a defect, not a redundancy, and no amount of patrolling
fixes them.

**I-2 — Prose is never generated; renders are never hand-edited.** MB writes
the reader-facing prose. The build emits everything else. A render that has
been hand-touched is corrupt and gets overwritten without ceremony.

**I-3 — Publication is opt-in.** Only files carrying `publish: true` are
rendered. Default is unpublished. This is not paranoia: the repo contains
grant-strategy material, a collaborator's unpublished manuscript
(`notes/aprv_thinking_state.md`), Hungarian working notes, and offhand
judgements about named researchers. A denylist will leak one of these
eventually; an allowlist cannot. Marking something publishable is a
deliberate act, like flipping a section to `reviewed`.

**I-4 — Review status ≠ epistemic status.** A fully-reviewed spec of a
conjecture is still a conjecture. Both are displayed, never merged into one
badge. Conflating them is the specific dishonesty a paper commits.

**I-5 — Un-vouched content is visibly marked.** Anything the build publishes
that no human has read carries a marker in the render. Silence is not a
vouch.

**I-6 — The build runs from a clean checkout** with `uv run`, no network, no
manual steps. If it needs a human in the loop it will rot.

---

## 2. Source of truth

| Fact | Home | Format |
|---|---|---|
| What a claim is, and what it depends on | front-matter of the spec/note that makes it (§3) | YAML |
| Epistemic status of a claim | front-matter `status` | controlled vocabulary (§3) |
| Review completeness of a spec | the existing per-section status table | parsed from markdown |
| Open questions | `OQ-n` headings inside each spec's §7 | parsed from markdown |
| Derivation gaps | the gap table in `notes/daisy_chain_derivation.md` | parsed from markdown |
| Results of a run | `experiments/<id>/REPORT.md` + `provenance.json` | existing convention |
| Review trail | `specs/*-redteam*.md` with `> M:` / `> C:` / `> M?:` | parsed from markdown |
| References | `resources/references.md` | extended per §6.3 |
| Antilibrary | `resources/antilibrary.md` (new) | per §6.3 |
| Reader-facing prose | `site/prose/*.md` | markdown, `covers:` front-matter |
| Nodes with no file (external theorems, known gaps) | `site/nodes.yml` | YAML registry |

Nothing else is authoritative. If the build needs a fact not in this table,
the table is wrong and gets extended — the fact does not get typed into a
template.

---

## 3. Front-matter schema

Added to the top of specs, notes, and experiment reports that should appear
as nodes. Existing content below it is untouched.

```yaml
---
id: spec-001                    # stable, never reused, kebab-case
kind: spec | note | experiment | result | external | gap
title: Does the infomax prior win at betting?
status: established | derived | conjectured | tested-survived
        | tested-failed | broken | not-started
layer: foundation | derivation | implementation | simulation | behavioural
thread: static-infomax | betting | foreign-q | daisy-chain | aprv
depends_on: [spec-000, ext-mattingly-2018]
summary: >
  One sentence, written by MB, in MB's voice. This is the only prose the
  build takes from front-matter and it is what shows on map hover.
publish: true | false
---
```

**Vocabulary notes.**

- `status` is about the *claim*, not the document. `tested-failed` is a
  first-class value and spec 001 currently holds it. Nothing about a failed
  test makes a node less worth showing — see §4 Results.
- `broken` means "we know this step does not work and downstream claims
  inherit the problem" — e.g. the line-316 derivation issue.
- `layer` fixes the vertical rank in the map. `thread` fixes the horizontal
  grouping. Together they make the layout deterministic (§5).
- `depends_on` is the only edge type. See §5 on why there is no `related_to`.

**Node granularity.** Start at one node per file, plus registry entries in
`site/nodes.yml` for things that are not files (Mattingly's theorem; the
line-316 gap; each `OQ-n` if it earns a node). Section-level anchoring is a
later migration if the coarse version proves too lossy — not a launch
requirement. See PQ-1.

---

## 4. Page inventory

Each page is a list of **slots**. A slot is `prose` (MB writes, build renders
verbatim), `render` (build generates, nobody edits), or `prose+render` (a
render that may carry an MB preamble; if absent, the render shows a
"no orientation written" marker per I-5).

| Page | Slots |
|---|---|
| **Home** | `prose`: the intro. `render`: map (small), current frontier, last-changed |
| **Map** | `render`: the full graph (§5). `prose+render`: a legend paragraph explaining what statuses mean |
| **Thread page** (one per `thread`) | `prose+render`: what this thread is after. `render`: its sub-graph, its nodes in dependency order, its open questions, its results |
| **Node page** (one per node) | `prose+render`: MB's orientation. `render`: status, dependencies both directions, links to the source document, the OQs anchored in it, its review trail (§6.1), provenance (§6.2) |
| **Results** | `prose+render`: what we now believe. `render`: every node with `status` in {tested-survived, tested-failed}, newest first, each linking to its `REPORT.md` and `provenance.json` |
| **Open questions** | `render` only: every `OQ-n` across all specs, grouped by thread, each showing its home spec, the text, and what it blocks. No separately authored text — this is the aggregated view MB asked for |
| **Experiments** | `prose+render`: the paradigm in words. `render`: spec sections, runnable links |
| **Notebooks** | `render`: JupyterLite embeds (§7) |
| **References & antilibrary** | `prose+render`: how to read this list. `render`: §6.3 |
| **Review trail** | `render`: §6.1 filtered view |
| **Colophon** | `prose`: how this object is made and why. `render`: provenance summary (§6.2), build timestamp, commit |

The Colophon is not decoration. The workflow is half the project, and it is
the half labmates are most likely to want. Its prose slot is the descendant
of MB's original statement of intent in
`transcripts/000-initial-planning-chat.md`.

---

## 5. The map

**Node.** A claim, not a file. Files hang off claims as links.

**Edge.** `depends_on`, and nothing else. There is deliberately no
`related_to` edge: association edges are unbounded in number, they connect
everything to everything, and they destroy the one property that makes a
dependency graph readable — that "upstream" means something. Association is
expressed by `thread` grouping and by prose, not by lines.

**Layout.** Layered DAG. Vertical rank from `layer`, horizontal grouping from
`thread`, positions computed deterministically so they do not move between
builds. A node that sat top-left last week sits top-left this week; spatial
memory is the whole point of having a map rather than a list.

**Colour.** `status`, and only `status`. It is the variable a reader most
needs and the one a paper hides.

**Interaction.** Every node clicks through to its node page. Filter by
status; highlight the transitive closure upstream and downstream of a
selected node — that single interaction answers "what does this break" and
"what is this waiting on", which are the two questions the map exists for.

**Frontier and graveyard.** Render `not-started` nodes whose dependencies are
all satisfied as the frontier (this is MB's own to-do list, which is why the
map stays maintained). Render abandoned directions greyed but present, with
the reason — sourced from `meta/what-didnt.md`, which is currently an empty
template and is the cheapest high-value thing to start filling.

**Implementation, staged.** Stage 1: build emits Mermaid, which GitHub
renders natively and which the repo already uses; good to ~30 nodes, zero
JS. Stage 2, when it outgrows that: same front-matter, `graphviz` for
deterministic positions, `cytoscape.js` for click-through and filtering. The
front-matter investment carries across; only the renderer is replaced.

---

## 6. The three filtered surfaces

The hard cases. Each is a firehose where the useful part is a small,
mechanically identifiable subset.

### 6.1 Review trail

Most red-team findings are routine and boring. A finding is **surfaced** if
any of:

1. It caused an edit to the spec (there is a `> C:` recording a change).
2. MB rejected it, with reasoning (a `> M:` that disagrees).
3. It carries an unresolved `> M?:` — MB flagged maths he could not evaluate.
4. It caused a section status regression (`reviewed → draft`).

Everything else collapses to a line: *"N further findings, accepted without
change — expand"*. No judgement call is needed; all four triggers are
greppable.

Category 3 is the valuable one and it is rare — currently 7 instances across
the whole repo. Those are the project's honest soft spots, they fit on one
screen, and surfacing them is something no paper does. Category 2 is the
second-best: a recorded disagreement with a reviewer, resolved in public.

### 6.2 Provenance

Per-sentence attribution is unreadable and nobody wants it. The unit is the
**vouch**, not the authorship. Three states:

- **human-written** — quiet marker.
- **machine-drafted, human-reviewed** — quiet marker, links to the review
  event (the red-team file, or the section status flip and its date).
- **machine-drafted, not yet reviewed** — loud marker, per I-5.

The third state is the only one that needs to be visually prominent, and the
existing `reviewed` status in spec section tables already encodes most of the
distinction. Model identity and effort tier come from the red-team roster in
`AGENTS.md`, which is already the single source of truth for that.

### 6.3 Antilibrary

"Haven't got round to it" is most of reality and the schema must accept that
without shame. Engagement ladder, cheapest states genuinely cheap to record:

| State | What it means | Cost to record |
|---|---|---|
| `noted` | someone mentioned it; one line on why it might matter | seconds |
| `skimmed` | abstract read; one line on whether it is relevant | a minute |
| `read` | read, with a note | — |
| `blocked` | read, and here is specifically what I cannot follow | half a day |
| `absorbed` | understood and positioned relative to the project | — |

The bulk will be `noted` and that is honest. The valuable, rare state is
`blocked`: it tells a reader exactly where the project's edges are, and it
doubles as a **request for help** — a visitor with the right background can
see precisely where they would be useful. That is a capability a paper does
not have, and it is worth rendering as its own view.

Seed material exists: the "To read" list recovered from the Google Doc, the
Notion TODO items, and the `> M?:` flags, which are `blocked` entries in all
but name.

---

## 7. Build pipeline

Python, uv-managed, consistent with the rest of the repo.

1. **Collect.** Walk the repo; parse front-matter; drop everything without
   `publish: true` (I-3). Parse the derived tables named in §2.
2. **Validate.** Fail the build on: unknown `id` in `depends_on`; cycle in
   the DAG; duplicate `id`; `prose` slot whose `covers:` names a
   non-existent node; a published node whose source file is unpublished.
3. **Render.** Markdown via `markdown-it-py`; maths via KaTeX (non-optional —
   the content is LaTeX-dense); notebooks via JupyterLite for anything small
   enough to run in Pyodide, `nbconvert` static output otherwise.
4. **Emit.** Static site into `site/_build/`.
5. **Publish.** GitHub Actions → Pages.

**Directory collision to avoid:** `docs/` is already per-experiment
documentation in this repo, so it cannot be the Pages root. Source lives in
`site/`, output in `site/_build/`, published from the Action.

```
site/
  prose/        # MB's slot files (§4)
  nodes.yml     # non-file nodes (§2)
  templates/
  build.py
  _build/       # generated; gitignored
```

---

## 8. Lawnmower checks

What the patrol does, what runs it, and where it reports. It **flags, never
fixes** — a silently repaired inconsistency is a signal MB needed and did not
get, which contradicts the project's premise that growing MB's command of the
mathematics is a goal rather than a side effect.

| Check | Mechanism | Trigger | Reports to |
|---|---|---|---|
| Prose stale: a slot's `covers:` target changed after the slot's last edit | git metadata; no LLM | every build | build warning + a badge on the page |
| Broken cross-reference (`§1.4`, `OQ-3`, node id) no longer exists | script | every build | build failure |
| Status regression not propagated downstream | script over the DAG | on commit | `meta/workflow-issues.md` |
| Spec `reviewed` but file modified since that date | git metadata | on commit | build warning |
| Orphan: published node nothing links to | script | every build | build warning |
| Terminology drift; notation diverged between documents | LLM | pre-session | conversation |
| Does conclusion X still follow now that Y broke? | LLM, **proposal only** | pre-session | `> M?:`-style flag for MB |

**Trigger discipline.** Pre-session, not weekly. A report that arrives when
MB has context loaded is worth ten that arrive on a schedule.

**Noise budget.** Top three findings or silence. "Nothing drifted" is a valid
and expected report. A patrol that emits twenty items a week is ignored by
week three.

**Scope limit.** Factual and referential drift only. The patrol is explicitly
forbidden from touching prose style — `notes/aprv_thinking_state.md` already
identifies homogenisation toward LLM-typical phrasing as a known failure mode
of LLM-maintained wikis, and the premise here is that the prose is MB's.

---

## 9. Open questions

- **PQ-1.** Node granularity: one node per file to start, or section-level
  anchors from the beginning? Coarse is proposed; the risk is that spec 002's
  internal structure is rich enough that one node under-serves it.
- **PQ-2.** Does the map need any second edge type after all, or does `thread`
  grouping plus prose fully cover association? Proposed: no second edge type
  until a concrete case forces it.
- **PQ-3.** Hungarian-language working notes: translate, exclude, or publish
  as-is? Affects a substantial share of `notes/` and the Notion material.
  Under I-3 the default is exclude, which may quietly drop real content.
- **PQ-4.** What is the review gate for `publish: true`? It is the highest-
  consequence flag in the schema and currently has no ceremony attached.
- **PQ-5.** Does the review trail (§6.1) need MB's consent per finding before
  publication, or is spec-level `publish: true` sufficient? Red-team files
  contain MB's unguarded first reactions.
- **PQ-6.** Multiple intro versions for different audiences were wanted. One
  `prose` slot per audience on Home, or separate entry pages?

---

## 10. Revision log

| Date | Change | By |
|---|---|---|
| 2026-09-22 | Initial draft | Claude (Opus 5), unreviewed |
