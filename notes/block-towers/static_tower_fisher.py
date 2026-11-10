"""Local Fisher spectrum of a static block tower judged under perceptual noise.

Untrusted exploratory script for notes/block-towers.md. A single column of n unit-width
blocks of equal mass in 2-D. Block k sits on block k-1 with horizontal centres c_k. The
column stands iff, at every interface, the centre of mass of everything above lies inside
the contact (the overlap of the two blocks). The observer sees each centre with independent
Gaussian noise sigma (block widths) and reports the outcome of the perceived tower:
"stands", or the lowest failing interface and the side it fails on (1 + 2(n-1) outcomes;
the number of blocks above the failing interface is the static count of fallen blocks).

The Fisher metric of this outcome distribution with respect to the true centres is
g = sum_o grad p_o grad p_o^T / p_o. Because the noise is Gaussian, grad p_o =
E[1{outcome = o} eps] / sigma (no derivative of the outcome map is needed). g is estimated
from two independent halves of the draws, so that Monte-Carlo noise does not bias it
upward. A common shift of all centres changes nothing, so g has an exact zero mode; its
estimate measures the Monte-Carlo noise floor.

Run from the repo root: uv run python notes/block-towers/static_tower_fisher.py
"""
import numpy as np

SEED = 20261110
N_BLOCKS = 10
N_TOWERS = 60
N_DRAWS = 400_000          # per tower, split in two halves
SIGMAS = [0.05, 0.1, 0.2, 0.4]


def outcomes(c):
    """Outcome index for each perceived tower in c (shape S x n): 0 = stands."""
    S, n = c.shape
    com = np.cumsum(c[:, ::-1], axis=1)[:, ::-1] / np.arange(n, 0, -1)   # COM of blocks k..n-1
    out = np.zeros(S, dtype=np.int64)
    for k in range(n - 1, 0, -1):                 # top to bottom: the lowest failure wins
        left = np.maximum(c[:, k], c[:, k - 1]) - 0.5
        right = np.minimum(c[:, k], c[:, k - 1]) + 0.5
        fail_l = com[:, k] < left
        fail_r = com[:, k] > right
        both = fail_l & fail_r                    # no contact at all: side = where block k sits
        fail_l = np.where(both, c[:, k] < c[:, k - 1], fail_l)
        fail_r = fail_r & ~fail_l
        out = np.where(fail_l, 1 + 2 * (k - 1), out)
        out = np.where(fail_r, 2 + 2 * (k - 1), out)
    return out


def fisher(c0, sigma, rng):
    n = c0.size
    n_out = 1 + 2 * (n - 1)
    half = N_DRAWS // 2
    grads, counts = [], np.zeros(n_out)
    for _ in range(2):
        eps = rng.standard_normal((half, n))
        o = outcomes(c0 + sigma * eps)
        G = np.zeros((n_out, n))
        np.add.at(G, o, eps)
        grads.append(G / (sigma * half))
        counts += np.bincount(o, minlength=n_out)
    p = counts / N_DRAWS
    keep = p > 0
    g = (grads[0][keep].T / p[keep]) @ grads[1][keep]
    return (g + g.T) / 2, p


def main():
    rng = np.random.default_rng(SEED)
    n = N_BLOCKS
    # Offset range a: how often random towers stand without noise. a = 0.25 is used below
    # because it puts the judged chance of falling near one half at sigma = 0.2.
    for a in [0.15, 0.2, 0.25, 0.3, 0.35]:
        d = rng.uniform(-a, a, size=(20000, n - 1))
        c = np.concatenate([np.zeros((20000, 1)), np.cumsum(d, axis=1)], axis=1)
        print(f"offsets uniform in +-{a:.2f}: {np.mean(outcomes(c) == 0):.2f} of towers stand")
    a = 0.25
    d = rng.uniform(-a, a, size=(N_TOWERS, n - 1))
    towers = np.concatenate([np.zeros((N_TOWERS, 1)), np.cumsum(d, axis=1)], axis=1)
    stands = outcomes(towers) == 0
    print(f"\n{N_TOWERS} towers, n = {n}, offsets uniform in +-{a}; {stands.mean():.2f} stand; "
          f"{N_DRAWS} draws per tower; seed {SEED}")
    ones = np.ones(n) / np.sqrt(n)
    for sigma in SIGMAS:
        spectra, floors, tops, pfall = [], [], [], []
        for c0 in towers:
            g, p = fisher(c0, sigma, rng)
            floors.append(abs(ones @ g @ ones))
            w, v = np.linalg.eigh(g)
            spectra.append(w[::-1][: n - 1])
            tops.append(v[:, -1])
            pfall.append(1 - p[0])
        spectra, floor = np.array(spectra), float(np.median(floors))
        med = np.median(spectra, axis=0)
        tops = np.array(tops)
        cos = np.abs(tops @ tops.T)[np.triu_indices(N_TOWERS, 1)]
        resolved = (spectra > 1 / a**2).sum(axis=1)       # a step of a moves the prediction > 1 Fisher length
        above = (spectra > 10 * floor).sum(axis=1)
        pf = np.array(pfall)
        print(f"\nsigma = {sigma}: P(fall) quartiles {np.quantile(pf, [.25, .5, .75]).round(2)}; "
              f"noise floor {floor:.1e}")
        print("  median eigenvalues, largest first: " + " ".join(f"{x:.2g}" for x in med))
        print("  median log10(lambda_i / lambda_1):  " + " ".join(
            f"{x:.1f}" for x in np.log10(np.maximum(med, floor) / med[0])))
        print(f"  eigenvalues above 10x floor per tower: median {np.median(above):.0f} of {n - 1}")
        print(f"  directions resolved at a step of {a}: median {np.median(resolved):.0f}, "
              f"range {resolved.min()}-{resolved.max()}")
        print(f"  |cos| between the stiffest directions of two towers: mean {cos.mean():.2f} "
              f"(random directions: {1 / np.sqrt(n - 1) * np.sqrt(2 / np.pi):.2f})")


if __name__ == "__main__":
    main()
