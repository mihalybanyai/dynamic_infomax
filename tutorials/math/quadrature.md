# Quadrature, calibrated to spec 002's integrals

> Just-in-time math explainer, requested during the implementation of
> `specs/002-foreign-q-prediction.md` (§4.2, §4.4). Goal: enough numerical integration to
> read the implementation's design decisions (DD-K1, DD-Q1–Q3 in
> `docs/002-foreign-q-prediction/README.md`), and to judge a claim that some number is
> accurate to `1e-3` nats. Not a numerical-analysis course; for that see Davis &
> Rabinowitz, *Methods of Numerical Integration*, and Owen, *Monte Carlo Theory, Methods
> and Examples* (ch. 15–17 on quasi-Monte Carlo) [recalled].

## What problem are we solving

Almost every number in spec 002 is an integral with no closed form:

- a prior's [Bayes mixture](../../GLOSSARY.md#bayes-mixture), integrated over parameters:
  $m_\pi(x) = \int p(x\mid\theta)\,\pi(\theta)\,d\theta$;
- the normaliser of Jeffreys, also over parameters:
  $V_g = \int_\Theta \sqrt{\det g(\theta)}\,d\theta$;
- the per-state divergence, integrated over data:
  $f(\theta) = D_{\mathrm{KL}}\big(p(\cdot\mid\theta)\,\|\,m_\pi\big) = \mathbb E_{x\mid\theta}\big[\log p(x\mid\theta) - \log m_\pi(x)\big]$.

The scores themselves, `R_N` and `r_N`, are deliberately Monte Carlo averages over nature's
draws (§4.4). Inside each draw, though, sit the integrals above. Every one of them must be
accurate to a fraction of the differences being reported, which are often hundredths of
a nat.

**Quadrature** approximates an integral by a weighted sum at chosen nodes,
$\int f \approx \sum_k w_k f(x_k)$. Monte Carlo is the special case with random nodes
and equal weights. The whole craft is in choosing nodes and weights to suit the integrand.

## The essentials

**Error rates.** The cost of an extra digit is what separates the methods:

| Method | Error with `n` nodes | Wants |
|---|---|---|
| Monte Carlo | $\propto n^{-1/2}$, any dimension | nothing: works for rough integrands |
| quasi-Monte Carlo (Sobol) | about $n^{-1}$, up to logs | a smooth integrand of low effective dimension |
| midpoint / trapezoid, cell width `h` | $\propto h^2$ | smooth integrand |
| Gauss–Legendre, `q` nodes per cell | $\propto h^{2q}$ | smooth integrand |

So Monte Carlo needs 100× more nodes per extra digit, quasi-Monte Carlo 10×, and a
Gauss rule only a few more nodes per cell [recalled]. The cheap rules are cheap only
when the integrand is smooth on the scale of a cell.

**Gauss rules.** With `q` nodes, a Gauss–Legendre rule integrates every polynomial of
degree up to `2q - 1` exactly on an interval [recalled]. A *composite* rule cuts the range
into cells and applies a small Gauss rule in each, which keeps working when the integrand
is only locally polynomial-like. **Gauss–Hermite** is the same idea for
$\int e^{-z^2/2} f(z)\,dz$, i.e. Gaussian expectations $\mathbb E[f(Z)]$, $Z\sim\mathcal N(0,1)$:
`q` nodes are exact for polynomials of degree up to `2q - 1` [recalled]. Gaussian noise
makes this the natural rule for anything of the form $\mathbb E_{x\mid\theta}[\cdot]$.

