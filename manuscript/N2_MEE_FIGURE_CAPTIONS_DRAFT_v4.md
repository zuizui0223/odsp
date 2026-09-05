# Figure captions — state-prediction manuscript v4

## Figure 1. From scalar ecological prediction to state-resolved prediction and transfer testing

Conceptual workflow of ODSP. A conventional ecological prediction may return one scalar support or suitability value for a location or contextual unit. ODSP instead defines one or more explicit ecological states `A` and predicts a normalized distribution `P(A|X)` from contextual information `X`. The fitted state distribution is summarized descriptively but receives its main evidential test in prospectively independent groups. The primary ODSP transfer score is the held-out log-score gain of the state-resolved prediction over the lower-information training marginal `P(A)`. Independent groups are classified separately as generalizing, non-generalizing or mixed; a structurally inadequate design can terminate as unavailable before transfer scoring.

## Figure 2. Known-truth finite-sample prediction benchmark

Mean conditional-versus-marginal held-out log-score gain across 128 replicates for stable-generalizing, unorganized and shifted-non-generalizing prediction families at 50, 250 and 1000 observations per base state. Stable organization remained positive in 128/128 replicates at every sample size, shifted organization remained negative in 128/128, and the unorganized family approached zero as sample size increased. The benchmark demonstrates that more precise recovery of a training-state distribution does not create positive transfer when held-out organization is shifted.

## Figure 3. Prospective BOP_RODENT cross-individual altitude-state prediction

Primary random-forest held-out log-score gains for 30 independently scored tagged raptors, grouped by species. The horizontal zero line marks equality with the lower-information training marginal altitude distribution. Twenty-seven individuals had positive gain and three had non-positive gain; the prospectively frozen all-individual rule therefore classified the endpoint as mixed despite a positive descriptive mean. *Buteo buteo* (5/5 positive) and *Circus pygargus* (9/9) were species-level generalizing, whereas *C. aeruginosus* (7/8) and *C. cyaneus* (6/8) were mixed. All 30 individuals showed positive multiclass Brier improvement, reported in the accompanying panel/annotation as a complementary bounded probability metric.
