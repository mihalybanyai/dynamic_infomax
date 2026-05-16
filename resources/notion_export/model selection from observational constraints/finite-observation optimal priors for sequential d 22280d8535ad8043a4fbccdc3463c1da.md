# finite-observation optimal priors for sequential decision making

Some intro and equations: [https://www.overleaf.com/project/67e6b295ffbc59a2071a3bdf](https://www.overleaf.com/project/67e6b295ffbc59a2071a3bdf)

Notebook with formulas and code: [https://github.com/mihalybanyai/infomax/blob/main/sequential_infomax.ipynb](https://github.com/mihalybanyai/infomax/blob/main/sequential_infomax.ipynb) 

Common doc that has a lot of exposition: [https://docs.google.com/document/d/19c29Vk7j_W8i_gIJkArIZV1b3-zW4_De_rS3S7f6fyM/edit?pli=1&tab=t.0#heading=h.bu1stjo2qfwj](https://docs.google.com/document/d/19c29Vk7j_W8i_gIJkArIZV1b3-zW4_De_rS3S7f6fyM/edit?pli=1&tab=t.0#heading=h.bu1stjo2qfwj)

[various discussion points](finite-observation%20optimal%20priors%20for%20sequential%20d/various%20discussion%20points%2026c80d8535ad80a4b79ed2c8a1005328.md)

[evaluation vs other priors](finite-observation%20optimal%20priors%20for%20sequential%20d/evaluation%20vs%20other%20priors%2026c80d8535ad80edba0ad74e3778024c.md)

[MI as RP](finite-observation%20optimal%20priors%20for%20sequential%20d/MI%20as%20RP%202e080d8535ad8077923cc6b14b34da3d.md)

TODO PETER:

- check if the KL between prior and posterior is actually maximal for p*
- check the betting game performances for n>2, where there are more than 2 atoms. does the determinism-leaning persevere there too?
- MI as RP points

TODO

- Pedro Ortega: With rigorous model of metareasoring you get a hierarchy of reasoning about reasoning. Harsanyi showed us that these cognitive hierarchies are resolved using random beliefs.
    - John C. Harsanyi, 1967. "Games with Incomplete Information Played by "Bayesian" Players, I-III Part I. The Basic Model," Management Science, INFORMS, vol. 14(3), pages 159-182, November. [https://www.jstor.org/stable/pdf/30046151.pdf?casa_token=D6xPZW6KhBgAAAAA:JARdfXiIvQWNX1zS6tYIy-ltyzuk4SfS8A-VHvhqeg1b4Z6mDlKyuEO4zmCeKVZFK3-QKhgY-UjRp-8Xst2Etlk5fN2CxL305W83aa49yX3n6QsKYURc](https://www.jstor.org/stable/pdf/30046151.pdf?casa_token=D6xPZW6KhBgAAAAA:JARdfXiIvQWNX1zS6tYIy-ltyzuk4SfS8A-VHvhqeg1b4Z6mDlKyuEO4zmCeKVZFK3-QKhgY-UjRp-8Xst2Etlk5fN2CxL305W83aa49yX3n6QsKYURc)
- ÁDÁM: [https://github.com/mihalybanyai/infomax/blob/main/Whiteboard 13.pdf](https://github.com/mihalybanyai/infomax/blob/main/Whiteboard%2013.pdf)
- a KL a poszterior és prior között konzisztens
    - ha nem tudok annyit tanulni, mint amit gondoltam, hogy fogok, az arrra utal, hogy a modellem nem tartalmaz valami változót, vagy rosszm a függyvényformája, etc.
- hogy mennyit tudok tanulni N megfigyelésből, az egy **model misspecification** mérőszám
    - **L gábor: új kontextust vezet be hasonló esetben! mit thresholdol meg ő és mit mi?**
- emiatt kell, hogy legyen róla sok irodalom
    - pl volatility is kapcsolódhat
- optimising a similar objective over the data is active learning: [https://arxiv.org/pdf/1112.5745](https://arxiv.org/pdf/1112.5745)
- Bayesian optimal experiment design when we ask what question is to be answered with a fixed setup is very similar to what we do
    - albeit OED is mostly the flip side, when the question is fixed and not the setup
    - both could actually be relevant in a niche construction way
    - there could be multiple **bootstrapping schemes** that work similarly, like the 3A idea, and maybe there is a meta-pattern here (unifying review?)
- Alemi broken elbo azt mondja, hogy a non-identifiability MI-vel feloldható, ez lehet, hogy kapcsolódik a misspecification feloldhatóságához

TODO/ÁDÁM/TÜNDE

- theta entrópiája ne legyen minél kisebb?
    - ez nem valósul meg automatikusan?
- az m minta az sztochasztikus közelítése végtelen mintának lesúlyozvan n/m-mel
    - ezt hogy kéne megcsinálni? mit implikál ennyire sok minta a joint eloszlásról?
- evaluate in purely informational terms
- when is information useful for a task?
    - either in utility terms, or otherwise under what kind of evaluation?

**Insights to incorporate:**

- Arumugam, D., & Van Roy, B. (2022). Deciding what to model: Value-equivalent sampling for reinforcement learning. *Advances in neural information processing systems*, *35*, 9024-9044. https://proceedings.neurips.cc/paper_files/paper/2022/file/3b18d368150474ac6fc9bb665d3eb3da-Paper-Conference.pdf
    - this does not have results, bc the BA step is too hard to compute
- is there anything useful in the few-shot learning literature? like something talking about how few should the “few” be?
- particle filter MI estimation here: [https://www.dauwels.com/Papers/memoryless.pdf](https://www.dauwels.com/Papers/memoryless.pdf)
- something similar to the kooky sampling thing happens in a sergey levine control as inference paper, when he wants to prevent the model to choose some maximally favorable belief to maximise expected reward [https://arxiv.org/abs/1805.00909](https://arxiv.org/abs/1805.00909)
- this is the inverse of the normative Bayesian experiment design thing. here we know what sort of experiment we will be able to conduct, and choose the most informative question that will be possible to decide with that sort of experiment
    - and then efficient coding is modifying what sort of experiment you can run

**Unsatisfactory hacks:**

- the sampling-based approximation of the KL produces negative values at small sample sizes, now these are capped to 1e-6
- M=0 doesn’t really give you back the original objective, now it’s just being subbed in when M=0

**Sequential version of the MI objective:**

- **MI with concatenated observations**
    - what is the joint p(theta | theta_old) implied by the samples X_tilde?
        - the samples directly only imply certain expectations
        - but through many expectations we can define the entire distribution, as with moments. how will this look like?
        - it’s still a slight of hand that the samples are from the posterior, and then I assume they are distributed according to the new prior
            - it’s ok as long as they are concrete samples, and not just a distribution
            - just switching them in into a distr that should be according to p(theta) feels slightly wrong still
            - something similar happens in a sergey levine control as inference paper, when he wants to prevent the model to choose some maximally favorable belief to maximise expected reward
        - it strongly feels like there should be some even latenter thing connecting the thetas properly into a joint
    - how does the m=0 case look like?
- **what happens if you treat n as a random variable, and calculate through that?**
    - this will be quite akin to confidence.
    - Gemini: A standard Kalman filter is used for tracking objects, but it assumes fixed levels of process noise (Q) and measurement noise (R). An adaptive or hierarchical Bayesian version places priors on Q and R and updates them based on the data. Here, the inferred values of Q and R represent the model's epistemic state about its own accuracy and the predictability of the environment, directly influencing how it weighs its own predictions against incoming sensor data.

**Perception-meta-action cycle:**

- passive sub-agent: there are only meta-cognitive actions, otherwise it just receives a fixed number of bits from the environment
    - that it would be implemented piecemeal in an inner cycle doesn’t matter
    - reward is proportional to KL after each cycle
        - this model something like a cross-entropy evaluation
- active sub-agent: there is an inner cycle, and the outer agent can have different kinds of knowledge about it
    - Optimising sub-agents: the outer agent knows that the sub-agent optimises a known objective function successfully, and doesn’t care about the algorithm
        - Same objective inside and outside
            - EV: Gittins agent inside, usual Bellman updates outside
            - Average reward
            - CVAR
        - Different objectives inside and outside
            - AR-EV: outer loop takes care of homeostasis, inner of momentary performance
            - EV-CVAR: inner loop also avoids risk
    - Noisy sub-agents: the inner agent only optimises it’s objective up to some noise ceiling
    - So the point here would be to avoid simulating the sub-agents when making the meta-cognitive decision, and just assume they will do their job
- Planning vs reactive external agents
    - planning: it sort of simulates the sub-agents, or makes an educated guess about what they’ll do, and computes present-value based on rollouts
    - **reactive: basically sees how well the internal agent did in terms of actually maximising the mutual information based on the observations, and adjusts the representation based on this feedback**
        - so this seems like an assumption about the likelihood, or its variance in particular. and the feedback is basically seeing how wrong the likelihood function was in the previous MI calculation
        - this connects it to 3A too: there, the main difference is that the likelihood changes continuously, thus it can trigger the representational change without waiting for the outer cycle to finish
- number of variables
    - the MI objective does have a way to effectively remove latents from the model
    - it does not however have a straightforward way to add one
    - could this capability be added? or some kind of signalling system that whatever we have seems inadequate given what we already know?
        - can there be an anticipatory component to such a decision or would it be a purely retrospective one?

[M Abbott](finite-observation%20optimal%20priors%20for%20sequential%20d/M%20Abbott%202f580d8535ad80a7a99efee32494e8c9.md)