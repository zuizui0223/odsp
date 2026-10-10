# How accurately must the seasonal animal passage-distance mix be known?

**Source-free, deterministic ecological sensitivity test, separate from
the already observed results in PR #252. It is NOT field power,
causal season memory, or a new general statistical theorem.**

## A physical/biological interpretation of delta

Reference camera calibration samples 50% near and 50% far independent
animal passages, detector q_near=.9 and q_far=.3 in ALL four
prespecified photoperiod branch×solar early/late bins. So effective
reference q=.6 and its detection OR=1. Real wild animal passages
may have a different near proportion w_bk. Declare only an EXTERNAL
constraint |w_bk-.5|<=delta IN EACH cell, with the same delta
used independently for all four cells; this is not a distributional
prior and does not assume joint correlation of the w shifts.

With q_near=.9 and q_far=.3 KNOWN exactly,
q_effective=.3+.6*w and each q lies in
[.6-.6delta,.6+.6delta]. The exact supremum detector seasonal
crossproduct is

    B_oracle(delta)=((1+delta)/(1-delta))^2.

Thus even small changes in the opportunity mix can generate a
considerable apparent season×time interaction without any change
in latent encounter time; at delta=.3 the B is 3.44897959 (the
same parent PR252 ecological confound).

The DATE×SEASON animal event count contrast is defined using the
original fixed 2 early/late solar-phase bins (still not all 96
original civil clock bins) and one original date-pair site. For
independently known four camera operating exposures E, the detected
count-rate OR is OR_count/OR_E. For a particular observed artificial
2×2 table, invert the exact conditional Fisher right tail at
alpha_animal=.025 to give the one-sided 97.5% lower count OR L.
For an externally justified deterministic maximum detector B(delta),
the lower latent encounter OR is L/(OR_E*B(delta)). Only >1
supports a positive latent encounter timing effect under the
declared sampling model.

The exact **oracle tipping radius** beyond which the positive
claim no longer holds is

    delta_star = (sqrt(L/OR_E)-1)/(sqrt(L/OR_E)+1),

if L/OR_E>1; otherwise the test is not positive even when delta=0.
At equality the conservative nonrandomized test condition p<alpha
is not met; the value is a supremum, not an included positive endpoint.

## Add detector-q sampling uncertainty honestly

Actual q is not known. Illustrate independent reference calibration
with eight binomial q values (two distance strata × four fixed
season/phase bins), each with representative successes round(n*q)
and n in the ORIGINAL frozen grid 50,200,1000,5000 PER q cell.
Use exact Clopper-Pearson 8-cell simultaneous 97.5% bands
(alpha_q=.025, Bonferroni over eight cells), requiring independent
and correctly labeled reference animal passages.

For each q bound, target qeff=w*qnear+(1-w)*qfar is separately
minimized/maximized over its q endpoint intervals and w in
[.5-delta,.5+delta]. Four resulting lower/upper qeff bounds
give maximal plausible detector OR. If a denominator is zero,
HOLD rather than unbounded false certainty. Split alpha_q=.025
and independent animal exact alpha=.025, so the combined false
certificate error is bounded by .05 ONLY IF the four external
target w limits are deterministic, truthful source-independent
assumptions. A statistically ESTIMATED w interval would need an
ADDITIONAL allocated error budget and must not inherit this .05.

Freeze five artificial count tables inherited from PR #247
(no shift, weak shift, strong shift, unequal effort negative-control,
and an observed OR2 count example), 6 delta values
(0/.05/.10/.15/.20/.30), and 5 calibration treatments (oracle
and the 4 n sizes): exactly 150 direct analytical cells. Report
all sign/pass/fail/HOLD outcomes, as well as oracle and calibrated
tipping-radius suprema. No first outcome is selected after viewing
results.

The 'unequal effort' algebraic stress table has an 8h observation
in one cell: this is physically legitimate ONLY for an aggregated
observation bin whose duration is at least 8h, and is NOT usable
as an original frozen 4h Uljin device-hour eligibility record.
No site-specific biological seasonal result is implied.

## What this implies for fieldwork

A threshold such as delta<=.10 must be supported by independently
observed *target passage opportunities* in BOTH astronomical season
branches and BOTH time categories. From focal-camera *detections*
alone one cannot reconstruct the true passage mix because distant
missed animals are systematically absent. Separate synchronized
reference video, thermal cameras, radar or other sensors could
supply independent near/far passage-opportunity counts, and their
own missed-opportunity process must be audited. If only an
estimated w bound is available, extend the simultaneous confidence
interval analysis with additional alpha spending rather than
using the deterministic delta formula as a falsely certain bound.

Also distinguish activity timing from animal movement route,
speed, angle, size and changing camera visibility with weather/
vegetation. The q model here only includes a two-level distance
stratum and is not known to transport to those additional
biological conditions. No original Uljin animal or hardware record
has been read; no previous ODSP qualified route has been modified.
