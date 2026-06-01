# NML, stochastic complexity, and the projected prior, calibrated to budget dependence

> Just-in-time math explainer triggered by `specs/002-foreign-q-prediction.md`
> §2.6, where the **projected-ML prior** `p_proj` is promoted from "control" to
> co-protagonist alongside the infomax prior `p*`. Goal: enough
> NML / minimum-description-length (MDL) machinery to see *why* `p_proj` is a
> principled, **budget-dependent** object — the **pointwise-regret** sibling of the
> **expected-regret** capacity prior of `redundancy-capacity.md` — why both collapse
> to Jeffreys only at infinite budget, and where they part. Not a general MDL theory;
> for that see Rissanen (`resources/rissanen.pdf`) and Grünwald, *The MDL Principle*.
> This is the pointwise-regret companion to `tutorials/math/redundancy-capacity.md`
> (expected regret / capacity), `kelly.md` (belief loss), and `kkt.md` (the optimiser
> behind `p*`).

## What problem are we solving

Spec 002 fields two "uninformative" priors that both claim to be the right thing to
use at finite data: the infomax / capacity prior `p*` and the projected-ML prior
`p_proj`. They look unrelated — one maximises mutual information, the other pushes a
funny data-space distribution through the MLE. The point of this file is that they
are **two solutions of one universal-coding problem under two regret notions**, both
*budget-dependent*, both reducing to Jeffreys at infinite budget; and that the single
property the project cares about — **budget dependence** — is exactly what they
share and Jeffreys lacks. We build NML, its stochastic complexity, the
MLE-pushforward that turns it into a prior, and the side-by-side comparison.

Throughout, the model is a parametric family $\{p(x\mid\theta):\theta\in\Theta\}$,
$\Theta\subset\mathbb R^k$ **compact**, observed with a per-experiment budget — $n$
i.i.d. repetitions, equivalently (for the Gaussian case of spec 002) noise $\sigma$
with $n$ scaling the Fisher information by $n$ (so "budget" = $n$ ≈ $1/\sigma^2$).

## The description-length picture (where the CS intuition fits)

The folk version of MDL is computer-science flavoured: *to model data, find the
shortest program that reproduces it.* That instinct is right and it lands exactly on
the $\log Z$ we are about to build — but it takes one refinement to get there, and
seeing the refinement is what makes "budget dependence" concrete.

**Two-part code (the literal "program + data").** Pick a model $\theta$ — the
"program" — pay to write it down, $L(\theta)$, then pay to write the data given it,
$L(x\mid\theta)=-\log p(x\mid\theta)$ (Shannon code length: likely data cheap,
surprising data dear). The total description length $L(\theta)+L(x\mid\theta)$,
minimised over $\theta$, rewards a program that is at once *simple* (small $L(\theta)$)
and a good *fit* (small $L(x\mid\theta)$). That sum is the original MDL objective and
the formal reading of "compress the generating code and its residual together." It is
**Rissanen's two-part code** — the thing his 1996 paper (`resources/rissanen.pdf`)
then sharpens.

**Where Kolmogorov sits, and why we don't use it.** Push "shortest program" to the
limit — shortest program on a *universal* computer — and $L(x)$ becomes the
Kolmogorov complexity $K(x)$. Two facts matter. (i) Changing the computer changes $K$
only by an additive constant (the invariance theorem): swapping languages costs a
fixed-size *compiler/interpreter*, $O(1)$ — that is the "compiler + code" half of the
folk memory. (ii) $K(x)$ is **uncomputable**. MDL is the computable, practical cousin:
instead of *all* programs on a universal machine, fix a **model class**
$\{p(x\mid\theta)\}$ — a restricted programming language — and ask for the shortest
code length *within that language*. The model class plays the role of the compiler;
what we compute is language-relative description length, not absolute $K$.

