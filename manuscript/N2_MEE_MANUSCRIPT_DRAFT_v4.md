# State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions

**Manuscript type:** Research Article  
**Target journal:** Methods in Ecology and Evolution  
**Review draft:** anonymized state-prediction version 4

## Abstract

1. Ecological prediction is commonly communicated as a scalar at each location: suitability, occurrence probability, occupancy, use or another collapsed support value. Yet organisms can occupy different height, depth, time, phenological or behavioural states under the same mapped conditions. A richer prediction should therefore return a probability distribution over ecological states, not only a single map value, and it should show that this added resolution transfers to independent data.

2. We introduce ODSP, a model-agnostic framework for **state-resolved ecological prediction**. For declared ecological states `A` and contextual predictors `X`, ODSP represents predictions as `P(A|X)` and evaluates them against the lower-information training marginal `P(A)`. The primary transfer score for independent group `j` is `G_j = E[log P_train(A|X) - log P_train(A)]`. Multiclass Brier improvement, top-1 accuracy and assigned-state probability provide complementary diagnostics. Known-truth benchmarks test stable, unorganized and shifted predictive regimes, while a separate information-theoretic layer quantifies added-state thickness and fitted organization.

3. Synthetic validation recovered the intended regimes: stable organization produced positive gain in all 128 replicates at every tested sample size, shifted organization produced negative gain in all replicates, and unorganized support converged toward zero. Two public tracking endpoints were then frozen prospectively before outcome access. A marsh-harrier endpoint contained 193,370 thinned events but only three eligible independent individuals and therefore closed as unavailable before model transfer was tested. A larger multi-species raptor endpoint admitted 154,655 events from 30 individuals and four species. Random-forest state predictions improved held-out log score for 27/30 individuals and Brier score for 30/30; the predeclared all-individual rule nevertheless retained a mixed terminal state because three log-score gains were non-positive.

4. ODSP therefore changes the prediction target from a collapsed ecological scalar to a distribution over explicit ecological states while keeping independent transfer as a separate evidential requirement. The framework can sit above different learners, including random forests, multinomial regression and other probabilistic models. It does not guarantee universal transfer, infer causal drivers or determine the biological meaning of an axis; instead it provides a reproducible way to ask **which state, with what probability, and does that extra resolution generalize?**

**Keywords:** ecological prediction; state-resolved prediction; transferability; species distribution models; information theory; random forest; biologging; ecological niche

## Data and code for peer review

All methods are implemented in the open-source ODSP Python package under the MIT License. Double-anonymous review code is supplied without author-identifying repository history. Machine-readable contracts freeze the source archive, state semantics, state bins, predictor set, independent groups, model settings, weighting, metrics and terminal rule before empirical outcome access. The empirical datasets are public archives supplied by their original data providers; no source tracking or camera-trap data are redistributed as newly authored data.

# 1. Introduction

Ecological prediction is often reduced to one number per place. Species distribution models map habitat suitability, occurrence probability or related support across geographic space; movement and habitat-use models similarly summarize where an organism is likely to occur or which areas receive high use. These products are useful because they compress complex ecological information into an interpretable surface. The compression, however, is also a scientific choice. Two locations with the same predicted suitability can support very different ecological states: animals may use different flight layers, water depths or times of day; plants may differ in phenological state; communities may divide the same site among temporal or behavioural states. A scalar prediction can therefore answer **where** while leaving unresolved **in which state**.

This gap is not solved simply by fitting a higher-dimensional model. A model can include more predictors, more response dimensions or a more elaborate latent structure and still fail to provide useful prediction outside its training sample. Ecological transferability has long been recognized as distinct from apparent fit (Wenger & Olden, 2012; Yates et al., 2018), and the choice of validation unit strongly affects the claim that can be supported (Roberts et al., 2017; Valavi et al., 2019). The same problem applies when the response itself is multidimensional. A fitted distribution over height or time can be descriptively rich yet fail for a new individual, site or year. Conversely, hidden ecological states can contain reproducible predictive structure that is invisible in a collapsed representation.

