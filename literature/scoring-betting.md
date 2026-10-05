# Scoring and betting

*Drafted by Claude on 2026-10-05 from specs 001 and 002, the Kelly tutorial and
Haussler's preprint. Not yet reviewed by MB.*

## Question and central object

How should probabilistic predictions be scored, and what does a score mean for someone
who acts on the predictions? The log score is [strictly proper](../GLOSSARY.md#proper-scoring-rule), equals [code length](../GLOSSARY.md#code-length), and
equals the log-wealth of a Kelly bettor, so spec 002's redundancy is at once a
prediction score, a coding cost and a betting loss.

## Findings we use

- **The log score is strictly proper:** reporting the true predictive uniquely optimises
  it (Gneiting & Raftery 2007). Feeds spec 002 §2.1 and §2.3: the matched prior is the
  ceiling.
- **Kelly betting.** Maximising expected log-wealth gives the Kelly fraction, and the
  growth rate of wealth equals an information rate (Kelly 1956) [recalled]. Spec 001
  scored `p*` this way; for a binary outcome the Kelly log-wealth on the next toss is the
  log score of the posterior predictive plus `log 2`. Feeds spec 001; `tutorials/math/kelly.md`.
- **Redundancy as lost wealth.** The cumulative relative-entropy risk is the expected
  loss in log compounded wealth from not knowing `θ` [read: Haussler 1996 preprint §1].
  So `R_N` is the wealth lost over `N` bets placed while learning, and `r_N` the loss on
  one bet placed after learning. Feeds the spec 002 score choice.
- **Prequential scoring.** Predict each observation from the ones before it, then reveal
  it (Dawid 1984); the cumulative log score of a Bayesian's sequential predictions is the
  code length of its [Bayes mixture](../GLOSSARY.md#bayes-mixture) (see [prequential](../GLOSSARY.md#prequential)). Feeds spec 002 eq. (2.1.4).
- **The growth curve.** Thorp's Fig. 1, the even-money growth rate `g(f)` against the
  bet fraction `f`, is spec 001's eye-test reference (Thorp 2006).

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Kelly 1956, "A new interpretation of information rate", *Bell Syst. Tech. J.* 35(4):917–926 | unread | log-optimal betting | 001 | – |
| Dawid 1984, "Statistical theory: the prequential approach", *JRSS-A* 147(2) | unread | prequential scoring | 002 (2.1.4) | – |
| Thorp 2006, "The Kelly criterion in blackjack, sports betting, and the stock market", in *Handbook of Asset and Liability Management*, vol. 1, 385–428 | Fig. 1 used | the growth-rate curve | 001 eye test | – |
| Gneiting & Raftery 2007, "Strictly proper scoring rules, prediction, and estimation", *JASA* 102(477):359–378 | unread | the log score is strictly proper | 001; 002 §2.1 | – |
| MacLean, Thorp & Ziemba 2010, *The Kelly Capital Growth Investment Criterion*, World Scientific | unread | modern reference on Kelly | 001 | – |

## Links to other clusters

- **Universal coding.** Haussler's gambling reading ([universal-coding.md](universal-coding.md)).
- **Learning curves.** Cumulative versus one-step scoring ([learning-curves.md](learning-curves.md)).
