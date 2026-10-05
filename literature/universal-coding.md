# Universal coding and minimax redundancy

*Drafted by Claude on 2026-10-05; Haussler's preprint read, the rest from citing works
and the repo's tutorials. Not yet reviewed by MB.*

## Question and central object

How well can one code, or predict, data from an unknown member of a family `{p_θ}`, and
which code is best in the worst case? The price of not knowing `θ` is the
[redundancy](../GLOSSARY.md#redundancy-and-regret) `D_KL(p_θ‖Q)` of the code `Q`. The
[redundancy-capacity theorem](../GLOSSARY.md#redundancy-capacity-theorem) says the [minimax](../GLOSSARY.md#minimax) redundancy equals the
[channel capacity](../GLOSSARY.md#channel-capacity), attained by the [Bayes mixture](../GLOSSARY.md#bayes-mixture) of the capacity-achieving prior. This
is rows (a), (c) and (d) of [One object, many names](README.md#one-object-many-names).

## Findings we use

- **Minimax redundancy equals capacity, in general.** For any measurable family on a
  complete separable metric space, minimax equals maximin and a minimax code lies in the
  closure of the Bayes mixtures [read: Haussler 1996 preprint, abstract and §1]. Earlier
  proofs needed finite alphabets (Gallager 1979; Davisson & Leon-Garcia 1980) [read:
  Haussler §1; Komaki 2011 §1]. No compactness is needed, so it covers spec 002's Gaussian
  data. Feeds spec 002 §2.1 (rows 1–2 of the table of three redundancies) and §3.1.
- **The cumulative game.** Haussler motivates the result by `n` sequential predictions,
  each from the previous observations; by the chain rule the cumulative KL loss is
  `D(P_θ^n‖Q)`, and the gambling reading is the expected loss in log compounded wealth
  from not knowing `θ` [read: Haussler §1]. Feeds spec 002 eq. (2.1.4) and the score
  choice.
- **Equalizer.** Under the capacity-achieving prior, `D_KL(p_θ‖m_{p*}) ≤ C` for every
  `θ`, with equality on its support (Kemperman 1974; Haussler 1997) [read: A&M Eqs. 4–5].
  Feeds spec 002 eq. (3.1.1), the cap on `p*`'s redundancy for any `q`.
- **Compensation identity.** `𝔼_{θ∼q} D_KL(p_θ‖Q) = I_q + D_KL(m_q‖Q)` (Topsøe 1979),
  derived in spec 002 §9.1. Feeds spec 002 eq. (2.1.2).
- **Information radius.** The minimax code is the KL-centre of the family and the
  capacity its radius (Sibson 1969) [recalled]; see [information radius](../GLOSSARY.md#information-radius).
- **Asymptotics.** Minimax redundancy grows like `(D/2) log N` (Rissanen 1984), and every
  smooth prior attains this leading term [read: Fogel & Feder 2024 §II.A]. The redundancy of a prior `π` is
  `(D/2) log(N/2πe) + log(√det g(θ)/π(θ)) + o(1)` (Clarke & Barron 1990), and Jeffreys is
  asymptotically least favourable, with minimax redundancy
  `(D/2) log(N/2πe) + log ∫√det g + o(1)` (Clarke & Barron 1994) [recalled; settled by
  reading Clarke & Barron 1994]. Feeds spec 002 §3.4 (footnote on asymptotics) and the
  claim that `p*` tends to Jeffreys.

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Sibson 1969, "Information radius", *Z. Wahrscheinlichkeitstheorie verw. Geb.* 14:149–160 | unread | KL-centre and radius | glossary | – |
| Davisson 1973, "Universal noiseless coding", *IEEE TIT* [recalled] | unread | minimax redundancy | redundancy-capacity tutorial | – |
| Kemperman 1974, on the capacity of an arbitrary channel [recalled] | unread | equalizer, minimax redundancy = capacity | 002 §3.1 | – |
| Gallager 1979, "Source coding with side information and universal coding", MIT report | unread | Bayes codes under the capacity prior are minimax (finite alphabets) | 002 §2.1 | – |
| Ryabko 1979, "Coding of a source with unknown but ordered probabilities", *Probl. Inf. Transm.* 15(2):134–138 | unread | the same, independently | 002 §2.1 | – |
| Topsøe 1979, "Information-theoretical optimization techniques", *Kybernetika* 15(1):8–27 | unread; identity derived in 002 §9.1 | compensation identity | 002 (2.1.2) | – |
| Davisson & Leon-Garcia 1980, "A source matching approach to finding minimax codes", *IEEE TIT* 26(2):166–174 | unread | minimax code = Bayes code under the capacity prior | 002 §2.1 | – |
| Rissanen 1984, "Universal coding, information, prediction, and estimation", *IEEE TIT* 30(4):629–636 | unread | leading term `(D/2) log N`, any smooth prior | 002 §3.1 | – |
| Clarke & Barron 1990, "Information-theoretic asymptotics of Bayes methods", *IEEE TIT* 36(3):453–471 | unread | redundancy expansion for a given prior | 002 §3.4 | – |
| Clarke & Barron 1994, "Jeffreys' prior is asymptotically least favorable under entropy risk", *JSPI* 41(1):37–60 | unread | Jeffreys least favourable; minimax redundancy constant | 000 §1.5; 002 §3.4 | ☆ the main theorem; settles 002's footnote on asymptotics |
| Haussler 1997, "A general minimax result for relative entropy", *IEEE TIT* 43(4):1276–1280; preprint UCSC-CRL-96-26 | read §1–3 (preprint) | general minimax theorem; cumulative game; gambling reading | 002 §2.1, §3.1, score choice | ☆ abstract and §1, two pages |

## Links to other clusters

- **Capacity.** The same number seen from the channel side ([capacity-rate-distortion.md](capacity-rate-distortion.md)).
- **Bernardo's circle.** Clarke & Barron 1994 make "the reference prior is Jeffreys"
  rigorous in regular models [read: Komaki 2011 §1].
- **MDL.** Pointwise regret replaces expected redundancy; the asymptotic constants differ
  by `D/2` nats ([mdl-nml.md](mdl-nml.md)).
- **Komaki and Feder.** Both prove the conditional version of the minimax theorem
  ([komaki-school.md](komaki-school.md), [feder-group.md](feder-group.md)).
- **Learning curves.** The cumulative risk is the area under the learning curve
  ([learning-curves.md](learning-curves.md)).
- **Scoring and betting.** Haussler's gambling reading ([scoring-betting.md](scoring-betting.md)).

## Open questions

- Is the minimax code in spec 002's compact Gaussian setting exactly `m_{p*}`, not only a
  limit of mixtures? Expected for compact `Θ` with continuous `θ ↦ p_θ` [guess].
