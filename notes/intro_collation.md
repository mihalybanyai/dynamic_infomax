# Intro collation: every intro-style piece of MB's own writing, in one place

**Status:** editorial collation, not a note with new content. Assembled by Claude
(Fable 5) on 2026-09-15 by searching the repo, the Notion export, the Overleaf
source, the transcripts, and git history. All fragment text is **verbatim MB
writing** (authorship flagged per fragment where uncertain); everything prefixed
`C:` is Claude annotation.

**Purpose.** Raw material for writing the project's missing intro — the
backbone text of the planned web-based project object. Neither `README.md` nor
`AGENTS.md` currently says what the project is about (both hold placeholder
brackets), so this is the complete inventory of what exists to edit down from.

**⚠ Before committing this file:** fragments 1–6 are recovered from
`resources/google_doc_export.md`, which was deliberately **removed from the repo
on 2026-05-17** (commit `da9b9eb`, "gdoc export removed") — plausibly because
the repo is public and the doc contains grant-strategy material and
collaborators' text. Review whether these excerpts may live in a public repo, or
keep this file local / trim it before committing. Recover the full source with:
`git show cad0a8a:resources/google_doc_export.md`

---

## Inventory at a glance

| # | Fragment | Source | Register | Authorship |
|---|----------|--------|----------|------------|
| 1 | "A generic intro not respecting any word limits" | gdoc (git history) | essayistic, first-person voice | MB (presumed — confirm) |
| 2 | FWF narrative | gdoc (git history) | polished grant prose | MB (presumed — confirm) |
| 3 | Compact 4-paragraph abstract | gdoc (git history) | abstract-length | MB (presumed — confirm) |
| 4 | "Misi's version of 1.1" | gdoc (git history) | one-paragraph pitch | MB (explicitly labelled) |
| 5 | "Old intro 1.1" | gdoc (git history) | early draft paragraph | MB (presumed) |
| 6 | Thesis one-liner + GIST attempts | gdoc (git history) | telegraphic | MB (partly Hungarian) |
| 7 | Overleaf `main.tex` opening + "Frame from finitude" | `resources/overleaf_doc/main.tex` | working-paper prose | MB |
| 8 | Talk narrative: "Amoebae and Humans" | Notion export, `writing notes` | talk outline, full arc | MB |
| 9 | APRV thread core claim | `notes/aprv_thinking_state.md` | thread-specific | MB (file is human-maintained) |
| 10 | Meta-project intro (the workflow layer) | `transcripts/000-initial-planning-chat.md` | conversational | MB |
| — | Co-authored / adjacent material | various | — | mixed — see end |

Dating: fragments 1–6 were committed to the repo 2026-05-16 (commit `cad0a8a`,
"added all old documentation") and accrued earlier during ERC/FWF drafting;
internal dates unknown. The Notion export and Overleaf copy are also snapshots
from 2026-05-16; their content predates the repo.

**C:** The project runs under at least four names across these sources —
"Representational coarse-graining from limits on observation" (Overleaf), "Model
selection from observational constraints" (Notion), "Finite-observation optimal
priors for sequential decision making" (Notion subpage), "The origin of symbolic
computation" (gdoc). The intro will implicitly pick one; worth doing it
deliberately.

---

## 1. "A generic intro not respecting any word limits"

**Source:** gdoc export (git history), section after the compact abstract.
**Register:** the least grant-constrained, most voice-carrying intro that exists.

