# Feder group: universal batch learning

*Drafted by Claude on 2026-10-05 from Fogel & Feder 2024 (read in full), Vituri & Feder
2024 (summary) and citations; not yet reviewed by MB.*

## Question and central object

Universal prediction with log-loss, extended from the online setting (every symbol of a
sequence is scored) to batch learning (train on `N`, score the next symbol) and to the
range between (train on `N`, score the next `L`). For data from a model in the class, the
minimax regret is a conditional capacity, `max_w (1/L) I(Y^L;Θ|Y^N)`, attained by the
[Bayes mixture](../GLOSSARY.md#bayes-mixture) under the maximising prior [read: Fogel & Feder 2024 Thm 1]. This is
Komaki's latent information prior at `(N, L)` ([komaki-school.md](komaki-school.md));
their "regret" in this setting is our [redundancy](../GLOSSARY.md#redundancy-and-regret), per symbol.

## Findings we use

- **One theorem covers both of our scores.** `N = 0` is the online problem, our `R_N`
  and Mattingly's game; `L = 1` is batch learning, our `r_N`. Minimax equals maximin, and
  the Bayes mixture under the maximising prior is minimax, for bounded `Θ` and a finite
  outcome space [read: Thm 1]. Feeds the spec 002 score choice.
- **The learning curve, exactly, for multinomials.** The minimax regret is
  `(1/L) Σ_{k<L} [(m−1)/(2(N+k)) + o(1/(N+k))]`, so scored step `k` costs
  `(m−1)/(2(N+k))` whichever window is scored [read: Thm 2]. For `L ≪ N` this is the
  batch rate `(m−1)/(2N)`; for `L ≫ N` the online rate `(m−1) log L/(2L)` [read: §V]. A
  Laplace-approximation argument gives the same with `k` parameters in smooth models,
  informally [read: §VI].
- **The prior enters at second order.** In online prediction the leading term is attained
  by every smooth prior [read: §II.A]; for batch learning with the boundary excluded, the
  second term is `∝ 1/N²` (citing Komaki 2012) [read: §II.B]. Both concern minimax
  values, not differences between given priors, but they are consistent with the
  `[guess]` in the score-choice discussion that `R_N` weights the early, data-poor steps,
  where priors matter most.
- **A solver with a built-in check.** A Blahut–Arimoto variant (accelerated, after Matz &
  Duhamel 2004) runs on a `θ` grid, and any trial prior bounds the minimax regret from
  both sides: `(1/L) I(Y^L;Θ|Y^N) ≤ R* ≤ max_θ (1/L) D_θ` [read: Cor. 1, Alg. 1]. Feeds
  spec 002 §4.2 if the endpoint prior is added.
- **Not necessarily discrete.** For `N > 0` discreteness is not guaranteed, and for some
  `(N, L)` the numerical optimum is non-zero on most grid points, even on grids much finer
  than `N` and `L` [read: §VII]. The prior figures are in a "full version" we have not
  found. Compare `p*`, discrete at `N = 0`, and Tanaka's discrete `(1, 1)` case.
- **Nature outside the model** (Vituri & Feder 2024). The minimax regret becomes a
  constrained conditional capacity; their Blahut–Arimoto extension iterates on the prior,
  without a convergence proof [read: Vituri & Feder 2024, summary]. Kept for the
  algorithm: spec 002's nature lies inside the model.

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Fogel & Feder 2024, "Combining batch and online prediction", ISIT Workshops ([pdf](../resources/8_Combining_Batch_and_Online_P.pdf)) | read in full | Thm 1, Thm 2, Cor. 1, §VII | 002 score choice | ★ five pages, our exact question |
| Fogel & Feder 2018, "Universal batch learning with log-loss", ISIT, pp. 21–25 | unread | the first minimax theorem for batch learning, as credited by Fogel & Feder 2024 and Vituri & Feder 2024 | 002 score choice | – |
| Vituri & Feder 2024, "Universal batch learning under the misspecification setting", arXiv:2405.07252 | summary | Blahut–Arimoto for the conditional objective | 002 §4.2 | ☆ the algorithm section |
| Merhav & Feder 1998, "Universal prediction", *IEEE TIT* 44(6):2124–2147 | unread | the survey of the online setting | background for `R_N` | – |
| Goldstein 2023, "Numerical calculations for universal batch learning" | unread, not located | numerical batch priors via Blahut–Arimoto [read: Fogel & Feder 2024 §II.B] | 002 §4.2 | – |

## Links to other clusters

- **Komaki school.** The same objective. Fogel & Feder 2024 cite Komaki 2011 for its
  numerics and Komaki 2012 for the `1/N²` term; Vituri & Feder 2024 cite neither [read:
  reference lists].
- **Machta group.** Fogel & Feder 2024 cite Mattingly et al. 2018 and Abbott & Machta
  2019 as Blahut–Arimoto studies of the online capacity prior [read: §II.A]. The Machta
  papers in `resources/` do not cite Feder [read: text search].
- **Universal coding.** Theorem 1 extends the redundancy–capacity theorem (Gallager 1979;
  Ryabko 1979; Davisson & Leon-Garcia 1980), via Fan's 1953 minimax theorem [read: §II.A,
  §IV].
- **Capacity and rate–distortion.** Blahut–Arimoto (Arimoto 1972; Blahut 1972).

## Open questions

- Where is the "full version" of Fogel & Feder 2024 with the prior figures?
- Does Theorem 1 extend to Gaussian outcomes? Its proof uses compactness of the set of
  predictors, which rests on the finite outcome space [read: §IV].
- Where is Goldstein 2023?
