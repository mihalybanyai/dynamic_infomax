# Machta group: sloppy models and infomax priors

*Drafted by Claude on 2026-10-05 from the passages read for specs 000 and 002. Not yet
reviewed by MB.*

## Question and central object

Why do models with many parameters predict well although most parameters cannot be
pinned down, and which prior should such [sloppy models](../GLOSSARY.md#sloppy-model) get? Their manifolds are
[hyperribbons](../GLOSSARY.md#hyperribbon): a few stiff directions and many exponentially thinner sloppy ones. The
group's prior is the finite-data mutual-information maximiser `p⋆` (spec 002's `p*`),
which adapts to what the data can resolve, against Jeffreys, which weights unresolvable
[co-volume](../GLOSSARY.md#co-volume). Spec 002 tests whether their result transfers to a foreign nature.

## Findings we use

- **Sloppiness.** Fisher-information eigenvalues of such models span many orders of
  magnitude [read: A&M §2.1, citing Transtrum et al. 2010]; their widths fall off roughly
  geometrically [read: Quinn §2]. Feeds spec 002 §1.2.
- **The finite-data prior.** `p⋆` is discrete, with about `√n` atoms for `n`
  observations in one dimension, and tends to Jeffreys as `n` grows; putting its mass on
  boundaries selects simpler models (Mattingly et al. 2018, reproduced by spec 000). In
  several dimensions it is "usually discrete" [read: A&M §1]; at large noise its weight
  sits on 0- and 1-dimensional edges [read: A&M §2.1, Fig. 2]. Feeds spec 000; spec 002
  §1.1, §1.2.
- **Jeffreys fails in high dimension.** At `D = 26` the Jeffreys posterior lies over 20
  standard deviations from the data [read: A&M §2.2, Fig. 3], and Jeffreys captures under
  1 bit [read: A&M Fig. 5]. Its worst-case [bias pressure](../GLOSSARY.md#bias-pressure) exceeds 500 bits in the
  exponential-decay model and is about 55 bits in the hypercone [read: A&M §3; App. A.1].
  A log-normal prior degrades too, less severely [read: A&M §2.2]. Feeds spec 002 §0,
  §1.2, §3.1.
- **`p⋆` is unbiased on its own data.** Zero bias pressure on `p⋆`'s support is its
  [equalizer condition](../GLOSSARY.md#equalizer-condition) [read: A&M Eq. 5], and the comparison of bias pressure with
  posterior deviation uses data drawn from `p⋆` [read: A&M Fig. 4]. This is the gap spec
  002 exists to test (§0).
- **Principle.** Predictions should not depend on unobservable model details [read: A&M
  §2.2]; avoiding measure-induced bias, not overfitting, is the job of model selection
  [read: A&M §3]. Feeds spec 002 §0, footnote on the detective example.
- **Resolution adaptation is nearly unique in hyperribbons.** `p_proj` captures about as
  much information as `p⋆` and far more than Jeffreys [read: Quinn §5.1, Fig. 12]; Quinn
  et al. call it the "adaptive slab-and-spike" prior [read: Quinn §5.2], and A&M note its
  extra weight on edges [read: A&M App. A.3]. Feeds spec 002 §3.4.
- **Terminology.** A&M object to calling `p⋆` a reference prior [read: A&M App. A.8].
- **Sloppy is not unidentifiable.** Sloppy directions are candidates for collapse, not
  verdicts; practical identifiability depends on the budget (Chis et al. 2016) [recalled,
  via `notes/infomax_two_hats_and_directions.md` §9].

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Transtrum, Machta & Sethna 2010, "Why are nonlinear fits to data so challenging?", *PRL* 104:060201 | unread | sloppy spectra; model manifolds | 002 §1.2 | – |
| Transtrum, Machta & Sethna 2011, "Geometry of nonlinear least squares with applications to sloppy models and optimization", *PRE* 83:036701 | unread | the geometry behind hyperribbons [recalled] | 002 §1.2 | – |
| Chis, Villaverde, Banga & Balsa-Canto 2016, "On the relationship between sloppiness and identifiability", *Math. Biosci.* 282:147–161 | unread | sloppiness ≠ unidentifiability | two-hats note §9 | – |
| Mattingly, Transtrum, Abbott & Machta 2018, "Maximizing the information learned from finite data selects a simple model", *PNAS* 115(8):1760–1765 ([pdf](../resources/mattingly_paper.pdf)) | read; Fig. 1 reproduced by spec 000 | `p⋆`: discrete, `√n` atoms, → Jeffreys | 000; 001; 002 | – |
| Abbott & Machta 2019, "A scaling law from discrete to continuous solutions of channel capacity problems in the low-noise limit", *J. Stat. Phys.* 176:214–227 | unread | how `p⋆`'s atoms become a continuum as noise falls (title) | 002 §0, budget dependence | ☆ the scaling law |
| Abbott & Machta 2023, "Far from asymptopia: unbiased high-dimensional inference cannot assume unlimited data", *Entropy* 25(3):434 ([pdf](../resources/abbott_machta.pdf)) | read §1–§3, App. A.1, A.3, A.7, A.8, Figs. 2–5 | bias pressure; hypercone and exponential decay; Jeffreys' high-`D` bias | 002 throughout | ★ spec 002's anchor |
| Quinn, Abbott, Transtrum, Machta & Sethna 2023, "Information geometry for multiparameter models: new perspectives on the origin of simplicity", *Rep. Prog. Phys.* 86:035901 ([pdf](../resources/quinn.pdf)) | read §1–§2, §5.1–§5.2 | hyperribbons; `p_proj` ≈ `p⋆` | 002 §1.2, §3.4 | ☆ §5 |
| Abbott, `mcabbott/AtomicPriors.jl` (code, [local copy](../resources/AtomicPriors.jl)) | used for fixtures | an independent implementation of `p⋆` | 002 §5.5 (T12) | – |

## Links to other clusters

- **Capacity.** `p⋆` is a capacity-achieving input, computed by Blahut–Arimoto
  ([capacity-rate-distortion.md](capacity-rate-distortion.md)).
- **Bernardo's circle.** `p⋆` is the finite-repetition maximiser that reference analysis
  sends to infinity ([bernardo-reference-priors.md](bernardo-reference-priors.md)).
- **MDL.** `p_proj` is built from NML ([mdl-nml.md](mdl-nml.md)).
- **Feder group.** Fogel & Feder 2024 cite Mattingly et al. 2018 and Abbott & Machta
  2019; these papers do not cite Feder or Komaki [read: text search of the PDFs in
  `resources/`].

## Open questions

- Does `p⋆`'s unbiasedness on its own data survive data from a foreign nature? This is
  spec 002.
- What does the 2019 scaling law say about how `p⋆`'s atoms depend on the budget?