**The refinement: one part, not two.** The two-part code is wasteful: you pay
$L(\theta)$ to name a model to some precision, the precision is arbitrary, and once
named the model still mispredicts — there is redundancy between "which model" and
"the residual." Rissanen's move (1996) removes it with a single code whose length is
$$
-\log p_{\rm NML}(x)=\underbrace{-\log \max_\theta p(x\mid\theta)}_{\text{best fit the class can give}}\;+\;\underbrace{\log Z}_{\text{one complexity charge for the whole class}}.
$$
The separate program length $L(\theta)$ is gone; in its place is a **single**
class-level charge $\log Z$, amortised identically across all data (the §2
equalizer). The CS intuition survives intact — *code length = how well the best model
in the class fits + how complex the class is* — with "class complexity" now pinned as
$\log Z$ rather than a hand-chosen $L(\theta)$.

**And that is budget dependence, in CS terms.** As §3 shows,
$\log Z=\frac k2\log\frac n{2\pi}+\log\int\sqrt{\det I}$ is the log of the **number of
programs the language can actually tell apart at this much data**. With little data
many nominally distinct parameter settings compile to indistinguishable behaviour —
the effective vocabulary is small; more data makes more distinctions real and the
vocabulary grows. In a sloppy model the resolvable vocabulary is set by the few stiff
directions, so the description-length budget should be spent only on distinctions the
data can pay for — which is exactly what the priors $p^\star$ / $p_{\rm proj}$ do.
"Find the shortest program" and "weight only what is resolvable at the budget" are
the same instruction.

## 1. Two regrets from one numerator

Fix a single predictor / code $q(x)$ — one distribution over data we must commit to
*before* knowing $\theta$. Score it by **regret** against the best-in-hindsight model
$p(x\mid\hat\theta(x))$, where $\hat\theta(x)=\arg\max_\theta p(x\mid\theta)$ is the
MLE. The same numerator $\max_\theta p(x\mid\theta)$ admits two "worst cases":

- **Pointwise (individual-sequence) regret**, worst case over *data*:
  $$
  \mathrm{reg}_{\rm pw}(q)=\max_{x}\ \log\frac{\max_\theta p(x\mid\theta)}{q(x)}.
  $$
- **Expected (Bayes / redundancy) regret**, worst case over *parameters*:
  $$
  \mathrm{reg}_{\rm exp}(q)=\max_\theta\ \mathbb E_{x\sim p(\cdot\mid\theta)}\log\frac{p(x\mid\theta)}{q(x)}=\max_\theta D_{\mathrm{KL}}\big(p(\cdot\mid\theta)\,\|\,q\big).
  $$

The expected one is the object of `redundancy-capacity.md`: its minimiser is the
Bayes mixture $m_{p^\star}$ under the capacity-achieving prior `p*`, value the
capacity $C$. The pointwise one is this file's object. *Same family, same "fit to the
best model", two ways of refusing to know $\theta$* — and, as we'll see, two
universal codes that nearly coincide.

## 2. NML is the pointwise-minimax code (and why the formula is forced)

Write the **unnormalised** best-fit $\hat p(x)=\max_\theta p(x\mid\theta)$ and
$Z=\int \hat p(x)\,dx$. Define the **normalized maximum likelihood (NML)**
distribution (Shtarkov 1987):
$$
\boxed{\;p_{\rm NML}(x)=\frac{\max_\theta p(x\mid\theta)}{Z},\qquad Z=\int \max_\theta p(x\mid\theta)\,dx.\;}
$$

