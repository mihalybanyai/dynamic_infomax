# Empowerment: the capacity of the action channel

*Adjacent area: it connects to the project and feeds no spec claim. Drafted by Claude on
2026-11-13 from Salge, Glackin & Polani 2014 (read §4.4–§4.6), Jung, Polani & Stone 2011
(read §3 and parts of §5), Eysenbach, Salakhutdinov & Levine 2022 (read §4, §6) and
Mohamed & Rezende 2015 (read §4); not yet reviewed by MB.*

## Question and central object

What is a state worth to an agent that has no task yet? *Empowerment* answers with the
[channel capacity](../GLOSSARY.md#channel-capacity) from the agent's next `n` actions to
its sensor state afterwards, `max_ω I(A_{1:n}; S_{t+n} | s)`, where `ω` is a distribution
over action sequences [read: Salge §4.4.2–§4.4.3]. The agent prefers states of high
capacity.

It is spec 002's `p*` with the channel turned round (Claude's mapping):

| Spec 002 | Empowerment |
|---|---|
| parameter `θ`, chosen by [nature](../GLOSSARY.md#nature) | action sequence, chosen by the agent |
| likelihood `p(x\|θ)` | dynamics plus sensor |
| `p*` and `C_N` | capacity-achieving `ω`; the empowerment of a state |
| budget `N`, noise `σ`, box `Θ` | horizon `n`, sensor noise, actuator limit |
| [atoms](../GLOSSARY.md#atom) | the few sequences given weight; "skills" |
| uniform prior `p_U` | uniformly random action sequences |
| [Jeffreys](../GLOSSARY.md#jeffreys-prior), the infinite-budget limit | an agent that senses every action it took |
| foreign nature `q` | a downstream reward chosen by someone else |

**MB's reading (2026-11-13).** Empowerment is one formalisation of affordance learning:
finding good grasps on nature. Representation learning, of which `p*` is one
formalisation, is the inverse: giving nature good grasps on oneself, so that observations
shape the learner efficiently. Representation learning here means the choice of the
prior. The choice of the likelihood is efficient coding, which MB counts as another
mirror of `p*` theory, along a different axis.

## What mirrors our objects

1. **A design object, not a behaviour.** The distribution that achieves capacity is not
   the one the agent acts by; empowerment measures what the agent could do [read: Salge
   §4.4.2]. This is the distinction behind the
   [two-hat error](../GLOSSARY.md#two-hat-error), built in from the start.
2. **Uniform inputs concentrate as dimension grows.** In a toy world, mutual information
   under uniformly random sequences falls toward zero as the horizon grows, because most
   sequences end in the same absorbing state, while empowerment stays constant [read: Jung
   §3.2–§3.3]. Compare the uniform prior on the motives of spec 002 §0, whose prior over
   fairness narrows as `1/√D` (computed in chat on 2026-11-11; the script is not in the
   repo).
3. **The infinite-budget limit is degenerate.** With a long horizon, or a sensor that
   registers every action, every sequence is distinguishable, every state scores the log
   of the number of sequences, and the landscape is flat. The authors call this the
   "Tragedy of the Greek Gods", conclude that limits on sensing and acting are needed, and
   call the choice of power and resolution an open question [read: Salge §4.5.4]. Jung et
   al. have no analytical account of how horizon, step size and noise interact [read: Jung
   fn. 5]. Compare `notes/infomax_two_hats_and_directions.md` §2: the limit brings the
   co-volume bias back.
4. **Relevant and irrelevant directions.** With Gaussian noise and a power limit on
   actions, a singular value decomposition splits the action-to-sensor map into parallel
   channels, and water-filling gives power only to the strong ones [read: Salge
   §4.6.8–§4.6.9]. This is the
   [relevant/irrelevant](../GLOSSARY.md#relevant-and-irrelevant-directions) split with an
   explicit threshold. With an amplitude limit the experiments discretise to the extreme
   controls [read: Jung §5.1].
5. **Sparse support by selection.** "Impoverished" empowerment keeps only the sequences
   that contribute most, and a little noise favours sequences whose outcomes lie far apart
   [read: Salge §4.5.5]. Compare `p*`'s atoms, about one
   [Fisher length](../GLOSSARY.md#fisher-length) apart.
6. **Minimax against a foreign task.** For skills `z` that maximise `I(S; Z)`: the skills
   lie on vertices of the polytope of achievable state distributions; all skills with
   weight are at equal divergence from their average (the
   [equalizer condition](../GLOSSARY.md#equalizer-condition)); there are at most `|S|`
   distinct ones; and their average state distribution is the minimax-regret starting
   point against an adversarially chosen reward, by the
   [redundancy–capacity theorem](../GLOSSARY.md#redundancy-capacity-theorem) [read:
   Eysenbach Thm 4.1, Lemmas 6.1–6.3, 6.5]. This is spec 002 §3.1 with tasks for natures.
   Their caveats: the result is worst-case, and it assumes an idealised learner that
   searches in the space of state distributions [read: Eysenbach §6.3–§6.5].
7. **A solver without the enumeration.** Mohamed & Rezende maximise the Barber–Agakov
   lower bound `H(A) + 𝔼[log q(a|s′, s)]` over a source network and a decoder network. For
   a fixed decoder the best source is `∝ exp(β 𝔼 log q)`, the
   [Blahut–Arimoto](../GLOSSARY.md#blahut-arimoto-algorithm) update with a network in
   place of the posterior table. Checked against exact Blahut–Arimoto on worlds of at most
   400 states, for the shape of the landscape; actions are discrete, horizon 5 [read:
   Mohamed & Rezende §4.1–§4.2, §5.1].

## Where the mirror breaks

- **Who owns the input.** The agent chooses its actions; nature chooses `θ`. Empowerment
  needs no belief about anyone else's choice, so spec 002's foreign-nature question arises
  there only for a foreign downstream task (item 6).
- **Two loops.** Empowerment is computed per state and then climbed. The counterpart of
  the outer loop would be choosing the measurement or model with the highest `C_N`
  [guess]. Klyubin et al. evolve sensors to maximise empowerment [read: Salge §4.5.6].
- **Horizon is not `N`.** A longer horizon adds input dimensions as well as resolution;
  repetitions only scale the Fisher metric. The horizon acts like `D` and `N` together.

## Works

| Work | Our status | What mirrors ours | Mirrors | You read? |
|---|---|---|---|---|
| Salge, Glackin & Polani 2014, "Empowerment: an introduction", arXiv:1310.1863; a chapter of *Guided Self-Organization: Inception* [recalled] ([pdf](../resources/salge_glackin_polani.pdf)) | read §4.4–§4.6 | items 1, 3, 4, 5 | 002 §0, §1.2; two-hats note §2 | ☆ §4.4.2, §4.5.4, §4.6.8–§4.6.9 |
| Jung, Polani & Stone 2011, "Empowerment for continuous agent–environment systems", arXiv:1201.6583; *Adaptive Behavior* 19(1) [recalled] ([pdf](../resources/jung_polani_stone.pdf)) | read §3, parts of §5 | items 2, 3, 4; empowerment as a generalisation of joint controllability and observability [read: abstract] | 002 `p_U` | ☆ §3.2–§3.3 |
| Eysenbach, Salakhutdinov & Levine 2022, "The information geometry of unsupervised reinforcement learning", arXiv:2110.02719; ICLR [recalled] ([pdf](../resources/eysenbach_salakhutdinov_levine.pdf)) | read §4, §6 | item 6 | 002 §3.1 | ★ short, and our theorem in another setting |
| Mohamed & Rezende 2015, "Variational information maximisation for intrinsically motivated reinforcement learning", NeurIPS ([pdf](../resources/mohamed_rezende.pdf)) | read §4, §5.1 | item 7 | 002 OQ-1; budget note §9 | ★ §4 |
| Klyubin, Polani & Nehaniv 2005, "Empowerment: a universal agent-centric measure of control", IEEE CEC 1:128–135 | summary | the definition | — | – |
| Laskin et al. 2021, "URLB: unsupervised reinforcement learning benchmark", NeurIPS Datasets and Benchmarks; arXiv:2110.15191 | summary | skill-discovery methods do worst on downstream tasks; the authors suspect small skill spaces [read: summary of §5, App. G] | 002 transfer question | – |

## Links to other clusters

- **Capacity and rate–distortion.** The same capacity problem and the same algorithm
  ([capacity-rate-distortion.md](capacity-rate-distortion.md)); the amplitude-constrained
  channel is where discreteness comes from.
- **Universal coding.** Item 6 rests on the theorem of
  [universal-coding.md](universal-coding.md).
- **Machta group.** Abbott & Machta optimise atom positions and weights directly, suggest
  variational families as practical stand-ins, and find the bound of Nalisnick & Smyth
  2017 too crude: it favours a prior of two atoms at any noise level [read: A&M App.
  A.2–A.3]. See [machta-sloppy-models.md](machta-sloppy-models.md).
- **Tishby & Polani** ([pdf](../resources/tishby_polani.pdf)): information theory of
  decisions and actions, on the adjacent-areas seed list in [README.md](README.md).

## Open questions

- Does the co-volume criterion of `notes/budget-value-of-information.md` §3.2 answer
  their open question of when the horizon and the noise level matter? [guess] Work on the
  horizon after 2014 has not been searched.
- Can item 7 give `p*` "on the fly"? Parked as
  [Budget-conditioned prior network](../notes/parked_ideas.md#budget-conditioned-prior-network-2026-11-13).
- Is the benchmark result of Laskin et al. the average-case price of a worst-case optimum,
  or only the small skill spaces its authors suspect?
- Efficient coding, MB's second mirror, has no file in this map yet. Wei & Stocker 2015
  and Sims 2016, 2018 are on the seed list in [README.md](README.md).
