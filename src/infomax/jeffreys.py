"""Closed-form Jeffreys prior for the Bernoulli model.

Spec: specs/000-static-infomax-fig1.md §1.5. p_J(theta) is the m -> infinity
limit of the MI-maximising prior; used as a qualitative comparison target
(test T4).
"""
from __future__ import annotations

import numpy as np


def jeffreys_bernoulli_pdf(theta: np.ndarray) -> np.ndarray:
    """p_J(theta) = 1 / (pi * sqrt(theta * (1 - theta))) on (0, 1)."""
    raise NotImplementedError


def jeffreys_bernoulli_cdf(theta: np.ndarray) -> np.ndarray:
    """CDF of the Jeffreys prior on the Bernoulli; used for the K-S test."""
    raise NotImplementedError