We therefore formulate a different prediction target. Let `A` denote one or more explicit ecological states, such as altitude class, depth class, activity-time bin, phenophase or behaviour, and let `X` denote the contextual information available to a predictor. Instead of returning only a scalar ecological support value, a state-resolved model returns

`P(A|X)`.

For a flight-height example, this means predicting a probability distribution across altitude states for each environmental and spatiotemporal context. For a camera-trap example, it could mean a distribution over time states conditional on site, species and environmental context. Multiple state axes can be predicted jointly. The conceptual change is small but consequential: the output of the model is no longer only “suitable here” but “given this context, these ecological states have these probabilities.”

A richer prediction requires a correspondingly stricter validation. Extra conditioning information will almost always create a more detailed fitted representation, but detail alone is not predictive value. We therefore compare the state-resolved prediction `P(A|X)` with an explicit lower-information comparator, the training marginal `P(A)`. On a prospectively independent group, the log-score gain

`G = E[log P_train(A|X) - log P_train(A)]`

asks whether retaining the contextual state structure improves probabilistic prediction over ignoring it. We score independent groups separately rather than allowing large groups to dominate a pooled average. This gives a fail-closed distinction among generalizing, non-generalizing and mixed outcomes. It also connects naturally to the information-theoretic foundation of ODSP: when training and target distributions are the same, expected conditional-versus-marginal log gain is the mutual information supplied by the conditioning state.

Here we develop ODSP as a general framework for state-resolved ecological prediction and independent transfer evaluation. ODSP is not a competing occurrence-SDM learner. It defines a response representation, probability-field interface, scoring architecture and claim hierarchy that can be used with different upstream learners. We provide a transparent Dirichlet-smoothed discrete reference learner and an interface for probabilistic covariate models; random forest and multinomial logistic regression are used as reference covariate learners in the empirical prediction demonstration. We validate the predictive behavior under known truth, retain an axis-agnostic information-theoretic audit of state thickness and organization, and then execute two new public-data prediction endpoints frozen before outcome access. The first tests whether a seemingly data-rich tracking archive contains enough independent individuals to open prediction transfer. The second tests species-aware altitude-state prediction across 30 independent raptors from four species. Earlier Tawaki, bat and Snapshot Serengeti endpoints are retained as supporting evidence for the broader inferential hierarchy: estimability can fail, added-state thickness can be present without transfer, and non-spatial state organization can generalize. Our central question is therefore no longer only how much a flat representation hides, but whether the hidden ecological state can be **predicted and independently transferred**.

# 2. Materials and Methods

## 2.1 State-resolved prediction target

ODSP assumes a declared ecological state axis or set of axes `A` and a set of contextual predictors or base states `X`. The prediction target is a normalized probability distribution

`P(A|X)`.

The elements of `A` must have explicit biological and measurement semantics. Examples include discretized flight altitude, depth, canopy stratum, activity-time class, phenological phase, microhabitat state or behaviour. Multiple axes can be combined into a joint state, for example `A=(depth,time)`. ODSP does not infer what an axis means from its values. A locality elevation is not automatically organism height, a camera timestamp is not automatically unbiased activity, and absolute altitude above mean sea level is not height above ground unless an explicit terrain transformation is applied.

This formulation differs from occurrence SDM. A conventional occurrence model may estimate `P(species occurrence|environment)`. ODSP can use outputs from such a model, but its state-resolved target is instead the conditional distribution of a declared ecological state. Thus random forest, multinomial regression, boosted trees, Bayesian models or neural networks can all act as state learners if they provide normalized predictive probabilities. ODSP supplies the common response representation and validation layer.

## 2.2 Discrete state support and native reference learner

