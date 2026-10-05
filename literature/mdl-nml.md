# MDL and NML

*Drafted by Claude on 2026-10-05; Rissanen 1996 read for the repo's tutorial, the rest
from abstracts and citing works. Not yet reviewed by MB.*

## Question and central object

Which code compresses every individual data set nearly as well as the best model in the
family, in hindsight? The [minimum description length](../GLOSSARY.md#minimum-description-length-mdl) answer is the [normalized maximum
likelihood](../GLOSSARY.md#normalized-maximum-likelihood-nml) distribution `p_NML(x) = max_θ p(x|θ) / Z`, minimax for the worst-case *pointwise*
regret, with [parametric complexity](../GLOSSARY.md#parametric-complexity) `log Z`. Pushed forward through the maximum-likelihood
map it gives spec 002's co-protagonist `p_proj` (row (g) of
[One object, many names](README.md#one-object-many-names)).

## Findings we use

- **NML is pointwise-minimax** (Shtarkov 1987) [recalled]. Feeds spec 002 §3.4.
- **Its complexity.** `log Z = (D/2) log(N/2π) + log ∫√det g + o(1)` [read: Rissanen
  1996, Thm 1]. The capacity's constant is smaller by `D/2` nats (Clarke & Barron 1994)
  [recalled]. Feeds spec 002 §3.4, footnote on asymptotics.
- **Counting distinguishable models.** `log ∫√det g` counts the distinguishable
  distributions in the model (Balasubramanian 1997) [recalled]. Feeds spec 002's
  distinguishable-prediction volume `V_g` (§1.2) and the tutorials.
- **`p_proj`.** The pushforward of NML through the maximum-likelihood map [read: A&M App.
  A.3; Quinn §5.2, as the "adaptive slab-and-spike" prior] puts extra weight on the edges
  [read: A&M App. A.3], from data that fall just outside convex boundaries. Feeds spec 002
  §3.4 and its two contrastive corners.
- **NML is a Bayes predictive with a complex-valued prior,** which also turns its
  computation into an integral over parameters [read: Suzuki & Yamanishi 2021, abstract].
  Spec 002 §3.4 says no prior's Bayes mixture equals `p_NML` at finite `N`; that holds
  for real priors only.
- **Budget dependence on the regret side.** For multinomials, asymptotic minimax regret
  is attained by a Dirichlet mixture whose parameter depends on the sample size, and the
  papers characterise when strategies that do not depend on it suffice [read: Watanabe,
  Roos & Myllymäki 2013, abstract]. The regret counterpart of spec 002 §0's budget
  dependence.
- **Between mixture and NML.** α-NML predictors interpolate between Bayes mixtures (the
  Laplace and Krichevsky–Trofimov predictors) and NML, and are optimal for a Rényi-
  divergence regret between the average and the worst case [read: Bondaschi & Gastpar
  2024, abstract]. A possible bridge between spec 002's two construction routes [guess].
- **Conditional NML.** Projected onto Bayes predictives, it is asymptotically Komaki's
  latent-information-prior predictive ([komaki-school.md](komaki-school.md)).

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Shtarkov 1987, "Universal sequential coding of single messages", *Probl. Inf. Transm.* 23(3) | unread | NML is pointwise-minimax | 002 §3.4 | – |
| Rissanen 1996, "Fisher information and stochastic complexity", *IEEE TIT* 42(1):40–47 ([pdf](../resources/rissanen.pdf)) | read Thm 1 | the complexity expansion | 002 §3.4; nml-mdl tutorial | ☆ Thm 1 and its setting, eight pages |
| Balasubramanian 1997, "Statistical inference, Occam's razor, and statistical mechanics on the space of probability distributions", *Neural Comput.* 9(2):349–368 | unread | `∫√det g` counts distinguishable models | 002 §1.2; tutorials | – |
| Grünwald 2007, *The Minimum Description Length Principle*, MIT Press | unread | MDL, Bayes–Jeffreys and capacity codes agree asymptotically | 002 §3.4 | – |
| Watanabe, Roos & Myllymäki 2013, "Achievability of asymptotic minimax regret in online and batch prediction", ACML, PMLR 29:181–196; extended as Watanabe & Roos 2015, *JMLR* 16:2357–2375 | abstract | minimax regret needs sample-size-dependent priors | 002 §0 | – |
| Suzuki & Yamanishi 2021, "Fourier-analysis-based form of normalized maximum likelihood", *IEEE TIT* 67(9):6164–6178 | abstract | NML = Bayes predictive under a complex prior | 002 §3.4 | – |
| Bondaschi & Gastpar 2024, "Alpha-NML universal predictors", *IEEE TIT*; arXiv:2202.12737 | abstract | a family from mixtures to NML | 002 §3.4 | – |

## Links to other clusters

- **Universal coding.** Expected redundancy (capacity) versus pointwise regret (NML):
  same leading terms, different constants ([universal-coding.md](universal-coding.md)).
- **Machta group.** A&M and Quinn et al. use `p_proj` as an approximation of `p*`; Quinn
  et al. note in a footnote that NML is also used in MDL [read: Quinn §5.2, footnote ‡‡].
- **Komaki school.** Conditional NML and latent information priors (Kojima & Komaki 2016).

## Open questions

- Does the complex-prior representation give a practical way to compute `p_NML`, and so
  `p_proj`, in spec 002's Gaussian models?
