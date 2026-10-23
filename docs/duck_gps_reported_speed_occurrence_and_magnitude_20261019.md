# Relative nightward change is not necessarily a nighttime increase

**2026-10-19 | ODSP PR #267 | Supplementary post-hoc sensor description. Not a calibrated behavioral hurdle model or a new independent ecological replication.**

## Question and scope

The preceding audit found that 95.3% of original accepted DAY/NIGHT date blocks had zero median GPS speed. The present analysis asks what the same observations say when separated into (i) the fraction of positive speed reports and (ii) the magnitude conditional on a positive report. This is not a redefinition of zero as animal inactivity, a fitted stop/move classifier, or a claim that the frequency of movement bouts was measured.

The original source describes `ground.speed` as a GPS sensor estimate in m/s and documents tag- and battery-dependent sampling. It supplies no validated low-speed behavioral threshold or scheduled-missing-fix denominator for this analysis: van Toor & Waldenstrom (2025), https://doi.org/10.5281/zenodo.16940654. Current tag documentation describes speed, accelerometry, and configurable day/night schedules as distinct outputs; it does not establish how the historical source's zeros map to behavior (https://www.ornitela.com/10g-transmitter).

The old median endpoint, all source filters, original greedy matched dates and cohort are unchanged. A new mean/positive-report endpoint cannot retroactively confirm or replace the old median result. The design was written after earlier effects and the zero audit were known and is explicitly exploratory, not preregistered confirmation.

## Definitions and weights

Let u = log(1 + reported speed in m/s). For each original matched date block calculate p = fraction of u > 0 and M = mean(u), including zeros. Within each individual-cell-cycle and branch/solar zone, average dates equally, then define C = M/p when p > 0. C is the positive-u conditional mean in this date-equal mixture; it is undefined when p = 0. Never fill it with zero.

All seasonal contrasts are (falling NIGHT - falling DAY) - (rising NIGHT - rising DAY). Multiple groups of an individual, if present, have equal weight, followed by equal individual weighting within a species. Raw reading counts are not analysis weights.

Where both branch conditional means exist in each solar zone, the mean-u change has the exact symmetric decomposition:

Delta M = mean(C_F, C_R) * (p_F - p_R) + mean(p_F, p_R) * (C_F - C_R).

Subtract the DAY decomposition from the NIGHT decomposition. These are arithmetic contributions to a sensor descriptor, not causal effects of movement frequency and movement intensity. If conditional values are absent, the decomposition is undefined but p and M remain reportable.

## Source replay and execution

Verified workflow: https://github.com/zuizui0223/odsp/actions/runs/39190221510 . All six known-truth tests passed before empirical execution, including date-equal versus reading-equal weighting, a zero median with positive reports, occurrence-only and magnitude-only examples, and no imputation of undefined conditional means.

The original source MD5 is `1972d0ef08b83c2b88a169ba07bb48b3`. The entire original GPS result was replayed byte-for-byte (SHA256 `557c21c6446556f16c24ccf496b0b2c7ea8e22c259830a9e9a764faec10e5e8b`) before new outputs. The accepted sample remains **9 birds, 186 matched pairs, 744 date/solar-zone blocks and 7,850 readings**. All seven source taxa and all old per-species median effects are unchanged. The two previously identified repeated timestamps in teal blocks are retained and counted; they are not asserted to be independent sampling opportunities.

New aggregate JSON SHA256: `16596b0740c135cfa4b8e82f8c587aae4669ce974f25a2a5db399a4c721e51ba`. Workflow artifact `duck-gps-reported-speed-two-part-20261019`, ID 12160220279. Archive SHA256: `f2ee738d1b5146632e8bc9972e0818eddf4322de0ab2d8db195656fb7dd2c361`.

## Main descriptive example: Northern pintail, five birds

Only pintail has the original minimum five-bird descriptive support. It contributes the same 57 date pairs; this remains a small, selected sample, not a powered population test.

| Solar zone | Rising-branch positive-report fraction | Falling-branch fraction | Falling minus rising |
|---|---:|---:|---:|
| DAY | 30.8005% | 27.5625% | **-3.2381 percentage points** |
| NIGHT | 26.4534% | 25.8698% | **-0.5837 percentage points** |