For event or support data that already define discrete base states `B` and added states `A`, ODSP constructs a non-negative support array `S(B,A)`. Counts, effort-adjusted weights or other explicitly justified non-negative support may be used. A native reference learner estimates `P(A|B)` with an explicit Dirichlet pseudocount. Unseen base states can be handled by a declared marginal backoff, a uniform distribution over structurally available states, or a fail-closed rule. No hidden smoothing is performed in the scoring layer.

For each base state the model can return the full state probability vector, dominant state and probability, Shannon entropy and the effective number of predicted states. These outputs make the prediction richer than a single scalar but remain descriptive until tested out of sample.

## 2.3 Covariate-to-state prediction

For continuous or mixed contextual predictors, ODSP exposes a generic `predict_proba` interface. A fitted probabilistic classifier receives a feature matrix `X` and state labels `A`, then returns a probability vector over the training state classes for each new covariate row. The same ODSP scoring functions can therefore compare predictions from different algorithms under an identical state target and comparator.

Two reference learners were used here. The primary empirical learner was a random-forest classifier with settings frozen before outcome access. Multinomial logistic regression, with continuous predictors standardized within each training fold, served as a sensitivity learner. The purpose of using two algorithms was not to perform post-outcome model selection; the random forest remained the primary endpoint regardless of the logistic result.

## 2.4 Predictive scoring against a lower-information comparator

The primary held-out metric is conditional-versus-marginal log-score gain. For independent held-out group `j`,

`G_j = E_heldout,j[log P_train(A|X) - log P_train(A)]`.

The marginal comparator is estimated from the same training data as the state-resolved predictor and discards contextual organization. It therefore answers a concrete question: does the detailed state prediction outperform simply knowing the overall state frequencies available from the training sample?

Positive gain means that the conditional model assigns higher geometric-mean probability to the realized held-out states than the marginal comparator. A negative gain means that the additional conditioning structure harms held-out log score. Because the logarithmic score is sensitive to confidently assigning very low probability to realized states, it can expose transfer failures that are less visible to bounded metrics.

We additionally report the multiclass Brier score, Brier improvement relative to the marginal comparator, top-1 state accuracy, top-1 improvement and mean probability assigned to the realized state. These are secondary diagnostics. They do not override the primary log-score terminal rule.

## 2.5 Independent groups and terminal decisions

Transferability is evaluated at the level of prospectively independent units, such as individuals, sites, years or instruments. Let `G_j` denote the primary gain for group `j`. Under the zero-gain rule used here:

- **generalizing:** every independently scored `G_j > 0`;
- **non-generalizing:** every `G_j <= 0`;
- **mixed:** positive and non-positive group gains coexist;
- **unavailable:** the frozen observation/admission architecture does not permit the intended transfer test.

Mean gain is descriptive only. A large or highly sampled group cannot rescue a conflicting independent group through pooled observation mass. Where multiple individuals are held out in one computational fold, each individual still receives its own score and sign.

## 2.6 Known-truth prediction benchmark

We tested finite-sample predictive behavior in three families, each repeated 128 times at 50, 250 and 1000 observations per base state.

In the **stable-generalizing** family, training and held-out data share the same context-state organization. The correct state-resolved model should therefore outperform the marginal comparator. In the **shifted-non-generalizing** family, the state organization in held-out data is deliberately reversed relative to training, so fitted state detail should transfer poorly. In the **unorganized** family, context provides no information about state, so conditional-versus-marginal gain should approach zero as sampling error decreases.

We recorded mean log-score gain, the fraction of positive or negative replicate gains, state-probability RMSE, Brier improvement and top-1 accuracy. These simulations validate predictive behavior rather than biological realism.

## 2.7 Information-theoretic audit and representation generality

The predictive layer retains the earlier ODSP information-theoretic audit. For non-negative support over base state `B` and added state `A`, conditional entropy

`H(A|B)`

measures how much added-state uncertainty remains after the base state is known, and `exp[H(A|B)]` gives the corresponding effective number of states. Fitted organization can be described by `I(A;B)` or an axis-appropriate conditional information quantity. Under the same generating distribution,