**The resolution rule: cells smaller than the noise.** In our models the integrand
$p(x\mid\theta) = \mathcal N(x; y(\theta), s^2)$ changes appreciably when the prediction
$y(\theta)$ moves by one noise unit `s`, that is, by one
[Fisher length](../../GLOSSARY.md#fisher-length). So grids are laid out in Fisher length,
not in `theta`. Uniform cells in `theta` waste nodes where the model is sloppy and
under-resolve where it is stiff.

**The curse of dimension.** A product of `n` nodes per axis costs $n^d$. Grids are
therefore affordable only at small `D` (§4.4: "quadrature over `Theta` at small `D`").
Beyond that the options are Monte Carlo, or finding a few directions that matter and
using a grid only on those.

**What breaks a rule.** Smoothness assumptions fail at **edges** (a density truncated at
a boundary: the midpoint rule's error there is $O(h^2)$ even when the interior is far more
accurate), at **kinks** (a $|\cdot|$ inside the integrand), at **singularities** (an
integrable spike or logarithm), and wherever the cells are **coarser than the noise**.
The cure is the same in every case: move the difficulty into the weights or a change of
variables, so that what the rule sees is smooth.

**The check that matters: refinement.** Halve the cells and recompute. The change
estimates the error of the coarser grid. A reference grid is only a reference if it has
passed this check; see the last section.

## How spec 002 uses it

**1. Continuous priors in exp-decay (DD-Q1).** For `p_J`, `p_U`, `p_LN` and `p_ref`, the
mixture $m_\pi(x)$ is a weighted sum over grid nodes in `xi`. Each axis is cut into cells
of equal *arc length*. The diagonal of the metric is the same function of `xi_mu` on every
axis, so one profile serves all axes, and every cell is 0.3 noise units long. The cells
hold two Gauss–Legendre nodes per axis at `D <= 2`, one beyond. The parameter set is
ordered (`xi_1 <= ... <= xi_D`), and that is handled by folding: for a cell whose indices
tie on `g` coordinates,

$$
\int_{\text{cell}\,\cap\,\text{ordered}} f \;=\; \frac{1}{\prod g!}\int_{\text{cell}} f(\operatorname{sort}\xi)\,d\xi ,
$$

because sorting maps the full cell onto its ordered part `prod g!` to one. A symmetric
integrand stays smooth under folding. Jeffreys' does not ($\sqrt{\det g}\propto|\xi_2-\xi_1|$
near the diagonal), but there it is small, so the kink costs little. The Jeffreys
normaliser agrees with an independent `scipy.integrate.dblquad` to `1e-4` (T4).

**2. A spiky density: nodes in the CDF (DD-Q2).** `p_LN`'s density in `xi` blows up
(integrably) as `xi -> 0`. Gauss–Legendre in `xi` misjudges the first cell's mass by
about 20%, and the error in $\log m_\pi$ was `1e-2` at cells of 0.4 noise units. The fix is a change of variables:
for a prior that is i.i.d. per rate before ordering, put the nodes at Gauss–Legendre
points *of each rate's CDF*, $\xi = H^{-1}\big(H(a) + (H(b)-H(a))u_k\big)$. Every cell then
carries its exact mass $H(b)-H(a)$, and the spike is absorbed into the node positions.
The error fell to `1.2e-3` at the same cells and `9e-5` at cells of 0.2.

**3. The cone: closed form where possible.** A cone prior that is uniform on the
cross-section integrates each cross-section coordinate exactly:
$\int_0^1 \mathcal N(x_\mu; a\theta, s^2)\,d\theta = [\Phi((a-x_\mu)/s) - \Phi(-x_\mu/s)]/a$.
Only the relevant coordinate `theta_1` needs a rule (composite Gauss–Legendre, cells of
half a noise unit, four nodes each). That is how `D_max = 26` stays cheap: one numerical
dimension, 25 analytic ones. It matches brute-force Monte Carlo over `10^6` draws
within its error (T7(a), T14(g)).

**4. The per-state divergence: Gauss–Hermite in a few directions (DD-K1).** This is the
integral the `p*` solver evaluates thousands of times. Write the data as
$x = y(\theta) + s z$ and the atoms' offsets in noise units, $c_j = (y_j - y(\theta))/s$. Then

$$
f(\theta) = \mathbb E_{z\sim\mathcal N(0,\mathbb 1_m)}\Big[-\log \sum_j w_j\, e^{-|c_j|^2/2 + z\cdot c_j}\Big].
$$

