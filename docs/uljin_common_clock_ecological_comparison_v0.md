# Which astronomical or seasonal clock best predicts animal detection timing?

**Experimental synthetic ecological design — not evidence for Uljin wildlife yet.**

## Why a new comparison is needed

Previously the original Jeon & Lim (2026) study already used clock
time and equinoctial solar-time sensitivity. Solar correction and
double-anchor transformations are NOT novel: Vazquez et al. (2019,
Methods in Ecology and Evolution, doi:10.1111/2041-210X.13290) compared
double anchoring methods including average anchoring; Iannarilli et al.
(2025, Journal of Animal Ecology, doi:10.1111/1365-2656.14213) explain
the need for hierarchical activity-time models with site differences
and unequal detection effort.

The **ecological** question is: under comparable daylength, which
environmental clock provides transportable information about detected
diel timing? Compare FIVE mechanistic predictions:
1. Fixed civil clock: stable response to time-based anthropogenic
   schedule or other clock-linked process, NOT proof of people.
2. Solar noon shift: activity follows solar daily geometry and
   equation-of-time displacement.
3. Equinoctial solar phase: behavior keyed to sunrise/sunset
   anchors, with day and night rescaled to 12h each.
4. Average anchoring: sunrise/sunset mapped to FROZEN average anchor
   times, retaining the original dataset's average daylength.
5. Solar phase plus photoperiod branch: the same two-anchor astronomy
   but with separate fitted rising versus falling branch peak. A
   positive effect is compatible with seasonal phenology, temperature
   history, reproductive state, disturbance or observation bias — not
   necessarily endogenous photoperiod memory.

## The methodological fairness problem

A simple comparison between a KDE scored on clock bins and a KDE
scored on shifted solar-phase bins is **NOT A COMMON PREDICTIVE TASK**.
The conditional likelihood targets differ; reclassifying the events
changes the scoring resolution and effectively changes where the camera
time exposure is placed. A profile defined as a *density per model
coordinate hour* has the CIVIL-TIME rate

  lambda_c(t) ∝ f( u_m(t) ) × | du_m(t) / dt | .

At each physical station/date, integrate that civil-clock intensity
**ONLY during independently recorded operating intervals** inside the
same 96 civil 15-minute bins. Normalize over the actual operating
frame to predict P(original civil-clock bin | same camera date/event
total). The models are scored on the IDENTICAL measured event counts.
A solar-phase JACOBIAN is essential for this density convention.
This convention differs from modeling a per-physical-hour hazard
directly as f(u(t)) without Jacobian; that would be a distinct
predeclared estimand and requires a separate route.

All five models are estimated on 16 simulated physical training
stations and scored on different 16 heldout stations, using the
original 41 frozen mirrored day pairs per site. The branch-dependent
candidate has a real extra parameter, so any heldout advantage is
descriptive predictive evidence only, NOT automatically a corrected
hypothesis test of biology or transport to a new ecological region.

## Frozen synthetic known-truth panel (no real events)

Five generating mechanisms: civil clock, solar noon, equinoctial
sunrise/sunset phase, average anchor, and solar phase with an
additional falling-branch peak shift from 7.5h to 9h. Fixed shape
kappa=4, background rate 0.04; 48 potential half-hour peaks,
15-minute common scoring bins, 8-node Gauss-Legendre quadrature
split at sunrise and sunset. Same period-day total per physical
station=20 or 200, 3 deterministic RNG seeds each. All original
41 matched dates retained. The model never reads original EcoBank
event times, camera-operation CSV rows, restricted station GPS or
hardware device uptime. It simulates ideal 24h cameras ONLY for
diagnostics.

Results must include ALL 30 worlds, per-model training-chosen peak
positions and site-equal heldout log score (nats/event), differences
relative to clock and phase, and winner counts only as descriptive
metadata. It does not claim calibrated model-selection error rates
or causal activity mechanism recovery.

## Real biological gates

Actual source-specific analysis requires verified, timestamped
deployment and downtime intervals independent of animal detections,
local clock accuracy and station-specific or uncertainty-bounded
astronomical coordinates, an event deduplication protocol, zero-event
site/date retention, and prespecified physical-site blocked validation.
If only date-censored operation exists, the structural support bound
of PR #244 cannot supply exact likelihood offsets; those must be
profiled through a separately qualified interval-exposure likelihood
or kept HOLD. A residual spring/autumn difference would remain
consistent with temperature history, food phenology, mating,
human disturbance, predator activity and detection changes.
Any causal claim needs independently observed ecological covariates
and time-resolved observational controls.

No previous qualified ODSP process inference or historical
empirical endpoints are reclassified.