`E[log P(A|B) - log P(A)] = I(A;B)`,

linking descriptive organization to the expected predictive advantage of conditioning.

The implementation was separately stress-tested for axis permutation, label relabelling, mass scaling, nuisance-axis refinement, chain-rule identities, coarse-graining behavior, sparse support and multi-axis composition. Across 1,873 property obligations there were no failures; maximum absolute numerical error was `2.49 x 10^-14`. This establishes implementation and representation genericity over the validated finite discrete domain, not universal biological generality.

## 2.8 Prospective empirical prediction endpoint 1: MH_ANTWERPEN

The first state-prediction endpoint used the public MH_ANTWERPEN tracking archive for western marsh harriers near Antwerp, Belgium (Spanoghe et al., 2023; Zenodo DOI `10.5281/zenodo.10054153`; Movebank study 938783961). The public archive contains GPS data with timestamp, longitude, latitude, external temperature, height above mean sea level and individual identity. The endpoint was frozen before GPS outcome access.

The target was a four-state absolute-altitude distribution: `<50`, `50-200`, `200-500` and `>=500 m` above mean sea level. Primary predictors were external temperature, latitude, longitude, cyclic local-solar time and cyclic day of year. Ground speed was excluded from the primary model. Events were thinned to the earliest admissible event in each individual-by-UTC-10-minute bin.

An individual required at least 300 thinned events, at least two supported altitude states and at least 10 events in each supported state. At least four eligible independent individuals were required to open leave-one-individual-out prediction. This threshold was frozen before outcome access; failure of the threshold required an unavailable terminal state without fitting the primary transfer model.

## 2.9 Prospective empirical prediction endpoint 2: BOP_RODENT

The second endpoint used the fixed BOP_RODENT v3 archive of rodent-specialized birds of prey in Flanders, Belgium (Spanoghe et al., 2023; Zenodo DOI `10.5281/zenodo.10055071`; Movebank study 1278021460). The archive version and MD5 checksums of the 2020-2022 GPS files were frozen before outcome access. The v3 archive reports 35 tagged individuals from five raptor species.

The response used the same four absolute-altitude states as the first endpoint. Contextual predictors were external temperature, latitude, longitude, cyclic local-solar time, cyclic day of year and species identity encoded as fixed one-hot columns. Absolute altitude was not interpreted as height above ground. Events were thinned to the earliest admissible event for each individual in each UTC hour.

Individuals required at least 300 hourly-thinned events, at least two supported altitude states and at least 20 events in each supported state. A species required at least three eligible individuals. The endpoint required at least three admitted species and 12 eligible individuals in total.

Eligible individuals were assigned to five deterministic folds within species by sorting IDs by SHA256 and assigning them round-robin. Training weights were hierarchical: each admitted species contributed equal total weight, and individuals within each training species contributed equal total weight. The primary model was a random forest with 500 trees, minimum leaf size 25, square-root feature subsampling and fixed seed 20260905. Standardized multinomial logistic regression with `C=1` was frozen as a sensitivity model.

Every held-out individual received its own primary log-score gain relative to the training marginal altitude distribution. The endpoint could be called generalizing only if all scored individuals had positive primary gain. Species-level categories were secondary and could not override the all-individual terminal state.

## 2.10 Supporting empirical diagnostics

Three earlier empirical endpoints were retained to test distinct pieces of the same evidence hierarchy. A Tawaki GPS-dive endpoint tested structural estimability before a biological thickness result was opened. A European free-tailed bat endpoint quantified native vertical-state thickness and cross-individual transfer of `P(z|x,y)`. A Snapshot Serengeti endpoint quantified temporal thickness, species-time partitioning and cross-fitted transfer across held-out site folds.

These analyses are not additional state-prediction training datasets. Their role is to establish why a richer prediction requires separate estimability, descriptive-state and transfer checks.

## 2.11 Software, reproducibility and prospective control