> In this proposal we are concerned with the process of learning, that is,
> adaptive behaviour as it actually happens in wild type humans and algorithms.
> To illustrate, imagine yourself to be in the learning situation most paramount
> to psychology: that of a Prolific subject. You, having been made the rational
> decision of not reading the instructions due to the opportunity cost of time
> you are exposed to, now face the ill-defined learning problem of figuring out
> the experiment on the fly, still making some of the bonus in the 200 or so
> trials. What aspects of the stimulus will actually be relevant to pay
> attention to? Should you be making distinctions based on the location of
> random-seeming elements? Do you have enough trials to figure out if the phase
> of the gratings matters at all and still capitalise on it in case it does, or
> are you better off not trying, shooting for 60% of the bonus and watching
> cartoons on the side? Your only consolation is that whatever you do, the
> researcher that hired you will have no theoretical tools to even attempt
> dissecting your behaviour.
>
> A more in-the-wild example, equally pressing to the average psychologist, is
> when you decide to learn to code properly on the side, so you can get a
> software job when you fail to secure a permanent research position. The task
> as a whole is to optimise some sort of long-term life satisfaction, and as
> such it's hopelessly vague - but at such a scale this is to be expected. When
> you nevertheless start breaking it down comes the horror of realisation that
> it is a fractal of vagueness: even at the smallest scale, when trying to
> figure out how to sort some numbers based on an example copied over from
> stackoverflow, you have to decide at what level of detail will you attempt to
> understand the solution (e.g. you might want your knowledge to generalise to
> sorting words alphabetically, but not to speeding up already-working sorting
> algorithms). Does it matter what libraries are imported? You very much hope
> that you don't need to get compiler-level shenanigans, but you still don't go
> all the way to learning chatGPT prompts instead. But who knows what is right
> and why? Even so, making progress in learning to code is no less possible than
> earning bonus on Prolific.
>
> We argue that basically all learning problems that people routinely solve are
> in this category, where the lion's share of the effort is circumscribing what
> needs to be learnt in the first place; so much so that when a learning problem
> is artificially set up to be well-defined, such as a game, people are still
> very prone to divinating from irrelevant stimulus features, seemingly unable
> to turn off their task-redefining facility completely during learning (while
> it seems eminently possible to turn off learning itself entirely). Tasks that
> are actually well-defined tend to only appear as very specific sub-skills of
> larger problems, typically through tutoring (the above examples were chosen
> such that they minimise the role of tutoring to keep the learning problems on
> the single-agent scale). In every other case you constantly have to fiddle
> with the definition of the task, and failing to do so somewhat efficiently is
> usually perceived as being dumb.
>
> Of course, the general shape of this idea isn't new: the literatures of
> learning theory, cybernetics, the psychology of perception and probably others
> all assert that the bulk of learning is to get from the raw sensory input to
> the few bits of information that can be used to learn how to decide - exactly
> the kind of task redefinition exemplified above, often termed representation
> learning. Nevertheless, there is no normative theory of doing this optimally
> in any of the computational frameworks for learning. In Bayesian inference,
> model selection, where one makes decisions about which variables might matter,
> is heuristic at best. In reinforcement learning, the dynamics of the
> representational component is usually not made explicit at all, and ad-hoc
> techniques are used to prevent the representation from converging to something
> strongly suboptimal. There is also no descriptive theory of how humans adjust
> their representations dynamically during a learning task. We aim to start
> filling both of these voids with a novel approach.
>
> The root of the problem with representation learning is that in general it's
> about finding an optimum (or at least a good spot) in a search space that is
> mind-numbingly vast even for the simplest of learning problems, and the usual
> objectives of expected reward and stimulus log-likelihood provide very little
> information about good directions to search in, leaving the search severely
> underconstrained. However, the agent-environment ecosystem has a lot of
> structure beyond what's usually formalised in the existing frameworks, such as
> resource limitations or rigid algorithmic architecture. Making agents reflect
> on such structural elements when making decisions is termed meta-cognition,
> and is an approach that already yielded insights into memory formation and
> confidence among other phenomena. We suggest that representation learning is
> best understood as meta-cognitive decision making as well, and the key to a
> normative theory is to incorporate the relevant constraints into the objective
> function the agent maximises during learning.
>
> We note that the choice of an optimal representation is informational and
> anticipatory in nature - what one has to consider is the information the
> representation preserves from the sensory input for decision making, and in
> particular, the possibility of learning the representation makes possible over
> a certain amount of time. This suggests that the relevant constraint to work
> into the meta-cognitive algorithm is that of the amount of time the agent has
> before it has to obtain mastery of the task - or equivalently, the expected
> number of observations it will have to work with. This constraint, which we
> call the urgency of learning, is inherently a part of every agent-environment
> interaction, yet rarely formalised in the learning algorithm. However, it
> holds promise both from the theoretical and the experimental points of view.
> Optimality results in rate-distortion theory provide a way to normatively
> assess information-maximising representations in exactly the kind of
> information-constrained settings that urgent learning problems are a subclass
> of. Specifically, they specify how many discretised feature values the agent
> should represent depending on how many observations it can expect. At the same
> time, the urgency of learning provides an excellent handle to control
> experiments and make measurements that allow for the empirical validation of
> the normative theory. Consequently, an agent that explicitly reflects on the
> finite nature of its expected experience usefully extends asymptotic Bayesian
> inference engines with normative model selection, and temporally discounted
> reinforcement learners with a principled representation learning that's
> computationally more feasible than model-based planning.
>
> Our approach will not solve the problem of representation learning in one fell
> swoop, but it establishes a foothold towards a normative theory of human
> representation learning. Other approaches to similar questions, like program
> induction or certain types of hierarchical Bayesian inference or deep
> reinforcement learning are complementary to ours because these address the
> representational search space with more efficient algorithmic structure for
> search, and we aim for extending the basic computational principle in a
> meta-cognitive direction, while keeping the algorithmic structure simple
> enough to be fully interpretable for researchers.

