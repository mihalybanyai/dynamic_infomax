# Bernardo's circle: reference priors

*Drafted by Claude on 2026-10-05 from passages read for spec 002 and from citing works.
Not yet reviewed by MB.*

## Question and central object

Which prior should one use when the data, not the analyst, are to decide? Jeffreys'
answer is invariance under reparametrisation; Bernardo's is to maximise the information
the experiment is expected to provide. The [reference prior](../GLOSSARY.md#reference-prior) maximises `I_π(Θ;X_{1:k})` in the
limit of infinitely many repetitions `k → ∞`, where it becomes [Jeffreys](../GLOSSARY.md#jeffreys-prior) in regular
one-parameter models. At finite `k` the same maximiser is spec 002's `p*`: the fork at
which this project and the Machta group leave Bernardo's road.

## Findings we use

- **Jeffreys.** `p_J ∝ √det g` follows from invariance under reparametrisation [read: A&M
  §1]; it ignores the data budget, since repeating the experiment rescales `g` but not
  `p_J` [read: A&M §2.1]. Feeds spec 002 §0 and §1.2.
- **The limit, and why it is taken.** A reference prior maximises the same mutual
  information as `p*`, in the limit of infinitely many repetitions [read: Bernardo 2005,
  preprint pp. 15–16]. The finite-`k` maximisers are discrete (Berger, Bernardo & Mendoza
  1989, not read), and Kass & Wasserman give that as Berger and Bernardo's reason for the
  limit [read: Kass & Wasserman 1996 p. 1355]. Bernardo's own reason is conceptual: the
  prior should maximise the information still missing relative to perfect knowledge,
  which only unlimited data approach [read: Bernardo 2005, preprint p. 16]. A&M reserve
  "reference prior" for the limit and object to calling `p*` one [read: A&M App. A.8].
  Feeds spec 002 §3.5, footnote on lineage.
- **The limit is Jeffreys** when there are no nuisance parameters (Clarke & Barron 1994)
  [read: Komaki 2011 §1, citing it]. Feeds spec 000 §1.5.
- **Ranked reference priors.** With several parameters ranked by interest, the less
  interesting ones are integrated out under their conditional prior before the more
  interesting ones get theirs. Ranking was introduced to avoid problems such as
  marginalisation paradoxes [read: Berger, Bernardo & Sun 2009 §1]. In the Neyman–Scott
  problem Jeffreys' variance estimate converges to half the truth, and ranking the
  variance first makes it consistent; the Berger–Bernardo formula gives the ranked prior
  [read: Kass & Wasserman 1996 §3.5.2]. Feeds spec 002 §3.5 (`p_ref`) and its footnote on
  the Schur complement.
- **Flat priors in many dimensions.** A flat prior on a many-dimensional normal mean
  badly overstates the mean's length [read: Stein 1959; Kass & Wasserman 1996 §4.2.2].
  Feeds spec 002 §1.2, footnote on everyday co-volume gradients.
- **Minimax prediction, proposed early.** Geisser (1979), in the discussion of Bernardo
  1979, proposed minimax prediction as an alternative to reference priors [read: Komaki
  2011 §1]. Komaki's latent information priors take this up ([komaki-school.md](komaki-school.md)).
- **Zellner's maximal data information prior** adds the prior's entropy to the average
  information in the data; its data term is not coupled through the mixture, so it is
  linear in the prior and differs from the reference prior (`notes/infomax_two_hats_and_directions.md`
  §9) [recalled]. A neighbouring construction, cited in the two-hats note.

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Jeffreys 1946, "An invariant form for the prior probability in estimation problems", *Proc. R. Soc. A* 186:453–461 | unread | invariance; `p_J ∝ √det g` | 000; 001; 002 | – |
| Stein 1959, "An example of wide discrepancy between fiducial and confidence intervals", *Ann. Math. Statist.* 30(4):877–880 | read | flat prior overstates a high-dimensional mean | 002 §1.2 footnote | – |
| Zellner 1977, "Maximal data information prior distributions" [recalled] | unread | a maxent–information hybrid prior | two-hats note §9 | – |
| Bernardo 1979, "Reference posterior distributions for Bayesian inference", *JRSS-B* 41(2):113–147 | unread | the reference prior, as a design device rather than a belief [recalled] | 000; 001; 002 | – |
| Geisser 1979, discussion of Bernardo 1979 | unread | minimax prediction as an alternative | link to Komaki | – |
| Berger, Bernardo & Mendoza 1989, "On priors that maximize expected information", in *Recent Developments in Statistics and their Applications* | unread | finite-`k` maximisers are discrete | 002 §3.5 footnote | – |
| Kass & Wasserman 1996, "The selection of prior distributions by formal rules", *JASA* 91(435):1343–1370 | read §3.5.2, §4.2.2, p. 1355 | ranked priors; Neyman–Scott; Stein; why the limit | 002 §1.2, §3.5 | ☆ §3.5.2 if `p_ref` matters to you |
| Bernardo 2005, "Reference analysis", *Handbook of Statistics* 25:17–90 ([preprint](https://www.uv.es/~bernardo/RefAna.pdf)) | read preprint pp. 15–16 | the definition as a limit, and Bernardo's reason for it | 002 §3.5 | ★ pp. 15–17: the fork this project takes the other branch of |
| Berger, Bernardo & Sun 2009, "The formal definition of reference priors", *Ann. Statist.* 37(2):905–938 | read §1 | why parameters are ranked | 002 §3.5 | – |

## Links to other clusters

- **Machta group.** Mattingly et al. keep the finite-`k` maximiser that Bernardo's limit
  discards ([machta-sloppy-models.md](machta-sloppy-models.md)).
- **Komaki school.** The `k`-reference prior is the latent information prior at `(0, k)`
  [read: Komaki 2011 §4]; Geisser's 1979 proposal is its ancestor.
- **Universal coding.** Clarke & Barron 1994 make the Jeffreys limit rigorous
  ([universal-coding.md](universal-coding.md)).

## Open questions

- What exactly do Berger, Bernardo & Mendoza 1989 prove about finite-`k` discreteness,
  and for which models?
