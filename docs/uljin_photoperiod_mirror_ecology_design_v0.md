# New independent ecological candidate: photoperiod-mirror hysteresis in Korean ungulates

**Status:** ONLY an outcome-free ASTRONOMICAL and source-provenance
study design. No animal event rows or camera-operation records were
downloaded, and no ecological support/prediction outcome or new
qualified ODSP route is asserted.

## Question worth testing

> For the SAME ungulate species at the SAME physical camera station,
> does detected daily time use the same sunrise/sunset-relative
> distribution on dates with nearly IDENTICAL daylength, when the
> photoperiod is LENGTHENING versus SHORTENING?

This is a sharper natural contrast than comparing January with July.
Under an invariant solar-phase organization, matching astronomical
daylength should largely remove that specific geometrical
driver. Systematic residual differences in the rising versus falling
photoperiod branch could indicate additional seasonal information
(historical temperature, food/vegetation, reproduction, human activity,
etc.) or residual detection biases. Such differences do NOT by
themselves prove a physiological molecular-clock hysteresis mechanism.

Seasonal activity and thermoregulatory changes are already known,
including mammals in Hokkaido (Ikeda et al. 2016, PLOS ONE
DOI 10.1371/journal.pone.0163602) and Japanese macaques in Yakushima
(Hanya et al. 2018, DOI 10.1371/journal.pone.0190631).
The science question is not merely whether seasons differ; it is
whether they differ **at comparable photoperiod and common sampling
support** beyond a correct astronomical transform.

## Public source: explicitly better effort metadata, NOT yet admitted

Jeon & Lim (2026), Biodiversity Data Journal 14:e191556,
DOI 10.3897/BDJ.14.e191556, describe a year-long camera study of
four sympatric ungulates in Uljin, South Korea.

Published source counts are:

| Public metadata | Published total |
|---|---:|
| Camera stations | 82 |
| Independent ungulate event detections | 4,623 |
| Camera nights scheduled | 30,410 |
| Downtime nights | 560 |
| Functional camera nights | 29,850 |
| Study regions | 2 (UJ1, UJ2) |
| Event date range | May 2022 – May 2023 |

The source paper reports files in NIE EcoBank
DOI 10.22756/ETC.20260000001022, Version 1.1,
including operation windows and downtime in
01_core_data/camera_operation_log.csv,
events in 01_core_data/cameratrap_event_records.csv,
station-season effort summaries and QA.

The scientific advantage over earlier attempted Snapshot USA dates
is **an explicit camera-operation log** instead of simply trusting
a photo-derived Survey_Nights variable. HOWEVER:
neither actual original operation-log values nor their
observation-independent provenance has been inspected, and the
public **functional nights** summary does not itself guarantee
hour-by-hour exposure. The data may be unusable for our clock-time
density comparison without more hardware timing evidence.

All station-specific coordinates are withheld. The released
coordinates are generalized for UJ1 and UJ2 with uncertainty
about 10 km. Our public astronomical comparison consequently
uses 36.85°N only as illustrative/study-area representative
context; no precise camera locations are invented.

The 82 cameras are NOT 82 independently sampled landscapes.
They belong to TWO site-regions, so any region-population generality
or strongly cluster-independent test is unavailable from this
dataset alone. Repeated station/site results would be interpreted
conditionally on this Uljin study design.

Paper's own example already analyzes solar adjusted time and
hour-normalized period categories. A mere solar transformation
is NOT a new scientific discovery here.

## Outcome-blind photoperiod mirror construction

Before ever opening the released event CSV, this contract fixes:

- public astronomical latitude 36.85° N;
- ascending dates 2022-05-01 through 2022-06-10;
- descending dates 2022-07-01 through 2022-08-31;
- same-year pairing only, separated by >=21 calendar days;
- apparent solar zenith 90.833 degrees, standard solar
  declination formula and daylength duration;
- absolute paired-daylength error <=0.15 h (= 9 minutes);
- one-to-one no-replacement selection. Enumerate all eligible
  ascending×descending date candidates, sort by ascending
  |daylength difference|, then ascending date then descending
  date, and greedily match without replacement.

This uses ONLY public astronomy and date ranges mentioned
in the source paper. It says NOTHING about whether any camera
actually worked on either matched day or whether a particular
ungulate appeared at that station.

The first frozen calendar, produced by
odsp/uljin_photoperiod_mirror_design_v0.py,
is an input DESIGNED BEFORE opening raw wildlife data. The
hard hourly uptime gate is independent and not passed by
printing eligible astronomical dates.

## Further admission gates before any animal outcome analysis

1. Verify source archive identity, legal public access and exact
   immutable operation-log and event-table hashes. Do not
   infer the raw download URL from the DOI without observing it.
2. Check original operator field logs truly record hardware
   operation and non-operating intervals independently of
   detection timestamps. A variable labelled start/end is
   insufficient: the Snapshot USA 2024 paper retrospectively
   corrected those values from first/last photos.
3. Derive actual operating minutes by local clock-hour/category
   for every physical station/date from real device logs.
   If only daily/nightly totals are available, STOP hourly
   exposure-corrected density scoring.
4. Freeze original station IDs, both study-region identities,
   unit-level exclusion and training/validation frame BEFORE
   reading events. A camera or repeat period is not a fresh
   independent site. Missing detections must not determine
   inclusion of a station or calendar day.
5. Use a correct normalized CONTINUOUS circular time density
   with explicit solar-to-civil Jacobian and training-only
   bandwidth/complexity selection. Compare an invariant
   solar-phase density against rising/falling-specific
   solar-phase densities, on the SAME observed civil time
   outcome and same complete operating-time exposure.
6. Evaluate each of the four reported ungulates, without
   post-outcome selecting whichever species shows a favorable
   seasonal sign. Report species-site coverage and multiple-
   comparison limitations; conditional site-level uncertainty
   does not become population-level iid confidence by assertion.
7. Temperature/prey/human-disturbance effects require
   independent predictors, measured outside the heldout
   wildlife response. The paper's frequency_of_people
   feature is itself detection-derived, not an independent
   field observation by default.

**Go/no-go:** Only a valid original hourly operation log plus
adequate common physical-station sampling and predeclared
scoring provenance would authorize the NEXT source version
to read ungulate event outcomes. This design does not authorize
it and cannot be silently promoted.

## Why this helps ODSP

The old Rhode Island result was a negative exploratory
prediction finding complicated by (i) species/site composition,
(ii) conditioning on season, (iii) solar six-bin projection
capacity, and (iv) potentially unequal camera detection.

This independent candidate would test a more precise ecological
idea: seasonal branch dependence *after matching solar geometry*,
with observation effort separated from event times. It remains
an observational contrast; sunrise, temperature, vegetation,
abundance and photoperiod response may still covary.

Results from this candidate must NEVER be counted as a
second positive ecological replication unless an actually
independent original source, scientific source-provenance
admission and outcome-blind frozen evaluation have all passed.

References:
- Jeon & Lim 2026: https://doi.org/10.3897/BDJ.14.e191556
- NIE EcoBank source DOI: https://doi.org/10.22756/ETC.20260000001022
- Vazquez et al. 2019: https://doi.org/10.1111/2041-210X.13290
- Ikeda et al. 2016: https://doi.org/10.1371/journal.pone.0163602
