# 000 — Reading summary

A first pass over `resources/`: the Overleaf draft (`overleaf_doc/main.tex`), the
Notion export (`notion_export/`), the Google-Doc grant draft
(`google_doc_export.md`), the Mattingly et al. 2018 paper and its supplement, and
the `sequential_infomax.ipynb` notebook.

This is reading-only; nothing has been built or specified yet. The point of the
document is to make sure I've understood what you're trying to do before we
write a spec.

## 1. What this project seems to be about

The same idea shows up under at least four names across the resources:

- "Representational coarse-graining from limits on observation" (Overleaf title)
- "Model selection from observational constraints" (Notion root page)
- "Finite-observation optimal priors for sequential decision making" (Notion subpage)
- "The origin of symbolic computation" (Google Doc grant draft)

Stripping the rebrandings, the project looks like this:

**Core claim.** Mattingly et al. (2018) showed that if you maximise mutual
information between a latent parameter θ and a *finite* number N of future
observations, the optimal Bayesian prior is generically discrete — a finite set
of delta-function atoms, possibly on boundaries of the parameter manifold. This
gives a normative reason for an agent to coarse-grain its representation: under
limited observation, fewer effective distinctions are worth maintaining.

**The move you want to make.** Treat this as a model of *cognitive*
representation learning, where the finite-observation budget N is reinterpreted
as a "learning urgency" signal — an agent's sense of how many observations it
will get before having to commit to a decision. Urgency is a piece of the task
specification that Bayesian and resource-rational models usually leave on the
floor; you want to put it at the centre.

**The technical extension you are actually working on.** Mattingly's setup is
one-shot. You want a sequential / dynamic version, where the agent already has
a posterior from past observations and has to choose a new prior given that
posterior *and* a fresh budget of N future observations. Your derivation in
section 2 of the Overleaf — the objective `L_dyn = I(θ, θ_old) + I(θ, X | θ_old)`,
the synthetic-sample trick to avoid defining `p(θ, θ_old)`, and the resulting
Blahut–Arimoto update — is the technical heart of the project. The notebook
has a working implementation of both the static and dynamic objectives on a
biased-coin model.

**The further extension (less mature).** The "daisy chain" (Overleaf §2.2):
alternating prior-optimisation steps with Bayesian-inference steps produces a
*model misspecification signal* — the gap between expected and actually realised
learning (i.e. the KL between prior and posterior compared with the predicted
MI). That signal is then fed into an efficient-coding-style update of the
likelihood function. This part is explicitly *not* normative; it's a process
model with feedback loops, and you flag in the Birds-eye-view notes that you
don't yet know what to call it or how to evaluate convergence.

**The empirical arm.** Behavioural experiments — "monster chef", a wind-tunnel
task, possibly a navigation / video-game paradigm — designed to test whether
humans actually discretise more under higher urgency, and (for the daisy chain)
whether mismatch between expected and realised learning predicts changes in
likelihood plasticity. The grant draft fleshes this out into four objectives
including a developmental arm. None of the experimental code or data appears in
`resources/`; this looks like prospective work.

**Where it sits in your broader programme.** You frame this as a tractable
slice of the "representational planning" line (Bányai & Dayan, Shen et al.) you
came from. RP was normatively clean but computationally intractable; the
information-theoretic angle buys you a closed-form objective (BA on the MI)
that — if you can extend it dynamically — gives you a principled
representation-update rule without the combinatorial explosion. The trade is
that you give up the RL framing and a lot of generality.

**Honest uncertainty.** The Notion and Google Doc material is sprawling and
contains many half-cooked ideas (autopoiesis, open-endedness, hierarchical
representations, transfer, chunking, developmental urgency, meta-cognitive
urgency, ITL, logical fallacies, …). It is unclear to me which of these are
*this* project and which are the umbrella ERC/FWF narrative. My current read is
that *this* project — `dynamic_infomax` — is specifically the maths and
simulations needed to (a) reproduce Mattingly faithfully, (b) make the
sequential extension rigorous, and (c) get the daisy chain to a state where it
can generate predictions for an experiment. The rest is grant scope, not code
scope. **Please confirm or correct.**

> M: I confirm the above is correct.

## 2. The Mattingly paper, in my own words

**Setup.** A parametric model `p(x | θ)` with θ ∈ Θ. The experimenter will
collect a finite number m of i.i.d. samples, i.e. observe `X ∈ X^m` distributed
as `p^m(X | θ) = Π p(x_i | θ)`. The question: what prior `p(θ)` should we use?

