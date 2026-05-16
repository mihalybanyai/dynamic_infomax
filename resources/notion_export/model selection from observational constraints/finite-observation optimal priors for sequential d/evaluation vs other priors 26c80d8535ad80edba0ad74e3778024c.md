# evaluation vs other priors

script for testing expected utility for various priors in a coin toss model: [https://github.com/mihalybanyai/infomax/blob/main/infomax_class.py](https://github.com/mihalybanyai/infomax/blob/main/infomax_class.py)

one thing:

- demonstrate that this idea solves some problem that would be difficult to solve otherwise
- what is such a problem?
- you could say that making a representational decision is something, when all the other algorithms don’t do such a thing, but this is weak sauce
- can be something wildly impractical as well, just as a proof of principle
- so what are even dramatic examples of this framing-like operations from humans?
    - and not the analogy part, because that seems complementary
    - so there should be some search space that you could not slice through reasonably without additional information, and choosing randomly doesn’t work
    - there could be other examples where a search space is effectively constrained by additional information through algorithmic computation, maybe those can infer this case as well
    - self referentiality can be a staple here, i.e. when deciding which problem is best to be solved you have to first solve all of them
        - this might be a good direction to look: a heuristic of solvability is exactly what the MI is
        - and all the computational and similar constraints ultimately play into the MI as well, as bottlenecks for the bits that come through

new understanding: you can always choose arbitrarily many tasks in which one representation wins over any other. so this is not interesting. what would potentially be is if you could delineate some task property that is always present in the class of tasks in which a particular representation doesn’t work, e.g. they involve some sort of infinity, or some other ecologically nonsensical stochasticity or some other thing. this would be good, but potentially difficult

TODO

- what about regrets? can I get around having to specify an eval horizon by instead arguing about how regret grows wrt an optimum?
- what about the jeffreys prior in terms of utility for various utility functions, vs the conjugate, maxent, etc, for various N-s
- what’s the deal in higher dimensions? it might be the case that things have to be close to deterministic only in the very simple setting
- what about an RL setting?
- non-ergodicity

**relevant ideas:**

- evaluation on expectations might not be straightforwardly the right thing to do
- of course, ergodicity

- **does it come out ahead in purely log-likelihood terms?**
    - overfitting: for 1 datapoint, you will overfit completely. and even for more, you will overfit as much as possible while maintaining a bayesian posterior. does this inform in any way the bias-variance dilemma dilemma?
- somehow it doesn’t fell right to evaluate using “true” probabilities on a finite sample. those don’t really exist without assuming the sampling process, and it’s exactly those that I want to figure out.
    - so is it correct to assume that the sample came as a finite iid sample from a potentially infinite source that has these probabilities as its properties?
    - what else can we do?
    - is this what the mutual information objective does?
    - two extremes could be the sample being an unbiased one from a true model capable of generating infinite samples with the same statistics, and the case when the sample is the totality of information that could have come from the source
        - but then the infomax objective is one of these extremes, isn’t it? - not exactly. the absolute extreme is learning to repeat the same series of observations forever. there is still a posterior and a likelihood with the infomax case
- it confers an advantage for extreme probabilities in terms of utility
    - does this correspond to the assumption that either probabilities or utilities naturally exist on a log scale?
    - does the advantage change with more outcomes? sparse ones?
        - what about continuous ones?
        - what about dimensionality? that sort of lower the effective sample size I guess
            - one of the main points of abbott is that **superfluous latent dimensions** are very harmful. maybe introducing one irrelevant latent dimension can show a big advantage?
                - e.g. 3 possible observations, 1 latent driving 1 vs (2, 3), and the other driving 3 vs (1,2)
                - it should be possible to set these so that they are differentially important in explaining observation variability
                - what are the **multiparameter examples in abbott**?
                - this paper: [https://www.mdpi.com/1099-4300/25/3/434](https://www.mdpi.com/1099-4300/25/3/434)
            - what about Sims though?
    - az mindenképpen benne van, hogy meg akarom adni a lehetőséget, hogy nincs is variancia valójában, és ha ezt tapasztalom, arra határozottan akarok tudni reagálni
        - ez a dimenziócsökkentés esetében releváns
- the advantage does increase for lower N.