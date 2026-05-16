# connection to efficient coding

- Approaches to relate to
    - david abel, info-theoretic agent plasticity [https://arxiv.org/pdf/2505.10361](https://arxiv.org/pdf/2505.10361)
    - what do they say in this, Barto , botwinick, statistics of neural tasks [https://www.sciencedirect.com/science/article/abs/pii/S2352154615001151?via%3Dihub](https://www.sciencedirect.com/science/article/abs/pii/S2352154615001151?via%3Dihub)
    - Sims efficient coding and RL: [https://www.nature.com/articles/s41467-025-58848-6](https://www.nature.com/articles/s41467-025-58848-6)
        - this seems to be just a lambda-weighted informational cost slapped onto the policy gradient objective
    - Wiktor and Tkacik paper [https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001889](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001889)
        - this is attentional modulation of the likelihood function, very similar to LG
    - Nemenman Bialek
    - Van Roy
        - info mindenhonnan mindenhova, ágens részeibe environment részeiből

**L Gábor connection**

- does the elasticity parameter fall out of our method?
    - top-down EC, not only bottom-up (efficient thinking, according to J)
- it’s an instantaneous, attention-like process in LG, as well as in WM&GT
- what is the difference between a non-EC version of the context model and the EC version of LG?

- mit implikál a szorosabb kapcsolat 1 és 3A között a double loopon keresztül?
- egy likelihoodot parametrizáló paraméter kell, de olyan, amit tudhat előre, meg amit tanulhat is
- **pl: víz átlátszósága vagy valami hasonló. lehet olyan, hogy tudja, hogy ránézésre meg lehet állpítani arányokat elég jól. de lehet olyan is, hogy nem, és akkor az lehet egy tanulandó dolog, hogy hogy kell azt becsülni**
    - lehetőség: amikor már tudja a policyt és csak a becslést kell tanulni. hogy ne elgyen olyan hosszú az egész
        - ez nem teszi megkülönböztethetővé a likelihood-triggered representational update-eket?
        - de ha ninc policy tanulás, i.e. R függvény, akkor van tanulás egyáltalán?
        - 2 irány!
- **fő nehézség: hogyan lesz ez mérhető. kereshetünk valami aha-t, de igazából simán lehet full graduális is ez a dolog, és ami különbözik az alapverziótól, hogy van egy interakció a likelihood learning és a representation dynamics között. de ez potenciálisan csak a tanulás folyamatában különbözik, és nem világos, hogy lehet mérni**