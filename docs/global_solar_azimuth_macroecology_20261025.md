# ODSP: Original-data solar-azimuth macroecology

Date: 2026-10-25. Status: DRAFT / registered metadata census and executable source-locked route. **No empirical solar-azimuth effect has yet been established.**

Protocol: ../research/GLOBAL_SOLAR_AZIMUTH_MACRO_V0_CONTRACT.json  
Geometry: ../scripts/solar_azimuth_macro_v0.py  
Original-source runner: ../scripts/run_global_solar_azimuth_macro_v0.py

## Central independent ecological question

**Do animal travel directions show repeatable solar-relative organization across species, environments, seasons and independently sampled field populations?**

This is a registry-first *primary analysis of public original observations*. It is not a meta-analysis of ecological effect sizes reported in the source papers. Original GPS files are the observations; publisher DOIs are provenance/attribution.

Use original UTC GPS timestamp, location and consecutive moving-step endpoints to calculate initial geodesic travel bearing B and simultaneous NOAA-approximate solar azimuth A clockwise from north. Analyze the relative circular angle B-A.

Crucial limitations: GPS displacement direction is **not animal body orientation**, solar gazing, actual solar exposure, shade avoidance, thermoregulation or evidence of use of a sun compass. Sun azimuth is geometrically coupled to time-of-day, latitude and season; migratory routes, slopes and habitual commuting directions can generate apparent alignment.

## Frozen complete public Movebank snapshot: 2026-10-19

Data source: ../research/seasonal_database_catalog/2026-10-19/movebank/catalog.json

| Source metadata category | Packages |
|---|---:|
| ALL public archived data packages in the frozen frame | 437 |
| Explicit GPS listed in original sensor metadata | 258 |
| GPS or GNSS | 259 |
| Argos Doppler Shift ONLY (no GPS/GNSS overlap) | 53 |
| Broad GPS/GNSS/Argos candidates | 312 |
| GPS/GNSS with metadata-reported location count >=10,000 | 205 |
| GPS/GNSS with metadata-reported animal count >=5 | 237 |
| GPS/GNSS meeting both metadata count thresholds | 198 |

The 259 GPS/GNSS packages carry **161 distinct literal scientific-name labels**; the broad 312 carry **195 labels**. These labels are **not validated independent wild species**. Other packages may be version duplicates, shared studies or incomplete tracking records. The 198 are *metadata priority*, not true GPS-interval admissions. Failed and low-coverage sources remain in the 437 denominator. Neither sufficient duration nor heading accuracy can be inferred from location counts.

## Predetermined movement outcomes

At each original source-qualified moving interval (30–120 min, displacement >=0.1km, <=60km/h, solar elevation at start/mid/end >=10°, no cross-solar-date):

1. **Raw sunward travel**: E[cos(B−A)].
2. **Raw solar-axis travel**: E[cos(2(B−A))], which treats sunward and antisunward axial movement together.
3. **Compensated solar-direction association**: E[cos(B−A)] − E[cosB]E[cosA] − E[sinB]E[sinA]. The subtraction removes a *fixed marginal geographic compass preference* but NOT arbitrary clock-time schedules.
4. **Clock-restricted circular covariance**: the same excess computed within animal × year × month × two-hour apparent-solar-time cells, with >=8 GPS steps, >=3 different solar dates and >=5° solar-azimuth span. Sparse blocks are **UNIDENTIFIABLE**, not a biological zero.

An admitted animal-year has >=30 eligible steps across >=5 distinct original solar dates. Equal eligible clock cells per animal-year, equal years within animal, equal animals within original source-taxon; do not weight global species means by GPS fixes. One thousand animal-cluster bootstrap draws are descriptive conditional on sampled animals.

Even a positive adjusted effect may be induced by within-clock-bin route shifts, wind, weather, migration or sample timing. This protocol measures potentially nontrivial ecological geometry, not direct sunlight causation. A stricter future model must explicitly measure environment and baseline route orientation.

## First original-source route

Prior-used source archives (exploratory for the NEW directional estimand; never untouched validation):

- Original provider-MD5 Canadian elk, Florida pig and Connecticut black bear GPS files (three complete frozen source manifests).
- Original provider-MD5 Utah 2019–20 four-ungulate archive, all four exact source taxon labels.
- Original provider-MD5 Wyoming 2019–20 two-ungulate archive, both labels.

Every cohort and unavailability must be reported. Original full GPS paths, exact locations, individual identifiers and timestamps remain within the ephemeral runner; group results only leave. Existing ODSP seasonal-speed and N2 terminal decisions do not change.

## Macroecological inference after the pilot

The intended unit is **independent study-population × species × geographic context**, not package or GPS fix. Audit overlapping study IDs, source versions, animal deployments and physical regions before pooling. Complete a provenance-aware source qualification table for ALL source candidates, not just positive pilot cases.

Prospective explanatory variables: hemisphere, latitude, study season, ERA5 thermal/water histories, wind, satellite vegetation phenology, habitat openness, terrain aspect, trophic and migration guild. Compare (i) azimuth-related directionality across independent populations, (ii) how local thermal/moisture states moderate its magnitude, (iii) season changes at matched solar geometry. Include source coverage selection, tracking interval, clock/elevation support, taxonomic and geographic imbalance in the model and its limitations.

No preferred positive sign is assumed. Preserve zero/negative effects, source unavailability and ecological confounds. Progression to a global claim requires independently supported spatial populations, not repeated paper examples.

Primary output envisioned: a reusable derived macroecological database with original source DOI, source-level unit independence, biological taxon, position/solar-time QC fractions, qualifying animal count, mean directional indices, uncertainty, and region/environment linkage. Coordinates/individual tracks are never redistributed.
