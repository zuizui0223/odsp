# Can independent camera reference calibration certify whole-day clock and solar forecast rankings?

**Distinct SOURCE-FREE post-PR256 method. This is not a new observation
of Uljin ungulates, nor a confidence interval for population behavior.**

## Correct connection to prior ODSP ecological analysis

PR245 trained CLOCK, SOLAR NOON, SUNRISE/SUNSET PHASE, mean-anchor,
and PHASE+SEASON families to predict the same 96 original local-CIVIL
quarter-hour event categories. PR256 then derived SHARP sample-score
sensitivity envelopes given an EXTERNALLY BOUNDED but NOT measured
per-clock-bin camera q. Here, for the FIRST time in the 96-bin route,
we test simultaneous Clopper–Pearson q confidence intervals from
independent source-free true-passage reference sensor trials.

To preserve the response target, all competing candidate models use
the SAME animal count frame and SAME unknown q on the original civil
clock. Their fixed-trained conditional observed-event density is

    p_model,k(q) = m_model,k*q_k / Σ_j m_model,j*q_j,

where each m_model,k already includes the model-coordinate solar-time
Jacobian and camera device-operation exposure used in PR245. Comparing
the SAME two models on the same event bins cancels the per-event q,
leaving only their SHARED normalizer ratio for optimization.

## Exact q confidence and a particularly important scope failure

There are 82 unchanged mirrored calendar dates. Compare independent
calibration at two reference resolutions:

- **6 clock 4-hour blocks per day**: 82×6=492 external independent
  binomial-q sources, each assumed constant within 16 original
  15-minute clock cells when used to correct a 96-bin model.
- **96 clock 15-minute bins per day**: 82×96=7872 independent source
  binomial-q values, fully resolving each original response cell.

Both methods use the SAME independent gold-standard total true
opportunity budget at each of two predeclared levels, not the same
number of opportunities per CALIBRATION CELL:

| Gold-standard source true passage opportunities | 4-hour q cells (per cell) | 15-minute q cells (per cell) |
|---:|---:|---:|
| 251,904 | 512 | 32 |
| 1,007,616 | 2,048 | 128 |

Each method uses Bonferroni **simultaneous q calibration noncoverage
alpha=.025 over ALL dates×groups** in its own arm, with exact
two-sided CP intervals at individual tail alpha/(2*G).
This is a familywise 97.5% q **source-calibration** guarantee
under correctly labeled independent Bernoulli opportunities. It
is NOT 97.5% coverage for an expected model score across newly
sampled animal sites or a 5% ecological model-selection test.

The physical q truth varies both by clock block and by season;
three original animal time-generating worlds (fixed civil clock,
invariant solar phase, seasonal solar phase) are crossed with
20/200 events per station/date. Crucially we freeze TWO temporal
truths of the CAMERA detector:

1. q truly constant within every original four-hour civil block.
   Both 6block and 96bin CP calibration models correctly cover
   their relevant actual q time targets, subject to the stated
   interval sampling uncertainty.
2. q fluctuates by a 0.13-amplitude *within-block* sinusoid over
   15-minute bins, with a ZERO block average. Each reference
   passage in a 4h calibration is uniformly randomized over the
   underlying quarter-hour clocks. Thus its 4h pooled reference
   detection SUCCESS is still genuinely **IID Bernoulli(q_block_mean)**
   and binomial CP can cover the source group mean perfectly, but
   that very valid interval CANNOT be used for the 16 heterogeneous
   quarter-hour q values. All coarse-block model order claims
   for this truth are explicitly UNQUALIFIED, never presented as
   calibrated findings, even when the single realized true score
   happens to lie inside the erroneous envelope.

This separates **source calibration validity** from
**target temporal transport validity**, mirroring the ecological
distance-mix issue from PR251–252.

## Frozen full-panel requirements

3 animal time truths ×2 animal event counts ×2 true q temporal
patterns ×2 equal total external calibration budgets ×2
calibration resolutions ×4 predeclared model pairs = **192** records.

The animal observations are generated independently using the
true detector-adjusted 96-clock-bin probability distribution, then
ALL five model family peak parameters are learned ONCE using only
16 independent training physical sites. The SAME heldout 16 sites
and their unchanged observed civil-bin events are compared between
the two calibration methods; no outcome-specific time rebinning,
no retuning the training model to get a preferred result.

For a given paired model A/B, the score difference's event term
does not depend on q and the date-specific normalizer ratio is
optimized sharply using the existing PR256 fractional-linear box
routine. q is SHARED across the two models AND all 16 heldout sites
on that DATE, independent across dates. If any q lower confidence
endpoint reaches zero, fail closed with HOLD; do not fabricate
missing observed events or q=0/unknown camera exposure.

An informative positive sign means ONLY *fixed-trained model*
observed-event conditional predictive ordering under the q box,
with independent q confidence on the correct TIME GRANULARITY.
There is still stochastic sample/site uncertainty in those same
heldout wildlife observations. A future **separate** source-free
route must add independently sampled physical-site score inference
with allocated error accounting if the scientific claim seeks
population-level expected predictive superiority; no such claim
is made here.

The synthetic q sampled per day and pooled across 16 sites implicitly
assumes q is shared across physical stations on that day. Actual
sensor-to-sensor sensitivity varies, weather/vegetation and angle/
distance/velocity matter, and the original source 41 date pairs may
have unverified device hours. None of those data are available, and
none are invented. The original ODSP source training/validation
routes remain unchanged.