**C:** This is the strongest candidate backbone for a web-object intro: it
motivates from lived examples, states the void honestly ("no normative theory",
"no descriptive theory"), and positions the constraint before any math. It never
mentions discreteness's *mechanism* (finite-n infomax / Mattingly) by name — a
reader would still need fragment 3 or 7 for that.

---

## 2. FWF narrative

**Source:** gdoc export (git history), "FWF narrative" section.
**Register:** polished grant prose, "we". Presumed sole-MB; confirm.

> Human learning experiments typically exhibit a large amount of variation
> across individuals and conditions that is unaccounted for by computational
> models. While there are several sources of noise in any such measurement, we
> propose that the largest systematic source, and thus the most fruitful target
> for novel modeling approaches, is the formalisation step that is performed by
> all participants at the beginning of experiments, and is typically not
> modeled: this is when a human in a novel situation translates the perceptual
> space into a problem to be solved, that is, it formalises it into a
> mathematically defined learning problem. E.g. a room with a desk, a lamp, a
> chair, a screen with 106 pixels on it, a keyboard with 100 keys on it, a
> carpet and a door gets translated into the orientation of a line segment with
> 8 possible values, 2 possible actions and a scalar reward. The models usually
> assume that this translation happened in a particular way, similarly for all
> participants. However, this translation process is one of the most significant
> components of any learning process, as is captured by two concepts we borrow
> from the artificial intelligence literature: the *frame problem* states that
> every computation performed by a biological or artificial agent has to start
> with choosing the relevant set of variables to work with (the frame), and this
> search problem has no known normative solution for any problem class of
> interest. Relatedly, the *big world hypothesis* states that any physically
> situated agent (thus any biological one) is always surrounded by vastly more
> information than necessary for solving any particular task, so much so that
> simplistic approaches for problem formalisation are hopeless to work in
> general. Consequently, a human in a learning experiment is less akin to the
> student solving a perfectly formalised textbook problem where the solution is
> known to exist, and more akin to the scientist faced with a natural
> phenomenon, having to figure out what part of it can be usefully formalised
> into a solvable problem in the first place.
>
> We don't propose that the problem of finding frames in a big world should be
> addressed directly in its full generality, as such an attempt is unlikely to
> be useful; but we do propose that we should aim to nibble away at it, by
> modelling the formalisation process itself in specific situations. Such
> advances will be critical to model human learning and problem solving, but
> will require new principles to augment existing modelling techniques that step
> in at the end of the formalisation stage. Our new principle will involve using
> a new piece of information that is part of any task definition for a
> biological agent, but is typically not used in modelling, at least not for
> setting the frame: the amount of information the agent expects to observe
> during learning, or analogously, the *urgency of the learning process*. This
> means that a learner always has a sense of how quickly it has to acquire the
> learning target, either due to external pressure, e.g. every new observation
> carrying additional risk (or in an experimental setting, simply running out of
> time), or an internal one, e.g. having to acquire food before starvation sets
> in. This urgency is importantly different from urgency within a single trial,
> where the amount of computation the agent can do on the sensory input before
> making a decision is limited (e.g. how precisely we can position the ping-pong
> racket before the ball gets too close), as in our case the urgency is applied
> to the entire learning process (e.g. we know we have about 20 games to get
> good enough at ping-pong so that the other kids don't get frustrated playing
> with us).
>
> The learning urgency signal is useful because it lends itself to partially
> constraining the frame problem: using an important result from information
> theory, for any variable that is a learning target, we can choose the set of
> possible values that we have to consider in order to maximise the amount of
> learning from a set number of observations. E.g. in the line segment
> orientation example, we can tell how many possible orientations do we have to
> consider *a priori*, in order for the incoming observations to teach us the
> most about the orientation distribution, based on the expected number of those
> observations. We use this result to model part of the formalisation process,
> namely the discretisation of target variables chosen by learners, in such a
> way that it is precisely predicted by a parameter of the experiment, the
> urgency of learning, that is reasonably easy to control in various paradigms.
>
> This way we end up with a three-fold goal: first, we build a model to make
> specific predictions about discretisation of learning targets in humans, which
> is also a prerequisite for the emergence of symbolic computation. Second, we
> develop a suite of experimental paradigms that directly test such predictions,
> providing a way to empirically address the formalisation stage of learning
> processes. Third, and in some sense most importantly, the mathematical
> technique we use to integrate a novel piece of information into our modelling
> to produce a normative constraint and thus predictions is a general one. We
> use but a small part of the task specification to make some headway into the
> frame problem; the bulk of it remains. However, beyond our particular model,
> our approach opens up the possibility to use the same technique to address
> different aspects of the task definition similarly. Thus our proposal is also
> that of a generative principle offering a modus operandi to future models of
> the human problem specification process.
>
> Our approach stands on a stage set by numerous existing methods aiming to
> model different aspects of learning processes: hierarchical Bayesian
> inference, reinforcement learning, resource rationality and efficient coding
> theory all capture important but complementary phenomena to our approach, and
> their results enable us to add a new direction to the search for comprehensive
> models of intelligent behaviour.

