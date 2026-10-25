# Original GPS solar-relative orientation × hourly ERA5 wind/irradiance

**ODSP ecological continuation, 2026-10-25. Exploratory source-primary observation; no causal or population-general claim.**

## Completed main question

Can a shared-site, shared-season, shared-solar-time difference between two species in their observed GPS travel bearing relative to the Sun be compared with the SAME original GPS steps relative to wind-flow direction and ERA5 shortwave/temperature weather?

**Yes, for all four previously supported original multispecies taxon pairs across two original study archives.** All source UUIDs were previously fixed, source provider-original bitstreams MD5-verified and every original matched-cell solar contrast replayed *before* opening new weather values. Exact weather match on original qualifying GPS steps was **100%** for every taxon in all four paired comparisons. Both source-specific GitHub Actions jobs passed.

This is a new original environmental data linkage, **not** a literature-effect reanalysis, a proof of solar-compass behavior or independent biome replication. These two original data sources were selected after earlier solar-only results disclosed common support; therefore this is post-outcome exploratory for the weather question, not a prospectively confirmed population-level test.

- [Frozen weather and ecological estimands](../research/SOLAR_WIND_IRRADIANCE_SHARED_GPS_V0_CONTRACT.json)
- [First original GPS × ERA5 CI, both source jobs successful](https://github.com/zuizui0223/odsp/actions/runs/40167349742)
- [Machine-readable full four-pair source primary environmental matrix](../research/SOLAR_WIND_IRRADIANCE_FOUR_PAIR_ORIGINAL_GPS_ERA5_V0_MATRIX_20261025.csv)
- [Complete provenance and first-results receipt](../research/SOLAR_WIND_IRRADIANCE_V0_COMBINED_FIRST_RESULT_SUMMARY_20261025.json)
- [Original detailed goose source receipt with nine weather JSON response hashes](../research/SOLAR_WIND_IRRADIANCE_GEESE_FIRST_ORIGINAL_ERA5_RESULT_20261025.json)
- [Original detailed vulture source receipt with four weather JSON response hashes](../research/SOLAR_WIND_IRRADIANCE_VULTURE_FIRST_ORIGINAL_ERA5_RESULT_20261025.json)

## Definitions

For each original consecutive GPS displacement (not body orientation), B is travel compass bearing from north. A is the Sun's NOAA-approximate astronomic bearing at actual original UTC midpoint and GPS midpoint position. Observed sun-relative movement: cos(B−A).

Source-independent gridded hourly ERA5 provides meteorological wind bearing FROM at 100m. Let W = (wind-direction-FROM + 180°) mod 360 denote direction of wind flow. We calculate cos(B−W) (movement downwind alignment) and cos(W−A) (wind direction relative to solar azimuth). The latter is computed only from source GPS location/time and weather: it does **not** use the animal GPS movement B. ERA5 also supplies hourly 100m wind speed in m/s, 2m model temperature in Celsius and surface shortwave radiation in W/m² (the last is a preceding-hour mean, not instantaneous rays on the animal).

Original shared observational context: each species meets >=3 tagged animals, >=3 solar dates, >=15 original 30–120min daytime moving GPS steps per original 1° geographical cell × year-month × 4-hour apparent solar clock bin. Each pair retains the >=3 previously admitted original shared bins. In each bin, average steps within each original animal, then animals within taxon, then common bins equally. Every reported delta is species A minus species B on exactly these previously matched original cells. "Same cell" does not mean animals encounter one another, sample the exact same GPS day or experience identical wind.

## Source-original ecological Results: all four pairs

| Matched taxa (A − B) | Shared original cells | Δ sun-relative travel | Δ wind-flow-relative travel | Δ wind-flow vs solar geometry | Δ shortwave (W/m²) |
| --- | ---: | ---: | ---: | ---: | ---: |
| *Anser albifrons* − *Anser anser* | 21 | **+0.03944** | **−0.04764** | +0.02275 | +1.19 |
| *Anser albifrons* − *Branta leucopsis* | 20 | **−0.11814** | **+0.01342** | **−0.11829** | −7.14 |
| *Anser anser* − *Branta leucopsis* | 36 | **+0.02227** | **+0.01971** | −0.05563 | +5.09 |
| *Cathartes melambrotus* − *Sarcoramphus papa* | 45 | **+0.03366** | **+0.00830** | +0.02505 | −36.91 |

All four rows are actual paired original observed GPS directions linked to newly retrieved original ERA5 hourly modelled weather, **NOT inferred from source paper ecological summaries**. Weather join coverage 100%, solar-only contrasts exact replay. There are **13 original ERA5 1° grid×UTC year requests** (nine in the goose source and four in the vulture source), with the SHA-256 of each raw weather response preserved, and **40,060 unique source-study GPS step records in the union of pairwise shared cells** (25,567 goose, 14,493 vulture; the three goose pair analyses overlap in source GPS records).

### What is positive and ecologically interesting?

**The solar-relative pattern is not numerically identical to a wind-relative movement pattern when both are computed from the same animal movement events.** Specifically, in the *A. albifrons*–*B. leucopsis* matched source, the between-species solar relative mean is −0.11814 while the corresponding wind-flow relative mean is +0.01342, of opposite sign. Their *wind-direction vs solar-bearing geometry* differs −0.11829: species were photographed/tracked in different combinations of modeled wind and Sun direction **even within the same coarse space/month/solar-clock cells**. That is evidence of *observed source sampling/environmental opportunity differences*, not proof that differing wind exposure causes the species' solar pattern. The similar −0.118 magnitudes are **NOT a validated proportion explained by wind**.

Within the *A. albifrons*–*A. anser* matched original source, solar difference is +0.03944 while wind-flow difference −0.04764. In *A. anser*–*B. leucopsis*, solar and wind-flow differences are both weak positive (+0.02227, +0.01971), with differing negative wind-sun geometry. Thus no single "sunward follows downwind" explanation is shared across the original three goose pairs. All are within **one field data archive** and taxon pairs overlap, not three source-independent outcomes.

Within the separate two-vulture field archive, solar species difference +0.03366 exceeds wind-flow difference +0.00830, while species sampling in source sunlight and modeled wind differs as Δ cos(W−A) +0.02505. Their modelled source-exposure shortwave means differ by **−36.91 W/m²** (species A minus B) despite the common 1°/month/solar-time cells. This is the most direct current evidence that *equal astronomical time support does not force equal modelled weather exposure within the observational sample*. However, different source sampling days and times remain confounders. Neither the modeled 100m wind nor surface shortwave is direct exposure at each soaring bird's true 3D path.

### Why the three directional cosines are not causal mediation

Although the per-step identity cos(B−A) = cos(B−W) cos(W−A) − sin(B−W) sin(W−A) is exact, mean cos(B−W), mean cos(W−A) and mean cos(B−A) **cannot** be multiplied or subtracted to yield fractions mediated by wind. Their joint sine/cosine distributions and confounding would matter. The present paired means are separate original observational estimands. Without actual topography, habitat and flight altitude/wind data, "wind explains X% of the solar effect" would be unjustified.

Other limitations: the newly queried historical ERA5 raw weather JSON bodies were NOT committed, only original JSON SHA receipts; the provider can revise retrospective values, as a prior ODSP ERA5 replay investigation illustrated. Preserve the exact first output but do not guarantee numerical reruns will match unless the weather body is preserved/version-pinned. No independent study/region p-values, individual bootstrap uncertainty for these new climate pair differences, multiple-testing correction, study population independence or source field sampling-effort standardization exists yet.

## Independent macroecological target

The present work motivates a biological hypothesis rather than a new time-coordinate prediction contest:

**A substantial fraction of the observed variation in animal solar-relative travel bearings arises from how species occupy different wind, irradiance and habitat states at given astronomical times, in addition to any direct directional response to light.** This is an UNTESTED causal hypothesis, and source observations could be affected by migration, sample schedules and habitat preferences.

To test it independently, expand the original-GPS taxon/population frame beyond these two postselected field archives and link actual time/location ERA5, wind direction, measured/local radiation, canopy, slope aspect and satellite vegetation without using published source effect sizes. Pair independently sampled study-populations and study years, and protect raw GPS data rights. Check whether climatic/terrain associations persist within independent fields and under shared ecological opportunity constraints, rather than increasing event count only.

**Status: Exploratory, source-verified primary GPS × gridded environmental data; not yet an independent worldwide mechanism test.**
