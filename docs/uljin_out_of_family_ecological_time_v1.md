# From astronomical predictive fit to an ecological mechanism claim

**Separate source-free robustness panel. Post-PR #245 first outcomes.**
The parent matched-generating-family benchmark recovered all 30
synthetic truths but that self-recovery is an implementation diagnostic,
NOT evidence the models will correctly describe actual ungulates.

This new test keeps exactly the previous five competing clock,
solar-noon, sunrise/sunset phase, average-anchor, and phase+season
models with the SAME 96 local-clock bins, Jacobian, training-site
split and device-operation convention. New intentionally unmatched
truths (20 or 200 events/site/date; three fixed seeds) are:

1. **Bimodal crepuscular use:** event density equal mixture of
   solar phase peaks at 06:00 and 18:00. Each candidate's one-peak
   assumption is wrong, so a winning single anchor does not mean
   a single physiological pacemaker.
2. **Mixed civil and solar schedules:** 50% fixed civil-clock peak
   and 50% sunrise/sunset-anchored peak. A single winner can hide
   simultaneous anthropogenic scheduling and changing light cues.
3. **True seasonal diel change:** animals switch from solar phase
   peak 07:30 rising branch to 09:00 falling branch, while detector
   sensitivity is invariant.
4. **Detector-only season effect:** true animal phase density remains
   fixed 07:30 in both branches. The detector varies by season AND
   time such that q_b(k)=c_b*p_seasonal_b(k)/p_fixed_b(k), for each
   already defined 15-minute CLOCK observation bin k, with c_b
   scaling to keep 0<q<=1. The resulting observed conditional
   detection-time distribution is **exactly the same as world #3**
   across all 82 original dates. The same fixed RNG makes the entire
   synthetic recorded event count array exactly identical too.
   Even infinite heldout stations could not distinguish these
   biologically opposing latent mechanisms from detections alone.
5. **Weak branch effect:** 07:30→08:00 phase peak shift, checking
   whether a small ecological residual is practically detectable
   rather than reporting only a strong easy effect.

A positive improvement by the branch-dependent solar-phase model
is evidence for a season-dependent **detected-event timing law**
in the synthetic benchmark, not proof of endogenous photoperiod
memory, temperature response, feeding phenology, animal learning,
or even latent activity change. Seasonal camera sensitivity,
vegetation occlusion, bait or operator effort and environmental
histories are competing explanations.

Every fitted candidate's EXPECTED KL regret against the known
synthetic truth is computed on the SAME civil-bin observation
distribution, alongside the actual heldout event log score.
This shows whether apparent winning models are truly adequate
as descriptions of the observed process; finite-sample model
ranks alone can be misleading.

Real Uljin seasonal work requires independently time-logged
camera operation, calibration of season×time detection bias
through non-animal triggers or concurrent independent sensors,
station-blocked validation, direct temperature/vegetation/
human disturbance records and fixed 41 astronomical date
pairs. Do not invent those covariates or reclassify any
previous primary ODSP route.
