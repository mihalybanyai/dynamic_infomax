"""Quadrature rules for spec 002's continuous priors and natures (§4.2, §4.4, §5.4).

Spec: specs/002-foreign-q-prediction.md §4.4 ("quadrature over Theta at small D") and
§5.4 (grids). New in spec 002.

* **Exp-decay** (`ordered_grid`). In `xi`, the diagonal of the metric is separable:
  `g_mumu = sum_t (t xi_mu^(t-1))^2 / (D sigma)^2` depends on `xi_mu` alone, the same
  function for every axis. Each axis is cut into cells of equal arc length of that
  profile, `ARC_CELL` noise units long (DD-Q1), so a cell step moves the prediction by
  at most `ARC_CELL` noise units along each axis. The ordered region is covered by the
  cells with non-decreasing indices; a cell whose indices tie on `g` coordinates
  holds `1/g!` of its box, and its Gauss–Legendre nodes are sorted into the ordered
  region (`∫_{cell ∩ ordered} f = (1/prod g!) ∫_cell f(sort xi) dxi`).
* **Hypercone** (`cone_theta1_rule`). Gauss–Legendre nodes along `theta_1` in cells of
  at most half a noise unit; the cross-section is integrated in closed form by the
  priors and natures that are uniform on it.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations_with_replacement
from math import factorial

import numpy as np

ARC_CELL: float = 0.3
"""Exp-decay grid cell length along each axis, in noise units (two GL nodes per cell):
about 4e-4 nats of error in `p_LN`'s log marginal at the cheap cell, 4e-5 in `p_U`'s."""

GL_NODES_PER_AXIS: dict[int, int] = {}
"""Gauss–Legendre nodes per axis cell by dimension (default 2). One node per cell is not
used: in a cell whose indices tie, the sorted single node lies on the diagonal, where
Jeffreys' density vanishes, and the cell's mass is lost (DD-Q1)."""

ARC_CELL_BY_D: dict[int, float] = {3: 0.6, 4: 0.6}
"""Cell length in noise units by dimension (default `ARC_CELL`): at `D >= 3`, two nodes in
cells of 0.6 cost about what one node in cells of 0.3 did, with per-state errors of
2.7e-4 (`p_LN`, `D = 4`), 2.4e-3 (`p_J`, `D = 3`) and 6e-2 (`p_J`, `D = 4`) nats."""

MAX_GRID_NODES: int = 2_000_000
"""Exp-decay grids are coarsened until they hold at most this many nodes."""


@lru_cache(maxsize=16)
def _arc_profile(m: int, lo: float, hi: float, n: int = 20001) -> tuple[np.ndarray, np.ndarray]:
    """Cumulative arc length `A(xi) = ∫_lo^xi sqrt(sum_t t^2 eta^(2t-2)) d eta` (per unit
    noise, before the `1/D` factor), on a fine grid of `xi`."""
    t = np.linspace(1.0, 5.0, m)
    xi = np.linspace(lo, hi, n)
    speed = np.sqrt(np.sum((t[None, :] * xi[:, None] ** (t[None, :] - 1.0)) ** 2, axis=1))
    A = np.concatenate([[0.0], np.cumsum(0.5 * (speed[1:] + speed[:-1]) * np.diff(xi))])
    return xi, A


def axis_edges(m: int, D: int, lo: float, hi: float, s: float, *, n_cells: int | None = None) -> np.ndarray:
    """Cell edges along one exp-decay axis, equal in arc length at noise `s` (or `n_cells`)."""
    xi, A = _arc_profile(m, float(lo), float(hi))
    total = A[-1] / D / s
    if n_cells is None:
        n_cells = max(4, int(np.ceil(total / ARC_CELL_BY_D.get(D, ARC_CELL))))
    targets = np.linspace(0.0, A[-1], n_cells + 1)
    edges = np.interp(targets, A, xi)
    edges[0], edges[-1] = lo, hi
    return edges


def n_ordered_cells(n: int, D: int) -> int:
    return factorial(n + D - 1) // (factorial(D) * factorial(n - 1))


def ordered_grid(
    edges: np.ndarray, D: int, q: int = 2, *, axis_nodes: tuple[np.ndarray, np.ndarray] | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Nodes, log weights (log volume elements) and cell ids of the ordered product grid.

    Returns `nodes` (n, D) sorted within each row, `log_vol` (n,) such that
    `sum exp(log_vol) f(nodes) ≈ ∫_{ordered} f`, and `cell` (n,) the cell index of each node.
    `axis_nodes = (pos, logw)`, each (n_cells, q), replaces the Gauss–Legendre nodes and
    log weights within each axis cell (for a measure other than `d xi`, DD-Q2).
    """
    edges = np.asarray(edges, dtype=float)
    n = edges.size - 1
    lo_e, hi_e = edges[:-1], edges[1:]
    width = hi_e - lo_e
    gx, gw = np.polynomial.legendre.leggauss(q)
    gx = 0.5 * (gx + 1.0)
    gw = 0.5 * gw
    cells = np.array(list(combinations_with_replacement(range(n), D)), dtype=int)  # (C, D), non-decreasing
    # tie-group factor 1/prod g!
    log_tie = np.zeros(len(cells))
    if D > 1:
        same = cells[:, 1:] == cells[:, :-1]
        run = np.zeros(len(cells), dtype=int)
        for k in range(D - 1):
            run = np.where(same[:, k], run + 1, 0)
            log_tie -= np.log(run + 1.0) * same[:, k]
    # Gauss–Legendre product nodes within each cell box
    mesh = np.array(np.meshgrid(*([np.arange(q)] * D), indexing="ij")).reshape(D, -1).T  # (q^D, D)
    if axis_nodes is None:
        node_frac = gx[mesh]  # (q^D, D)
        node_logw = np.sum(np.log(gw[mesh]), axis=1)  # (q^D,)
        lo_c = lo_e[cells]  # (C, D)
        w_c = width[cells]
        nodes = lo_c[:, None, :] + w_c[:, None, :] * node_frac[None, :, :]
        log_vol = (np.sum(np.log(w_c), axis=1) + log_tie)[:, None] + node_logw[None, :]
    else:
        pos, lw = axis_nodes  # (n, q) each
        # node (k_1..k_D) of cell (i_1..i_D): coordinate mu at pos[i_mu, k_mu]
        nodes = pos[cells[:, None, :], mesh[None, :, :]]  # (C, q^D, D)
        log_vol = np.sum(lw[cells[:, None, :], mesh[None, :, :]], axis=-1) + log_tie[:, None]
    nodes = np.sort(nodes, axis=-1).reshape(-1, D)
    cell = np.repeat(np.arange(len(cells)), mesh.shape[0])
    return nodes, log_vol.ravel(), cell


