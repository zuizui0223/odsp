# Where does uncertainty in season×solar-phase detector response come from?

**Post-PR254 analytical method plus independent source-free validation.**
This is a prospective sensitivity study with prior PR254 simulation
results already exposed. It is NOT actual Uljin ecology, a new
time-coordinate transformation, a global field allocation theorem,
or a calibrated test of an endogenous photoperiod zeitgeber.

## Decomposition at the ecological measurement stage

In four originally preselected season×early/late solar phase bins, a
camera detects near-distance passages with probability a_i and
far-distance passages with b_i. Wildlife passage opportunities have
independently measured near-distance fraction w_i. The detector
sensitivity for TARGET events is:

    p_i = w_i*a_i + (1-w_i)*b_i

and its nuisance seasonal interaction is:

    gamma_q = (p_falling_early * p_rising_late) /
              (p_rising_early * p_falling_late).

Eight independent, correctly labeled binomial reference detector
samples (nq passages for each 4×2 distance cell) estimate a and b,
while FOUR other independently labeled passage opportunities
(nw references for each 4 season×solar bin) estimate w. Both reference
streams are independent of source animal detections.

By the multivariate delta method, the first-order sampling variance
of the LOG detector interaction is

    Var(log gamma_hat) ≈ A/nq + C/nw,

    A = Σ_i { w_i² a_i(1-a_i)
             + (1-w_i)² b_i(1-b_i) }/p_i²,

    C = Σ_i (a_i-b_i)² w_i(1-w_i)/p_i².

No independence is claimed between observations in the same animal
passage; the binomial independence is an EXPLICIT artificial
assumption. Each of the 4 log interaction coefficients is ±1 so its
squared sign disappears in the first-order variance.

This is **ONLY camera detector calibration uncertainty**, not the
sampling variance of original animal event counts, nor unknown
camera uptime, station clustering, wrong opportunity labels or
causal season-specific behavior. The earlier correctly controlled
Clopper–Pearson + exact Fisher decision remains unchanged.

## Continuous idealized measurement allocation

With equal *per-passage reference opportunity cost* across all 8 q
and 4 w cells, the original fixed total external opportunity budget
is T=8*nq+4*nw. For the variance criterion only, differentiating
A/nq+C/nw subject to the cost constraint gives

    (nq/nw)_variance-optimal = sqrt(A/(2C))

with q's fraction of total opportunity cost equal to
8*(nq/nw)/(8*(nq/nw)+4).

This continuous optimum is NOT guaranteed to maximize finite-sample
Clopper–Pearson+Fisher certification probability, nor to minimize
person-hours/camera installation costs or site opportunity access.

The frozen truth mechanisms and total costs are exactly inherited
from PR254 (source-free qnear=.9, qfar=.3; balanced near mix=.5
or seasonal near mix [.2,.8,.8,.2]; T=2400/6000/12000/24000).
Compare all 3 preselected reference allocations per budget:
equal-nq=nw, q-heavy and w-heavy, on 4 prior truth worlds. No
post-first-outcome new candidate selection.

## A direct numerical falsification check

Freeze 800 NEW independent q and w reference calibration draws
per world×budget×design (48×800=38,400). Compute the estimated
log detector OR per replicate and its sample variance. Compare the
observed Monte Carlo variance to the first-order delta prediction,
including separate q-only and w-only uncertainty diagnostics.
The acceptance gate requires absolute relative discrepancy <=20%
for ALL 48 cases (nq,nw>=100); a failure remains recorded and
is not repaired by tuning the biological cases or finding a
favorable random seed. The pre-result contract and its SHA are
logged separately from the first scoring receipt.

The ecological follow-through is straightforward: if a study
claims seasonal phase activity changes after adjusting for camera
response, it should estimate BOTH calibration precision and target
passage-mix precision and report their contribution to the
uncertainty in gamma. Even then, accurate independent camera
operation logs and matched stations/dates and species need
source validation. Clock vs solar comparisons should maintain the
same civil-clock observation bins as PR245; one two-bin gamma
contrast cannot identify a whole-day diel density, temperature
history, vegetation, individual circadian rhythms or photoperiod
memory.

**The original EcoBank v1.1 ZIP, original operating records,
independent passage opportunities and species detections have
not been accessed. All qualified ODSP inference routes are
unchanged.**
