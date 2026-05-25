"""Plate-notation diagram for spec 001-infomax-betting.

This is the generative model of nature (the external environment), NOT
what the agent assumes — see the prose under "Generative model" in the
spec. The agent only ever observes X_{1:n} and reasons through one of
the fixed priors p ∈ {p*_n, p_J, p_U, p_MM}; q and 𝓗 are nature's.

Two stacked plates capture the simulation structure:

  - Outer plate (s = 1, ..., S_q): independent samples of the
    data-generating density q drawn from one of the Beta-mixture
    hyperpriors 𝓗 ∈ {H1, H2, H3} (see spec §1.9). 𝓗 sits OUTSIDE the
    outer plate — it is fixed across q-samples.
  - Inner plate (n + k_+ Bernoulli draws): the n observations fed to
    the agent plus the k_+ future tosses the bet is on. In practice
    both θ and X_{1:n+k_+} are integrated out analytically against q
    (see spec §1.4, §1.5); the plate is shown for conceptual
    completeness.

Run:    python diagrams/001-infomax-betting-pgm.py
Output: diagrams/001-infomax-betting-pgm.svg
"""
import daft

pgm = daft.PGM()

# Hyperprior tag 𝓗 — an input parameter, fixed across q-samples, so it
# sits OUTSIDE the outer plate. Drawn as a fixed (double-circle) node.
pgm.add_node("H", r"$\mathcal{H}$", x=0.5, y=2.0, fixed=True)

# Generative chain: q ~ 𝓗, θ ~ q, x ~ Bern(θ).
pgm.add_node("q",     r"$q$",      x=2.5, y=3.0)
pgm.add_node("theta", r"$\theta$", x=2.5, y=2.0)
pgm.add_node("x",     r"$x$",      x=2.5, y=1.0, observed=True)

pgm.add_edge("H",     "q")
pgm.add_edge("q",     "theta")
pgm.add_edge("theta", "x")

# NB on plate order: daft draws plates with a *white* fill, so a later
# plate paints over an earlier one in the overlap region. The outer
# plate is therefore added FIRST so the inner plate, drawn second,
# renders on top of it — otherwise the inner plate disappears entirely.

# Outer plate: S_q independent draws of q (and hence θ, x). Excludes 𝓗.
# Made wider so its bottom-right "S_q" label is clearly outside the
# inner plate's footprint and so the inner plate has clear margin on
# all four sides.
pgm.add_plate(
    [1.55, 0.15, 1.9, 3.35],
    label=r"$S_q$",
    position="bottom right",
)

# Inner plate: n + k_+ i.i.d. Bernoulli draws conditional on θ.
# Sized larger than the x node and with the label at the bottom-right
# corner so the label sits BELOW the observed variable (not above it,
# where it would otherwise clash with the θ→x arrow). Generous
# left/right/top margin from the outer plate so both borders render
# distinctly.
pgm.add_plate(
    [2.05, 0.4, 0.9, 1.2],
    label=r"$n + k_+$",
    position="bottom right",
)

pgm.render()
pgm.savefig("diagrams/001-infomax-betting-pgm.svg")
