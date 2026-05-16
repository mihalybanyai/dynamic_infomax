"""Plate-notation diagram for spec 000-static-infomax-fig1.

The generative model behind Mattingly's static MI objective for the
Bernoulli experiment: a latent bias theta drawn from the (to-be-optimised)
prior p(theta), then m i.i.d. Bernoulli observations conditional on theta.

Run:    python diagrams/000-static-infomax-fig1-pgm.py
Output: diagrams/000-static-infomax-fig1-pgm.svg
"""
import daft

pgm = daft.PGM()

pgm.add_node("theta", r"$\theta$", x=2, y=2)
pgm.add_node("x", r"$x_i$", x=2, y=1, observed=True)

pgm.add_edge("theta", "x")

pgm.add_plate([1.4, 0.5, 1.2, 1.0], label=r"$i = 1, \ldots, m$", position="bottom right")

pgm.render()
pgm.savefig("diagrams/000-static-infomax-fig1-pgm.svg")