**C:** The most complete single intro: frame problem → big world → urgency →
discretisation → three-fold goal → related work, in five paragraphs. The
lamp-desk-carpet-to-line-segment example and the ping-pong contrast are the two
most reusable images in the whole inventory. Note the ping-pong passage recurs
almost verbatim in fragment 7 (`main.tex` §1) — pick one home for it.

---

## 3. Compact abstract-style intro

**Source:** gdoc export (git history), unlabelled section preceding fragment 1.

> When humans construct representations of environmental stimuli, they do so in
> settings where they can expect to access a limited amount of observations
> before having to make a decision based on what they learned.
>
> While there is a growing wealth of empirical knowledge about what pieces of
> information humans use for decision making and retain in memory, and what they
> discard, and there are various computational theories of learning and decision
> making, we lack a general theory of representational dynamics over the course
> of learning a task. In fact there is neither a normative characterisation of
> an optimal solution to task learning problems with representational
> components, nor an empirical exploration of humans' actual representational
> trajectories to compare to what such a theory would predict. The two main
> obstacles to obtaining those things are on the one hand the need to cut
> through a combinatorial explosion of possible representations every step of
> the way, which will require us to leverage a computational principle in
> addition to maximising task performance or making stimulus encoding efficient;
> on the other hand the difficulty of experimentally assessing human
> representations based on behaviour only.
>
> We propose that a meta-cognitive representation learning algorithm that can
> explicitly reason about the finitude of the set of observations it will have
> to work with, offers exactly the kind of leverage point that enables a
> theoretically motivated algorithmic narrowing of the representational search
> space, and lends itself to empirical tests that can check its predictions
> using data that is reasonably collectable in behavioural experiments.
>
> Specifically, we ask how the sense of urgency during task learning modulates
> how strongly humans discretise their representation of a feature space.

**C:** The tightest existing statement of the whole project; the last sentence
is the project in one line. Good candidate for the web object's above-the-fold
text.

---

## 4. "Misi's version of 1.1"

**Source:** gdoc export (git history), "Older snippets", explicitly delimited
`Misi's version`.