**Bernardo's reference prior (1979)** chose the prior that maximises
`I(Θ; X^m)`, in the limit `m → ∞`. Under regularity that limit is the Jeffreys
prior `p_J(θ) ∝ √det g(θ)`, where g is the Fisher information matrix. The
Jeffreys prior depends on the *form* of the experiment but not on how much data
you'll collect.

**Mattingly's move.** Don't take `m → ∞`. Solve the same optimisation
problem `p* = argmax_p I(Θ; X^m)` keeping m finite. The objective can be written

```
I(Θ; X) = ∫ dθ p(θ) f_KL(θ),    f_KL(θ) = D_KL[ p(X|θ) ‖ p(X) ]
```

with `p(X) = ∫ dθ' p(X|θ') p(θ')`. This is concave in p, so the maximum is
unique. The KKT conditions for `argmax_p I` subject to `p ≥ 0` and `∫ p = 1`
are:

```
on support of p*:   f_KL(θ) = I*    (= the achieved MI)
off support:        f_KL(θ) < I*
```

Because `f_KL(θ) − I*` is analytic in θ (at finite m), it has only finitely
many zeros, so `p*` is a sum of delta functions:

```
p*(θ) = Σ_{a=1..K} λ_a δ(θ − θ_a).
```

**Why this is a model-selection procedure.** In higher-dimensional Θ, the atoms
preferentially sit on lower-dimensional boundaries of the parameter manifold.
Each boundary corresponds to a *reduced model* — some parameter combination set
to its limiting value, i.e. switched off. So `p*` doesn't just discretise; it
picks out which parameters are worth keeping at all. The paper makes this
explicit in the sum-of-exponentials example (Fig 4), where as σ shrinks the
prior moves from corners (0-D models) to edges (1-D models) to the interior
(2-D model). They define `d_eff = Σ r Ω_r`, the weighted effective
dimensionality, and show it grows smoothly with `1/σ`.

**Algorithm: Blahut–Arimoto.** A fixed-point iteration on a discretised θ:

```
p_{τ+1}(θ) = (1/Z_τ) · exp( f_KL(θ; p_τ) ) · p_τ(θ),
Z_τ = Σ_θ exp( f_KL(θ; p_τ) ) · p_τ(θ),
```

where `f_KL(θ; p_τ) = D_KL[ p(X|θ) ‖ Σ_θ' p(X|θ') p_τ(θ') ]` is recomputed each
step. This is the convex-optimisation algorithm from rate-distortion theory
(Blahut 1972, Arimoto 1972); convergence to the global max is guaranteed. An
alternative is to assume discreteness up front and gradient-optimise the K atom
positions and weights `(θ_a, λ_a)` directly.

**Asymptotic behaviour.** As m grows, the atom count K grows with proper
spacing in the Fisher metric tending to a constant; numerically `MI ≈ ζ log K`
with `ζ ≈ 3/4`. The atom density per unit Fisher length scales as
`ρ ∼ L^{1/ζ − 1} ≈ L^{1/3}`. In the `m → ∞` limit `p*` converges to the
Jeffreys prior.

**The headline argument of the paper** is that on "sloppy" parameter manifolds
(long in a few stiff directions, very narrow in many sloppy directions), the
Jeffreys prior is pathological — it weights total volume, so irrelevant
parameters bleed into the prior over the relevant ones. The finite-m optimal
prior `p*` instead concentrates on a discrete set that respects only the
*distinguishable* directions, which is exactly what makes it usable as a
principled model-selection device.

## 3. Reproducing Mattingly Fig 1 qualitatively

**What Fig 1 shows.** The Bernoulli/coin model, `p(x | θ) = Binomial(x; m, θ)`
with θ ∈ [0,1]. For several values of m (the figure shows roughly m = 1, 2, 3,
4, 5 in one row and large m in the right panel), it plots:

- the positions of the delta-function atoms of `p*(θ)` as vertical red lines;
- the function `f_KL(θ; p*)`, which is flat (= MI) where atoms live and dips
  below MI between atoms;
- the limiting Jeffreys prior `p_J(θ) = 1 / (π √(θ(1−θ)))` as a smooth curve
  for comparison.

The qualitative pattern: at m = 1, two atoms at 0 and 1, each weight ½, MI =
log 2 (one bit). As m grows, atoms multiply and move inward; by m of order 10
the atoms approximate the U-shaped Jeffreys prior.

