# model selection from observational constraints

[finite-observation optimal priors for sequential decision making](model%20selection%20from%20observational%20constraints/finite-observation%20optimal%20priors%20for%20sequential%20d%2022280d8535ad8043a4fbccdc3463c1da.md)

task inference

- ádám és barna cuccosában a látensek instantaneousak, és amire a hosszabb időskálájú inferencia vonatkozik, ahol van értelmezhető N, az a task mibenléte
- ekkor nem a diszkretizáció lesz érdekes, hanem valami véges lehetőség közül a választás, de ezzel technikai probléma nincs
- igazából ez ráültethető egyből a transzfer témára is, lindánál nem vagyok biztos, de lehet, hogy ott is
- viszont: mi a likelihood ebben az esetben?
    - ez valahogy el fogja kódolni azt, hogy a cue mennyire teszi valószínűvé melyiket
    - viszont annak is ebben kéne lennie, hogy mennyi adat mennyire fogja tudni constrainelni a látenseket, azaz a taskot
    - itt valahogy össze kell kötni azt, hogy ha sikerül alacsony posterior uncertaintyt elérni, akkor valószínűbb, hogy ez volt a task, mint ha nem

neil

- diagnostics about subparts - deciding which quesitons to ask, discretisation
- short-horizon resource rationality paper
- representational complexity is traded off against computational cost, fred callaway, prob. preprint, josh too
- adjacent possible is post-prcessing dependent infomax
    - it is sort of complementary to our thing, but aims at asking the right quesiton
- says that non-ecological tasks are not infomax strictly, but valid ones are

