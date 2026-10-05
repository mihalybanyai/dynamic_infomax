# Learning curves and predictive information

*Drafted by Claude on 2026-10-05 from abstracts and a derivation from the 2026-10-05
discussion of spec 002's score. Not yet reviewed by MB.*

## Question and central object

How does what is learned, or what prediction still costs, change with the number of
observations `N`? The central object is the learning curve `r_i`, the expected excess
log-loss on observation `i+1` after `i` observations, and its running sum, the cumulative
risk `R_N = Σ_{i<N} r_i`. Under one's own prior the sum is the mutual information
`I_π(Θ;X_{1:N})`, and in identifiable models it equals Bialek, Nemenman & Tishby's
predictive information.

## Findings we use

- **Information is the area under the learning curve.** By the chain rule,
  `I_π(Θ;X_{1:N}) = Σ_{i<N} I_π(Θ;X_{i+1}|X_{1:i})`, and each term equals
  `𝔼_{θ∼π} 𝔼 D_KL(p(·|θ) ‖ m_π(·|X_{1:i}))`, the Bayes agent's expected excess log-loss
  on step `i+1` when nature follows its own prior. So maximising the information learned
  from `N` observations (Mattingly et al.) maximises the total surprise over `N` bets.
  Feeds the spec 002 score choice.
- **Learning has diminishing returns.** Under one's own prior the information per step
  never increases:
  `I(Θ;X_{i+2}|X_{1:i+1}) = I(Θ;X_{i+1}|X_{1:i}) − I(X_{i+1};X_{i+2}|X_{1:i})`, by
  exchangeability and conditional independence given `θ`. The decrement is what one
  observation says about the next. Under a foreign nature this monotonicity can fail: a
  discrete prior's step loss levels off when `θ` sits between atoms. Haussler, Kearns &
  Schapire 1994 study the per-step ("instantaneous") information gain [recalled].
- **Predictive information.** `I_pred(T)`, the mutual information between the past and
  the future of a series, stays finite, grows logarithmically, or grows as a power; for a
  model with finitely many parameters it grows logarithmically with a coefficient that
  counts the dimension, and its divergent part measures complexity [read: Bialek,
  Nemenman & Tishby 2001, abstract]. For i.i.d. data from an identifiable model,
  `I(X_{1:N}; future) = I_π(Θ;X_{1:N})`: past and future are independent given `θ`, and
  the infinite future determines `θ`, so data processing gives the inequality both ways.
  Mattingly's `p⋆` is therefore the prior that maximises the predictive information of
  `N` observations. In sloppy models `θ` is replaced by the distribution `p_θ` it
  indexes.
- **Bounds on cumulative risk.** Haussler & Opper 1997 bound mutual information and
  cumulative relative-entropy risk by metric entropy [recalled]. Feeds spec 002 §3.1's
  growth of `C_N`.
- **An exact learning curve.** For multinomials the minimax cost of step `k` after `N`
  observations is `(m−1)/(2(N+k))` to leading order ([feder-group.md](feder-group.md)).

## Works

| Work | Our status | Finding we use | Feeds | You read? |
|---|---|---|---|---|
| Haussler, Kearns & Schapire 1994, "Bounds on the sample complexity of Bayesian learning using information theory and the VC dimension", *Mach. Learn.* 14(1):83–113 | unread | instantaneous versus cumulative information gain [recalled] | 002 score choice | ☆ if the per-step view becomes central |
| Haussler & Opper 1997, "Mutual information, metric entropy and cumulative relative entropy risk", *Ann. Statist.* 25(6) | unread | bounds on cumulative risk [recalled] | 002 §3.1 | – |
| Bialek, Nemenman & Tishby 2001, "Predictability, complexity, and learning", *Neural Comput.* 13:2409–2463; arXiv:physics/0007070 | abstract | predictive information; its logarithmic growth counts parameters | 002 score choice; project framing | ★ MB's request |

## Links to other clusters

- **Universal coding.** The cumulative risk is Haussler's game ([universal-coding.md](universal-coding.md)).
- **Feder and Komaki.** Each window of the learning curve has its own minimax prior
  ([feder-group.md](feder-group.md), [komaki-school.md](komaki-school.md)).
- **Machta group.** `p⋆` maximises the area under its own learning curve.

## Open questions

- In sloppy models, how does predictive information split between stiff and sloppy
  directions, and does `p⋆` maximise the stiff part?