**Ingredients to reproduce qualitatively.**

1. *No dataset.* Everything is theoretical / generated from the model. We don't
   fit to data; we compute `p*` directly from `p(x|θ)`.
2. *A discretisation of θ.* The natural choice for the coin is a uniform grid
   on `[0,1]` — your notebook uses 100 bins. We can sanity-check insensitivity
   by varying the grid (Mattingly's Fig 2 explicitly checks 10× refinement).
3. *The likelihood.* For each grid θ and each `x ∈ {0, …, m}`, evaluate
   `p(x | θ) = Binomial(x; m, θ)`. The data space `X` for the binomial is
   `m + 1` points; no need to enumerate `X^m` since the sample is summarised by
   the count.
4. *Blahut–Arimoto.* Initialise `p_0(θ)` uniform. Iterate the BA update above
   until `‖p_{τ+1} − p_τ‖` falls below a tolerance. Discrete atoms appear as
   spikes; "atom positions" can be read off as grid bins whose mass exceeds a
   threshold (or by clustering nearby high-mass bins, since the discretisation
   smears single atoms across one or two grid cells).
5. *Repeat for several m.* m = 1, 2, 3, 5, 10, 20, say, to recover the
   progression.
6. *Compare to Jeffreys.* Overlay the closed-form `p_J(θ) = 1 / (π √(θ(1−θ)))`.
7. *Check the f_KL flatness condition.* For each converged `p*`, plot
   `f_KL(θ)` over the grid. It should sit at the achieved MI exactly at atom
   positions and below it elsewhere — this is the cleanest internal sanity
   check that BA actually found the maximum.

**Equations involved (all from §2 above).** The binomial likelihood; the
MI written as `∫ p(θ) f_KL(θ) dθ`; the BA update; the Jeffreys prior for the
Bernoulli (closed form). No optimisation beyond BA is needed for the
one-parameter case.

**What we already have.** `sequential_infomax.ipynb` contains a class
`biased_coin_GM` with `blahut_arimoto_prior(...)` and a `posterior()` method.
The static case appears to work; the dynamic case has known issues (negative
KL clipped at 1e-6; m = 0 handled by special case; an unresolved derivation
factor flagged in §A.2.5 of the Overleaf). The supporting `infomax_class.py`
referenced in the notebook is not in `resources/` — it lives in your
`github.com/mihalybanyai/infomax` repo. **[?]** flagged below.

**Effort estimate.** Qualitative Fig 1 reproduction in a clean implementation
is small — maybe a few hundred lines including tests. The real care is in
test cases: f_KL flatness, MI ≤ log K, convergence to Jeffreys as m grows,
agreement with the closed-form m=1 solution. That's where AGENTS.md's
"tests as specification" principle pays off.

## 4. Open questions

Scoping and ambition:

- [?] Is `dynamic_infomax` the *whole* programme (theory + experiments +
  developmental + meta-cognitive + daisy chain + …) or specifically the
  computational/theoretical core (faithful Mattingly reproduction → sequential
  extension → daisy-chain simulations → predictions for one experiment)? I've
  assumed the latter in §1 — please correct if you mean broader.
  > M: it's primarily indeed the latter. I would like to keep the broader context around, but as a thechnical project, the scope is narrower. If you like, the broader stuff is for Chat, you don't need to deal with it.
- [?] What is the *first concrete deliverable* you want out of this repo? My
  default guess: a clean, tested implementation of static-Mattingly BA, with
  Fig 1 reproduced, as the foundation for everything else. Alternatives that
  make sense: jumping straight to a clean dynamic objective; or focusing on
  the multiparameter Fig 4 case because that's where the model-selection
  story lives.
  > M: Indeed first I want the reproduction. No jumping ahead. But I want a full workflow, with math, alg spec, a test suite and a report.
- [?] What's the target audience for the eventual outputs — a methods paper,
  the ERC/FWF grant case, a lab-meeting talk, a teaching artefact, or all of
  the above? This affects how much exposition we bake into specs and notes
  vs. keep terse.
  > M: the first target audience will be a lab meeting talk, where the focus will actually be the LLM-assisted workflow, not the science itself, which I already talked about to them and will too. Eventually, I want to write a theoretical paper, but that's not the next step. You don't need to think about the grant. So lotsa lotsa exposition.

Relationship to existing code and material:

- [?] Should this repo *reimplement* from scratch in `src/`, or wrap / port
  the existing `sequential_infomax.ipynb` + `infomax_class.py` from
  `github.com/mihalybanyai/infomax`? My instinct is to reimplement (the
  notebook has known bugs and ad-hoc fixes), but that's not free.
  > M: don't wrap or port anything. All implementation should be from scratch. The notebook is there for the maths.
- [?] Do you want `infomax_class.py` pulled into `resources/` so I can read
  the static implementation you've validated against?
  > M: let's try without that first.
- [?] The Overleaf cites a couple of GitHub artefacts (RP poster, lab meeting
  talk PDF) that aren't in `resources/`. Are those useful here, or strictly
  background?
  > M: those won't be useful here.

The dynamic objective itself:

- [?] In Overleaf §A.2.5 you flag a derivation gap between two forms of
  `L_dyn` that differ by a factor of `p_new(x̃_s)` outside the log (the form
  with the factor "obviously wants to be" the form without it, and the latter
  matches simulations). Do you want this nailed down as part of the spec
  phase — i.e. is "find the missing derivation step or prove the
  empirically-correct form rigorously" in scope? Or do we provisionally
  adopt the empirical form and flag it as a known math debt?
  > M: we will definitely want to nail this down but only later.
- [?] Same question for the m = 0 limit (currently special-cased in the
  notebook) and the negative-KL approximations capped at 1e-6. Are these
  numerical wrinkles we should just inherit, or open problems to solve before
  building the daisy chain on top?
  > M: we should look at these too eventually, but for the first reproduction step probably not necessary 
- [?] The dynamic objective sidesteps defining `p(θ, θ_old | n, m)` via the
  synthetic-sample trick. The Notion notes ask "what is the joint p(θ |
  θ_old) implied by the samples?" — is unpacking this an open theoretical
  goal, or a "leave it alone" pragmatic choice?
  > M: same as above: eventually importnant, not now
