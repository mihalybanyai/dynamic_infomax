# Anticipated exposure and the coarseness of impressions

*Opened 2026-10-29, from the budget thread (`notes/budget-value-of-information.md`);
restructured the same day around three levels. Impressions of individual people, chosen
as an everyday setting with no political reading. Claude's draft from a chat with MB.*

**Claim.** If priors are built for the data one *expects*, as `p*` is, then the same
evidence about a person should yield a coarser, more extreme impression when little
further exposure is expected. The case rests on three levels: an everyday situation, a
stripped-down experiment, and spec 002's formal model. The mappings between them are the
subject of this file (§2). **To decide:** whether the gaps in §2 are acceptable, and which
existing results in §3 to model first.

## 1. The three levels

| Level | What it is | Role |
|---|---|---|
| **E**, everyday | Impressions of someone's temper after one or two provocations, for a plumber you will see once and for a new flatmate. Upset decays with a quick flare and a slow grudge. | Builds intuition; nebulous, embedded in the rest of life |
| **X**, experiment | Aliens whose glow after a poke is `y(t) = a_1 e^{−k_1 t} + a_2 e^{−k_2 t}` plus Gaussian noise, at fixed sample times. Everyone sees the same `N` pokes of an alien, then is told truthfully that `9N` more pokes of *this* alien will follow, or none. Control: `9N` more pokes of a *different* alien. Measures: bets on the next poke's glow; the drawn expected curve; sorting aliens into kinds; how extreme the rate estimates are. | Every variable of stimulus generation is known and set |
| **M**, model | Spec 002's exp-decay family at `D = 2`. An agent expecting `10N` pokes in all is `p*_{10N}` scored at budget `N`; one expecting no more is `p*_N`. A Bayesian with any fixed prior predicts no effect of the announcement, since the current posterior does not depend on future data. | Simulations and quantitative predictions |

The predicted direction at M [guess, until simulated]: when few pokes are expected, the
representation sits on the model's boundary, with one timescale, or decay that is
"instant" or "never". When many are expected, it uses two timescales and moderate rates.
On a barely resolved direction the coarse representation takes the two *extremes*
(`notes/infomax_two_hats_and_directions.md` §7.4), where a rate–distortion code would take
the quartiles.

## 2. The mappings, and where they could fail

### X ↔ M: formal, exact by construction, with gaps in the readout

*Exact.* Stimulus generation is spec 002's exp-decay model (A&M Eq. 6) with `D = 2`, fixed
amplitudes and fixed sample times. The announcement sets the budget the prior is built
for: `p*_{10N}` against `p*_N` at the same `N`, which spec 002 already carries as its
mis-budgeted agent `p*_{10N}` (§2.2). The bets map onto spec 002's one-step score `r_N`.
Mattingly et al. computed `p*` for this model and place the change from one relevant
parameter to two between `σ = 1/7` and `σ = 1/50`, about 50 times more data [read:
Mattingly 2018, exp-decay discussion]. That fixes where to set `σ` and `N` so that the
two conditions straddle the change.

*Could fail.*
- **The readouts other than bets have no counterpart in spec 002 yet:** the effective
  number of timescales, the kinds, the extremity. Spec 002 would need a readout of the
  representation, for example the posterior's effective dimension.
- **`D = 2` may give too weak a gradient.** In the cone the budget's effect grew with `D`
  (budget note §3.3); a three-timescale alien may be needed.
- **Competitors need predictions of their own.** A fixed-prior Bayesian predicts no
  effect. An engagement or effort effect is addressed by the different-alien control.
  Simple heuristics are not yet specified.
- **Participants must believe the announcement**, which is why it has to be truthful.

### E ↔ X: informal, argued

*Argument.* E and X share the generative structure (recovery from a provocation on two
timescales), the kind of evidence (a few noisy episodes) and the manipulation (expected
further episodes). X strips out social priors, stakes and communication on purpose.

