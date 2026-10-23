# ODSP public-data seasonal ecology: native source and individual observation support

Date: 2026-10-19. Research programme: [solar vs ecological calendar](database_seasonal_ecology_programme_20261019.md). Source frame: [437-package public archive snapshot](../research/seasonal_database_catalog/README.md).

## What was measured from original sources

This advances beyond reanalyzing individual published animal-activity figures. The study first enumerated **all 437 public Movebank Data Repository packages**, then examined the provider's native ORIGINAL file bundles for every fixed UUID without selecting on published effects. [Complete native-file audit, Action 39202214632](https://github.com/zuizui0223/odsp/actions/runs/39202214632) passed its two jobs:

- **437/437** package ORIGINAL bundle inventories resolved; **0** source-listing failures.
- **1,677** ORIGINAL bitstream entries across the packages. **These are files, not 1,677 tracking studies or unique biological samples**; README and reference-data files are included.
- This first-stage catalog retains provider bundle UUID, file name, size, checksum and package attribution. File discovery alone does not establish sampling cadence, permission to redistribute, or hypothesis eligibility.

A separately frozen, deliberately *non-representative* observation-opportunity pilot then read three original mammal GPS CSVs by exact provider bitstream UUID and verified the official MD5 of **every file** before counting recorded positions. The three cases contrast northern latitude and feeding ecology and were specified from package metadata before opening their movement values.

| Source | GPS rows authenticated | Distinct source-qualified individuals | Observed individual×years with ≥10 conservative equal-photoperiod date pairs |
| --- | ---: | ---: | ---: |
| Ya Ha Tinda elk, Canada (*Cervus elaphus*, DOI 10.5441/001/1.5g4h5t6c) | 1,585,456 | 175 | **200** |
| Florida wild pig (*Sus scrofa*, DOI 10.5441/001/1.719) | 79,165 | 10 | **5** |
| Connecticut black bear (*Ursus americanus*, DOI 10.5441/001/1.706) | 156,366 | 21 | **34** |
| **Total** | **1,820,987** | **206 within sources** | **239 individual×years**, not 239 independent populations |

No source rows were missing a valid timestamp, individual identifier or coordinates under this source-only audit. The pilot individually matched dates with at least three source GPS points in day *and* night on each date, opposite northern-summer-solstice branches, approximate source daylength mismatch ≤5 minutes and ≥30 days of date separation, with no reused dates. Geometric day/night classification is approximate mean-solar time and sunlight (no measured terrain shading). These are **candidate observation opportunities, not verified movement-interval day/night exposure or effect estimates**. A year with ten candidate date pairs can fail the later valid-adjacent-GPS-step and sampling balance criteria. The 200 elk years arise from one archive population, and any repeated elk ID in multiple years remains one biological individual.

The successful workflow generated a full native bundle manifest and an aggregate candidate-coverage receipt as action artifacts. No individual identifiers, exact GPS points or original CSV files were committed or uploaded.

## Direct biological continuation

The source-only coverage was completed before the separate GPS-step response contract [v0](../research/MOVEBANK_SOLAR_MOVEMENT_V0_20261019.json) was committed. The next source-verifiable estimate uses only consecutive positions from an individual 30–120 minutes apart, fully within a common day/night solar interval, normalized by elapsed time. It estimates source-specific **within-individual seasonal contrasts in straight-line observed movement speed**, reporting daytime and nighttime terms separately. It does not treat photos, fix counts or the speed of a single recorded instant as a validated 24-hour activity budget.

**Current claim ceiling:** Three openly archived, independent studies can support exploratory *within-individual ecological patterns* if their actual displacement cadence qualifies; they do not yet prove thermal/vegetation causation, a common species sign or global generality. The macroclimate pilot is an independently sampled environmental database and not three additional animal populations.

References: [source code](../scripts/movebank_native_ecology_20261019.py), [fixed source roster](../research/MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json), [observation tests](../tests/test_movebank_native_ecology_20261019.py), [original inventory Action 39202214632](https://github.com/zuizui0223/odsp/actions/runs/39202214632).
