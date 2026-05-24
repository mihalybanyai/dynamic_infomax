"""Plate-notation diagram for spec 001-infomax-betting.

Two stacked plates capture the simulation structure of the infomax
betting experiment:

  - Outer plate (s = 1, ..., S_q): independent samples of the
    data-generating density q drawn from one of the Beta-mixture
    hyperpriors 𝓗 ∈ {H1, H2, H3} (see spec §1.9).
  - Inner plate (n + k_+ observations): the n Bernoulli observations
    fed to the agent and the k_+ future tosses the bet is on. In
    practice both θ and X_{1:n+k_+} are integrated out analytically
    against q (see spec §1.4, §1.5); the plate is shown for
    conceptual completeness.

Run:    python diagrams/001-infomax-betting-pgm.py
Output: diagrams/001-infomax-betting-pgm.svg
"""
import daft

pgm = daft.PGM()

# Hyperprior tag (fixed per cell) and per-sample density q.
pgm.add_node("H", r"$\mathcal{H}$", x=1.0, y=3.0, fixed=True)
pgm.add_node("q", r"$q$", x=2.5, y=3.0)
pgm.add_edge("H", "q")

# True theta drawn from q; observations and bet-future conditional on theta.
pgm.add_node("theta", r"$\theta$", x=2.5, y=2.0)
pgm.add_node("x", r"$x$", x=2.5, y=1.0, observed=True)
pgm.add_edge("q", "theta")
pgm.add_edge("theta", "x")

# Inner plate: the n + k_+ Bernoulli draws (training data plus the bet
# outcomes). Drawn for conceptual completeness only — the algorithm
# integrates this plate out analytically.
pgm.add_plate(
    [1.9, 0.55, 1.2, 1.0], label=r"$n + k_{+}$", position="bottom right"
)

# Outer plate: S_q independent draws of q from the hyperprior 𝓗.
pgm.add_plate(
    [1.8, 0.3, 1.45, 3.05], label=r"$S_q$", position="bottom right"
)

pgm.render()
pgm.savefig("diagrams/001-infomax-betting-pgm.svg")
