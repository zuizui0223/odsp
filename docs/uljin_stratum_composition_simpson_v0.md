# Does partial pooling create a fictitious diel-shape response? (source free)

This deliberately constructs **two physical-site baseline diel phase profiles**
(early and late). Every site has one original-mirror-pair active exposure
and 40 other empty pairs in the fixed 41×6/site scoring denominator. With
the global null `Y_fall(s,k)/Y_rise(s,k) = r_s` **constant over six time bins
within each site**, the null has no seasonal change in any site's diel-shape.

However, if early sites have branch multiplier 3 and late sites have
multiplier 1/3, summing across sites yields a high falling/rising ratio in
early bins and a low ratio in late bins: a constructive Simpson
compositional interaction. This **does not involve solar-noon geometry**,
and is different from PR #236. Training and test contain both site types.

## Three procedures, intentionally different estimands

1. Pooled shared branch×time six-bin logistic predictor (previous
   `fit_conditional_branch_model`, lambda=2). A positive entire-site
   heldout score gain signals prediction of the *mixed sampled-site
   population*, NOT within-site biological reorganization. Its gain>0
   decision is NOT a nominal alpha=0.05 significance test.
2. Two partially pooled logistic predictors with one site-specific
   **overall** season-branch effect and ridge lambda_u=0.2 or 10.
   We only report the fitted global phase-specific branch-coefficient
   RANGE as a descriptive estimator; no formal coverage claim.
   The different penalties express different exchangeability strength.
3. Exact site-pair conditional simulation holding both observed
   branch total D_s and all six pooled bin totals M_s,k fixed.
   Under the strict within-site shape-invariance null, falling events
   are multivariate hypergeometric. A score based on standardized
   six-bin residual sums is compared to 99 synthetic conditional
   permutations on whole heldout sites, with p=(1+#>=)/(100).
   This controls conditional size at most 0.05 under the modeled
   exchangeability null, including heterogeneous r_s, while needing
   repeat detections in both branches and across bins.

These procedures CANNOT be compared as if they had the same inferential
target, false-positive definition, or sampling universe.

## Frozen synthetic panel

3 truth worlds (homogeneous null, rate-composition confound null, true
within-site diel phase change) × intensity 0.1 and 1.2 × 100 worlds,
separate deterministic sampling and permutation seed identities.
42 of 82 independent simulated physical sites are held out for pooling
and conditional tests. Every 2022 astronomical pair has one early and
one late site, but exact calendar shift and real camera data are not
read. All null effects and failures must be shown as run.

The central point: **out-of-sample predictive improvement under
composition change does NOT establish within-site seasonal evolution,
learning or behavioral plasticity**. Independent real device activity,
actual within-species site-pair support and heldout external data would
still be needed to assert real Uljin seasonal ecology.
