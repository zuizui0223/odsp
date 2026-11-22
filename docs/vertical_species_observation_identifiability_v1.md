# Observation-aware projection loss: species × vertical state (v1, 2026-11-22)

**Status:** prospective, *source-free identifiability counterexample and design only*. This does NOT revise the frozen ODSP/N2 manuscript, past bat vertical null, Serengeti temporal positive, `batter` JAE manuscript, `esdm` E5 (0/17 eligible), or existing data receipts. Do not label the synthetic counterexample a biological field effect.

## 1. What mathematical identity does and does not guarantee

Hutchinson (1957) characterized environmental *niche* axes, not a theorem that GPS location, flight altitude, behavioral state and time are all biologically interchangeable niche variables. Colwell & Rangel (2009), DOI `10.1073/pnas.0901650106`, explicitly distinguish geographic/biotope and environmental niche spaces.

For a well-defined latent species-specific intensity (or normalized state use) at fixed time `t`, the correct 2-D projection is a marginal:
`lambda_s^XY(x,t) = sum_b integral_{z in D(x,t)} lambda_s(x,z,b,t) dz`.
For a time-averaged surface, define the time window and integration/exposure weight as well. A normalized joint probability also marginalizes, provided the base support and normalization are the same. An **independently fitted occurrence probability, presence-only Maxent suitability score or detection-biased 2-D model is not automatically equal to this marginal**. Under Poisson quadrat occupancy with integrated intensity `L`, `P(occupied)=1-exp(-L)`, not an additive sum of height-specific occupancy probabilities.

The factorization `p(x,t,b,z)=p(x,t)p(b|x,t)p(z|x,t,b)` is a chain-rule identity for an existing joint distribution, **not a proof that all factors can be identified** from samples or transferred across sites. Maxent/IPP equivalences (Warton & Shepherd 2010; Fithian & Hastie 2013 DOI `10.1214/13-AOAS667`) have sampling/background/model conditions; they do not remove these identification constraints.

## 2. The observational integral is not the biological marginal

For observation stream/method `m`, an idealized thinned marked point-process observation has expected measure

`mu_{m,s}(y) = integral lambda_s(u) * effort_m(u) * q_{m,s}(u) * K_m(y|u) du`, `u=(x,z,t,b)`.

`q` = detection/registration probability. `K` = measurement or missing-axis kernel. For presence-only coordinates, unrecorded height is integrated **after multiplication by effort and detection**. Thus no-height GBIF observations constrain a detection-weighted horizontal observation process; they do not automatically provide an unbiased `lambda_s^XY(x)` unless effort and detectability assumptions justify that step. Any joint likelihood must share an explicitly identified latent target and accommodate source-specific observation kernels.

For repeated detections, co-observation data or controlled calibration, some detector parameters can be identified under restrictive assumptions. **Two methods measuring unlinked aggregate counts alone do not suffice** when each method's species×height-specific detection factors are free. Fithian et al. (2015), DOI `10.1111/2041-210X.12242`, rely on explicit multispecies sampling-bias assumptions and survey data. Nothing in this result proves arbitrary z/state recovery.

## 3. Registered source-free nonidentification witness

One shared geographic cell, two species S1/S2, two flight layers Low/High, two *unlinked* independent count-survey methods M1/M2, equal latent species horizontal sums (100,100).

**World A (true vertical partition):** latent per-species `[[90,10],[10,90]]` (columns Low/High), detection M1=0.10 and M2=0.05 everywhere.

**World B (no true vertical partition):** latent `[[50,50],[50,50]]`, M1 detection `[[0.18,0.02],[0.02,0.18]]`, M2 detection half of M1. All detector probabilities are legal [0,1].

Both worlds produce exactly the same expected observed count tables:
- M1: `[[9,1],[1,9]]`;
- M2: `[[4.5,0.5],[0.5,4.5]]`.

Under independent Poisson **unlinked** observation streams, equal expected tables imply the same full likelihood of aggregate count observations. Both worlds also share identical 2D latent species sums, yet:
- True `I(S;Z|X)`: A = `ln 2 - H_Bernoulli(0.9) = 0.368064...` nats (0.531 bits); B = 0.
- Naively treating M1 detections as latent abundance returns `0.368064...` nats in **both** worlds.
- Two-dimensional Schoener overlap of the species = 1 in both. Actual full species×height overlap A=0.2 vs B=1. Projection-inflation A=0.8 vs B=0.

This is an **exact identifiability counterexample**, not a claim that any real acoustic dataset has these detector probabilities. Additional detectors *with independently linked detection histories*, independent effort/known q anchors, or restrictions shared across species can break this equivalence if assumptions are verifiable.

## 4. What counts as ecological 'need for a 3D SDM'?

On **calibrated, same-site/time, same-response-target** intensities, compute
`I(S;Z|X) = sum_x w_x sum_{s,z} p(s,z|x) log[p(z|s,x)/p(z|x)]`.
Declare `w_x`: the estimated community intensity share over sites, **or** externally specified equal-site weights, not one hidden default. At the ecological-population level, this is how informative height is about which species is using airspace once x is known. It is NOT `H(Z|X)` (vertical thickness), `I(X;Z)` (vertical site organization), or `I(S;T|X)` (time partition). ODSP implements the latter and separate heldout transferability; see `odsp.niche_geometry`, `odsp.transferability`, `odsp.projection_loss`.

Even `I(S;Z|X)=0` does **not** mean height never matters: it only implies height is not informative about species identity given the declared x/time/reference distribution. Height can still improve species-specific risk, collision, resource or state predictions.

**Two separate validation gates:**
1. **Identifiability:** q/effort or repeated, linked observation architecture sufficient to distinguish true species×z from detector-specific profiles. If not, only observed-record `I(S;Z|X,D=1)` is estimable.
2. **Transport utility:** on independent held-out **sites/years/communities** (not fixes), compare properly scored 2D-derived identity-blind height vs 3D species-conditioned height, with the *same heldout events, observation kernel and reference measure*. A positive fitted I alone is descriptive and cannot certify transport.

Relative to existing outcomes, ODSP N2's detected Serengeti species×time result is `I(S;T|Site)=0.224275987396` nats with three positive heldout site-fold scores, but remains **camera-detected local-clock-time**, not detector-corrected animal activity. Its Tadarida vertical conditional predictor did not generalize to two held-out individuals. Batter's taxa are not a common co-sampled multi-species airspace community across matching cells/time. The recent two-bat lunar-height experiment did not provide positive heldout lunar prediction. ESDM E5 has 0/17 sources qualifying for independently separating activity from registration. None of these records is a direct calibrated estimate of `I(S;Z|X)` for a multi-species bat community.

## 5. Scientific next gate before field inference

Target a prospectively chosen **co-located multi-species, repeated, simultaneous vertical recording** dataset with aligned time periods, independently characterized vertical detector range/sensitivity, and enough independent sites to hold out. Keep detected-airspace information and latent ecological information labeled separately. Before accessing source-specific species/height outcome values, freeze source coverage, detector-calibration eligibility, observation effort, height binning, study-area support, and independent holdout units.

This new module's output is solely a known-truth **identification failure**; no new ecological positive, no source outcome opening, no manuscript claim promotion.
