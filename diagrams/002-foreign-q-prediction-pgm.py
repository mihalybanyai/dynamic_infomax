"""Plate-notation diagram for spec 002-foreign-q-prediction.

This is the generative model of NATURE (the external environment), NOT what
the agent assumes — exactly as in spec 001. The agent never sees q or the
q-family knob c; it reasons through one fixed prior
pi in {p*, p_J, p_U, p_LN} (plus q-bar as a reference ceiling) chosen from
the likelihood geometry and the data budget alone, never coupled to q. That
decoupling (agent != nature) is the whole point: it is what lets the
held-out predictive log-loss test whether p*'s A&M-unbiasedness transfers to
a foreign q (see spec sec 0, sec 2). The agent's prior is therefore omitted
from this nature-only diagram and described in prose.

Structure:

  - c (q-family / "cooperativeness" knob): fixes which foreign nature q is
    sampled, swept from cooperative (q ~ m_{p*}) to non-cooperative (mass in
    p*'s atom gaps / on the thin end). Fixed input, OUTSIDE the plates.
  - Outer plate (s = 1, ..., S_q): independent draws of the data-generating
    density q_s and the truth theta_s ~ q_s. The likelihood geometry
    (taper, rotation, dimension d, noise sigma) is fixed across draws and is
    described in the spec, not drawn here.
  - theta ~ q: nature's true parameter for this draw.
  - Training plate (i = 1, ..., N): the observations x_i ~ p(x|theta) the
    agent conditions on to form its posterior.
  - x' : a fresh held-out observation x' ~ p(x|theta), the prediction target
    the log-loss scores. Observed only at scoring time, never conditioned on
    (cf. spec 001's shaded-node convention).

Run:    python diagrams/002-foreign-q-prediction-pgm.py
Output: diagrams/002-foreign-q-prediction-pgm.svg
"""
import daft

pgm = daft.PGM()

# q-family knob c: an input parameter, fixed across q-samples, so it sits
# OUTSIDE the outer plate. Drawn as a fixed (double-circle) node.
pgm.add_node("c", r"$c$", x=0.5, y=2.0, fixed=True)

# Generative chain: q ~ c, theta ~ q, then both the training x_i and the
# held-out x' are drawn from p(.|theta).
pgm.add_node("q",     r"$q$",      x=2.5, y=3.0)
pgm.add_node("theta", r"$\theta$", x=2.5, y=2.0)
pgm.add_node("x",     r"$x_i$",    x=1.8, y=1.0, observed=True)
pgm.add_node("xp",    r"$x'$",     x=3.4, y=1.0, observed=True)

pgm.add_edge("c",     "q")
pgm.add_edge("q",     "theta")
pgm.add_edge("theta", "x")
pgm.add_edge("theta", "xp")

# Fixed likelihood inputs collected in one double-circled node: the noise scale
# sigma and the geometry config psi (dimension d, observation times, taper,
# rotation). Constant across draws, so OUTSIDE the S_q plate; it feeds every
# observation. Answers the review note "can sigma and other parameters be put on
# the generative model".
pgm.add_node("phi", r"$\sigma,\psi$", x=2.6, y=-0.5, fixed=True)
pgm.add_edge("phi", "x")
pgm.add_edge("phi", "xp")

# NB on plate order: daft draws plates with a *white* fill, so a later plate
# paints over an earlier one in the overlap region. The outer plate is added
# FIRST so the inner training plate, drawn second, renders on top of it.

# Outer plate: S_q independent draws of q (and hence theta, x_i, x'). Excludes c.
pgm.add_plate(
    [1.15, 0.2, 2.95, 3.35],
    label=r"$S_q$",
    position="bottom right",
)

# Inner training plate: N i.i.d. observations x_i conditional on theta. Sized
# around the x_i node only (x' is the single held-out target, not in the plate),
# label at bottom-left so it sits clear of the theta->x_i arrow and of x'.
pgm.add_plate(
    [1.25, 0.45, 1.15, 1.05],
    label=r"$N$",
    position="bottom left",
)

pgm.render()
pgm.savefig("diagrams/002-foreign-q-prediction-pgm.svg")
