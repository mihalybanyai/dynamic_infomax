# What knowing the information budget is worth

*Created 2026-10-24. Working note, not a spec. Claude's draft from a chat thread with MB
(2026-10-08 to 2026-10-24). The framework of §1 is MB's; the computations and the
criterion of §3 are Claude's.*

**Claim.** Knowing the budget `N` (how much data the agent will get) before learning
pays only if something is fixed before the data are in. Against an agent free to mix
priors built for many budgets, it is worth at most a few nats under log-loss (§2). For an
agent that commits to one prior, how strongly the right prior depends on `N` is set by a
co-volume criterion (§3). Against Jeffreys, the automatic prior without the budget, it
pays decisively, in betting terms too (§4). The settings where it is worth nothing are
collected in §5. **To decide:** which open thread to pursue (§7).

## 1. Classifying tasks

A *task* is the likelihood, the set of [natures](../GLOSSARY.md#nature) the agent cannot
rule out, an aggregation over them (worst case, regret, or an average over a family),
the loss, and any constraint on the agent. The constraint is absorbed into the task, so
the reference is the best agent the constraint allows.

- **Task level.** The value of the information `V(T)` is the best value achievable
  knowing `N` minus the best achievable without it. It is never negative, since ignoring
  `N` is an allowed policy. Against a single nature it is zero: the prior matched to that
  nature is optimal either way. So the aggregation over natures is part of the task.
- **Algorithm level.** An algorithm `A` that uses `N` captures
  `e(A) = (value(A) − V_blind*)/V(T)`, where `V_blind*` is the best value without `N`.
  Capture can be negative: the algorithm turns the information into a disadvantage.
  `e(A)` divides by `V(T)`, so it is meaningful only where `V(T)` is large.
- **Classes.** Tasks where `V(T)` is decidedly positive, practically zero, or a swamp in
  between. Algorithms are tested in the first class only.
- **Interesting** means *everyday*: people meet and solve isomorphic tasks, constraint
  included.

Learning is online. An agent that can wait until its data are counted knows `N` when it
decides, and `V(T) = 0`. In the project's Gaussian models `N` and the sample mean `x̄` are
sufficient (`Σ_i‖x_i − y(θ)‖² = N‖x̄ − y(θ)‖² + const`), so waiting costs only `m + 1` stored
numbers. "No waiting" therefore has to be imposed on the representation itself.

## 2. Mixing as the control

Mix the priors `π_{N_k}` built for a grid of budgets, with weights `w_k`. The mixture's
data marginal is at least `w_k·m_{π_{N_k}}` everywhere, so on every nature `q`

$$R_N^q(\pi_{\text{mix}}) \;\le\; R_N^q(\pi_{N_k}) + \log(1/w_k) .$$

At the grid budgets, an agent that does not know `N` loses at most `log(1/w_k)` to one that
does: about 5 nats at `N ≈ 1000` for `N_k = 2^k` and `w_k ∝ 1/k²`. Off the grid the gap
between `π_N` and the nearest grid component adds to this; a finer grid shrinks it at a
log-log cost.

The mixture is cheaper than "every resolution in parallel" suggests. Along a geometric
grid of budgets the [atom](../GLOSSARY.md#atom) count of `p*` grows geometrically (about
`√N` in 1-D, spec 000), so the mixture's size is a constant multiple of its finest
component. What knowing `N` saves is mainly representation: the finest resolution needed
is set by the largest plausible budget.

The bound is specific to log-loss, which is *mixable*: a weighted set of predictions can
be replaced by one prediction that never does much worse than the weighted set
[read: van Erven, Grünwald, Mehta, Reid & Williamson 2015, *JMLR* 16, §2.3]. For decision
losses see `notes/daisy_chain_derivation.md` §7.5. Mixing is kept as the control: an
agent with no practical limit on storage or compute. How specific constraints modulate it
is open (§7).

## 3. Agents that commit to one prior

The agent commits to the `p*` of one budget `M`, `p*_M`, without knowing the true `N`. The
informed agent uses `p*_N`; Jeffreys is `M → ∞`. Scripts and outputs are in
`notes/budget-value-of-information/`.

### 3.1 1-D: too coarse is catastrophic, too fine is cheap

Bounded Gaussian channel, Fisher length 3 at `N = 1`. Extra cumulative log-loss over
`p*_N` in nats, worst case over `θ` (`misbudget_1d.py`):

| `N` \ prior | `p*_1` | `p*_16` | `p*_256` | Jeffreys |
|---|---|---|---|---|
| 1 | 0 | 0.08 | 0.14 | 0.17 |
| 16 | 12.5 | 0 | 0.43 | 0.71 |
| 256 | 267 | 9.0 | 0 | 0.90 |

Too coarse, the posterior settles on the nearest atom and each observation pays the
divergence to it. On a uniform nature this predicts `0.375·N` nats for `p*_1`; the
computation gives `0.366·N` at `N = 256`. Too fine stays under one nat. A committed agent
should err fine, and then the budget is worth under a nat: swamp. Every prior does worse
than `p*_N` in the worst case at budget `N`, as minimaxity requires (all budgets
`1…256`). Blahut–Arimoto is not fully converged at the larger budgets.

### 3.2 High dimension: the criterion

In the reduced square hypercone ([co-volume](../GLOSSARY.md#co-volume) gradient
`√det g ∝ θ_1^{D−1}`), `p*_M` weights a resolvable state `θ` by `exp(C⊥_M(θ))`. Here
`C⊥_M(θ)` is the information the sub-resolution directions still carry at `θ` at budget
`M`[^criterion]. So `p*_M` and `p*_N` differ by the tilt `exp(ΔC⊥(θ))`, with
`ΔC⊥ = C⊥_M − C⊥_N`. On a nature `q`, the predicted difference in mismatch is

$$\log \mathbb{E}_{p^\star_N}\!\big[e^{\Delta C_\perp}\big] \;-\; \mathbb{E}_q\big[\Delta C_\perp\big] .$$

It is large when `ΔC⊥` varies strongly across the resolvable states. That needs three
things: a wide range of plausible budgets, directions that cross resolution within it,
and a coupling (the taper) that makes the crossing detail unequal across states.

### 3.3 Test in the reduced cone

`D = 26`, `L = 50`, `σ = 1`. Excess mismatch of `p*_M` over `p*_N` on the relevant
coordinate in nats, with the §3.2 prediction in brackets (`cone_misbudget.py`):

| nature | `N = 1`, `M = 16` | `N = 16`, `M = 1` |
|---|---|---|
| uniform in `θ_1` | 5.27 [5.63] | −4.82 [−5.43] |
| thin end (`θ_1 < L/5`) | 11.81 [12.13] | −10.82 [−11.93] |

- **Control.** With a constant cross-section the excess is at most 0.04 nats, except a
  1-D locking term of 0.48 (uniform) and 1.10 (thin end) nats at `N = 16`, `M = 1`. Many
  crossing directions with no gradient give no budget dependence beyond 1-D locking.
- **Magnitude.** On the fine side the prediction is within 15% at `D = 10` and `D = 26`.
  On the coarse side, the prediction plus the control's locking term matches:
  `−11.93 + 1.10 = −10.83` against `−10.82` computed (thin end, `D = 26`), and
  `−1.33 + 0.48 = −0.85` against `−0.84` (uniform, `D = 10`).
- **Hidden coordinates.** Their own score adds at most 0.39 nats (`cone_misbudget_full.py`).
- **Sign.** On both natures the *coarser* prior wins at every budget tested: at `N = 16`,
  `p*_1` beats `p*_16` by 4.4 nats on the uniform nature. `p*_N`'s own tilt toward the
  thick end grows with `N`, and natures away from the thick end pay for it.

Limits: the reduced model ignores what the hidden data say about `θ_1`, and the hidden
score assumes `θ_1` known. The tilt part reproduces the 2026-10-08 computation
(`cone_pstar.py`): `p*`'s tip/base weight ratio 0.074 at `D = 26`, against 0.062 predicted.

## 4. Where knowing the budget is definite

- **Worst case over natures.** `p*_N` is minimax at budget `N`, so knowing `N` helps, by
  about the spread of `ΔC⊥` [guess][^criterion].
- **Against Jeffreys, the automatic prior without the budget** (`jeffreys_vs_pstar.py`,
  `D = 26`, excess cumulative log-loss in nats). `p*_N` wins on the uniform nature
  (0.51 against 18.65 at `N = 1`; 5.84 against 20.98 at `N = 16`), on the thin end (2.90
  against 50.08; 14.84 against 59.87) and on the thick end (0.63 against 0.87). Jeffreys
  wins only in its own corner, `θ_1 > 48` (0.18 against 1.12; 0.36 against 0.81).
- **Average over a nature family.** The sign depends on whether nature sits where the
  hidden detail grows. For natures uniform in the relevant coordinate, every `p*_M` tilts
  the wrong way, and the ordering route ([reference prior](../GLOSSARY.md#reference-prior)
  `p_ref`, spec 002 §3.5) does better without any budget. There, `p*` is an algorithm with
  negative capture.

A prior that keeps hidden detail from tilting the relevant coordinate does what `p*_N`
does not (`budget_relative.py`). It equalises regret against an oracle that knows only
the relevant coordinate, so it is flat in `θ_1` at resolution `N`, with `p*`'s conditional
treatment of the hidden directions. At `N = 16`, `D = 26`, its mismatch is 0.01 nats on
the uniform nature (`p*_N`: 5.84), 1.58 on the thin end (14.84) and 1.58 on the thick end
(0.38). In the worst case it costs 20.2 nats, against `p*_N`'s 17.8. This is essentially
the ranked reference prior: the ranking makes it flat, and the budget sets only its
discreteness. The comparison favours it: all three natures are defined in `θ_1`, and the
uniform one is this prior's own world (its 0.01 nats is a self-sampling floor). Spec
002's tilt family, with self-sampling controls marked, is the fair test.

| task | budget range | crossing directions | gradient across states | budget's value (committed agent) |
|---|---|---|---|---|
| 1-D channel | any | none | none | < 1 nat (§3.1) |
| constant cross-section | wide | `D − 1` | none | ≈ 0 (§3.3) |
| square hypercone | wide | `D − 1` at once | ∝ `D − 1` | tens of nats; sign set by nature (§3.3) |
| exp-decay | wide | a few per decade | from curvature | moderate [guess] |
| budget known within ~2× | narrow | few | — | small |

## 5. Grimoire: settings fatal to the budget's usefulness

Started 2026-10-25 from MB's list (entries 1, 2, 5, 6, 10) and completed from this note.
Each entry is a setting in which knowing the budget is worth little or nothing; the last
column says how we know.

[TODO] Come back to these, not now:
- entry 2's exception for humans (sources in §8, unread);
- entry 5, which rests on A&M's abstract only;
- entry 8 for budgets that change the geometry's shape, such as an observation window;
- entry 9's generality, so far shown in two models.

| # | Setting | Why it is fatal | Evidence |
|---|---|---|---|
| | **Another resource does the budget's job** | | |
| 1 | Unconstrained computation and memory, with a mixable loss (log-loss) | Mixing the priors of many budgets costs at most `log(1/w_k)` on every nature | shown, §2 |
| 2 | An ordering is available: the goal is clear and the relevant/irrelevant split is global (non-curved geometry) | An ordered reference prior removes the co-volume bias without a budget; the budget buys only insurance | computed, §4 (`budget_relative.py`); for humans, cheap rankings may exist only along privileged perceptual axes [recalled; sources in §8, unread] |
| 3 | The budget is revealed before it matters: episodic storage, or a compact sufficient statistic (`N` and `x̄` in Gaussian models) | The agent chooses its prior after counting its data | shown, §1 |
| 4 | Nature, or a hyperprior over natures, is known | The matched prior is optimal at every budget | shown, §1 |
| | **Nothing for the budget to act on** | | |
| 5 | Very large budgets: every direction is resolved at every plausible budget | `p*_N` approaches Jeffreys, and one prior serves all budgets | [read: A&M abstract] |
| 6 | No co-volume gradient among the directions that cross resolution within the plausible budget range | The right prior barely changes with the budget | computed, §3.1 (1-D) and §3.3 (constant cross-section) |
| 7 | The budget is known to within a small factor | Few directions cross resolution in the range | computed, §3.1 (neighbouring budgets differ by about a nat) |
| 8 | The decision depends only on relative resolvability, as in allocating a fixed capacity, and the budget is a count of repetitions | Repetitions scale the Fisher metric uniformly (`g_N = N·g`), so the best allocation is the same at every budget | computed, §7 (`capacity_allocation.py`) |
| 9 | Knowledge is never sunk: active learning with persistent knowledge and diminishing returns | The best policy for a short horizon is nearly the start of the best for a long one; a myopic or fixed schedule matches the informed agent | computed in two models, §7 (`active_calibration.py`, `active_investment.py`); generality [guess] |
| | **The budget cannot be used** | | |
| 10 | `p*`, or another useful budget-aware prior, cannot be computed or approximated | No budget-aware prior to deploy | spec 002 OQ-1 (feasibility) |
| | **The evaluation favours the budget-blind prior** | | |
| 11 | Average-case scoring on natures concentrated where the measurement sees most detail | Jeffreys' own corner: it wins there | computed, §4 (`jeffreys_vs_pstar.py`, `θ_1 > 48`) |

The complement is short: the budget is decidedly useful when entries 1–4 fail together,
the agent must build its prior from the likelihood alone, and the comparison is with
Jeffreys (§4). It is also useful wherever a commitment consumes a resource that learning
cannot recover, as in ski rental (§7).

## 6. Everyday candidates

Each case of spec 002's footnote `[^1-everyday]` has a taper; an uncertain budget makes it
a candidate [guess, each]:

- **A glance or a long look at a face down the street.** Facial detail resolves only near,
  and viewing time is the budget. An observer tuned to long looks tilts a glimpse toward
  "near". Whether that helps depends on how far people really are.
- **Integration window and neural gain.** A decoder tuned to long spike-count windows
  tilts short windows toward high gain.
- **The detective and the taster**, with an unknown number of clues or tastes.

## 7. Open threads

- **The full models.** Spec 002 now carries `p*_{N/10}` and `p*_{10N}` (its §2.2, §2.4),
  which measures this in the full hypercone and in exp-decay.
- **Spending the budget: tested, no advantage for learning stakes.** In
  `active_calibration.py` the agent bets each round on the target and chooses between a
  confounded measurement and a calibration. Myopic greedy, which ignores the horizon,
  matches the informed optimum at every `N`. In `active_investment.py` an instrument costs
  `B` rounds without measurement and then removes the confound (a ski-rental structure).
  The best single schedule is within 5% of the informed one at every `N` (three settings).
  The reason appears general [guess]: knowledge is never sunk. What was learned before an
  investment keeps paying during and after it, so the best policy for a short horizon is
  nearly the start of the best for a long one, and then the horizon is worth nothing. In
  ski rental with money, rent paid is gone, and an uninformed agent pays up to twice the
  informed cost [recalled: Karlin, Manasse, McGeoch & Owicki 1994].
- **Capacity: tested, no advantage from repetitions** (`capacity_allocation.py`). `K` units
  are split between atoms along `θ_1` and a shared codebook per hidden direction, with
  neutral mass. The best split is almost the same for every assumed budget, so knowing `N`
  barely changes anything (`D = 2, 26`; `K` from 20 to 400). In the one case where it did
  change the split (`D = 26`, `K = 150`), the informed split was worse on average, because
  the rule chooses by worst case. The reason: repetitions scale the whole Fisher metric
  (`g_N = N·g`), and an allocation depends only on ratios of widths. This retires the
  earlier guess that the value peaks at capacity ≈ `C_N`. A budget that changes the
  geometry's *shape* should matter instead [guess], for example exp-decay's observation
  window: later times inform slow rates disproportionately (`∂y/∂k = −a·t·e^{−kt}`), and
  later measurement times add thin directions [read: Mattingly et al. 2018, exp-decay
  discussion].
- **Priors fixed in advance** (development, evolution, convention), selected by a cue, with
  a terminal one-step bet. Here the mixture hedges less well. Its terminal loss exceeds
  component `k`'s by at most `−log` of `k`'s posterior weight, and that weight is earned on
  the past data, not on the next observation.
- **Decision losses.** Hedging is governed by stochastic mixability, a joint property of
  loss, model and natures [read: van Erven et al. 2015, eq. (8)]. A misspecified agent must
  also choose its update (`notes/daisy_chain_derivation.md` §7.5).
- **Advantage per unit of construction cost**: parked (`notes/parked_ideas.md`).

## 8. To read

[TODO] Read these before any claim rests on them. All are recalled, not opened; the
bibliographic details need checking.

On whether people get rankings cheaply (entry 2's exception; candidates for `empirics/`):

- Garner, W. R. (1974). *The Processing of Information and Structure.* Integral versus
  separable dimensions: some dimensions cannot be attended to separately.
- Shepard, R. N. (1964). Attention and the metric structure of the stimulus space.
  *Journal of Mathematical Psychology* 1. Similarity spaces with and without privileged
  axes.
- Ashby, F. G., Alfonso-Reese, L. A., Turken, A. U. & Waldron, E. M. (1998). A
  neuropsychological theory of multiple systems in category learning. *Psychological
  Review* 105. Axis-aligned boundaries are learned quickly as rules, diagonal ones slowly.
- Ashby, F. G. & Maddox, W. T. (2005). Human category learning. *Annual Review of
  Psychology* 56. Review of the same line.
- Kruschke, J. K. (1992). ALCOVE: an exemplar-based connectionist model of category
  learning. *Psychological Review* 99. Attention weights only along the given axes.
- Smith, L. B. & Kemler, D. G. (1977) [CITATION NEEDED: title and journal]. Young
  children classify by overall similarity before attending to dimensions.
- Ward, T. B. (1983) [CITATION NEEDED: title and journal]. Under time pressure, adults
  fall back to overall similarity.

Also recalled in this note and unread: Krause & Guestrin (2005) on greedy design, and
Karlin, Manasse, McGeoch & Owicki (1994) on ski rental (both §7).

[^criterion]: From the reduced-cone heuristic: given the resolvable state, the hidden
    directions are parallel channels, so `p*`'s weight on a state is `e` to the power of their
    conditional capacity. Checked on `p*`'s own tilt (§3.3) and on the mis-budgeted
    differences (§3.3 table). Settled for general geometries by computing `p*_M` against
    `p*_N` in the full hypercone and in exp-decay (spec 002, `budget_value.png`).