All prediction functions, contracts, synthetic benchmarks and empirical runners are version-controlled. The empirical prediction workflows verify source checksums, run contract and synthetic implementation tests before public outcome access, execute only the frozen model settings, validate the result schema and record whether retuning occurred. Canonical receipts preserve the initial prospective outcome rather than replacing it with results from a later archive version or altered rule.

## 2.12 Ethics and use of archived data

This study performed no new animal capture, handling, manipulation or field sampling. It reanalysed publicly archived ecological datasets collected by the original data providers. Ethical approvals, permits and animal-welfare procedures governing original data collection remain those reported by the source studies and archives.

## 2.13 Generative-AI assistance

OpenAI ChatGPT (GPT-5.6 Sol) was used as a development assistant for language editing, code drafting and revision, test scaffolding, documentation and repository organization. The authors defined the scientific questions, prospective contracts, estimands, frozen decision rules and claim boundaries; executed and validated analyses; inspected failures and outputs; reviewed the submitted code and text; and retain responsibility for interpretation and submission. Review-code files are conservatively annotated where iterative AI assistance may have contributed and exact line-level provenance is unavailable.

# 3. Results

## 3.1 Known-truth prediction recovered stable, null and shifted regimes

The finite-sample benchmark behaved as intended. Stable organization produced positive conditional-versus-marginal log-score gain in all 128 replicates at every tested sample size. Mean gain was `+0.30034` nats/event at 50 observations per base state and `+0.32294` at 1000. State-probability RMSE fell from `0.0503` to `0.0119` across the same sample-size range.

Shifted organization produced negative gain in all 128 replicates at every sample size. Mean gain was `-0.78236` at 50 observations per base state and `-0.77330` at 1000, despite probability-estimation RMSE declining from `0.0508` to `0.0116`. Thus increasingly precise estimation of the training-state distribution did not create false transfer when the held-out organization differed.

The unorganized family approached the marginal comparator as sample size increased. Mean gain changed from `-0.00944` at n=50 to `-0.000682` at n=1000. The benchmark therefore distinguished genuine predictive organization from finite-sample structure and from precise but non-transferable organization.

## 3.2 The generic information and prediction core was representation-stable

All 1,873 axis-agnostic property obligations passed. The maximum absolute numerical error was `2.49 x 10^-14`. Tested properties included mass-scaling invariance, axis and category relabelling, nuisance-axis refinement, conditional-entropy monotonicity, chain rules, coarse-graining, sparse support, unavailable-mask invariance and multi-axis composition. This supports an axis-agnostic implementation over finite discrete state spaces; it does not imply that all biological axes are equally meaningful or equally predictable.

## 3.3 A data-rich marsh-harrier endpoint was unavailable because independent replication was insufficient

The MH_ANTWERPEN archive yielded 393,122 raw GPS rows, of which 386,072 passed the frozen filters. Ten-minute thinning retained 193,370 events. All three tagged individuals represented in the frozen primary GPS endpoint passed the individual event/state admission rule.

The prospectively frozen design, however, required at least four eligible independent individuals. Only three were available. The endpoint therefore terminated as `empirical_state_prediction_unavailable`, and zero random-forest held-out folds were executed. The state bins, minimum-individual threshold and model specification were not changed. Abundant repeated events therefore did not substitute for independent replication.

## 3.4 Multi-species altitude-state prediction transferred to most, but not all, held-out individuals

The fixed BOP_RODENT v3 files contained 1,988,907 raw GPS rows. After the frozen complete-case and range filters, 1,983,483 events remained; hourly thinning retained 158,586 events. Final individual/species admission yielded 154,655 events from 30 independent individuals and four species: five *Buteo buteo*, eight *Circus aeruginosus*, eight *C. cyaneus* and nine *C. pygargus*.

The primary random forest produced positive held-out log-score gain for 27 of 30 individuals (`90%`). Three individuals had non-positive gains. Individual gains ranged from `-0.23078` to `+1.49999` nats/event, with median `+0.39577` and descriptive mean `+0.57091`. Because the terminal rule required every independently held-out individual to have positive gain, the endpoint was classified as `empirical_state_prediction_mixed` rather than generalizing.