**Why this exact form is the minimax solution.** For *any* code $q$,
$$
\log\frac{\hat p(x)}{q(x)}=\log Z+\log\frac{p_{\rm NML}(x)}{q(x)}
\quad\Longrightarrow\quad
\mathrm{reg}_{\rm pw}(q)=\log Z+\max_x\log\frac{p_{\rm NML}(x)}{q(x)}.
$$
Both $p_{\rm NML}$ and $q$ are probability densities, so they integrate to the same
$1$; hence $\int (p_{\rm NML}-q)=0$, so unless $q=p_{\rm NML}$ everywhere there is a
point where $p_{\rm NML}>q$, making $\log(p_{\rm NML}/q)>0$ there. Therefore
$\max_x\log(p_{\rm NML}/q)\ge 0$, with equality **iff** $q=p_{\rm NML}$. So
$$
\min_q\ \mathrm{reg}_{\rm pw}(q)=\log Z,\quad\text{attained uniquely at } q=p_{\rm NML},
$$
and at that optimum $\log\frac{\hat p(x)}{p_{\rm NML}(x)}=\log Z$ for **every** $x$.
That last line is the **pointwise equalizer property**: NML spreads its regret
perfectly flat across all data, exactly mirroring how the capacity prior's mixture
equalises redundancy flat across $\theta$ (`redundancy-capacity.md`, equalizer
section). NML is the "centre" of the model family in the worst-case-over-data sense,
as $m_{p^\star}$ is the centre in the worst-case-over-$\theta$ sense.

(Compactness of $\Theta$ — and finiteness of the noise — is what makes $Z<\infty$.
For unbounded models $Z$ diverges, NML is undefined, and so is capacity; both need a
budget to be finite. This is the well-known NML divergence problem.)

## 3. Stochastic complexity $\log Z$, term by term

The minimax regret $\log Z$ is Rissanen's (1996) **stochastic / parametric
complexity** — the irreducible price of not knowing $\theta$. Under a CLT on the MLE,
its asymptotic form (Rissanen 1996, the central result of `resources/rissanen.pdf`)
is
$$
\boxed{\;\log Z_n=\underbrace{\frac{k}{2}\log\frac{n}{2\pi}}_{\text{budget / resolution}}+\underbrace{\log\!\int_\Theta\!\sqrt{\det I(\theta)}\,d\theta}_{\text{shape / geometric complexity}}+o(1).\;}
$$

