# When can a seasonal phase effect survive camera-detection bias?

**Source-free exact statistics and partial identification; NOT a study of
actual Uljin ungulates or a new general theorem.**

A good heldout seasonal phase model (PR #245) still cannot discriminate
between two biologically different explanations: a change in animal
time-of-day activity and a time×season change in camera sensitivity
(PR #246). Therefore an ecological claim requires independent, quantified
calibration of camera trigger/registration efficiency, not only accurate
camera ON/OFF logging.

## Fixed two-bin, within-physical-site matched-date estimand

Given PRESELECTED two solar-phase categories (early/late) on both
rising/falling photoperiod branches, define four independently recorded
device operating times E_bk, latent animal passage/encounter rates A_bk
and detection probabilities q_bk. Assume independent event arrivals
and independently recorded operating exposure, so expected detected
event rates have mu_bk=E_bk * A_bk * q_bk.

The three crossproduct odds ratios obey EXACTLY

  OR_detected_counts = OR_effort * OR_encounter * OR_detector,

where OR = (falling_early*rising_late)/
           (rising_early*falling_late).

Correct device-hour effort yields OR_observed_rate = OR_counts/OR_effort,
but animal occurrence and detector response are STILL multiplied.
Without calibration q in (0,1], the detector crossproduct can be
arbitrarily large or small, so the latent encounter OR is not bounded.

Under independent Poisson four-cell sampling, conditional on fixed
season and phase-bin margins, the falling-early X count is Fisher
noncentral hypergeometric:
  P_theta(X=x) ∝ C(K,x) C(N-K,D-x) theta^x.
Here the null theta under zero/negative latent encounter interaction is
bounded above by theta_E*B, where externally justified B>=1 bounds the
crossproduct of four detector sensitivities. A conservative one-sided
exact test uses the right tail at theta_E*B. Its one-sided exact 95%
lower bound on latent encounter OR is the inverted lower limit of
the count-OR distribution divided by theta_E*B.

**Key: confidence calibration of q matters.** A four-cell q-interval
obtained by synthetic independent detector tests needs JOINT coverage
(or alpha allocation) before the resulting OR lower bound can retain
overall 95% coverage; pointwise individual 95% q intervals alone do
not suffice. If q calibrations use new external sensor devices, physical
replicates and sampling efforts must be documented. If calibration
interval is deterministic based on true engineering limits, then the
conditional exact lower bound coverage is as stated. If it is itself
statistically uncertain, a new combined-coverage procedure is needed.

The frozen synthetic panel holds:
- Five hypothetical observed 2×2 tables (no shift, weak shift, strong
  shift, operating-effort-only artifact, detector-only artifact);
- Known hypothetical four device-hour exposures, including one
  unequal-effort table where raw count OR=2 but exposure-adjusted OR=1;
- Detection interaction upper bounds B=1,1.25,1.5,2,3;
- Two independently *imagined* q calibration patterns for illustration.
All 5×5 robustness cases, two q interval examples/table, null and
negative results must be kept. There are NO original camera events
or Uljin source ZIP bytes in this analysis.

## What this changes about the time/astronomy comparison

A branch-dependent detected phase timing signal can be reported as
a **predictive seasonal detection law** if validated. It can be
called a within-site latent encounter timing change only when a
calibrated bound B is low enough that the effort-corrected, uncertainty
adjusted lower limit is greater than 1. Even that is NOT automatically
a change in individual circadian timing or memory of earlier
photoperiods. The same latent passage schedule could change with
temperature, vegetation, migration, reproductive period and local
disturbance. Multiple sites and taxa need new predefined clustered
analyses and multiple-testing handling.

Camera sensor calibration could be designed with concurrent thermal
video or overlapping independent detectors (cf. Hofmeester et al.,
2019, Ecology and Evolution, doi:10.1002/ece3.4878; Rowcliffe et al.,
2014, Methods in Ecology and Evolution,
doi:10.1111/2041-210X.12278). A direct independent video reference
has been used in studies of camera false negatives, but no such
data are verified for Uljin. These established recognition/detection
issues are not presented as a new scientific discovery.

The original 41 photoperiod-mirror dates and qualified ODSP routes
are unchanged; field-original hourly device logs, exact detector
response, physical station identity and source events remain HOLD.
