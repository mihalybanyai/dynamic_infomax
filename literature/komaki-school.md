# Komaki school: latent information priors

*Drafted by Claude on 2026-10-05 from Komaki 2011 (read in full) and abstracts; not yet
reviewed by MB.*

## Question and central object

Which prior makes the Bayes predictive of future data `y`, given observed data `x`,
[minimax](../GLOSSARY.md#minimax) under KL loss? Komaki's answer is the **latent information prior**,
`argmax_π I_π(Θ;Y|X)` [read: Komaki 2011 §3]. With `x = X_{1:N}` and `y = X_{N+1:N+M}` it
has two budgets: `N` observations seen and `M` still to predict. The case `(0, N)` is
spec 002's `p*`; the case `(N, 1)` is the endpoint score `r_N` (row (a) and (e) of
[One object, many names](README.md#one-object-many-names)).

## Findings we use

- **Minimax.** If `π̂` maximises `I_π(Θ;Y|X)` and gives every `x` positive probability,
  its Bayes predictive is minimax; in general a limit of Bayes predictives is [read:
  Komaki 2011 Thm 2]. Proven for finite sample spaces and compact `Θ`; Komaki expects it
  to extend under regularity, as Haussler's unconditional result does [read: §4]. Feeds
  the spec 002 score choice: this is the endpoint score's native prior.
- **Least favourable, and concave.** `I_π(Θ;Y|X)` equals the Bayes risk of `π`'s own
  predictive [read: §4]. Under the maximiser, `θ` holds the most information about `y`
  that `x` has not yet revealed, hence "latent"; that is the worst case [read: §3]. A
  Bayes risk is an infimum of functions linear in `π`, so it is concave, as Komaki states
  [read: §4]. A Blahut–Arimoto-type solver is therefore natural; the Feder group has one
  ([feder-group.md](feder-group.md)).
- **Budget dependence.** In a binomial model with 11 parameter values, the priors change
  strongly with `(N, M)`: few support points when both are small, close to uniform at
  `(0, 1000)`, close to a Jeffreys histogram at `(0, 100)`, and weight moving toward
  `θ = 0.5` as `N` grows. Komaki concludes that priors must give up context invariance
  [read: §4]. Feeds spec 002 §0, "second protagonist: budget dependence".
- **The reference priors are the `N = 0` cases.** `(0, k)` is the `k`-reference prior of
  Berger, Bernardo & Mendoza 1989, and `(0, M → ∞)` the [reference prior](../GLOSSARY.md#reference-prior) [read: §4].
- **Many data, one step.** For one-step-ahead prediction in multinomials, the
  asymptotically minimax prior is a particular Dirichlet, neither Jeffreys nor uniform
  [read: Komaki 2012, abstract]. The cumulative score's asymptotic least-favourable prior
  is Jeffreys instead (Clarke & Barron 1994) [read: Komaki 2011 §1, citing it].
- **Discreteness.** At `(N, M) = (1, 1)` in the binomial, the latent information prior is
  discrete, derived analytically [read: Tanaka 2014, abstract]. Fogel & Feder 2024 find
  optima with full support for some `(N, L)` (see [feder-group.md](feder-group.md)), so
  discreteness at `N > 0` is open.
- **MDL counterpart.** Projected onto Bayes predictives, conditional NML (variant CNML3)
  is asymptotically the latent-information-prior predictive, and exactly under stronger
  assumptions [read: Kojima & Komaki 2016, abstract]. This is the one-step analogue of
  spec 002's `p*` and `p_proj` pair (§3.4).
- **High-dimensional Gaussian prediction.** For the mean of a `d`-dimensional normal,
  `d ≥ 3`, the Bayes predictive under Stein's shrinkage prior dominates the one under the
  uniform prior [read: Komaki 2001, search summary]. It is the nearest known case of a
  prior mattering for prediction in high dimension, the effect spec 002 tests; spec 002
  §1.2 cites Stein 1959 in the footnote on everyday examples.

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Komaki 2011, "Bayesian predictive densities based on latent information priors", *J. Stat. Plan. Inference* 141(12):3705–3715; arXiv:1009.5072 ([pdf](../resources/komaki.pdf)) | read in full | defines the prior; minimax (Thm 2); concave; `(N, M)` dependence; `(0, k)` is the `k`-reference prior | 002 score choice; 002 §0 | ★ §1, §3 to Thm 2, §4 |
| Komaki 2012, "Asymptotically minimax Bayesian predictive densities for multinomial models", *EJS* 6:934–957; arXiv:1112.0818 | abstract | one-step asymptotically minimax prior is neither Jeffreys nor uniform | 002 score choice | – |
| Tanaka 2014, "An analytic example of latent information prior", arXiv:1410.2961 | abstract | discrete at `(1, 1)`, binomial | discreteness, open | ☆ short |
| Kojima & Komaki 2016, "Relations between the conditional normalized maximum likelihood distributions and the latent information priors", *IEEE TIT* 62(1); arXiv:1412.7794 | abstract | conditional NML ≈ latent-information-prior predictive | 002 §3.4 analogue | – |
| Komaki 2001, "A shrinkage predictive distribution for multivariate normal observables", *Biometrika* 88:859–864 | search summary | shrinkage prior beats uniform for Gaussian prediction, `d ≥ 3` | 002 §1.2 footnote | – |

## Links to other clusters

- **Bernardo's circle.** The `N = 0` cases are its reference priors. Geisser (1979), in
  the discussion of Bernardo 1979, proposed minimax prediction under this risk as an
  alternative to reference priors; Komaki presents his priors as bridging the two [read:
  Komaki 2011 §1].
- **Universal coding.** Theorem 2 is the conditional version of the result that Bayes
  codes under the capacity-achieving prior are minimax (Gallager 1979; Davisson &
  Leon-Garcia 1980; Haussler 1997) [read: §1, §4].
- **Feder group.** The same objective, derived independently as the capacity of batch
  learning (Fogel & Feder 2018). Fogel & Feder 2024 cite Komaki 2011 only for its
  numerics [read: Fogel & Feder 2024 §II.B].
- **Machta group.** `p*` is the `(0, N)` case. Abbott & Machta 2023, Mattingly et al.
  2018 and Quinn et al. do not cite Komaki [read: text search of the PDFs in
  `resources/`].
- **MDL and NML.** Kojima & Komaki 2016.

## Open questions

- Is the latent information prior at `(N, 1)` discrete in Gaussian ribbon models?
- Does Theorem 2 extend to Gaussian data? Komaki expects so [read: §4].
- At what order in `1/N` does the prior enter the one-step risk? Fogel & Feder 2024 cite
  Komaki 2012 for a `1/N²` second term in multinomials [read: Fogel & Feder 2024 §V].