The integrand depends on the 26-dimensional `z` only through its projections on the
`c_j`. On a sloppy model those span effectively two or three dimensions (relative singular
values 1, 0.2–0.7, 0.05–0.1, then below 0.015 at the cheap cell). So the expectation
splits:

- **leading 1–3 directions:** a Gauss–Hermite tensor rule (48, 20² or 10³ nodes);
- **residual directions:** expand to second order. The second derivative of
  $-\log\sum e^{(\cdot)}$ along a direction is minus the variance of the `c_j` components
  under the posterior over atoms, which gives the term $-\tfrac12\sum_r \mathrm{Var}(c_r)$.

Against the mean of two 32 768-point Sobol estimates, the error is at most `3.4e-4` nats
over 406 states. Sobol at 1024 points was off by `2e-3`, and plain Monte Carlo at the
spec's 64 draws would be off by several hundredths [guess: from the per-draw spread].
Neither supports T3's `1e-2` equalizer check across thousands of states. With one-dimensional data the rule is plain Gauss–Hermite (96
nodes), accurate to rounding.

**5. Removing a logarithm (DD-R1).** The reference prior's exponent integrates
$\tfrac12\log(\text{Schur complement})$ along a nuisance coordinate `t`, and the Schur
complement vanishes like $(\psi - t)^2$ where two rates coincide. Substituting
$t = \psi - (\psi - \text{lo})\,v^2$ turns $\log|\psi - t|$ into $2\log v$ times a factor
`v` from $dt$. The integrand $v\log v$ is bounded, and 64 Gauss–Legendre nodes then match
`scipy.integrate.quad` to `5e-3` in log density (T15(d)).

**6. Monte Carlo where it belongs.** Monte Carlo remains for the scores (an average
over nature's draws is the object itself, §4.4), and for continuous priors' information
and per-state divergence. There the integrand is $\log m_\pi$, itself a quadrature, at
dimensions where a grid over the data would be hopeless.

## What a red-team finding in this region might be flagging

1. **A grid coarser than the noise.** Any rule whose cells exceed about half a noise unit
   in prediction space aliases the likelihood. Check the cell size in Fisher length, not
   in `theta`.
2. **Edges, kinks and spikes in an "accurate" rule.** Ask where the integrand is not
   smooth and how the rule treats it (folding, a change of variables, exact masses).
3. **A reference that was never refined.** Spec 002's T7(a) compares the quadrature with
   a 400 x 400 midpoint grid. That grid gives the diagonal cells full weight instead of
   half, an $O(h)$ error: off by 0.0025 nats for `p_U` (0.00125 at 800 x 800). For
   `p_LN`, whose spike it samples by midpoints, it is off by 0.1. Between cells of 0.4 and
   0.1 noise units, the implementation's rule changes by `4e-5` for `p_U` and `1.2e-3`
   for `p_LN`. A failing comparison can mean
   that the reference is the less accurate side.
4. **Monte Carlo noise read as a result.** A Monte Carlo estimate with standard error
   0.02 cannot support a `1e-3` inequality. Either the test's slack or the estimator
   must change.

## When you'd want more than this calibration

To bound errors rigorously rather than by refinement, to use adaptive or sparse-grid
rules at moderate `D`, or to put randomized quasi-Monte Carlo error bars on the scores,
start from Davis & Rabinowitz, and from Owen (ch. 15–17) for randomized quasi-Monte Carlo
[recalled]. The calibrated story above covers only the rules this repo uses and why.

## Provenance

Requested by the human during the implementation of spec 002 (2026-11-25), after the
divergence estimator, the exp-decay grids and the T7(a) reference question had come up
in the codegen work. The numbers quoted are those measured then and recorded in
`docs/002-foreign-q-prediction/README.md` (DD-K1, DD-Q1, DD-Q2, *Testing notes*). If
later specs need quadrature on curved manifolds or adaptive rules, add siblings rather
than growing this file.
