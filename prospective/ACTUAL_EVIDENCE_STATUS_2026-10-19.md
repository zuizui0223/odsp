# ODSP descendant biological generality — evidence and next gate

**Updated 2026-10-19; this file does not revise any frozen ODSP, batter or mina endpoint.**

## Verified source-screen findings

### INBO lesser black-backed gull / Schiermonnikoog
- Version-pinned archive: Zenodo 20706447, 2017–2020 GPS yearly exports.
- Reference metadata: 29 individuals.
- Completed archive-pinned, altitude-blind x-y/time/flight-screen CI: [run 39216613590](https://github.com/zuizui0223/odsp/actions/runs/39216613590).
- 435,570 flight-proxy events; 108,365 earliest 5-min bins.
- **9 different animals** retain >=2 scorable days on supported 5-km cells across years (2018 best within-year screen: 8).
- Frozen source minimum 10. **Structural source gate FAILS**. This is not a negative biological result. No vertical values opened.

### INBO Mediterranean gull / Antwerp
- Version-pinned archive: Zenodo 15685037, 2021–2024 GPS yearly exports.
- Reference metadata: 14 animals.
- Altitude-blind screen: 142,285 flight-proxy events, 115,189 earliest 5-min bins, 14 individuals with >=2 matched days in at least one year; by year 2021=3, 2022=13, 2023=9, 2024=7.
- Structural screen: [run 39216613590](https://github.com/zuizui0223/odsp/actions/runs/39216613590).
- Independent biology freeze: `prospective/MEDGULL_CENTERED_ALTITUDE_TEST_FREEZE_V1.json`, selected 2022 **prior to altitude access** from the maximal x-y/time support.
- Biological run [39218355817](https://github.com/zuizui0223/odsp/actions/runs/39218355817) completed. Earlier run 39218148543 failed at Python import **before opening altitude**, and only the entrypoint invocation was repaired.
- 2022 raw GPS rows = **458,251**; flight-proxy 5-min bins = **46,508**. Altitude QC passes: **46,505 / 46,508 (99.99355%)**, with 0 missing and 3 out-of-bound.
- 401 sessions/days have >=50 QC-valid bins. However, after strict own-other-day vs other-species-matched-cell-and-other-date scoring, only **9 animals** meet >=2 complete scored days, below preregistered **10**.
- **Terminal = `altitude_supported_individuals_unavailable`**. The uncalibrated mean self-vs-other score = **-0.014494591842618162 nats/event**, 241 scored day sessions, is DESCRIPTIVE ONLY; no valid permutation p-value exists. Do not present as a supported biological negative, null identity or a failure to find specialization.
- The initial structure screen overestimated final availability because its conspecific reference included other birds recorded on the **same date**, while final scoring requires comparator birds on other dates. Future structural screens should explicitly evaluate full endpoint support, including same-date removal, before proclaiming final statistical eligibility. This is a data/contract mismatch, not evidence that more liberal thresholds should be chosen.

## Next independent dataset: DELTATRACK corrected v5

- Corrected Zenodo record [22102508](https://zenodo.org/records/22102508) has a mixed-species tracked colony at Neeltje Jans.
- Reference CSV contains 100 rows but **99 unique animals**: *Larus argentatus* = 25, *Larus fuscus* = 74.
- Deployment-date metadata alone suggest up to 25 animals from **each species** overlap May–July 2020, more than later years. This is a **metadata upper bound**, not independently recorded flight eligibility.
- Frozen source `DELTATRACK-gps-2020.csv.gz`, MD5 `730549beb8079213ac893d3bf126c2bf`.
- Two species are screened **separately** using prior May–July, 5–55 m/s, 5-min, 5-km, minimum two matched days, minimum ten different birds design.
- Structural workflow: [DELTA run 39219324200](https://github.com/zuizui0223/odsp/actions/runs/39219324200) was queued when this ledger was authored.
- No 2020 DELTATRACK altitude has been opened; no result or claim should be imagined.

## Biological inference until a successful independent nonbat source

The original question 'bat versus penguin: coincidence or special clades?' remains unresolved. They are **different ecological endpoints**, not a matched clade contrast:
1. `batter`: individual flight-altitude identity/centered shape among bats.
2. `mina`: within-colony breeding-component spatial concentration during decline.
A shared central-place perspective is a *hypothesis*; no common mechanism is established.

The next falsifiable question is whether independently tracked **nonbat flight taxa** show whole-session-centered individual vertical shape identity under the same coarse x-y occupancy and source-specific permutation null as `batter`. No successful independent nonbat species-wide result exists in the current prospective extension as of this update.