- [?] Is the case of *uncertain* N (overleaf p.46, "extending to when n is a
  random variable") in scope, or strictly future work?
  > M: future, maybe not so distant, but not now
- [?] Is the case of *unknown* likelihood — i.e. the EC leg of the daisy
  chain where the likelihood is being learned — in scope for code/spec, or
  only conceptual at this stage?
  > M: also for later

Modelling choices:

- [?] Are we restricting to *discrete* θ throughout (grid + BA, as in your
  notebook), or do you want the framework to admit continuous θ at some
  point (e.g. via the Dauwels-style particle filter MI estimator you've
  flagged as a TODO)? This is a fairly load-bearing architectural choice.
  > M: there should be an option to have a continuous theta. but it's ok to start with a discrete-but-fine-grained one. this point we should probably discuss.
- [?] Multiparameter examples: do you want to reproduce Mattingly's
  sum-of-exponentials Fig 4 as well, or stay one-dimensional for now? Fig 4
  is where the "model selection" story really shows up; without it the
  discreteness can feel like a curiosity.
  > M: this will probably be the second step. so let's keep the possibility of multi-dimensional thetas open
- [?] Mattingly's `d_eff` (Fig 4C) and the `MI ∼ (3/4) log K` scaling
  (Fig 3C) — are these reproduction targets too, or just nice-to-haves?
  > M: not a primary goal to have these

Daisy chain and downstream:

- [?] What does "success" look like for the daisy-chain simulations? You
  flag in the Birds-eye-view that it has no closed-form objective and you
  don't know what it converges to. Are we trying to prove a property, observe
  qualitative behaviour, generate experimental predictions, or all three?
  > M: let's come back to this later
- [?] Is the planned experiment (monster chef / wind tunnel / etc.) something
  this repo will eventually simulate participants for, or do experiments
  live elsewhere and we only generate predictions?
  > M: this is way outside the scope now

Workflow / repo:

- [?] Should `resources/` carry a `references.bib` (your Overleaf
  `infomax_refs.bib`) and the actual referenced PDFs as we accumulate them,
  or do you keep that elsewhere?
  > M: let's not burden the repo with a million pdfs for now
- [?] AGENTS.md prescribes "spec → tests → code". For the very first
  Mattingly reproduction, do you want a full spec in `specs/` even though the
  maths is fully in the paper, or is "spec = pointer to paper + a paragraph
  on numerical choices" enough?
  > M: let's do full spec. this is a test run for the workflow as well. 
