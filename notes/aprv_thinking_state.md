# Project state: infomax-discretization × latent dynamics inference

**Last updated:** 2026-05-24
**Maintained by:** the human. Claude reads this; Claude does not rewrite it.

---

## Opening prompt for next session

> I'm continuing a line of thinking about applying a finite-data infomax framework
> to a perceptual decision-making experiment. Context is in two source documents
> I'll attach: `main.tex` (the infomax/coarse-graining sketch) and `ERC_reference_Adam.pdf`
> (the manuscript on inferring latent dynamics from observation dynamics). This file
> (`state.md`) is the running state of our thinking. I'll also attach
> `infomax_aprv_seed.md` (the math seed for the computational experiment, with my
> margin notes). Please read all four before responding. Treat the source documents
> as canonical; treat this state file as a scratchpad of open questions and
> provisional framings, not as settled conclusions. Don't summarize what's in the
> source documents back to me — assume I've read them. Start by going through my
> margin notes on the seed file with me, and then we'll decide what to derive or
> simulate next.

---

## The core claim being developed

The manuscript treats the asymmetry between AP and RV dynamics — RV behaves jumpily (CP-like), AP behaves driftily — as a brute fact about prior experience, manipulable via training (Exp 7–9) but otherwise unexplained at the default level. The new framing: **this asymmetry follows from how finite-$n$ infomax discretizes the two parameters**, because they carry information about themselves through structurally different likelihoods.

Specifically: RV warps $P(x \mid z)$ in a localized diagnostic region of observation space (Methods §8.4), giving it Fisher information that is concentrated/spiky. AP enters as a Bernoulli mixing weight, with smooth bounded Fisher information. The conjecture is that finite-$n$ BA discretizes RV at modest $n$ while leaving AP diffuse. Discrete representation of RV mechanically implies CP-like inference trajectories for it (jumps between atoms, no intermediate states), while continuous representation of AP allows drift-like updates.

This is a sharper target than the earlier "infomax explains the discrete atoms" framing, because it explains a load-bearing piece of the manuscript that is currently unexplained, rather than re-deriving the manuscript's ridge endpoints.

## What's load-bearing here, what's still soft

