# Source-free proof-of-method: conditional Poisson branch-by-time prediction with zero cells

**Status:** SYNTHETIC method only. This is a stacked, independent methods
candidate and is not a new Uljin animal detection result. The original
82-camera / 41 astronomical date-pair study still needs a verified
EcoBank Version 1.1 archive, independent camera-operation logs,
hourly exposure and physical-site/region sampling provenance.

## The real design failure we are fixing

The public 2026 ungulate paper reports 4,623 independent detections
over 29,850 functional camera nights, but this number is distributed
unequally among four taxa. Selecting only camera×taxon×date pairs that
produce detections on BOTH mirrored dates would severely enrich
high-detection taxa and confound observation effort with selection.

Yet not all zero cells mean the same thing:

- A camera was operating for a positive duration and detected ZERO
  events: a genuine recorded nondetection for the detection-rate
  process, not a missing response;
- A camera was not operating in that time bin: zero animals
  recorded is NOT a biological nondetection;
- A model assigns positive detection count to zero recorded
  operating hours: the exposure/recording contract is inconsistent
  and must fail closed.

All stations, including those with zero detections, must be selected
from the ORIGINAL operation roster before reading animal events.

## Conditional exact cancellation of unknown baseline rate

For each original camera station s, original 41 paired dates p, one of
four fixed ungulate species t, and common 4h civil-clock bin b:

    Y_R ~ Poisson(E_R * lambda_{sptb})
    Y_F ~ Poisson(E_F * lambda_{sptb} * exp(beta_b))

where R is rising photoperiod and F is falling photoperiod, and
E_R/E_F are independently logged real camera-operating HOURS within
the bin.

Condition on N=Y_R+Y_F:

    Y_F | N ~ Binomial(
       N, sigmoid(log(E_F/E_R)+beta_b)
    ).

The nuisance lambda_{sptb} cancels exactly. Positive detections on
only ONE date remain informative, and zero/zero pairs remain in the
complete observation frame even though their CONDITIONAL likelihood
is 1, contributing zero to this particular *conditional* score.

**This does not estimate absolute abundance or occupancy.** Because
we condition on N, an all-zero pair by itself supplies no estimate
of the branch rate ratio. A separate properly offset Poisson or
negative-binomial observation model would be needed for absolute
detection intensity. Calling conditional zero/zero cells positive
evidence of equivalence would be incorrect.

## Meaningful null and alternative

The simple null is NOT “no branch difference whatsoever”.
That would confound a daily increase in all detections with changing
diel organization.

**Null C:** one shared branch log rate ratio alpha in ALL six bins.
Detection rate is allowed to change by a constant factor between
the two calendar branches.

**Alternative T:** separate beta_b for six bins, with frozen
quadratic shrinkage toward their common mean (penalty 2.0);
the overall intercept remains unrestricted except for a tiny
1e-6 numerical ridge.

The alternative targets a season×clock-time SHAPE interaction,
not a change in total detections alone. Training uses source-disjoint
physical stations. Both models score the SAME heldout branch counts
conditional on totals, with identical independently logged hour
offsets. Their heldout conditional log-score difference is averaged
within each physical station over all its original paired cells,
then equally across stations. UJ1/UJ2 are reported separately.

This is a regularized prediction comparison, NOT a p-value or a
confidence theorem. Real station spatial independence remains
unproven, and two study regions cannot support general regional
population inference.

## The second confound we cannot yet eliminate

The original 41 date pairs were matched to within 0.55 minutes in
DAYLENGTH. They still differ in SOLAR NOON / sunrise / sunset CLOCK
time by about 5–10.5 minutes owing to the equation of time.

A true species-invariant *SOLAR-PHASE* detection distribution may
therefore produce different 4h CIVIL-CLOCK bin rates on paired
dates EVEN WITH NO biological branch hysteresis. Thus a positive
branch×clock-bin gain in the current conditional Poisson method
would NOT yet establish branch-specific solar-phase reorganization.

The corrected scientific model would integrate a continuous
solar-phase intensity and the real camera exposure function over
the same civil-clock observation bins, with the correct solar-to-clock
Jacobian. Alternatively, evaluate response in solar-phase bins
while transforming the operating-time exposure measure consistently.
All bandwidth/complexity and astronomy choices would need a NEW
pre-outcome freeze and independently verified source station
metadata. Do NOT silently promote this first structural algorithm
as a test of animal photoperiod memory.

## First synthetic acceptance tests

The frozen plan
ULJIN_CONDITIONAL_BINOMIAL_ZERO_PRESERVING_V0_CONTRACT.json
declares two artificial worlds:

1. All bins have the SAME branch log rate ratio 0.25: a
   season-level rate change but NO diel shape change.
   The trained branch-shape model should not gain material
   heldout conditional predictive score.
2. The branch rate ratio changes systematically across clock
   bins: [-1.3, -.9, -.4, +.4, +.9, +1.3].
   The fitted bin-dependent model should improve heldout score
   at new invented stations.

The tests also require exact exposure-ratio behavior, rejection
of positive detections at zero exposure, inclusion of single-day
only detections, retention of double-zero cells and physical
train/test station disjointness. These are synthetic
method-validation tests, not empirical estimates for goral,
water deer, roe deer or wild boar.

The initial source-free experiment can succeed while the real
EcoBank record admission remains entirely on HOLD.

## Source and earlier work

- Jeon & Lim (2026), Biodiversity Data Journal 14:e191556:
  https://doi.org/10.3897/BDJ.14.e191556
- Original Uljin astronomical pairing and operation-log feasibility:
  PR #230 / ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json
- Published-taxonomic-rate-only scenarios in the same parent:
  ULJIN_PUBLISHED_SPECIES_SPARSE_MATCH_SENSITIVITY_V1_CONTRACT.json

No source event table, species/timestamp row, original log or
protected camera coordinate is read in this synthetic study.
No Rhode Island result, ODSP qualified process or prior failed
endpoint is reclassified.