def exp_decay_grid(model, s: float, *, n_per_axis: int | None = None, q: int | None = None, axis_measure=None):
    """The ordered grid for an exp-decay model at noise `s` (cells of `ARC_CELL` noise
    units), coarsened until it fits `MAX_GRID_NODES`. Returns `(nodes, log_vol, cell, edges)`.

    `axis_measure = (log_H_interval, inv_H)` integrates against a per-rate probability law
    instead of `d xi`: within each axis cell the nodes are Gauss–Legendre in that law's CDF,
    `xi = H^-1(H(a) + (H(b) - H(a)) u_k)`, with log weights `log (H(b) - H(a)) + log w_k`."""
    D = model.D
    lo, hi = float(model.box.low[0]), float(model.box.high[0])
    q = GL_NODES_PER_AXIS.get(D, 2) if q is None else q
    if n_per_axis is not None:
        edges = axis_edges(model.m, D, lo, hi, s, n_cells=max(1, n_per_axis // q))
    else:
        edges = axis_edges(model.m, D, lo, hi, s)
        while n_ordered_cells(edges.size - 1, D) * q**D > MAX_GRID_NODES and edges.size > 5:
            edges = axis_edges(model.m, D, lo, hi, s, n_cells=int((edges.size - 1) * 0.8))
    axis_nodes = None
    if axis_measure is not None:
        log_H_interval, inv_H = axis_measure
        gx, gw = np.polynomial.legendre.leggauss(q)
        gx, gw = 0.5 * (gx + 1.0), 0.5 * gw
        a, b = edges[:-1], edges[1:]
        lm = log_H_interval(a, b)  # (n,)
        pos = inv_H(a[:, None], b[:, None], gx[None, :])
        axis_nodes = (pos, lm[:, None] + np.log(gw)[None, :])
    nodes, log_vol, cell = ordered_grid(edges, D, q, axis_nodes=axis_nodes)
    return nodes, log_vol, cell, edges


def cone_theta1_rule(W: float, s: float, *, q: int = 4, cell: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """Gauss–Legendre nodes and weights on `[0, W]`, cells of at most `cell * s`."""
    n_cells = max(4, int(np.ceil(W / (cell * s))))
    edges = np.linspace(0.0, W, n_cells + 1)
    gx, gw = np.polynomial.legendre.leggauss(q)
    h = np.diff(edges)
    nodes = (edges[:-1, None] + 0.5 * h[:, None] * (gx[None, :] + 1.0)).ravel()
    weights = (0.5 * h[:, None] * gw[None, :]).ravel()
    return nodes, weights