- mi → IB → VAE → GCRL (kaelbling?) → subtask, Sutton reward respecting
    - [https://proceedings.mlr.press/v139/choi21b.html](https://proceedings.mlr.press/v139/choi21b.html)
    - eric, peter, ben eysenbach: [https://arxiv.org/pdf/2605.06145](https://arxiv.org/pdf/2605.06145)
    - goal generation: https://proceedings.mlr.press/v80/florensa18a/florensa18a.pdf
    - contrastive as goal-conditioned [https://proceedings.neurips.cc/paper_files/paper/2022/file/e7663e974c4ee7a2b475a4775201ce1f-Paper-Conference.pdf](https://proceedings.neurips.cc/paper_files/paper/2022/file/e7663e974c4ee7a2b475a4775201ce1f-Paper-Conference.pdf)
- timescale follows, from daisy chain, it’s an inverse slow feature anlysis, evolution connects this way too
- the non-fluidity comes from the asymmetry. symmetry breaking is structure. but structure is rigid, and must correspond to something. or not?
- kemp cikk beszél a diszkréten megjelenő új kategóriákról, supporting info: [https://www.pnas.org/doi/full/10.1073/pnas.1800521115](https://www.pnas.org/doi/full/10.1073/pnas.1800521115)

TODO:

- Oana: reward function miért túl könnyű?
- How to think about inference timescales?
    - There are instantaneously inferred quantities, inferred from 1 observation, but they are still not binary
    - they are expected to continually change though
    - so is there some kind of stability assumption also involved here?
    - or the fact that we typically don’t do much with an instantaneously inferred thing?
        - but sometimes we do
        - EC deals with those though
    - what do you actually want to maximise mutual information with?
        - it seems that with instantaneous latents you don’t want to do that
        - maybe it’s a value of information thing? can we go from the RL angle?
    - if we have a slow-feature-type picture of the world, on what level does something like the infomax objective come in?
        - it seems to have something to do with decision making as well
        - even though it wasn’t straigthforward to show that this objective is good for all decision making situations.
        - decision making can climb up and down the hierarchy, rich turner-style
        - a fairly general setup: on instantaneous latent, one slow-moving one (a context or something) and one static one (this might be a parameter)
            - probably the best target for our approach is the middle layer
- Within trial urgency: when it’s about gathering information instead of purely internal computation it’s a lot closer!
    - There are a lot of papers about this; any representational ones?
    - Optimal search in eye movements
    - Optimal stopping in information search?

split-merge: [https://proceedings.mlr.press/v54/gardner17a/gardner17a.pdf](https://proceedings.mlr.press/v54/gardner17a/gardner17a.pdf)

foraging: [https://www.biorxiv.org/content/10.1101/2025.07.04.663150v1](https://www.biorxiv.org/content/10.1101/2025.07.04.663150v1) 

How does one corroborate the assumption that representations are important?

- maybe don’t call them representations
- the word comes from machine learning, where it has a clear meaning which is in some ways the opposite of the cognitive science meaning
    - it’s just the transformation of the input that makes it easier to learn something like value or a policy on top of it
    - with this comes intuition about algorithmic complexity for e.g. value learning, that makes it basically inevitable in practice that something like this has to happen
- then comes the interpretation part, which basically says that this intermediate transformation is the same thing that underpins concepts, objects, etc. cognitively
    - and then the assumption that these exist in a somewhat task-independent manner, at least in the sense that they persist after the task is gone, and may serve as an initial condition for the next one
    - here there is a connection to the transfer/generalisation literature
- but all this is basically computational intuition, not underpinned by any empiricism, and somewhat arbitrarily following from machine learning’s architectural choices regarding the details
- the minimum requirement to ensure that all this makes sense would be that people are actually building such representations, at least temporally locally
- actually, the cogtom paper is some amount of evidence for this
- are all the bayesian results evidence in the sense of combining a prior requires that prior to exist a priori?
    - that could exist on the level of actions as well in principle
- **and also that learning deficits come from not trying to learn using the right abstractions**
    - this is very intuitive from everyday life, but how can you pin it down?
        - Anne Collins - Gershman world?
        - griffiths world? maybe some experiment does address this
        - Wiktor: is it just a threshold, above which you are ok, or is there an optimum above which it gets worse again?
    - and also that abstractions not only exist as action abstractions, i.e. options and the like, but perceptual abstractions as well
    - this is linguistically somewhat supported, but might be hard to disentangle if we consider that language is action
- **this is trivial, as the mapping to policy is always more complicated with the incorrect representation**
    - dinamically still interesting? 3-state RL problem

- TODO
    - Regret-based eval
    - How can we get closer to an empirically clear assessment of what the phenomenon even is?
        - this should clarify the videogame idea in measurability as well
    - a jövő határozza meg, hogy milyen kérdéseket tudok föltenni, a múlt csak azt, hogy erre milyen válaszokat fogok adni
        - MIért??!!!?
        - Mit kell csinálnom ahhoz, hogy ez ne így legyen?
    - hogy mennyit tudok tanulni N megfigyelésből, az egy **model misspecification** mérőszám
    - simulate how do the two informational components trade off against each other
        - okay something doesn’t normalise properly
        - **shouldn’t there be an 1/M in the first place?** sure seems like it
        - still with that KLs are way higher than in the static case, infing out on the regular
        - there is some sort of a positive feedback loop that doesn’t come to effect in the M=0 case
        - **the probability ratios are getting very large** - those look a bit suspicious in the first place, they break form with the KL
            - **try out not dividing by the marginal outside of the log**
    - handle the m=0 case
        - seems like I have to set p(X^m)=1 to get back the original
    - evaluate further using the todo items in the evaluation page
- GET FEEDBACK
    - 

[measurability](model%20selection%20from%20observational%20constraints/measurability%2022280d8535ad8024a647fa8eb67700f0.md)

- TODO
    - calculate the learnability of specific latents using the formulas
    - simulation to figure out how much data we need to be able to compare two conditions

[connection to efficient coding](model%20selection%20from%20observational%20constraints/connection%20to%20efficient%20coding%2022280d8535ad808abc15eaee88624b52.md)

- TODO
    - how does this not get so flexible that it cannot be constrained?

[normative hierarchies](model%20selection%20from%20observational%20constraints/normative%20hierarchies%2022280d8535ad80bc96d4c40c3a70efa8.md)

- TODO
    - what differentiates policy-level habit formation from the representational counterpart?
    - what is the right word to use for the latter?

[birds-eye view](model%20selection%20from%20observational%20constraints/birds-eye%20view%2022280d8535ad801da58cc27657e31085.md)

Potential student projects:

- explore the evaluation landscape

![image.png](model%20selection%20from%20observational%20constraints/image.png)

https://x.com/docmilanfar/status/1948592329390260571

[https://x.com/docmilanfar/status/1977550570790719617](https://x.com/docmilanfar/status/1977550570790719617)

![image.png](model%20selection%20from%20observational%20constraints/image%201.png)

[writing notes](model%20selection%20from%20observational%20constraints/writing%20notes%202b380d8535ad8006839fe99f3f330a12.md)