The secondary Brier result was more uniformly positive. All 30 individuals had positive Brier improvement relative to their training-fold marginal comparator. Mean Brier improvement was `+0.33498`, mean top-1 altitude-state accuracy was `0.7562`, and mean probability assigned to the realized state was `0.6484`. The difference between universal Brier improvement and three negative log-score gains indicates that the conditional model generally improved probability allocation while still making sufficiently costly probability errors for three individuals to fail the primary logarithmic score.

Species-level sign patterns were heterogeneous. *Buteo buteo* was generalizing under the within-species all-positive rule (`5/5` positive) and *C. pygargus* was likewise generalizing (`9/9`). *C. aeruginosus* was mixed (`7/8`) and *C. cyaneus* was mixed (`6/8`). These secondary species categories did not override the all-individual mixed endpoint.

The frozen multinomial-logit sensitivity was weaker but directionally informative. It produced positive log-score gain for 22 of 30 individuals with descriptive mean gain `+0.08618`. *Buteo buteo* and *C. pygargus* again had all-positive species-level gains, whereas both other *Circus* species remained mixed. Because random forest was prospectively designated as primary, this sensitivity result was not used for model selection or terminal reclassification.

## 3.5 Earlier empirical diagnostics explain why richer state prediction needs a transfer audit

The Tawaki endpoint failed its frozen structural estimability gate before biological added-state inference opened. The European free-tailed bat endpoint, by contrast, was vertically thick after horizontal state was known: `H(Z|X,Y)=1.39186` nats, corresponding to `4.0223` effective vertical states. Yet both prospectively sealed bat gains were negative (`-0.43541` and `-0.02194`). Descriptive state richness therefore did not imply transferable cross-individual organization.

Snapshot Serengeti provided the complementary case on a temporal axis. Time remained broad within sites (`H(T|Site)=1.63962`, `5.1532` effective states of six), species identity partitioned time within sites (`I(Species;T|Site)=0.22428`, permutation `p=0.005`), and all three held-out spatial-fold gains were positive (`+0.05724`, `+0.04516`, `+0.04514`). Thus independent transfer can occur on an added ecological-state axis, but it is an empirical property rather than a consequence of dimensionality itself.

## 3.6 The empirical prediction evidence spans unavailable, mixed and generalizing substructures

Taken together, the new prediction endpoints and the earlier diagnostic chain reject a binary view of multidimensional prediction. The marsh-harrier endpoint shows that prediction may be unavailable even with hundreds of thousands of repeated events when independent replication is inadequate. BOP_RODENT shows strong but heterogeneous state prediction: most individuals benefited in primary log score, every individual benefited in Brier score, two species had all-positive individual gains, and two species retained transfer failures. The earlier bat and Serengeti endpoints show why those failures cannot be inferred from descriptive thickness alone.

# 4. Discussion

## 4.1 State-resolved prediction adds a response dimension, not merely another predictor

The central methodological shift is from predicting a scalar ecological surface to predicting a distribution over ecological states. Adding temperature, vegetation or topography to an occurrence model enriches the predictor set but can still return one number per location. ODSP instead changes the response representation: the model asks which ecological state is expected under a context and with what probability. A spatial map can therefore be accompanied by a vertical, temporal, phenological or behavioural state distribution at each prediction unit.

This distinction is useful because many management and ecological questions are inherently state-specific. A location may be broadly suitable but only at particular times; airspace may be used predominantly in one altitude band; aquatic habitat may be suitable while the relevant depth state changes with season or temperature. A state-resolved output retains this information in a form that can be scored directly.

## 4.2 Extra state detail is useful only when it improves independent prediction

The BOP_RODENT result provides a prospective empirical demonstration of this principle. Context- and species-conditioned altitude probabilities improved primary log score for 90% of held-out individuals and Brier score for all individuals. Thus the richer response was not merely a descriptive decomposition of the training data. It carried predictive information for most independent organisms.

