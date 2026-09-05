# N2 state-resolved prediction synthesis — 2026-09-05

## Revised scientific center

The strongest current ODSP use case is no longer merely to quantify how much information a flat ecological representation discards. The predictive formulation is:

`context X -> P(ecological state A | X) -> independent-group scoring`

The output is a distribution over declared ecological states such as altitude layer, depth class, time bin, phenophase or behaviour, rather than a single suitability scalar. The framework then tests whether the richer state prediction improves held-out probabilistic prediction relative to a lower-information marginal state distribution.

## What ODSP is

ODSP is a **model-agnostic state-resolved ecological prediction and evaluation framework**. It is not a new MaxEnt- or random-forest-style occurrence algorithm. A native discrete conditional learner provides a transparent baseline; covariate learners such as multinomial logistic regression and random forest can generate `P(A|X)`; arbitrary external probability fields can be scored under the same ODSP metrics.

The primary held-out contrast is

`G_j = E_heldout,j[log P_train(A|X) - log P_train(A)]`,

computed separately for prospectively independent group `j`. Positive gain means the state-resolved model assigns higher held-out log probability than the training marginal state representation. Group signs are not pooled away: all positive = generalizing, all non-positive = non-generalizing, conflicting signs = mixed.

## Validation chain

### 1. Known-truth predictive behavior

Across 128 replicates per cell, stable predictive organization yielded positive gain in every replicate at n=50, 250 and 1000 per base state. Shifted organization yielded negative gain in every replicate. Unorganized support converged toward zero gain as sample size increased. State-probability RMSE fell from about 0.05 at n=50 to about 0.012 at n=1000.

This establishes that the implementation recovers the intended predictive regimes rather than simply rewarding extra conditioning structure.

### 2. Prospective empirical estimability: MH_ANTWERPEN

The marsh-harrier endpoint contained 193,370 thinned admissible events, but only three independent tagged individuals. The frozen design required at least four. The endpoint therefore terminated as `empirical_state_prediction_unavailable` before any RF transfer fold was executed.

This is not a prediction failure or a biological null. It demonstrates that event abundance cannot substitute for independent replication.

### 3. Prospective multi-species state prediction: BOP_RODENT

The fixed BOP_RODENT v3 endpoint admitted 154,655 events from 30 individuals and four species. The primary RF predicted one of four absolute-altitude states from external temperature, geographic position, cyclic local-solar time, cyclic day-of-year and species identity.

Results across prospectively held-out individuals:

- 27/30 positive primary log-score gain relative to the training marginal altitude distribution;
- mean gain +0.570910 nats/event (descriptive only);
- 30/30 positive multiclass Brier improvement;
- mean Brier improvement +0.334984;
- mean top-1 accuracy 0.7562;
- mean assigned probability 0.6484.

The frozen all-individual rule nevertheless yields `empirical_state_prediction_mixed` because three individuals had non-positive log-score gain. Species-level results were generalizing for *Buteo buteo* (5/5) and *Circus pygargus* (9/9), and mixed for *Circus aeruginosus* (7/8) and *C. cyaneus* (6/8).

The multinomial-logit sensitivity was weaker but still positive for 22/30 individuals, indicating that the RF result is not equivalent to a universal learner-independent claim.

## Role of the earlier N2 empirical chain

The earlier Tawaki, bat and Serengeti analyses should remain in the paper, but their role changes.

- Tawaki: estimability can fail before a biological claim opens.
- *Tadarida teniotis*: substantial added-axis thickness can coexist with failed cross-individual transfer.
- Snapshot Serengeti: added temporal organization can transfer across independent spatial folds.

Together they motivate why a state-resolved predictor requires an independent transfer audit rather than only a richer fitted representation.

## Revised central claim

> **ODSP extends ecological prediction from a collapsed scalar representation to a probability distribution over declared ecological states, and tests whether that additional state resolution improves prediction in independent groups.**

The public-data evidence supports strong but heterogeneous state prediction, not universal transfer: one prospectively chosen endpoint was structurally unavailable, while a larger multi-species endpoint improved primary log score for 27/30 independent individuals and Brier score for all 30, yet retained three genuine transfer failures under the predeclared terminal rule.

## Claim ceiling

Do not claim that ODSP automatically estimates fundamental niche, causal mechanisms, unbiased animal use, height above ground from AMSL, or universal cross-species transfer. The state axis and observation process remain biological design choices. ODSP supplies a prediction target, scoring architecture and fail-closed transfer decision, not semantic truth by itself.
