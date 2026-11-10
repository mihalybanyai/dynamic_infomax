# Meeting with FJ: teaching a likelihood; stimulus geometry; context switches

*Written 2026-11-09 at a meeting with FJ ([people](handwriting.md#people)). Transcribed by
Claude on 2026-11-10; transcription and glosses checked by MB the same day. Action items:
MB's, with Claude's suggestions marked. Markup: [README](README.md#markup).*

## Page

- how to teach a likelihood?
  - teach it hard, like with an adaptive sampler until convergence. people surely do this.
  - a likelihood is basically physics, or rather the causal structure of the environment.
  - could allow interventions as well, as well as observing latents directly
    - a many-D latent space can be tricky to learn

---

- tudjuk-e konstruálni a stimulusgeometriát? — *en: can we construct the stimulus
  geometry?*
  - ennek mekkora része a likelihood? lehet azt fixen tartani? — *en: how much of it is
    the likelihood? can that be held fixed?*
  - és mi marad akkor a priornak? — *en: and what is then left for the prior?*
- olyan altér, amin tudunk definiálni az egyenletest és nem szörnyű — *en: a subspace on
  which we can define the uniform [distribution], and which is not terrible*
- Solomonoff priorok? Más írt erről? — *en: Solomonoff priors? Has anyone else written
  about this?*

---

- a tanításnak része kell lennie, hogy kontext switchek vannak — *en: the teaching must
  include that there are context switches*
- Feri-féle kontext-switcheken keresztüli kauzalitás ⇒ ez a likelihood — *en:
  causality across context switches, Feri-style ⇒ this is the likelihood*
  - ↑ ez no-intervention setting *[arrow up to the line above, written beside the next
    line]* — *en: this is a no-intervention setting*
  - van humán evidencia? — *en: is there human evidence?*
  - milyen arányban van a viselkedésben intervenciós és obszervációs
    kauzalitásbecslés? — *en: in what proportion does behaviour use interventional vs.
    observational causal estimation?*

## Action items

### Empirics

- can we design a pre-training phase in human experiments that teaches the likelihood,
  potentially making use of adaptive and active sampling and interventions?
  - *Claude:* end pre-training with a criterion test that the likelihood has been
    learnt, so that a failure to learn the prior cannot be a failure to learn the
    likelihood. The adaptive sampler "until convergence" could serve as that criterion.
  - *Claude:* whether pre-training uses interventions or only observation decides which
    kind of causal learning the third item can study. Making it a factor would also
    answer the page's last question, on interventional against observational causal
    estimation in behaviour.
- JF: this phase needs to teach that the context (the prior) will change, so when we
  transition into the training phase, it's familiar
  - *Claude:* a pre-training built from context switches is already the setting of the
    next item. If the likelihood is what stays fixed across switches, the same phase
    tests whether people learn it that way, so the two items may be one manipulation
    [guess].
- in machine learning, observational inference of causal structure (which I think is
  largely the same as learning a likelihood), is done by looking at structure preserved
  over context switches (Feri has 2 papers about it with the Schölkopf gang). do we know
  if this modus operandi is relevant to humans to any degree?
  - *Claude:* the two papers are probably [Causal de Finetti](https://papers.neurips.cc/paper_files/paper/2023/file/7279908471a7dd4898d2715f7c6a7413-Paper-Conference.pdf)
    (Guo, Tóth, Schölkopf & Huszár, NeurIPS 2023) and
    [Do Finetti](https://arxiv.org/abs/2405.18836) (Guo, Zhang, Mohan, Huszár & Schölkopf,
    NeurIPS 2024) [read: search-result abstracts only]. Both treat multi-environment data
    as exchangeable; the first identifies causal structure from such data without
    interventions. By de Finetti's theorem, exchangeable data are a mixture over a latent
    parameter, which is spec 002's own setup (a nature draws `θ`, the likelihood
    generates data). So "the likelihood is preserved across contexts, the prior changes"
    may be the same split those papers use [guess][^definetti].
  - *Claude:* human causal learning from interventions against observation has a
    literature (Steyvers et al. 2003; Lagnado & Sloman 2004) [recalled][^human-causal].
    Whether humans use invariance across contexts: not checked.

### Theory

- this is about how to choose a hyperprior over natures for spec 002
  - *Claude:* the same day's parked idea
    [Benchmark natures](../../notes/parked_ideas.md#benchmark-natures-2026-11-09) states
    the obstacle: any weighting of natures is itself a prior. Spec 002 already has one:
    `q̄` pools the tilt grid "with equal weight per nature" (§4.3), a uniform hyperprior
    whose meaning depends on how the `t` grid is spaced. **Route?** spec 002 §4.3: an
    unstated choice in an active spec, best settled before the sweep runs.
- is it possible to look at a decision making problem, e.g. a simple game, and
  reconstruct the latent parameter geometry for it?
  - *Claude:* in spec 002 the geometry is `g`, the Fisher metric of the likelihood, so
    this asks for the game's likelihood; it is the page's "how much of it is the
    likelihood?". For a game scored by something other than log-loss, the metric would
    come from that loss instead [guess]. It is also the reduction "Benchmark natures"
    asks for: one everyday task cut down to a few tens of parameters.
- is there such a subspace of the space of all possible natures on which the uniform
  distribution is possible to define in a way that's useful for us? - I guess this is
  what we've been doing when developing the spec anyway
  - *Claude:* yes: the tilt family `q_t ∝ (√det g)^t` (spec 002 §2.3) is a
    one-dimensional subspace of natures. Uniform on it is the next problem, since
    another parametrisation of the axis changes it. `q_t` is an exponential family in `t`
    with statistic `s = log √det g` (floored), so its Fisher information in `t` is
    `Var_{q_t}(s)`, and the reparametrisation-invariant choice on the axis is Jeffreys,
    `∝ √Var_{q_t}(s)`. It is computable from the nature samples already drawn. How it
    behaves near `t_min`, where conc04 F1 finds `q_t` collapsing, is unknown [guess].
    **Route?** spec 002 OQ-2, with the item above: a candidate weighting for `q̄`.
- a wilder idea: Solomonoff-type hyperpriors in the space of natures. does this make
  sense even?
  - *Claude:* formally yes, for computable natures: weight each by `2^{−K(q)}`, with `K`
    its shortest program length. Its one claim to neutrality is the invariance theorem:
    changing the universal machine changes `K` only by an additive constant
    [recalled][^solomonoff]. It is still a weighting and favours simple natures, so the
    Benchmark-natures objection holds, up to that constant. A computable stand-in is the
    code length of each nature in a chosen description language, which ties it to
    [MDL](../../GLOSSARY.md#minimum-description-length-mdl) and to the parked idea on
    construction cost [guess].

[^definetti]: Settled by reading what Causal de Finetti holds fixed across environments
    and what it lets vary.
[^human-causal]: Steyvers, Tenenbaum, Wagenmakers & Blum 2003, *Cognitive Science*;
    Lagnado & Sloman 2004, *JEP: Learning, Memory, and Cognition* [recalled]. Settled by
    opening both.
[^solomonoff]: Settled by Li & Vitányi, *An Introduction to Kolmogorov Complexity and Its
    Applications*, the invariance theorem [recalled].