The NIGHT-minus-DAY gap is -4.3471 pp in the rising branch and -1.6927 pp in the falling branch. Its seasonal change is therefore **+2.6544 pp**. The relative nighttime difference becomes less negative even though positive-speed reports decrease in BOTH zones. This is not a measured increase in nighttime movement or a shift to greater absolute nocturnal activity.

Three of five individual positive-report contrasts are positive and two negative. Leave-one-individual-out mean difference ranges from **-0.5727 to +4.8253 pp** (NOT a confidence interval). Thus the positive aggregate direction is not stable to all single-individual exclusions.

For mean log1p reported speed, the seasonal NIGHT-minus-DAY double difference is **+0.0488321**. Its arithmetic contributions are **+0.0172348** from changes in the positive-report fraction and **+0.0315972** from changes in conditional positive magnitude. All five birds have defined conditional branch/zone means, so these contributions sum to the same full five-bird descriptor. This does not establish either causal component biologically. The original median-based mean effect remains **+0.0296940**, unchanged, and is a different estimand.

## All seven taxa retained

| Original taxon | Birds | Original pairs | Double difference in positive-report fraction (pp) | Double difference in mean log1p speed |
|---|---:|---:|---:|---:|
| Anas acuta | 5 | 57 | +2.6544 | +0.048832 |
| Anas clypeata | 1 | 10 | -18.2857 | -0.068597 |
| Anas crecca | 1 | 8 | -14.6131 | -0.144913 |
| Anas penelope | 0 | 0 | undefined | undefined |
| Anas platyrhynchos | 0 | 0 | undefined | undefined |
| Anas querquedula | 1 | 13 | +4.2399 | +0.029911 |
| Anas strepera | 1 | 98 | +6.5855 | +0.017786 |

The teal and garganey original median contrasts were zero, while their positive-report and mean-u contrasts are nonzero and oppositely signed. This illustrates that a zero median difference does not imply identical sampled distributions; **one bird per species does not justify species-level ecological conclusions**. Teal has no positive falling NIGHT reports, so its conditional positive-magnitude contrast and symmetric decomposition remain undefined. No pseudo-observation was inserted.

## Ecological use and stopping rule

The useful distinction is between **relative temporal allocation** and **absolute behavior within a time window**. A more positive night-minus-day contrast can result from reduced daytime observations, greater nighttime observations, or a mixture. A biological study should distinguish daytime avoidance from exploitation of nighttime opportunities with calibrated activity measures; the current GPS source cannot identify either mechanism.

Do not make this sensor diagnostic the main ecology result. The main manuscript's source-backed core remains the original matched-photoperiod vegetation differences and separation of within-camera timing from among-camera recording-location composition. This GPS follow-up belongs in supplementary measurement interpretation. It adds no new animals, ecosystems or behavioral validation, and should not trigger another speed-cutoff search.

A relevant validation precedent is Yu et al. (2022), https://doi.org/10.1111/2041-210X.13878: six Pacific black ducks, directly behavior-labeled accelerometry, eight behavior classes every two seconds, and reported overall classification accuracy 92.04%, with field records lasting 56 days to 14 months. That paper shows what independently labeled behavioral observations can look like. It is **not** a calibration for the OrniTrack speed values used here. Its authors archive labeled accelerometer data at https://doi.org/10.5061/dryad.rbnzs7hd5, but availability of a complete seasonal field time series was not verified here. No such data were downloaded or claimed as another seasonal replication.

## Implementation

- `research/DUCK_GPS_REPORTED_SPEED_TWO_PART_20261019.json`
- `scripts/duck_gps_reported_speed_two_part_20261019.py`
- `tests/test_duck_gps_reported_speed_two_part_20261019.py`
- `.github/workflows/duck-gps-reported-speed-two-part-20261019.yml`

PR #267 remains Draft. No original numerical result is replaced; no activity, predation, migration, energy expenditure or universal solar-seasonal law is inferred from these uncalibrated sensor reports.