At the same time, the three negative log-score gains are central rather than inconvenient. A method that reports only average improvement would classify this endpoint as strongly successful because the descriptive mean gain was large and positive. The independent-group rule instead preserves heterogeneity. The correct conclusion is not that altitude-state prediction universally generalized, but that it generalized broadly while failing for specific independent individuals.

## 4.3 Mixed outcomes are a feature of the evidence architecture

Ecological prediction often operates across individuals, populations, sites and years that are not exchangeable. A mixed terminal state makes that variation visible. In BOP_RODENT, two species had all-positive RF gains while two contained individual failures. The result could reflect biological heterogeneity, covariate shift, observation differences, measurement error, unmodelled state dependence or some combination. ODSP does not assign a cause. It prevents pooled observation mass from erasing the fact that transfer differs among independent units.

The contrast between log score and Brier improvement is also informative. All 30 Brier improvements were positive, whereas three log-score gains were not. Brier score rewards improved probability allocation in a bounded way; logarithmic score places stronger cost on assigning very low probability to realized events. Reporting both makes model behavior more transparent while retaining one predeclared primary metric.

## 4.4 ODSP complements rather than competes with MaxEnt, random forests and other ecological learners

ODSP should not be presented as another entry in an algorithm tournament. MaxEnt, random forest, boosted trees, generalized additive models, hierarchical Bayesian models and neural networks differ in how they learn relationships. ODSP instead specifies **what is predicted and how the extra state resolution is audited**. Any learner that supplies a normalized state-probability field can be compared under the same state target, marginal comparator and independent-group scores.

This architecture creates two useful comparison levels. First, researchers can ask whether state-resolved prediction adds value over a collapsed state marginal. Second, once a state target is justified, they can compare learners by held-out log score, Brier score, calibration or other proper predictive criteria. The BOP analysis used random forest as primary and multinomial regression only as a frozen sensitivity analysis, illustrating that learner choice can affect transfer magnitude without changing the ODSP target or decision logic.

## 4.5 Mathematical genericity is broader than current biological validation

The information and scoring core is axis-agnostic over validated finite discrete support. Height, depth, time, behaviour and multiple joint states can be represented through the same probability architecture, and the property benchmark confirms expected invariances and information identities. This is mathematical and implementation genericity.

Biological generality is narrower. The prospective state-prediction demonstration currently concerns absolute-altitude states in tagged raptors. The earlier supporting chain adds temporal camera-trap states and bat vertical states, but it does not establish that every ecological axis will be equally predictable or transferable. Wider biological generality requires new prospectively designed state-prediction endpoints with different organisms, sensors, state semantics and independence structures.

## 4.6 Observation architecture remains part of the method

State prediction can be only as meaningful as the state variable being measured. In the raptor analyses, the response was GPS height above mean sea level. It should not be relabelled as flight height above ground without a terrain model and an error analysis. Camera-detected time is not automatically true activity independent of detection. Opportunistic observations do not automatically represent unbiased use probabilities.

The MH_ANTWERPEN result makes a related point about replication. Nearly 200,000 thinned events did not satisfy a design requiring four independent organisms because only three eligible individuals were available. Effective sample size for transfer is determined by the intended generalization unit, not simply by event count.

## 4.7 Prediction audit should remain separate from causal or downstream state claims

A positive state-prediction gain means that the conditional probability field improves held-out prediction relative to its declared marginal comparator. It does not show that the predictors causally determine the state, that the predicted state is a fundamental niche dimension, or that an independently meaningful downstream ecological state has been identified. Those claims require separate designs.

For the same reason, ODSP terminal summaries are not automatically promoted to a subsequent N3 state artifact. Prediction and transfer are evidence about the reproducibility of state organization; downstream process or reachability inference requires its own integrity-pinned state definition and validation.

# 5. Conclusions

