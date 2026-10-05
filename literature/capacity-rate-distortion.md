# Capacity and rate–distortion

*Drafted by Claude on 2026-10-05 from the specs, notes and tutorials that cite these
works; none of the works below has been opened in this repo. Not yet reviewed by MB.*

## Question and central object

How much information can a noisy channel carry, which input distribution achieves it,
and how is it computed? The [channel capacity](../GLOSSARY.md#channel-capacity) `C = sup_π I_π(Θ;X)` and its
capacity-achieving input are, read as a prior, spec 002's `p*`. The dual problem,
rate–distortion, optimises an encoder for a given source under a distortion cost; the
[Blahut–Arimoto algorithm](../GLOSSARY.md#blahut-arimoto-algorithm) computes both.

## Findings we use

- **Capacity-achieving inputs are often discrete.** For the scalar amplitude-constrained
  Gaussian channel the achiever has finitely many atoms (Smith 1971) [recalled: the paper
  could not be fetched]; Chan, Hranilovic & Kschischang 2005 extend this to conditionally
  Gaussian channels with bounded inputs [recalled: scope known from the title only]. The
  repo's 1-D Blahut–Arimoto recovers the two-atom regime below an interval of about 3.3
  noise standard deviations (`notes/infomax_two_hats_and_directions.md` §7.4). With a
  finite output alphabet the achiever is discrete (Witsenhausen 1980) [read: Fogel &
  Feder 2024 §II.A, citing it]. Feeds spec 002 §1.1 (`p*` discrete) and the footnote on
  atoms at the corners of the cross-sections (§1.2); spec 000's atoms.
- **Blahut–Arimoto.** Alternating maximisation computes capacity (Arimoto 1972; Blahut
  1972) and the rate–distortion function (Blahut 1972). Spec 000 uses it with an
  over-relaxed step (Vontobel 2003; Naja, Alajaji & Yanikomeroglu 2009); spec 002 §4.2
  extends it to several dimensions. Fogel & Feder 2024 build their solver on the
  accelerated form of Matz & Duhamel 2004 ([feder-group.md](feder-group.md)).
- **A sanity bound.** Capacity is at most `log |Y|` for an output alphabet `Y` (Cover &
  Thomas 2006, Thm 7.2.1). Feeds spec 000 test T3b.
- **Rate–distortion is the other dual of mutual information.** The two-hats note argues
  that questions about representations belong on the rate–distortion side, not the
  capacity side (`notes/infomax_two_hats_and_directions.md` §7.2). Feeds the notes, not
  the specs; rate–distortion agents are left for the map of adjacent areas
  ([README](README.md#clusters)).

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Shannon 1948, "A mathematical theory of communication", *Bell Syst. Tech. J.* 27 | unread | mutual information; capacity | all specs | – |
| Shannon 1959, "Coding theorems for a discrete source with a fidelity criterion", *IRE Natl. Conv. Rec.* | unread | rate–distortion | two-hats note §7 | – |
| Smith 1971, *Information and Control* 18(3):203–219 | unread (not fetched) | discrete achiever, scalar amplitude-constrained Gaussian channel | 002 §1.1, §1.2 | ☆ the main theorem, to hold the discreteness claim first-hand |
| Arimoto 1972, *IEEE TIT* 18(1):14–20 | unread | Blahut–Arimoto for capacity | 000 | – |
| Blahut 1972, *IEEE TIT* 18(4):460–473 | unread | Blahut–Arimoto for capacity and rate–distortion | 000; 002 §4.2 | – |
| Witsenhausen 1980, "Some aspects of convexity useful in information theory", *IEEE TIT* 26(3):265–271 | unread | finite output alphabet ⇒ discrete achiever | redundancy-capacity tutorial | – |
| Vontobel 2003, "A generalization of the Blahut–Arimoto algorithm", Allerton | unread | step-size variants and their convergence | 000 §3.4 | – |
| Matz & Duhamel 2004, "Information geometric formulation and interpretation of accelerated Blahut–Arimoto-type algorithms", IEEE ITW, 66–70 | unread | accelerated Blahut–Arimoto | Feder group's solver | – |
| Chan, Hranilovic & Kschischang 2005, "Capacity-achieving probability measure for conditionally Gaussian channels with bounded inputs", *IEEE TIT* 51(6):2073–2088 | unread | discreteness beyond Smith's setting | 002 §1.1 | – |
| Cover & Thomas 2006, *Elements of Information Theory*, 2nd ed., Wiley | Thm 7.2.1 used | `C ≤ log \|Y\|` | 000 T3b | – |
| Naja, Alajaji & Yanikomeroglu 2009, "Accelerating the Blahut–Arimoto algorithm", ISIT | unread | over-relaxation speeds it up 2–10× | 000 §3.4 | – |

## Links to other clusters

- **Universal coding.** Capacity equals [minimax](../GLOSSARY.md#minimax) redundancy, which turns the channel
  problem into a prediction problem ([universal-coding.md](universal-coding.md)).
- **Machta group.** `p*` is the capacity-achieving input of the experiment's channel,
  computed by Blahut–Arimoto (Mattingly et al. 2018); Abbott & Machta 2019 study how its
  atoms turn continuous as noise falls ([machta-sloppy-models.md](machta-sloppy-models.md)).
- **Feder and Komaki.** The conditional objectives are solved by Blahut–Arimoto variants
  ([feder-group.md](feder-group.md)).

## Open questions

- Is `p*` discrete in multi-dimensional Gaussian models? A&M call it "usually discrete"
  [read: A&M §1]; no theorem for that case is in the repo.