**Load-bearing (don't relitigate without new information):**
- The manuscript's RV-vs-AP dynamics asymmetry is unexplained at the default level — Exp 7–9 show it's *trainable* but not where the default comes from
- AP and RV carry information differently through the likelihood: AP through a discrete-output Bernoulli channel, RV through localized warping of a continuous likelihood
- Daisy-chain (likelihood drift) is implementable; can drive follow-up experiments

**Still soft:**
- Whether finite-$n$ BA on the manuscript's actual likelihood produces the predicted discretization asymmetry. This is the load-bearing test; nothing builds on it until it's run.
- Reading-1 vs Reading-2 of "discrete representation implies CP-like dynamics" — the trivial mechanical reading vs. the interesting claim that a finite-data learner with two-atom RV will impose CP-like updates on a world whose RV actually drifts. Want Reading-2; need to argue for it explicitly.
- Whether the discretization (if it appears) is robust to support-boundary choices or is a grid-truncation artifact
- What plays the role of $n$ for an undergraduate in a 220-trial test phase. Current best candidate: expected trials until next change point, with regime length governed by the dynamics hyperprior $D_{RV}$ itself. Attractive because it ties the static infomax story to the *same* hyperprior the manuscript already manipulates in Exp 7–9.

## Open questions, roughly in priority order

1. **Walk through margin notes on `infomax_aprv_seed.md`.** Resolve the math questions before any simulation runs: the i.i.d.-within-regime assumption, the multi-trial KL evaluation strategy, whether the existing BA implementation handles the RV-only case, sufficient statistics if any.
2. **Paper-and-pencil step: compute $\mathcal{I}_{AP}$ and $\mathcal{I}_{RV}$.** Before any BA. Their qualitative shapes (smooth vs. spiked) already tell us whether the asymmetry hypothesis is on the right track — the Jeffreys priors $\propto \sqrt{\mathcal{I}}$ are the $n \to \infty$ infomax limit.
3. **Run the marginal experiments first.** AP-only and RV-only BA, varying $n$. The asymmetry should show up here in isolation if the hypothesis is right. The joint AP–RV case is downstream of this and partly a confirmation rather than the primary test.
4. **Boundary sensitivity.** Run BA on at least two support choices for each parameter, to check whether atoms appear at endpoints because of truncation or because the geometry actually localizes them there.
5. **Reading-1 vs Reading-2 argument.** Once the static result is in, need to write down explicitly why the implication runs "discrete representation → CP-like inference trajectories on a drifty world," not just the cheap mechanical version.
6. **Tie $n$ to the dynamics hyperprior.** If $n$ is "expected trials until next CP" and that's governed by $D_{RV}$, then the manipulations in Exp 7–9 should shift not just *which* atom wins but *how discretized the representation is in the first place*. This is a candidate distinctive prediction vs. hierarchical Bayes with structured priors. Needs to be made precise.
7. **Daisy-chain follow-up experiment design.** Deferred — only worth designing once we know whether the static story works.

## Provisional framings I've tried out and want to keep around

- The asymmetry in default dynamics (RV jumpy, AP drifty) as a *consequence of representational discretization*, not as a separate fact about world dynamics. The manuscript's hyperpriors $D_{AP}, D_{RV}$ partly redundant with the representation itself.
- Heald et al. (2021) as conceptual neighbour but with a weaker claim: they treat switch-vs-adapt as a free representational choice; we'd be saying it's determined by likelihood geometry and data budget.
- The full story has three layers: (1) infomax + likelihood geometry sets the granularity of each parameter's representation given $n$, (2) granularity determines what dynamics are *expressible* for each parameter (discrete → jumps only, continuous → drift), (3) observation dynamics select which atom wins after a change point. The manuscript covers (3); the new contribution is (1)→(2).
- A skeptic's distinctive-prediction target: representational granularity should *split* (number of atoms increase) when expected $n$ grows — testable in a paradigm where the likelihood ridge supports more than two well-separated points.

## Things explicitly *not* in scope right now

- The red-teaming ideas (separate thread, bring up later)
- Full reconciliation with active inference / Friston framework — but worth knowing which specific paper a reviewer would cite, given the daisy-chain in `main.tex` §3.3 is in adjacent territory
- Anything about RP (representational planning) beyond what's in `main.tex` §4
- The dynamic version of the model (BA with sequential updates). Static result has to land first.

---

## Meta-level: how this artifact is meant to work

**Source of truth lives elsewhere.** `main.tex` and the manuscript are append-only and human-authored. Claude reads them; Claude does not rewrite them. The seed note (`infomax_aprv_seed.md`) is a session output that gets margin-noted by the human and revisited next session — it's a working artifact, not a canonical one. This `state.md` is the only file Claude updates, and even this gets edited by the human at the end of each session.

**What goes in this file:**
- Open questions (sharpest section, drives the next session)
- Provisional framings I want to test against the source docs
- Things deliberately out of scope
- The opening prompt itself

**What does *not* go in this file:**
- Summaries of `main.tex` or the manuscript (those are the canonical artifacts, don't paraphrase)
- Detailed math from session outputs like the seed note (lives in its own file)
- Accumulated "knowledge about the project" that competes with the source docs
- Claude's outputs from previous sessions verbatim — re-derive when needed; the source docs and the human's notes on session outputs are what's stable

**End-of-session ritual (five minutes, human writes):**
1. Update the "open questions" section based on what was actually clarified
2. Move anything that became settled into the load-bearing list, anything that became unsettled out of it
3. Add new provisional framings, prune ones that didn't survive
4. If a session produced a working artifact (like the seed note), name it in the opening prompt for next session
5. Do not let this file grow past ~2 pages. If it's growing, that means content belongs in `main.tex` or a session artifact, not here.

**Why this shape:**
- Karpathy-style LLM Wiki has known drift problems for conceptual work: information loss through compression, write-time synthesis as a loan against future correctness, homogenization toward LLM-typical phrasing
- Code-repo persistence works because the code itself is the load-bearing artifact, and tests catch drift. Conceptual work has no equivalent ground-truth signal, so the human-written source docs have to play that role
- Plain markdown is the lingua franca across models and humans; format should not be optimized for any specific model
- Relaxing human-readability means the artifact gets too long for the human to actually maintain, which kills the system

**Session-artifact pattern (new this session).** Working math notes that come out of a session — like the seed note — live in their own files, get margin-noted by the human, and re-enter the next session as named context. This keeps `state.md` short and lets the working artifact stay detailed without polluting the running state. The state file's job is to point at the right session artifacts and frame the open questions; it is not where derivations live.

**Claude's role, named honestly:** very good first reader, not Besso. Independent peer judgment stays with human collaborators. The artifact's job is to make collaborator interactions sharper (better-prepared questions, cleaner drafts), not replace them.
