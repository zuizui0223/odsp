# Familywise certification of predictive transfer ceilings

A point predictive-resolution ceiling does not distinguish genuine transfer from sampling variation. ODSP therefore treats the full `independent group × adjacent resolution step` table as one simultaneous inference family.

## Estimand

For group `g` and adjacent levels `k-1 -> k`, define row-wise score gain

```text
delta_igk = s_ik - s_i{k-1}
```

and weighted group mean `G_gk`. These are the same realized transfer increments returned by `decompose_predictive_resolution`; the uncertainty layer does not redefine the estimand.

## Aligned block bootstrap

Within each independent group, the user supplies a defensible resampling block such as day, bout or camera-day. If no block is supplied, ODSP treats rows as independent and records that assumption explicitly.

For every bootstrap draw within a group, the same sampled block indices are used for every resolution step. This preserves covariance among the adjacent increments rather than bootstrapping each step independently. Independent groups are resampled separately, with draw indices aligned to form the joint bootstrap distribution across the full family.

## Global max-t interval

For every estimable cell, let `SE_gk` be the bootstrap standard error. For draw `b`,

```text
T_bgk = |G*_bgk - G_gk| / SE_gk
M_b   = max over all estimable (g,k) of T_bgk.
```

For familywise confidence level `1-alpha`, the common critical value is `quantile_{1-alpha}(M_b)`. Each simultaneous interval is

```text
G_gk ± c SE_gk.
```

One critical value therefore covers the whole estimable resolution family.

## Decisions and certified ceiling

For tolerance `tau`, a cell is `robust_positive` when its lower simultaneous bound exceeds `tau`, `robust_nonpositive` when its upper bound is at or below `tau`, and otherwise `uncertain`. A cell is `unavailable` if its positive-weight row gains are non-finite or if its group has too few resampling blocks.

An adjacent step is `robust_generalizing` only when every independent group is robust-positive. Any unavailable group makes the step unavailable; otherwise uncertainty or conflicting signs remain visible rather than being pooled away.

The **certified transfer ceiling** begins at the lowest-information level and advances only through consecutive `robust_generalizing` steps. Once a step is uncertain, mixed, unavailable or robust-non-generalizing, the ceiling stops. A later positive step cannot jump over that failure.

This separates three claims:

```text
full model > pooled overall                     total predictive gain
species -> context point gain > 0              point resolution increment
species -> context robust in every group       certified resolution transfer
```

Only the third advances the certified ceiling.

## Boundaries

`certify_predictive_resolution` conditions on the supplied held-out predictive scores. Its block bootstrap quantifies validation-sample uncertainty and controls familywise multiplicity across the resolution ladder. It does not by itself include uncertainty from refitting an upstream learner; ODSP's separate refit-ensemble machinery remains a distinct layer.

Intermediate comparator levels must have finite scores on all positive-weight held-out rows. The richest predictor may assign zero probability or density and therefore `-inf`; the affected final-step cell then becomes unavailable for interval certification. Earlier finite steps can still be certified, but the ceiling cannot pass the unavailable step.

## Usage

```python
from odsp.predictive_resolution_certification import certify_predictive_resolution

result = certify_predictive_resolution(
    levels=(
        ("pooled", pooled_log_score),
        ("species", species_log_score),
        ("context", context_log_score),
        ("full", full_log_score),
    ),
    groups=individual_id,
    blocks=day_id,
    sample_weight=weights,
    familywise_confidence_level=0.95,
    bootstrap_draws=4000,
    minimum_blocks_per_group=8,
)

print(result.point_transfer_ceiling)
print(result.certified_transfer_ceiling)
```

The score vectors may come from Python, R, Stan, INLA, `brms`, `mgcv`, neural networks or any other modelling system, provided all levels are evaluated on the same held-out outcomes with a common score orientation.