> Knowing that one's budget of making observations will run out before getting
> perfectly informed for a decision is a glass half full. While certainly
> limiting in terms of expected performance, such a limitation can be turned
> around to serve as the basis of decision when choosing an efficient
> representation of the stimulus space - a problem otherwise woefully
> underconstrained [Bramley?]. We propose that such a consideration can be used
> to predict how humans will choose to discretise their representation used in a
> novel task, which choice in turn can also be measured using an appropriately
> designed two-stage task structure [Orbán08]. Taken together, the theory and
> the experimental paradigm allows for the empirical testing of a representation
> learning hypothesis that naturally extends Bayesian inference [Tenenbaum?,
> FiseretalTICS?, ?Bernardo] and resource rationality [Falk&Tom] based on
> results from information theory [e.g. Rose]. Specifically, we predict that
> people will continually adjust the resolution of their discretised
> representation of a continuous parameter space depending on their estimation
> of the information available in the environment before being forced to make a
> good decision. Furthermore, we propose that such discretisation serves as the
> basis for hierarchical representations [fragment grammars?] via internally
> imposed information budgets for meta-cognitive decision making. As
> representational dynamics changes during development [?], we intend to test
> both the basic prediction and the hierarchical extension in children of
> various ages using an appropriately adjusted experimental paradigm
> [Oana/Ernő?], as a further empirical test of the theory and measurement
> paradigm.

**C:** "A glass half full" is the best one-phrase framing of the core move
(constraint → resource) in the inventory.

---

## 5. "Old intro 1.1"

**Source:** gdoc export (git history), "Older snippets".

> While decision making can be successfully described as inference in a model
> (e.g. Bayesian inference, or policy evaluation in RL), and learning in a
> pre-defined setting can similarly characterised as parameter estimation in
> such models, a big component of problem solving is to decide what model we
> want to do inference and estimation in the first place. This corresponds to
> the choice of generative model in BI, and to learning a good representation to
> base the policy on in RL. In its full generality, the model picking /
> representation learning problem is almost always intractable due to the search
> space being infinite and lacking a useful metric; what an agent should aim for
> is to drastically slash the space of possible models or representations using
> a principled heuristic.

**C:** Superseded by fragments 1–3 in substance; kept for completeness.

---

## 6. Thesis one-liner and GIST attempts

**Source:** gdoc export (git history), "Thesis" section and "GIST" attempts.

The thesis, with its named competitors:

> Discrete representations come about due to their information content being
> maximal when the number of observations is expected to be limited.
>
> Competing theses: resource-rational models with scarce resources other than
> the expected number of observations; hierarchical Bayesian models that
> implicitly model-select based on context; plain old RL with discounting;
> consequence of cellular architecture (way easier to implement a stable
> flip-flop than a continuous-value storage); affordances, when the
> discretisation comes from the action space.

GIST attempt #3 (the most complete of the three):

> - Formal models describing mental processes are usually picked from an
>   infinite model space in an *ad hoc* manner and model selection chooses the
>   best of them
> - We explore the claim that a more generic tabulation of any given model space
>   can be derived on a normative basis using resource rationalization based on
>   limited TIME (is this new? What is new in it?)
> - Specifically, as a resource gets scarcer, the optimal prior of the model
>   will shift from continuous to a discrete representation in a particular
>   pattern of discretization. This is the Theory of Urgency. (needs
>   justification: why?)
> - We demonstrate the generality of this phenomenon by showing the emergence of
>   discretization of the internal prior representation in a standard setup of a
>   behavioral learning experiment
> - As discretization of the prior has a strong link to chunking, hierarchy,
>   categorization, explicit thinking, meta-learning, language, we will explore
>   the consequences of our findings in the context of these phenomena in human
>   cognition

**C:** The competing-theses list is exactly the kind of honesty the web object
wants on its front page — most intros hide this. (Reformatted from bullet
telegraphese; wording preserved.)

---

## 7. Overleaf `main.tex`: opening + "Frame from finitude"

**Source:** [main.tex](../resources/overleaf_doc/main.tex) lines 27–33, title
"Representational coarse-graining from limits on observation". In-repo snapshot
2026-05-16; written earlier on Overleaf. First person singular — the only
polished intro in *I* voice.

