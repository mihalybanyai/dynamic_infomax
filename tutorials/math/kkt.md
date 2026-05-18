# KKT conditions, calibrated to Blahut-Arimoto

> Just-in-time math explainer triggered by red-team findings on
> `specs/000-static-infomax-fig1.md`. Goal: enough KKT to evaluate
> claims about the BA-optimal prior, not a general theory of
> constrained optimisation. For the latter, see Boyd &
> Vandenberghe, *Convex Optimization*, §5.5.

## What problem are we solving

Blahut-Arimoto finds the input distribution $p^*(\theta)$ over a
finite alphabet that maximises the mutual information $I(\Theta; X)$
through a fixed channel $p(x|\theta)$. The optimisation problem:

$$
\max_{p(\theta)} I(\Theta; X) \quad \text{subject to} \quad
\sum_\theta p(\theta) = 1, \quad p(\theta) \ge 0 \text{ for all } \theta.
$$

Two kinds of constraint: one equality (probabilities sum to 1), $m$
inequalities (probabilities nonnegative, where $m$ is the alphabet
size). KKT is the right tool because we have inequality constraints
and want a *characterisation* of the optimum, not just a numerical
method.

## The KKT conditions in one paragraph of generality

For a problem
$$
\max f(x) \quad \text{s.t.} \quad g_i(x) \le 0, \ h_j(x) = 0
$$
with $f, g_i, h_j$ differentiable, a point $x^*$ that is optimal
satisfies:

1. **Stationarity**: $\nabla f(x^*) = \sum_i \mu_i \nabla g_i(x^*)
   + \sum_j \lambda_j \nabla h_j(x^*)$ for some multipliers
   $\mu_i, \lambda_j$.
2. **Primal feasibility**: $g_i(x^*) \le 0$, $h_j(x^*) = 0$.
3. **Dual feasibility**: $\mu_i \ge 0$ (for $\le$ constraints).
4. **Complementary slackness**: $\mu_i g_i(x^*) = 0$ for every $i$.

For convex problems (and the BA problem is convex in $p(\theta)$
once you fix the right parameterisation — see below), these are
sufficient as well as necessary.

The condition that does most of the work in our case is
**complementary slackness**: for each inequality constraint, either
the multiplier is zero *or* the constraint is active (holds with
equality). Active means "the constraint is binding at the
optimum"; the multiplier nonzero means "loosening the constraint
would let us do better."

## What the conditions say in the BA case

Set up the Lagrangian for the BA problem:

$$
\mathcal{L}(p, \lambda, \mu) = I(\Theta; X) - \lambda \left(\sum_\theta p(\theta) - 1\right) + \sum_\theta \mu_\theta p(\theta).
$$

The sign convention on the $\mu$ term is "+" because we wrote the
inequality as $-p(\theta) \le 0$ and then absorbed the minus sign.
This is one of the small bookkeeping points where signs get flipped
in red-team findings — worth doing slowly when checking a derivation.

Stationarity (differentiate w.r.t. $p(\theta)$, treating each
$p(\theta)$ as an independent variable):

$$
\frac{\partial I(\Theta; X)}{\partial p(\theta)} - \lambda + \mu_\theta = 0.
$$

The mutual-information derivative is a standard result:

$$
\frac{\partial I(\Theta; X)}{\partial p(\theta)} = D\big(p(x|\theta) \,\|\, p(x)\big),
$$

where $D(\cdot \| \cdot)$ is the KL divergence between the
conditional output distribution given input $\theta$ and the
marginal output distribution. Call this quantity $c(\theta)$ — it
is the "per-input contribution" to the mutual information.

Substituting:

$$
c(\theta) = \lambda - \mu_\theta.
$$

Now apply complementary slackness $\mu_\theta p(\theta) = 0$:

- If $p^*(\theta) > 0$: then $\mu_\theta = 0$, so $c(\theta) = \lambda$.
- If $p^*(\theta) = 0$: then $\mu_\theta \ge 0$, so $c(\theta) \le \lambda$.

This is the characterisation we wanted. **At the BA optimum, every
input with positive probability contributes the same per-input
information $\lambda$; inputs with zero probability contribute at
most $\lambda$.** The shared value $\lambda$ is the channel
capacity.

## Why this is the right tool, in one sentence

The reason KKT (rather than Lagrange multipliers alone) is the
correct framework is the inequality constraint $p(\theta) \ge 0$:
the BA optimum can have some inputs at zero probability (the
"three-atom solution" your eye test is checking for, where only 3
of $m$ inputs get used), and a pure Lagrange-multipliers
formulation can't represent this correctly — it would give
multipliers for the equality but no condition for which inputs are
active.

## What a red-team finding in this region might be flagging

Common failure modes in BA derivations or implementations:

1. **Wrong sign on $\mu_\theta$.** If the inequality is written
   $p(\theta) \ge 0$ vs $-p(\theta) \le 0$ inconsistently across
   the derivation, the $\mu$ term lands with the wrong sign in
   stationarity, and the final characterisation has the wrong
   direction for inputs at zero probability. Check: in the
   end-state characterisation, inputs at zero probability should
   have $c(\theta) \le \lambda$, not $\ge$. The "support set"
   of the optimum has the *high*-information inputs.
2. **Conflating "contribution at the optimum" with "contribution
   at iterate $t$".** The KKT characterisation holds *at the
   fixed point*. During BA iteration, the per-input contributions
   $c(\theta)$ are not yet equalised; the algorithm is in the
   process of moving probability mass toward inputs with above-
   average $c(\theta)$. Implementations that check "are
   contributions equal" as a *convergence* criterion are using
   the KKT condition correctly; implementations that check it
   *during* an iteration as a step-validity condition are
   misusing it.
3. **Forgetting complementary slackness when proving uniqueness or
   support-size claims.** "The optimum has support on at most $K$
   inputs" claims usually rest on the inactive-constraint side
   of complementary slackness, where $p^*(\theta) = 0$ is forced
   for inputs with $c(\theta) < \lambda$. A red-team finding that
   asks "why can't the optimum have full support?" is asking for
   this argument explicitly.

## When you'd want general KKT, not this calibration

If you find yourself working on a problem with multiple inequality
constraints that interact (not just nonnegativity), or with a
non-convex objective where KKT is necessary but not sufficient, the
calibrated story above is too thin. At that point read Boyd &
Vandenberghe §5.5 in full; the project-specific calibration only
takes you through the BA-shaped uses.

## Provenance

Triggered by red-team finding(s) on `specs/000-static-infomax-fig1.md`
referencing KKT-based characterisation of the BA optimum. If
subsequent specs raise KKT for other constrained-optimisation
problems (rate-distortion, capacity with cost constraints), expand
this file or split into siblings rather than rewriting the BA-
specific content.