**Where it comes from.** $Z_n=\int p(x^n\mid\hat\theta(x^n))\,dx^n$. Re-index the data
integral by *which* MLE value the data produce: near a value $\theta$, the
log-likelihood is locally quadratic with curvature the Fisher information,
$p(x^n\mid\theta')\approx p(x^n\mid\hat\theta)\exp\!\big(-\tfrac n2(\theta'-\hat\theta)^\top I(\hat\theta)(\theta'-\hat\theta)\big)$,
so the "amount of data mapping to a $\theta$-cell of size $d\theta$" carries the
Gaussian-integral Jacobian $\sqrt{\det\!\big(nI(\theta)/2\pi\big)}$. Integrating over
$\Theta$,
$$
Z_n=\Big(\tfrac{n}{2\pi}\Big)^{k/2}\!\int_\Theta\sqrt{\det I(\theta)}\,d\theta\,\big(1+o(1)\big),
$$
which is the boxed log. Reading the two terms — this is the whole payoff:

- $\frac{k}{2}\log\frac{n}{2\pi}$ is $k$ parameters times $\tfrac12\log\frac{n}{2\pi}$
  each: each parameter is resolvable to precision $\sim 1/\sqrt n$, i.e. to
  $\sim\sqrt{n/2\pi}$ distinguishable values, so there are $\sim(n/2\pi)^{k/2}$
  distinguishable models. **This is the budget term — it grows with the data.**
- $\log\int\sqrt{\det I}\,d\theta$ is the log of the **Fisher (Jeffreys) volume** =
  the number of distinguishable distributions at unit resolution = Balasubramanian's
  geometric complexity. **This is the shape term — budget-free.**

And here is the bridge to Jeffreys: $\int\sqrt{\det I}\,d\theta$ is precisely the
*normaliser* of the Jeffreys prior $p_J(\theta)=\sqrt{\det I(\theta)}/\!\int\sqrt{\det I}$.
The shape term of the NML complexity **is** the Jeffreys volume.

## 4. From a code over data to a prior over parameters: $p_{\rm proj}$

NML lives over data $x$, not over $\theta$. To get a *prior*, push it through the MLE
map — i.e. take the law of $\hat\theta(x)$ when $x\sim p_{\rm NML}$:
$$
\boxed{\;p_{\rm proj}(\theta)=\int p_{\rm NML}(x)\,\delta\big(\theta-\hat\theta(x)\big)\,dx.\;}
$$
This is A&M's "projected maximum likelihood" prior / Quinn's "adaptive
slab-and-spike".

**Why it is Jeffreys at infinite budget.** By the same Laplace weighting as §3, the
density of MLE values is $\propto\sqrt{\det\!\big(nI(\theta)/2\pi\big)}\propto\sqrt{\det I(\theta)}$,
so
$$
p_{\rm proj}(\theta)\ \xrightarrow{\ n\to\infty\ }\ \frac{\sqrt{\det I(\theta)}}{\int\sqrt{\det I}}=p_J(\theta).
$$
So `p_proj` $\to$ Jeffreys as the budget grows — **the same limit `p*` has**
(`redundancy-capacity.md`: $p^\star\to p_J$ as $n\to\infty$). The interesting,
budget-dependent behaviour is all in the finite-$n$ corrections.

**The finite-budget picture (Gaussian, spec 002's case).** With
$p(x\mid\theta)=\mathcal N(y(\theta),\sigma^2 I_m)$,
$$
\max_\theta p(x\mid\theta)=(2\pi\sigma^2)^{-m/2}\exp\!\Big(-\frac{d(x,\mathcal Y)^2}{2\sigma^2}\Big),\qquad d(x,\mathcal Y)=\min_\theta\|x-y(\theta)\|,
$$
so $p_{\rm NML}(x)\propto e^{-d(x,\mathcal Y)^2/2\sigma^2}$ is a **tube of width
$\sigma$ around the prediction manifold $\mathcal Y$** (uniform along $\mathcal Y$,
Gaussian transverse), and $\hat\theta(x)$ is the nearest point of $\mathcal Y$.
Therefore $p_{\rm proj}$ is the law of the *nearest-point projection of that
$\sigma$-tube*:

- where $\mathcal Y$ is locally flat (interior), projection is uniform;
- at a **convex boundary / vertex**, the entire exterior halo of the tube projects
  *onto the boundary*, piling extra weight there — an amount set by the exterior
  solid angle times $\sigma$.

So `p_proj` adapts to budget through the tube width $\sigma$: large $\sigma$ (little
data) $\Rightarrow$ fat halo $\Rightarrow$ weight collapses onto edges (simpler,
lower-dimensional models); small $\sigma$ $\Rightarrow$ the tube hugs $\mathcal Y$
$\Rightarrow$ Jeffreys. This is the same edge-at-large-$\sigma$, bulk-at-small-$\sigma$
story `p*` shows — reached by a different mechanism.

## 5. The two budget-dependent priors, side by side

| | capacity / infomax `p*` | NML / MDL `p_proj` |
|---|---|---|
| solves | $\min_q\max_\theta\,\mathbb E_{x\mid\theta}\log\frac{p}{q}$ (**expected** regret) | $\min_q\max_x\log\frac{\max_\theta p}{q}$ (**pointwise** regret) |
| optimum value | capacity $C$ | stochastic complexity $\log Z$ |
| equalizes | redundancy across $\theta$ | regret across $x$ |
| the object | a **prior** (argmax of $I(\Theta;X)$), discrete, $\sim\sqrt n$ atoms | a **code over data** ($p_{\rm NML}$), made a prior via the MLE |
| budget enters via | atom count / resolution $\sim\sqrt n$ | halo width $\sigma$ |
| $n\to\infty$ limit | Jeffreys | Jeffreys |

**Why they coincide here.** Two reasons, and they are the heart of the matter.

1. *Asymptotically.* Both minimax values are the **same stochastic complexity**
   $\frac k2\log\frac{n}{2\pi}+\log\int\sqrt{\det I}+o(1)$ — capacity via Clarke–Barron
   (`redundancy-capacity.md`), regret via Rissanen — sharing the budget term and the
   shape term. (They can differ at $O(1)$: the worst-case-over-data NML pays a touch
   more than the average-case redundancy, by a constant $\sim\!k/2$ nats — the price
   of pointwise vs expected — but this is a vanishing *rate* and does not change the
   prior limit.) Both shape terms are the Jeffreys volume, so both priors converge to
   Jeffreys.
2. *In hyperribbon geometry at finite budget.* The manifold has a few stiff
   directions and many exponentially-thin sloppy ones; resolution-adaptation then has
   essentially **one** sensible answer — weight the few resolvable directions, collapse
   the sloppy ones onto edges — and both universal codes find it. Their information
   scores nearly agree (Quinn et al. Fig. 12: `p_proj` tracks `p*`, far above
   Jeffreys).

**The reading the project cares about.** Strip the two constructions to their
content: *a good uninformative prior is the resolution map of the experiment at its
budget* — it weights $\theta$ by what the data, at that $n$/$\sigma$, can tell apart.
NML and capacity are two routes to that map. **Jeffreys is the $n\to\infty$ (shape
term only) limit of both, and its budget-independence is precisely why it fails when
the budget is finite and the model is sloppy.** Budget dependence, not discreteness,
is the shared principle; `p*`'s discreteness is one route's incidental signature, not
the principle itself.

## 6. What each one assumes about the world — and where they part

§5 said *how* they coincide; this is *why* they differ, which turns out to be a
single fork with everything hanging off it. Both are **minimax / robust** objects —
neither is the matched, average-case prior (that is `q̄`). They differ only in the
**axis of the worst case**: `p*` takes the worst case over the **parameter** (data
*averaged* given $\theta$); NML over the **data sequence** itself (no expectation, no
generating assumption). Two foundational commitments fall out:

- **Well-specified vs individual-sequence.** `p*` lives in the stochastic world —
  there *is* a true $\theta$ and honest data $x\sim p(\cdot\mid\theta)$, averaged
  over. NML assumes *nothing* about where the data came from — it competes with the
  best model in hindsight on whatever sequence arrives, so it is
  **misspecification-robust by construction**.
- **Realist/estimation vs instrumentalist/coding.** `p*` reads the model as a model
  *of* something: there is a parameter to identify, and infomax maximises the bits the
  experiment transmits *about* it. NML reads the model class as a *language*, not a
  truth (Rissanen denied that any "true model" exists); the goal is to *describe /
  predict* the data with the shortest code, truth not assumed. In a slogan: `p*` asks
  *"which hypothesis is true, and which truth is hardest?"*; NML asks *"how well can I
  describe the data, and which data is hardest to describe?"*

**The non-asymptotic crux.** This is also *why* they agree as $n\to\infty$ yet differ
at finite budget. By the CLT, typical data from $\theta$ concentrates where $\theta$
predicts, so worst-case-over-data $\approx$ worst-case-over-typical-data $\approx$
worst-case-over-$\theta$ — the two close to the same value. They diverge only on
**atypical data**: sequences far from *any* $\theta$'s typical set — in the Gaussian
picture, the $\sigma$-halo *off* the manifold. `p*` (averaging over data given
$\theta$) never sees that region; NML (worst case over every $x$) must insure against
it. **The entire non-asymptotic gap is the large-deviations / atypical-data
contribution, which shrinks relative to the budget term as $n\to\infty$.** That is
the mechanism behind §4: at finite budget NML/`p_proj` over-weights the convex
boundaries where atypical data projects, while `p*` weights by *expected*
distinguishability (Fisher length) and can be lumpy — right only on average. The
contrastive corners of spec 002 §2.6 are this fork's geometric signature; mapping
them (§2.6 / §4.3) is what isolates whatever the capacity object buys over the cheap
MDL sibling.

**When to prefer which.** Reach for `p*` when you trust the model to be
well-specified and you care about *identifying the parameter* (or your loss really is
worst-case-over-hypotheses): *"a truth is in here, nature may pick the nastiest one,
but the data is honest."* Reach for NML/`p_proj` when you *distrust* the
specification and care about *prediction on whatever data arrives*: *"models are
languages, not truths; just never code much worse than the best one in hindsight."*

**The reflexive point for spec 002 (a hypothesis, not a fact).** Its foreign `q` is
exactly **prior-misspecification** ($\theta\sim q\neq p^\star$) — the regime NML's
worldview is built for — so one might expect `p_proj` to transfer to a foreign `q`
more gracefully. The honest counter: once NML is pushed to a prior and Bayes-scored,
that robustness is just "$m_{p_{\rm proj}}$ spreads to cover atypical data (the
halo)" — the *same* worst-case insurance as `p*`'s, on a different axis, and equally
wasteable on a benign interior `q`. So the principle only says *where to look*
(`p_proj` more foreign-`q`-robust where `q` produces boundary/atypical predictions;
`p*` better-tuned for typical-interior `q`); the §2.4/§4.3 sweep adjudicates.

**Algorithmic aside (the axis flips the cost, too).** `p_proj` is
*simulate-don't-optimise* — sample the $\sigma$-tube, project each draw to its MLE; no
global search — so it scales in $d$, which is why A&M/Quinn reach for it. `p*` is a
*flat, ill-conditioned global solve* for a discrete measure (the gradient of
$I(\Theta;X)$ is tiny near the optimum, where the atoms settle). Neither is free:
`p_proj` pays a per-sample MLE projection and needs $Z<\infty$; `p*` pays the solve.
The clean triangulation: **`q̄` is the non-paranoid (matched) prior; `p*` is paranoid
about which hypothesis is true; NML is paranoid about which data arrive** — same
budget dependence, three stances toward the unknown.

## Connections worth noting

- **Two duals, two tutorials.** `redundancy-capacity.md` is the expected-regret face
  (capacity, `p*`); this file is the pointwise-regret face (NML, `p_proj`). `kkt.md`
  is the optimiser that finds `p*`. `kelly.md` is the *belief* loss, a different game
  again (note the two-hat split).
- **MDL model selection.** $\log Z$ is the NML stochastic-complexity penalty used to
  *choose a model* before seeing data — it depends only on the experiment's
  resolution, not its outcome (Quinn). $=$ geometric complexity (Balasubramanian) $=$
  "number of distinguishable distributions" (note §6). The model-selection sibling of
  the capacity story.
- **NML is not a Bayes mixture.** No prior makes $m_\pi=p_{\rm NML}$ exactly at finite
  $n$; the two universal codes agree only asymptotically. `p_proj` is the
  MLE-*pushforward* of $p_{\rm NML}$, a prior — not $p_{\rm NML}$ itself, and not a
  mixture of the family.

## Why this is the right tool, in one sentence

NML / stochastic complexity is the pointwise-regret face of the *same*
budget-dependent universal-coding problem whose expected-regret face is capacity, the
projected-ML prior is NML read back onto parameters through the MLE, and both reduce
to Jeffreys only at infinite budget — which is exactly why the project reads them as
two takes on **budget dependence** rather than one approximating the other.

## What a red-team finding in this region might be flagging

1. **Code-vs-prior confusion.** $p_{\rm NML}$ is over *data*; `p_proj` is its
   pushforward over *parameters*. A claim that "`p_proj` is NML" or that you can score
   `p_proj` the way you score a code is conflating the two.
2. **"Approximation" framing.** Treating `p_proj` as a numerical approximation of
   `p*` misses that it is the *pointwise-regret* optimum in its own right; they are
   siblings that coincide asymptotically, not original-and-approximation.
3. **Forgetting the budget.** $Z=\infty$ for non-compact $\Theta$ — NML undefined.
   Any "uninformative" claim that ignores the budget (Jeffreys) has silently taken the
   $n\to\infty$ shape term and dropped the resolution term.
4. **Wrong regret.** Pointwise = $\max_x$; expected = $\max_\theta\mathbb E_{x\mid\theta}$.
   Swapping them turns NML into capacity. A "minimax" claim must say *over what*.
5. **Constant chasing.** The $O(1)$ gap between $\log Z$ ($2\pi$) and the expected
   minimax redundancy ($\sim\! 2\pi e$) is real but rate-vanishing; treating it as the
   reason `p*` and `p_proj` differ as *priors* over-reads it (the prior difference is
   the finite-$n$ edge/halo geometry of §4–§6, not the constant).
6. **Two-part vs refined, and Kolmogorov.** "MDL = code the model, then the data" is
   the *two-part* code; $\log Z$ is the *refined* one-part complexity that removes its
   redundancy (the description-length section above). And MDL is **not** Kolmogorov
   complexity: $K(x)$ is universal-machine / model-class-free and uncomputable,
   whereas $\log Z$ is relative to the chosen class $\{p(x\mid\theta)\}$ and
   computable. A claim that invokes "the shortest program" without naming the model
   class has slipped from MDL to $K$.

## References

External:

- **Shtarkov, Yu. M. (1987).** Universal sequential coding of single messages.
  *Problems of Information Transmission* 23(3). The NML distribution and its
  minimax-pointwise-regret optimality. *(Exact pagination of the Russian original vs
  English translation not independently verified here — flag before quoting page
  numbers.)*
- **Rissanen, J. (1996).** Fisher information and stochastic complexity. *IEEE Trans.
  Inf. Theory* 42(1), 40–47. [doi:10.1109/18.481776](https://doi.org/10.1109/18.481776);
  copy in `resources/rissanen.pdf`. The $\log Z=\frac k2\log\frac n{2\pi}+\log\int\sqrt{\det I}$
  result and the ML-code derivation; verified against the in-repo PDF.
- **Grünwald, P. D. (2007).** *The Minimum Description Length Principle.* MIT Press
  (ISBN 978-0-262-07281-6). Book-length NML / stochastic-complexity treatment; the
  asymptotic equivalence of MDL, Bayes/Jeffreys, and capacity codes.
- For Clarke–Barron (asymptotic minimax redundancy $=$ same complexity, $p^\star\to$
  Jeffreys) and Balasubramanian (geometric complexity), see the References of
  `redundancy-capacity.md` rather than duplicating.

In-repo:

- `resources/rissanen.pdf` — the source for §3.
- `tutorials/math/redundancy-capacity.md` — the expected-regret / capacity sibling
  (compensation identity, equalizer, $p^\star$ discreteness, the $C_n$ expansion).
- `tutorials/math/kkt.md` (BA optimiser for `p*`), `tutorials/math/kelly.md` (belief
  loss).
- `specs/002-foreign-q-prediction.md` §2.6 (the co-protagonist decision this file
  supports), §4 (the model family and the two priors), §2.4/§4.3 (the contrastive
  sweep).
- `notes/prediction_objective_for_priors.md`, `notes/infomax_two_hats_and_directions.md`.

## Provenance

Triggered by the §2.6 decision in `specs/002-foreign-q-prediction.md` to treat the
projected-ML prior as a budget-dependent co-protagonist of `p*`, and by the request
to pin down the NML/MDL principle behind it and its relation to infomax. Calibrated
to that purpose — the pointwise-regret dual, the stochastic-complexity formula and
its budget/shape split, the MLE-pushforward, and the asymptotic-and-hyperribbon
coincidence with capacity — deliberately *not* a general MDL course. If a later spec
needs the full NML model-selection apparatus or the rate–distortion encoder dual,
expand into siblings rather than growing this file past its budget-dependence scope.
The Rissanen reference here is grounded in `resources/rissanen.pdf`; the Shtarkov
pagination remains unverified (so flagged), and the same caveat applies to the
Shtarkov entry in `specs/002` §8.
