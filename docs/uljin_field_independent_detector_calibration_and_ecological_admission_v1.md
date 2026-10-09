# Field-ready admission protocol: Uljin temporal cue and detector calibration

**Status: methods specification only, not source admission or an invitation
to open animal events.** This document is an implementation proposal
created *after* the first completed CP-vs-Hoeffding synthetic results.
It does not amend any frozen trial results, statistical alpha budgets or
the original 41 daylength-mirror calendar.

## 1. Biological estimands must stay distinct

1. **Detection-time law:** among animal detections, does a civil-clock,
   solar-noon, sunrise/sunset solar-phase, mean-anchor or solar-phase +
   rising/falling photoperiod model predict *the same* 15-minute civil
   observation bins on held-out stations? All candidates are ranked in
   the SAME clock-time outcome space and integrate independently logged
   camera exposure, using coordinate Jacobians.
2. **Latent passage/encounter timing:** after accounting for separately
   recorded device operating hours AND independent q calibration, does
   detected season×phase interaction imply a change in animal passage
   rate? This requires a calibrated simultaneous q bias envelope.
3. **Causal seasonal zeitgeber, seasonal memory, or internal clock:**
   not identified by (1) or (2) alone. Weather history, food phenology,
   reproduction, predators, human schedules and animal detectability
   must be separately measured and hypotheses differentiated.

These targets should never be interchanged in a manuscript.

## 2. Define the *opportunity* before calibrating

A q-reference **trial** is one independently labeled complete animal
passage through the camera's prespecified trigger/recognition field,
whether or not the focal camera detects it. A video FRAME is NOT a
new independent passage. For the binomial model, a passage must be
reliably distinct from previous passages and conditionally independent
after specified sampling/blocking; repeated images of one animal,
group movements and consecutive frames must not inflate n.

Reference sensor requirements:
- continuous independently time-stamped video/thermal or overlapping
  device, with calibrated own missed-passage risk, not the focal
  camera's image-derived first/last operation times;
- common clock synchronization and documented drift against
  Asia/Seoul civil time at deployment, maintenance and retrieval;
- reference reviewed/annotated without seeing whether focal camera
  detected a passage; a detection failure is a legitimate q=0 outcome;
- prespecified observable passage gate, min separation to deduplicate,
  treatment of animal group crossings and camera malfunction;
- all known missing periods and ambiguous reference passage labels
  reported, NOT silently interpreted as clean negatives.

Without independent assurance that reference labels are correct,
Binomial(n,q) over *all* true opportunities is not justified.

## 3. Preserve the original astronomically frozen observation frame

For each original physical station and each of the original 41
ascending/descending date pairs, archive a response-independent
structured device-operation frame with locally offset-aware start,
end and downtime timestamps. Include **zero animal detections** where
the device truly ran. Reject positive animal events outside verified
operation. Only the original source operation and independent q trial
records may define monitoring eligibility—not wildlife photo counts.

The original PR230 solar geometry is based on coarse public geographic
representatives. Station-specific coordinates are withheld; do not
invent them. Carry prespecified solar-phase uncertainty envelopes
into comparisons if actual protected coordinates are unavailable.

The first ecological model comparison should use all five unchanged
PR245 candidate families in identical 96×15min civil-time bins.
The original two solar phase bins used for the q hypothesis must be
fixed *before* inspecting per-species seasonal outcomes and should not
be selected to maximize an observed detector bias adjustment.

## 4. Required protected source field groups (not actual values)

- **Operation:** anonymized immutable physical device ID, original
  field-deployment/install/retrieval/maintenance log source timestamps,
  time zone, downtime reason, source entry/revision history, clock drift.
- **Detection event:** hashed event ID, animal species (with error/
  uncertain label), timestamp, linked physical device, image/video
  deduplication lineage, trigger mode, animal group/pass identifier.
- **Reference calibration trial:** reference passage ID and time;
  time uncertainty; station and season×phase allocation; verified
  passage through focal capture geometry; focal detection yes/no;
  focal detector event linkage; reference sensor uptime; reference
  labeler blinding; observation certainty; distance/angle/velocity and
  weather/vegetation occlusion if independently observed.
- **Environmental alternative explanations:** time-stamped ambient
  and past temperature, illumination/cloud cover, vegetation and
  food phenology, mating/reproduction indicators, predators and human
  traffic, each with clear source and measurement window.

The draft model must operate on anonymized outputs only and avoid
exposing protected camera coordinates or exact sensitive site metadata.

## 5. Simultaneous calibration and audit gates

For the prespecified site/date-pair/taxon/two-bin hypothesis, retain
the four independent reference trial success/total counts:
(rising,early), (rising,late), (falling,early), (falling,late).
No assumption that n is identical across bins is necessary for
exact cellwise CP intervals, but the current *frozen simulation*
uses n=50,200,1000,5000 per cell. Any real unequal-n extension must be
a separately preregistered/source-qualified route.

The corresponding q intervals require four-cell simultaneous
coverage and proper alpha spending (e.g. .025 calibration + .025
animal test), not four 95% intervals plus an additional 5% test.
The detector interaction upper cap

    B = upper(q_fall_early)*upper(q_rise_late) /
        [lower(q_rise_early)*lower(q_fall_late)]

is undefined/unbounded if a denominator lower bound is zero. Return
HOLD—not a positive ecological effect. If provenance independence,
reference sensor opportunities or exact original device exposure are
unverifiable, keep the real-data branch HOLD.

Document calibration q variation across species/body size, passage
angle/distance and vegetation. If the reference opportunity mixture
is unlike genuine movements, pooled q may not transport to wildlife
events even if its intervals are numerically narrow.

## 6. Biological falsification and reporting

A branch×solar-phase prediction that survives both independent device
effort and detector bias still supports ONLY *season-dependent
encounter timing* at sampled sites. Correlating with temperature,
vegetation or reproduction does not by itself prove causation. Report
the competing clock, noon, anchor, solar phase and branch models,
held-out site uncertainty, all zero-effort and zero-event site/date
cells, two-region dependence, and detector-efficiency sensitivity
rather than merely whichever model wins.

**Empirical status:** exact Version 1.1 EcoBank source archive and
independently authenticated hourly camera logs have NOT been
materialized; q-reference opportunities have NOT been observed.
Therefore no animal activity, photoperiod hysteresis, or biological
memory conclusion is available at present. Previously qualified
ODSP routes remain unchanged.
