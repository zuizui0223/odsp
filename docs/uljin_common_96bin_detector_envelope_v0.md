# When is clock versus solar-time model superiority robust to unknown camera detection?

**Source-free post-PR255 numerical method, NOT evidence of real Uljin
animal behavior.** This is a distinct exact sensitivity route, not
another synthetic two-bin odds-ratio test or a new likelihood theorem.

## The central problem solved

Five predeclared behavioral mechanism candidates — fixed civil clock,
solar-noon clock corrected for equation of time, sunrise/sunset double
anchoring, frozen mean anchoring, and sunrise/sunset phase with a
rising-vs-falling photoperiod branch-specific parameter — were
previously trained and evaluated in PR245 on the **SAME original 96
civil 15-minute bins**. They already account for the change of time
coordinates (including the piecewise solar-phase density Jacobian)
and hypothetical clock-hour device exposure.

But a model predicting the observed timing of *camera detections*
implicitly assumes the camera's detection sensitivity q to true animal
passages is constant across original civil-clock bins, or known.

For fixed, TRAINED model A/B day-specific positive integrated clock-bin
masses a_k and b_k, let the SAME physically true detector q_k be used
for both forecasts. Their conditional probabilities for a fixed
station/date observed event are

    p_A,k(q) = a_k*q_k / sum_j a_j*q_j
    p_B,k(q) = b_k*q_k / sum_j b_j*q_j.

Their log score gap, **on the SAME observed original civil bin k**,
is

    log p_A,k(q)-log p_B,k(q)
      = log(a_k/b_k) - log(Z_A(q)/Z_B(q)).

The per-event q_k cancels exactly only because the detector is SHARED
by the two models for the SAME physical observation cell. The
normalizer ratio Z_A/Z_B still depends on q. Comparing independently
optimized q for model A and model B, or rebinning the species events
into separate solar-phase supports, would give a different and invalid
interpretation.

## Sharp rather than arbitrary detector sensitivity bounds

Suppose the new EXTERNALLY warranted source-free toy near/far camera
detection probabilities q_near=.9 and q_far=.3 hold INSIDE each of
the 96 civil bins. If the true wildlife near-distance passage fraction
w_k lies in [.5−δ,.5+δ] independently per day×civil bin, then
q_k=.3+.6*w_k lies in [.6−.6δ,.6+.6δ]. δ is a hypothetical bound,
not estimated from two broader solar early/late categories in
prior PR253, and **not a confidence interval**.

Test the precommitted δ=0,.02,.05,.1,.2 and two detector-response
structure classes:

- unrestricted **96 q** values independently bounded for each DATE
  and 15-minute CIVIL clock bin, but shared over physical heldout
  stations on the same date and among all candidate predictions;
- more restrictive **6 q** values for six ORIGINAL CIVIL four-hour
  blocks (each group holds sixteen 15-minute cells), independently
  varying by DATE. These intervals must be nested inside the
  unrestricted sharp 96-bin interval.

For group g, define A_g=sum_{k in g}a_k, B_g=sum b_k. Extremize
the positive linear-fractional normalizer ratio

    R(q) = (sum_g A_g*q_g)/(sum_g B_g*q_g)

over the same q hyperrectangle. Its SHARP min and max occur at box
vertices. Solve exactly up to floating point by the sign of
min_q Σ_g (A_g−r B_g)q_g and
max_q Σ_g (A_g−r B_g)q_g, with a FIXED 65 binary iterations.
No need to enumerate 2^96 vertices or make an unwarranted
independence-of-models assumption. Unit tests compare its exact
extrema to an EXHAUSTIVE 2^4 small-cell witness.

For heldout physical sites, each site receives weight 1/16 divided
by its own total detected counts. For each date, the q normalizer
ratio is SHARED by all sites, and detector q can vary independently
across dates; the sharp bounds sum date-wise weighted extrema.
Prediction peaks are trained ONCE using original independent
training physical stations with q constant and then held fixed.
This v0 is robustness of the **fixed-trained** model scores, not a
q-refitted model selection procedure.

## Locked ecological comparisons

The original 41 frozen mirrored astronomical date pairs (82 branch
dates), the original 16 training/16 heldout synthetic physical
stations and all original 96 response bins remain unchanged. Freeze
three generating processes (civil-clock fixed, solar-phase invariant,
season-dependent solar-phase), two event counts 20/200 per
site-date, and single new fixed seed 2026101008.

Freeze exactly FOUR informative candidate score gaps:
(1) sunrise/sunset solar-phase vs fixed civil clock,
(2) rising/falling seasonal solar-phase vs invariant phase,
(3) solar-noon clock vs civil clock,
(4) mean-anchor vs solar-phase.

For these 3×2×4×5×2=240 original paired forecast intervals,
report nominal score gap, sharp lower and upper detector-sensitive
gap, and whether the pairwise ranking survives ALL detector q in
its external hyperrectangle. Weak or contradictory cases are
reported; NO p-values or model evidence posterior implied.

A positive robust gap means only: **with those exact trained
candidate predictive shapes and that source-verified common detector
q envelope, the conditional observational log score ordering
cannot be overturned**. It does not establish a unique ecological
zeitgeber, latent animal activity, endogenous photoperiod memory,
or independent causal temperature/food phenology. Intervals are
SET-IDENTIFICATION of model scores, NOT statistical CIs or protection
against observation count stochastic error, unknown source camera
hours, q heterogeneity across sites, site dependence, or sensor
gold-standard opportunity errors. Statistical q intervals for 96
clock bins would require their OWN simultaneous detector calibration
and alpha budget; four previous broad two-bin q intervals cannot
be silently projected to 96 narrower bins.

The EcoBank Version 1.1 original ZIP, independent camera operation
and calibration source, individual ungulate events and protected
station GPS remain unavailable/unverified. Prior preregistered ODSP
and all terminal prior synthetic results are unchanged.
