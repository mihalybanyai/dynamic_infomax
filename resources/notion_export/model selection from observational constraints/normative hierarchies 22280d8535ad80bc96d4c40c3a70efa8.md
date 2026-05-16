# normative hierarchies

- Approaches to relate to:
    - Icard [https://philpapers.org/archive/ICARRT.pdf](https://philpapers.org/archive/ICARRT.pdf)
    - precup machado HRL review [https://arxiv.org/pdf/2506.14045](https://arxiv.org/pdf/2506.14045)
    - dual process, maneesh, botvinick: [https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1012383](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1012383)
    - dual IB: [https://arxiv.org/pdf/2006.04641](https://arxiv.org/pdf/2006.04641)
    - decodable IB: [https://arxiv.org/pdf/2009.12789](https://arxiv.org/pdf/2009.12789)
    - HRL overview, machado, precup, konidaris [https://www.arxiv.org/abs/2506.14045](https://www.arxiv.org/abs/2506.14045)

Todo:

- hogyan viszonyul egymáshoz az open-loop reprezentációkra való átállás, és a habitualizált résztaszkok újrahasznosítása?
    - utóbbi a habitba rakja a reprezentációt, előbbi a taskhoz rendeli hozzá
    - ki mondja meg, hogy mi egy objektum?
    - miben különböztethető ez meg viselkedésben?

Dávid:

- Icard resource rationality könyv
- policy hierarchiáktól mennyire különbözik (yee whye)
- Dávid cikk utolsó section
- anticipatív-e ez még?
- ne legyen bottleneck a task változóval? az MI helyett
- mi teremti meg a balanszt abban, hogy mennyire akarsz fölmenni a piramison?
    - vagy lehet csak két szintről beszélni?

random ideas:

- this is about anticipating future tasks, without necessarily knowing much about them
- here we can bring in reflectivity in the agent to the fact that discrete representations **unlock** logic-like operators
- **isomorphisms** of feature spaces, together with reward functions and dynamics, which might be harder to establish in a continuous realm
    - this is akin to analogies in Dávid’s world
    - there are two kind here: one is the group theory-style analogy, where the state spaces have similar structure, and the category theory style one, where they are pluggable into the same algorithmic machinery
        - **the latter can be done with a single task as well**
        - but it seems very hard to figure out what would be a controllably-existing such algorithm
        - but then it can tie into decodable information bottlenecks
            - you can try on various decoder heads - some of these could be algorithms, some policies from other tasks.
            - you can try to create **decoder heads** that are as general as possible
            - **this could be a staircase that leads to the creation of symbols when the decoders are certain algorithms - but the critical capacity is to try on multiple of such decoders to shape a representation**
                - this sounds suspiciously like auxiliary tasks
                - the same urgency with different decoders? or actually trying different urgencies?
- there could be a co-evolution between algorithms and representations, as simpler representations unlock more algorithms
    - the variant of information theory where the read-out isn’t arbitrary?
- symbols may emerge to foster such isomorphisms, for which it’s useful to shed the embedding space
- but how is this connected to urgency exactly? even if just internal, “fake” urgency
- maybe the effective number of observations will be so low that you have hardly any chance to learn anything. but crafting an analogy allows you to pool observations
- or you are aware that you have the symbolic machinery, and via artificial urgency you can contort your state space into a format that conforms its input specification → win
- the more down-to-earth side of the story is just that you anticipate there being future tasks, so you sort of shake-and-try explore the representational space, to basically get an estimate of the advantage of the maximum. and if there isn’t much, you lower resolution, so you can learn faster in a novel task
- people might do this automatically to unlock rule learning
    - this is of course always explicit, and cannot be implicit at all
- *******************************–
- egyáltalán milyen okok vannak arra, hogy valaki hierarchikus reprezentációkat használjon?
- önmagában a resource rationality kiesik, mert ha a részletesebb domaint tudod konstruálni, akkor eleve jó a helyzet
    - igaz ez? segíthet a részletesebb domain konstrukciójában egy coarse-grainedebb domain? kb ilyen exploration guide-ként? simán.
- maga a statisztika rávesz: azaz a taskok eloszlásában megvan ez a hierarchikus struktúra
    - és ezt valahonnan tudod is
    - ez a generalizációs érv végeredményben: azért csinálod, mert tudod, hogy hasznos lesz
- megváltoznak a constraintek
    - de úgy, hogy akár vissza is változhatnak
    - ez egy olyasmi lesz, hogy az első megoldás unscalable, mert túl sok figyelmet igényel. ha ismételt a taszk vagy taszktípus, akkor azt akarod, hogy legyen hozzá egy rutin, amiből csak akkor kell kilépni, ha valami váratlan van
    - egy ilyen rutin nem tartalmaz tanulást asszem, de ez nem biztos. mindenesetre lehet, hogy meta-kognitív tanulást nem.
- kapcsolódik létező megoldásokhoz
    - dávid-féle module library and whatnot
    - ez kapcsolódik az előzőhöz is
    - valahogy az egy fontos dolognak tűnik, hogy folyamatosan növekedjen a non-effortful competence. és ehhez vezetnek el a jó absztrakciók valahogy. és az effort az mindig a frontieren van. it never gets any easier you just go faster.
        - itt a kérdés az, hogy **mit jelent az effort**?
            - ez jelenthet egy computational constraintet is, ahol azt akarod elkerülni, hogy pl a drága mutual information-optimalizációt ki kelljen számolni újra és újra
            - de tekinthetünk rá úgy is, hogy van egy meta-ágens, aki információt kap a sima-ágensről, mint a környezet eleméről, és azt az információt akarja minimalizálni, amihez hozzá kell így jutnia
                - opening the closed loop of meta-control
        - model-free vs model-based mennyire írja már le az ilyen jellegű átmeneteket?
            - reprezentációs komponens van-e kellően bennük?
                - episodic control vs model-based csinál ilyen átmeneteket, és végeredményben a value function is bizonyos értelemben. de abban ami engem érdekel?
        - milyen algoritmikus feltételezésekre van szükség itt?
            - meta-loop költséges, tehát ki akarom kapcsolni
            - de a meta-loop egy tanulási dolog, nem annyira döntéshozási, tehát a figyelemmel nem annyira közvetlenül analóg, csak valami tanulási változatban
            - tehát nem igazán az, mint egy habit, hanem egy ilyen tanulási meta-habit
        - valamilyen meta-kogníciót valószínűleg
        - lehet ezt információs keretben karakterizálni? pl mit kell választanod, ha tudod, hogy később nem választhatsz
            - ez függeni látszik olyasmitől is, hogy mennyi kontrollod van az állapot fölött, azaz be tudod-e vinni a kedvelt állapotokba akkor is, ha nem ott van, vagy akkor azzal külön kell foglalkoznod?
- elephant in the room: multi-agent stuff