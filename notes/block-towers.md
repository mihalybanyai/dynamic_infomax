# Block towers: a candidate model family and experiment

> **Status: exploratory note, not a spec. Parked until spec 002 is finished** (MB,
> 2026-11-10). From a chat on 2026-11-10 about Battaglia, Hamrick & Tenenbaum (2013), in
> the session that rewrote the natures of spec 002. It takes up the "reduced models of
> everyday situations" candidate of [parked ideas](parked_ideas.md), *Benchmark natures*.
> The script is untrusted. Drafted by Claude; not yet reviewed by MB.

**Claim.** Judging whether a tower of blocks will fall gives a model family we did not
design, a [nature](../GLOSSARY.md#nature) we control (the distribution of towers shown),
and human data. A first check of its geometry is mixed: which direction is stiff varies
from tower to tower, as hoped, but at the noise level fitted to people there is no
hierarchy of widths. **MB decides, after spec 002:** whether the mass-learning version
([§4](#4-where-a-prior-would-matter)) becomes spec 003, or the idea stays a lead in
`empirics/`.

## 1. The source

Battaglia, Hamrick & Tenenbaum (2013), "Simulation as an engine of physical scene
understanding", *PNAS* 110(45), with its SI appendix. The PDFs are not in `resources/`.

- People's judgments of towers of ten blocks (will it fall, in which direction) are fitted
  by an "intuitive physics engine": a rigid-body simulator run on a few noisy copies of the
  scene [read: main text, model section].
- It has three inputs. `σ` is the observer's uncertainty about each block's position,
  fitted at 0.2 of a block's short side; `φ` is the size of possible unseen forces; `μ` is
  relative mass [read: main text].
- `σ` and `φ` "influenced the model's predictions in similar ways" [read: main text; SI
  Fig. S3], and people's judgments fit three to seven simulation runs [read: main text].
- Simpler physics (convex hulls, uniform mass, coarse time steps, tower height as a
  heuristic) is discussed in the SI, not tested as the model. In one case tower height
  predicts people better than the model does [read: SI, *Approximations*].

## 2. Two models on one parameter space

The parameters are the same for both: block positions, and masses where they vary.

- **The static model** answers only whether the tower starts to fall. For a single column
  it is exact and closed-form: at every interface, the centre of mass of everything above
  must lie inside the contact. Towers in which a block rests on several others need a
  feasibility problem for the contact forces [recalled: statics of rigid-block
  assemblies]. Its count of fallen blocks is the number above the lowest failing
  interface; collisions and changes of load after the fall starts are left out.
- **The engine** answers everything, by simulation. Its
  [Fisher metric](../GLOSSARY.md#fisher-information-metric) can be estimated without
  differentiating the simulator: with Gaussian noise `ε` of size `σ` on the inputs, the
  gradient of an outcome's probability is the average of `ε/σ` over the runs that gave
  that outcome. Not run; it needs a physics-engine dependency.

Both are budgeted by `σ`, and exact physics is the engine at `σ → 0`. So "full against
simplified" has two parts here: more noise (a budget), and a narrower question (a reduced
model).

## 3. First check: the static tower's Fisher spectrum

`notes/block-towers/static_tower_fisher.py`, output in `static_tower_fisher.out`. A
single column of ten unit-width blocks of equal mass, in 2-D. Each block is offset from
the one below by a uniform draw in ±0.25 block widths; 88% of such towers stand. The
observer sees each block's centre with noise `σ` and reports the outcome of the perceived
tower: it stands, or the lowest failing interface and its side (19 outcomes). The table
gives the local Fisher spectrum of that outcome with respect to the nine free directions
of the true tower, as medians over 60 towers.

| `σ` | Median chance of "falls" | Spread of the nine eigenvalues, in decades | Stiffest directions of two towers, mean \|cos\| (random: 0.27) |
|---|---|---|---|
| 0.05 | 0.00 | 2.9 across the first three; the rest are below the Monte-Carlo floor | 0.21 |
| 0.1 | 0.09 | 3.0 across eight; the ninth is below the floor | 0.16 |
| 0.2 (fitted to people) | 0.59 | 1.3 | 0.36 |
| 0.4 | 0.97 | 1.9 | 0.99 |

- **The stiff direction depends on the tower** for `σ ≤ 0.2`: two towers' stiffest
  directions are no more aligned than random ones. That is like exp-decay and unlike the
  hypercone (spec 002 §1.2). At `σ = 0.4` one direction is shared by all towers.
- **A hierarchy of widths appears only at fine budgets.** At `σ ≤ 0.1` the eigenvalues
  span three decades, because most interfaces are far from critical and their directions
  are saturated. At the value fitted to people all nine lie within 1.3 decades: every
  interface is comparably near critical. The guess that this family is a
  [hyperribbon](../GLOSSARY.md#hyperribbon) at the human budget is not supported in this
  ensemble.
- **One judgment resolves almost nothing.** It carries at most `log 19 = 2.9` nats. The
  largest median eigenvalue is 23 (at `σ = 0.1`), so a step of 0.25 block widths along the
  stiffest direction moves the prediction by 1.2
  [Fisher lengths](../GLOSSARY.md#fisher-length).
- So the geometry changes type with the budget: one shared direction, then nine comparable
  ones, then a hierarchy.

Limits: local spectra, not the manifold's global widths; one ensemble of towers; a single
column in 2-D; statics only; eigenvalues below about ten times the Monte-Carlo floor
(printed per `σ`) are not measured.

## 4. Where a prior would matter

As described, the budget is perceptual noise on block positions. That channel has the same
Fisher metric everywhere, so [Jeffreys](../GLOSSARY.md#jeffreys-prior) is uniform on it,
there is no [co-volume](../GLOSSARY.md#co-volume) gradient, and the contrast of spec 002
has nothing to act on. The sloppiness of §3 is in the map from positions to outcome, which
is not the channel the observer learns through. Two ways to give a prior work to do, both
`[guess]`:

- **Learn hidden properties from outcomes.** This has spec 002's structure:

  | Spec 002 | Mass-learning towers |
  |---|---|
  | parameter `θ` | block masses or frictions, which cannot be seen |
  | observation | the outcome of one tower built from those blocks |
  | budget `N` | the number of towers watched |
  | held-out target | the outcome of a new tower |
  | nature `q` | the distribution of block properties, set by the experimenter |
  | model geometry | computed per set of towers, statically or with the engine |

- **Keep perception and change the object:** ask which three to seven posterior samples
  predict the outcome best. That concerns discreteness under a budget, but of a posterior,
  not a prior.

## 5. Human budgets

Limiting viewing time, or how far a tower can be turned, would be the manipulation.
Whether the fitted `σ` moves with either is unknown. The paper found no effect of practice
or feedback, which is a different manipulation [read: main text, Exp. 1].

## 6. Next steps, in order

None before spec 002 is finished.

1. The spread of `log det g` across towers, from the same script: is there a co-volume
   gradient at all?
2. The Fisher geometry of the mass-learning version in the static toy. A hierarchy with a
   co-volume gradient at a realistic number of towers would make it a spec; without one
   it is an `empirics/` lead.
3. The engine's geometry by the estimator of §2, and whether its stiff directions at
   `σ = 0.2` span the static margins (then the dynamics is sloppy at the human budget).
4. Only then spec 003, or a file in `empirics/`.