*Could fail.*
- **Two timescales in everyday temper.** Recovery speed is treated as one dimension of
  emotional style [recalled: Davidson's affective chronometry], but two separable
  timescales that observers track is our assumption [guess].
- **Curve or disposition.** People may treat the glow as a perceptual curve rather than a
  temperament. Framing it as temper and asking dispositional questions should help.
- **Explicitness.** Everyday expectations of exposure are vague and often implicit; X
  states them outright.
- **No exact everyday measure.** An extreme label ("hothead") has no exact counterpart in
  X; sorting and extremity are proxies.

### E ↔ M: only through X, and through existing results

There is no direct formal mapping from E to M. The results in §3 are the only evidence
that touches E without new data, and each brings its own mapping problem.

## 3. Existing results usable as targets

Studies whose manipulations act like a change in expected exposure without an
invalidating confound, whatever question they were asking. The statuses come from
abstracts and secondary summaries found by web search; no original was opened.

| Study | Manipulation | Measure | As expected exposure | Status |
|---|---|---|---|---|
| Cognitive tuning: Zajonc 1960; Cohen 1961; Leventhal 1962 | set to receive more information, or to transmit one's impression | polarisation; unity of the impression | receivers expect more data, but transmitters also have a communication goal | confounded: Lassiter, Geers & Apple 2002 find the effect comes from transmitting |
| Outcome dependency: Erber & Fiske 1984; Neuberg & Fiske 1987 | depending on the person | individuation | expected interaction bundled with stakes | explained by motivation |
| Construal level, probability: Wakslak, Trope, Liberman & Alony 2006 | unlikely or likely events | abstractness; fewer categories | the cleanest: an unlikely encounter means little expected data | one replication failed (Calderon et al. 2020) |
| Construal level, time: Liberman, Sagristano & Trope 2002 | distant or near future | fewer, broader categories in sorting | ambiguous, see below | not checked |
| Construal level, persons: Nussbaum, Trope & Liberman 2003 | predicting distant or near-future behaviour | more dispositional prediction; more expected cross-situational consistency; seeking broad-disposition information | a coarser model of a person for distant use; same ambiguity | not checked |
| Horizon task: Wilson, Geana, White, Ludvig & Cohen 2014 | 1 or 6 future choices | directed exploration and decision noise, both rising with the horizon | exactly an expected budget, but each option is a 1-D mean, where the budget's effect on representation should be small (budget note §3.1, grimoire entry 6) | a negative constraint: explore–exploit already explains it, and the model must not predict large representational effects here; data availability unclear |

**The mapping question construal level raises.** Two readings of "budget" give opposite
predictions for temporal distance:
- **The data available before the representation is used.** A distant event leaves more
  time to learn, so an anticipatory prior should be *finer*, contrary to construal level.
- **The exposure one typically gets to the target itself.** Distant, unlikely or remote
  targets usually come with less detail, so the prior is built for less. This is
  consistent with construal level.

Which reading people follow is open. The probability manipulation fits the second most
cleanly, but its one replication failed. Any model of the construal-level results has to
commit to a reading, and that choice is the main weakness of using them as targets.

## 4. Related, kept separate

What happens when the realised exposure differs from the expected one, as when an
acquaintance expected to be brief lasts, is the daisy chain's misspecification signal
(`notes/daisy_chain_derivation.md` §7.1). It presupposes the anticipatory effect above.

## References

- Zajonc, R. B. (1960). The process of cognitive tuning in communication. *Journal of
  Abnormal and Social Psychology* 61, 159–167.
- Cohen, A. R. (1961). Cognitive tuning as a factor affecting impression formation.
  *Journal of Personality* [CITATION NEEDED: volume and pages].
- Leventhal, H. (1962) [CITATION NEEDED: title and journal].
- Lassiter, G. D., Geers, A. L. & Apple, K. J. (2002). Communication set and the
  perception of ongoing behavior. *Personality and Social Psychology Bulletin* 28(2).
- Erber, R. & Fiske, S. T. (1984). Outcome dependency and attention to inconsistent
  information. *Journal of Personality and Social Psychology* 47(4), 709–726.
- Neuberg, S. L. & Fiske, S. T. (1987) [CITATION NEEDED: title and journal].
- Wakslak, C. J., Trope, Y., Liberman, N. & Alony, R. (2006). Seeing the forest when
  entry is unlikely: probability and the mental representation of events. *Journal of
  Experimental Psychology: General* 135(4), 641–653.
- Calderon et al. (2020), replication of Wakslak et al. (2006) [CITATION NEEDED: full
  reference].
- Liberman, N., Sagristano, M. D. & Trope, Y. (2002). The effect of temporal distance on
  level of mental construal. *Journal of Experimental Social Psychology* 38, 523–534.
- Nussbaum, S., Trope, Y. & Liberman, N. (2003). Creeping dispositionism: the temporal
  dynamics of behavior prediction. *Journal of Personality and Social Psychology* 84(3),
  485–497.
- Trope, Y. & Liberman, N. (2010). Construal-level theory of psychological distance.
  *Psychological Review* 117(2), 440–463.
- Wilson, R. C., Geana, A., White, J. M., Ludvig, E. A. & Cohen, J. D. (2014). Humans use
  directed and random exploration to solve the explore–exploit dilemma. *Journal of
  Experimental Psychology: General* 143(6), 2074–2081.
- Mattingly, H. H., Transtrum, M. K., Abbott, M. C. & Machta, B. B. (2018). Maximizing the
  information learned from finite data selects a simple model. *PNAS* (`resources/`).
