# Empirics

Which priors do humans and animals behave as if they used, and when? The specs ask what
budget-conscious priors such as `p*` achieve. This folder collects evidence and
candidate tests on whether behaviour looks like them, like volume-counting priors
(Jeffreys), or like uniform or learned priors. It is part of the same line of thinking
as the specs, but no spec depends on it.

Each lead below gets its own file once someone works on it.

## Leads

- **Perception vs deliberate judgement** (MB's hypothesis) [guess]. Evolved perception
  may weigh only what its senses resolve, as `p*` does. Deliberate, formal reasoning may
  count the distinctions it models, as the neutral observer of spec 002 §0 does.
  Related work: infomax as a principle of perceptual coding (Linsker 1988; Laughlin
  1981) [recalled]. Also support theory: splitting a hypothesis into more detailed
  sub-scenarios raises its judged probability (Tversky & Koehler 1994) [recalled].
- **Ranking versus budget** (MB's corollary). The co-volume bias can be removed by
  ranking the parameters by interest, an attention-like mechanism, or by
  budget-consciousness. Which do organisms use, where, and how well does each work?
  Spec 002 §3.5 compares the two priors on prediction; the behavioural question is open.
  Background: `notes/infomax_two_hats_and_directions.md` §2.6.
- **Instructions as a handed-over ranking.** Instructions that name the stimulus dimension
  that matters hand participants the ranking: spec 002's control where ranking is free
  (§3.5). Being told may help only when the ranking lies along named dimensions.
  Describing the optimal strategy before training raised final category-learning
  accuracy when the strategy was a rule on named dimensions (0.82 against 0.65), and left
  it unchanged when the strategy integrated them (0.80 against 0.80) [read: Rosedahl,
  Serota & Ashby 2021, abstract and results]. Their point that research asks how to give
  instructions rather than whether they help is the opening for this lead. Spec 002 §3.5's
  three cases (ranking handed over, computable, unavailable) suggest three instruction
  conditions. The third, where which dimension matters depends on the stimulus, may be
  close to context-dependent attention in category learning [guess]; to read: George &
  Kruschke 2012, and the signaling principle of instructional design (meta-analysis:
  Richter, Scheiter & Eitel 2016).
- **Repertoire dependence as a test.** A volume-counting prior's conclusions move with
  the size of a repertoire the evidence cannot see: spices known, faces known, tuning
  parameters modelled (spec 002, footnote `[^1-everyday]`). Do human estimates move with
  it? We know of no study.
- **The slow-speed prior in motion perception** as a possible co-volume gradient:
  [`slow_speed_prior.md`](slow_speed_prior.md).
- **Anticipated exposure and the coarseness of impressions.** If priors are built for
  the data one expects, impressions of a person one expects to meet once should be
  coarser and more extreme than of one expected to stay, on the same evidence. Laid out
  on three levels (everyday situation, experiment, spec 002's model), with existing
  results from cognitive tuning, construal level and the horizon task as targets:
  [`anticipated_exposure.md`](anticipated_exposure.md).
- **Block towers as a budgeted judgment.** People's judgments of whether a tower of
  blocks will fall are fitted by a simulator run on a few noisy copies of the scene, with
  position noise of 0.2 of a block's side [read: Battaglia, Hamrick & Tenenbaum 2013].
  That noise is a measured budget, and viewing time is a candidate way to vary it
  [guess]. Geometry and next steps are in
  [`notes/block-towers.md`](../notes/block-towers.md); parked until spec 002 is
  finished.
- **Older material**, written for spec 001's betting framing:
  [`real_world_analogues.md`](real_world_analogues.md) covers clinical
  trials, foraging, probability weighting and categorical perception.