ODSP provides a way to move beyond ecological predictions that collapse an organism or community to one scalar value. The framework predicts a probability distribution over explicitly declared ecological states and tests whether the additional resolution improves prediction for prospectively independent groups. Its known-truth benchmark distinguishes stable, null and shifted predictive regimes; its prospective empirical tests show both fail-closed unavailability and strong but heterogeneous cross-individual prediction.

The multi-species raptor application demonstrates the practical value of the approach: state-resolved altitude prediction improved primary log score for 27 of 30 held-out individuals and Brier score for all 30, yet a conservative all-individual rule retained the three transfer failures rather than hiding them behind a positive average. The resulting question is richer than “where is the species?” but stricter than “can we fit another dimension?”: **which ecological state is predicted, with what probability, and does that prediction transfer?**

# References

Blonder, B., Lamanna, C., Violle, C. & Enquist, B. J. (2014). The n-dimensional hypervolume. *Global Ecology and Biogeography*. https://doi.org/10.1111/geb.12146

Cover, T. M. & Thomas, J. A. (2006). *Elements of Information Theory*, 2nd edn. Wiley.

Hutchinson, G. E. (1957). Concluding remarks. *Cold Spring Harbor Symposia on Quantitative Biology*, 22, 415-427. https://doi.org/10.1101/SQB.1957.022.01.039

Milotic, T. et al. (2020). Dataset description associated with the MH_ANTWERPEN bird-tracking project. *ZooKeys*, 947. https://doi.org/10.3897/zookeys.947.52570

O'Mara, M. T., Amorim, F., Scacco, M., McCracken, G. F., Safi, K., Mata, V., Tome, R., Swartz, S., Wikelski, M., Beja, P., Rebelo, H. & Dechmann, D. K. N. (2021). Bats use topography and nocturnal updrafts to fly high and fast. *Current Biology*, 31, 1311-1316.e4. https://doi.org/10.1016/j.cub.2020.12.042

Otis, M., Mattern, T., Ellenberg, U., Long, R., Garcia Borboroglu, P., Seddon, P. J. & van Heezik, Y. (2025). Inter-colony and inter-annual behavioural plasticity in the foraging strategies of a fjord-dwelling penguin. *PeerJ*, 13, e19650. https://doi.org/10.7717/peerj.19650

Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40, 913-929. https://doi.org/10.1111/ecog.02881

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27, 379-423, 623-656.

Spanoghe, G., Desmet, P., Milotic, T., Janssens, K., De Regge, N., Vanoverbeke, J. & Bouten, W. (2023). MH_ANTWERPEN - Western marsh harriers breeding near Antwerp (Belgium), version v6 [Data set]. Research Institute for Nature and Forest. Zenodo. https://doi.org/10.5281/zenodo.10054153

Spanoghe, G., Janssens, K., Klaassen, R., Schaub, T., Milotic, T. & Desmet, P. (2023). BOP_RODENT - Rodent specialized birds of prey in Flanders (Belgium), version v3 [Data set]. Research Institute for Nature and Forest. Zenodo. https://doi.org/10.5281/zenodo.10055071

Swanson, A., Kosmala, M., Lintott, C., Simpson, R., Smith, A. & Packer, C. (2015). Snapshot Serengeti, high-frequency annotated camera trap images of 40 mammalian species in an African savanna. *Scientific Data*, 2, 150026. https://doi.org/10.1038/sdata.2015.26

Valavi, R., Elith, J., Lahoz-Monfort, J. J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution*. https://doi.org/10.1111/2041-210X.13107

Wenger, S. J. & Olden, J. D. (2012). Assessing transferability of ecological models: an underappreciated aspect of statistical validation. *Methods in Ecology and Evolution*. https://doi.org/10.1111/j.2041-210X.2011.00170.x

Yates, K. L. et al. (2018). Outstanding challenges in the transferability of ecological models. *Trends in Ecology & Evolution*, 33, 790-802. https://doi.org/10.1016/j.tree.2018.08.001