> This project came about as part of a broader research effort aiming to develop
> a computational tool that can be used to model representational dynamics; that
> is, the meta-cognitive choices learning agents continually make about what
> information they ought to retain from their sensory streams to make decisions.
> I believe representational dynamics to be the backbone of any intelligent
> behaviour, and to encompass e.g. concept formation, belief changes and all
> what is interesting about human cognition. My approach is concerned with three
> major aspects of this dynamic: first, setting frames, in the sense of choosing
> the model in which to make inferences, second, the actual temporal dynamics of
> the framing choices over the course of a learning process, and third, task
> switching in the sense of the agent realising that it should solve a related
> but different task to what it's currently solving (e.g. one at a much coarser
> granularity in terms of choices), based on a meta-cognitive evaluation of its
> situation and performance.

(Footnotes elided here — including the thermostat/representationalism footnote,
which is itself a compact position statement worth promoting to body text in a
web intro.)

From §1, "Frame from finitude":

> A simpler scenario in which the frame problem applies just as well is passive
> statistical learning, usually modelled as Bayesian inference (BI). However, in
> order to constrain any property of the model itself beyond the posterior BI
> would result in, one will need to use an additional piece of information about
> the learning scenario. One such possibility arises from the fact that a
> learner typically has a sense of how quickly it has to acquire the learning
> target, either due to external pressure, e.g. every new observation carrying
> additional risk, or an internal one, e.g. having to acquire food before
> starvation sets in. This urgency is importantly different from urgency within
> a single trial [...] as in our case the urgency is applied to the entire
> learning process (e.g. we know we have about 20 games to get good enough at
> ping-pong so that the other kids don't get frustrated playing with us). This
> extra constraint won't solve us the entire frame problem, but it will solve a
> small slice of it, namely when we have a set of candidate variables, which
> possible values should we consider for those a priori.

**C:** The only intro that names the antecedent (representational planning) and
positions the MI move as a deliberate retreat to a tractable lens — that
origin-story honesty exists nowhere else in the inventory. Also the only one
mentioning the daisy chain's role. Section header "Frame from finitude" is a
strong candidate section title for the web object.

---

## 8. Talk narrative: "The missing link between Amoebae and Humans"

**Source:** Notion export,
[writing notes](../resources/notion_export/model%20selection%20from%20observational%20constraints/writing%20notes%202b380d8535ad8006839fe99f3f330a12.md).
Bullet outline, but a complete narrative arc. Key opening moves, verbatim:

> Talk: The missing link between Amoebae and Humans: a process model of
> specifying the model for inference
>
> - **Lotsa unexplained variance in learning.**
>     - lots of it feels like this conceptual advancement, like getting to the
>       right kind of abstractions, and then learning with those becomes easy.
>     - the Hofstadter kinda thing: ok I banged my head against the wall in this
>       formalism enough, what about trying a different one?
>     - so this is actually a process, not just a goal
>     - none of the popular learning algorithms have such a component
>     - a blast from the past: the ***frame problem***
>         - this is actually very simple: how to decide what variables even
>           matter?
>         - equivalent to choosing a model to do BI in
>         - for the computational complexity nerds out there: even worse, as a
>           problem class the frame problem is almost certainly incomputable, as
>           any solution to it would formalise the process by which
>           formalisation happens in agents, strongly hinting at Gödelian issues
>         - but we don't lose much sleep over BI being NP-complete either. it
>           just means there won't be fully general solutions, but biological
>           agents aren't fully general either, so that's fine
>     - BI has this kinda flat view of the world, as one big statistician's
>       assignment
>         - while there is a detailed agent-environment dynamic with boundaries
>           and various constraints at play
>         - a lot of the confusion in the bayesian literature comes from
>           ignoring this structure I think

(The full outline continues through: attempts to say something about this
structure — resource rationality / RL / autopoiesis all "saying zilch" about the
interesting part; the information flow at the agent-environment boundary; the
time-allotted constraint and proto-symbols; the daisy chain process model and
the misspecification signal; "the future gives the shape, the past the
weighting". See source for the rest.)

**C:** This is the only source that carries the *whole* story — frame problem
through daisy chain — in one arc, and the phrase "the future gives the shape,
the past the weighting" is the best one-line summary of the first simulation
result anywhere in the repo.

---

## 9. APRV thread: the core claim

**Source:** [aprv_thinking_state.md](aprv_thinking_state.md) (human-maintained
by convention; last updated 2026-05-24). Thread-specific intro — the application
of the framework to the AP/RV perceptual-decision manuscript:

> The manuscript treats the asymmetry between AP and RV dynamics — RV behaves
> jumpily (CP-like), AP behaves driftily — as a brute fact about prior
> experience, manipulable via training (Exp 7–9) but otherwise unexplained at
> the default level. The new framing: **this asymmetry follows from how
> finite-$n$ infomax discretizes the two parameters**, because they carry
> information about themselves through structurally different likelihoods.

**C:** Not a project intro, but the model for what a per-thread intro on the web
object should look like: claim, what it explains, what's load-bearing vs. soft.

---

## 10. The meta-project intro (workflow layer)

**Source:**
[000-initial-planning-chat.md](../transcripts/000-initial-planning-chat.md),
MB's second prompt, 2026-05-16. The project's other half — the workflow — has
its intro only here:

> I have been long interested in improving not only scientific software
> practices, but also communication between supervisors, students and readers.
> This means that I think there should be a lot more documentation (especially
> on the math and algorithms side), diagramming, test suite specification, etc.
> between supervisors and students, to relieve both from the situation that the
> student is left alone with implementation and the supervisor just strongly
> hopes everything is fine. [...] I'm open to any other setting that helps work
> with LLMs as if they were teammates, focusing on the amount of (reliable)
> scientific understanding that is produced in the end, instead of old-fashioned
> coding or publishing "productivity". And I want to explore this space in such
> a way that I can summarise effectively to my labmates as well.

**C:** The planned web object is itself a continuation of this paragraph; the
site will need it (or a descendant of it) to explain its own form, not just the
science.

---

## Co-authored and adjacent material (not collated verbatim)

- **ERC abstract ("Jozsef's version") and ERC §1.1–1.4** — gdoc export. The
  abstract sits under Jozsef's heading; §1.1–1.4 read as mixed authorship
  (§1.3's "glass half full" logic is clearly MB-derived, §1.1's framing around
  symbolic computation likely joint). Usable as raw material only after
  untangling whose sentences are whose. §1.4 (relation to RR / RL / hierarchical
  Bayes) is the most complete related-work prose anywhere.
- **"Anatomy of a cost"** — Notion `writing notes`, "Earlier overleaf" block.
  MB-written; a framing piece on how physical constraints become informational
  costs. Intro-adjacent: belongs in a "why this constraint" section, not the
  opening.
- **birds-eye view** — Notion export. Process-view / open-endedness / Peter
  discussion. Working map, not intro; but it is the only text on *why the daisy
  chain is not (and needn't be) normative*, which any honest intro must
  eventually say.
- **`notes/000-reading-summary.md` §1 "What this project seems to be about"** —
  Claude-written (2026-05-16). Explicitly not MB's voice, but the cleanest
  existing third-party reconstruction; useful as a comprehension check against
  whatever intro gets written.

---

## C: What none of these fragments say (gaps a new intro must fill)

Flagged from the stance of the uninitiated-but-technical reader; all four are
absent from *every* fragment above:

1. **What has actually been built and found.** Every fragment is promissory
   ("we will show..."). None states: spec 000 reproduced Mattingly Fig 1; the
   betting experiment (spec 001) came back *negative* for the naive claim and
   forced the two-hats reframing (`notes/infomax_two_hats_and_directions.md`);
   spec 002 is testing foreign-q prediction. The web object's intro has the
   chance to be the first version written *after* contact with evidence.
2. **The status of the daisy chain.** Fragments 7–8 introduce it as the payoff,
   but the derivation issue (line-316 problem, `notes/daisy_chain_derivation.md`)
   and its non-normative status are only in working notes. A credible intro
   says which parts are solid (static result: textbook), which are conjecture
   (dynamic objective), and which are broken-and-known (the derivation step).
3. **One name.** Four titles across sources (see inventory note).
4. **Who this is for.** Each fragment implicitly addresses a panel (FWF, ERC) or
   an audience of peers; none addresses "a stranger with math who found this
   repo" — the stated audience of the web object.
