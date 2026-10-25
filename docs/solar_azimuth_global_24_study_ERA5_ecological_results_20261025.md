# Original GPS macroecology: solar-relative animal movement and hourly weather

**2026-10-25 | Ecological source-level report | Original public tracking data, not reported-paper effect synthesis**

This is a **descriptive analysis across the 24 previously frozen header-qualified Movebank original GPS archives**. The purpose is ecological interpretation of observed animal movement relative to the Sun and same-hour modeled radiation and wind. It is NOT an experimental sunlight-cue study, a globally representative random population survey, or a true animal body-orientation dataset. A separate source-novel external radiation hypothesis source roster was frozen *after this exploratory finding* but before the new data outcomes, and is evaluated independently.

## Current measured result: move beyond two bird study examples

- Source universe: all **437** public Movebank archived data packages in a frozen 2026-10-19 catalog; GPS/GNSS sensor-listed 259; canonical original CSV headers with native timestamp/id/lat/lon columns 159. Prior original solar-azimuth analysis verified 40 original archives, 41 species×source cohorts.
- Newly predeclared weather frame: **all 24** original archive files in the previous outcome-blind new-source v2 selection frame, WITHOUT choosing taxa or population according to favorable sunward effects.
- The frozen previously observed original sunward/clock/circular-covariance source×taxon results, individual counts and accepted GPS step counts were **reproduced exactly for 24/24 original source archives BEFORE any new ERA5 weather request**. The provider-original GPS bitstream checksum was verified for all 24/24. [First six-shard original weather source workflow](https://github.com/zuizui0223/odsp/actions/runs/40179789925).
- Source-blind top TWO 1-degree GPS grid × original UTC-year support cells per native species were selected by number of original GPS tagged animals, then original daytime moving steps, never movement-sun response sign or actual weather values. **47** original source×taxon gridyear candidates emerged. **26** met environmental n>=5 tagged-animal source sample support, across **13 distinct original study-source IDs**, **14 literal taxon names**, summing **60,341 same-source GPS daytime moving intervals with matched ERA5 hourly weather**. These source intervals, species and gridyears are **not independent 60k experiments**.
- **21** of the original 47 source×taxon gridyear candidates remained undefined: **19** failed source-level tagged animal support and **2** did not have qualifying original full-year ERA5 weather responses. There were **45** original 1-degree × year historical ERA5 requests in total; **43** have response SHA256 receipts, **2** weather SOURCE_HOLD. Original animal location/IDs/UTC source event times remain unpublished. [Every source, exact previous GPS replay, context eligibility, ERA5 SHA and hold](../research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_FIRST_ALL_RESULTS_20261025.json).

## First ecological hypothesis and source-block inference

Let B be the original observed tagged animal's geodesic GPS movement direction, and A the NOAA-approximate contemporaneous solar azimuth at its real original source location. We study Y = cos(B−A), where positive is movement toward the solar azimuth and negative is movement opposite the solar azimuth. Y does NOT measure animal head/gaze orientation, light detection, direct bodily exposure or body temperature.

For each source field individual and selected original site-year, the environmental predictor and Y are centered in **calendar month × four-hour apparent-solar-clock cells**; a block needs >=8 original weather-matched moving intervals across >=3 distinct original solar dates. An individual slope requires >=2 such blocks and >=20 accepted steps with adequate environmental predictor variation. Each original source×taxon climate effect needs **at least 5 tagged animals**, with seed-locked original animal bootstrap descriptives. Across the study database, siteyears are equally weighted within taxon, taxa are equally weighted within original study, and **each source-study ID is one equal population-context sampling unit** (not weighted by GPS events). Original studies might share actual ecological region or biological population, so their statistical independence is NOT certified.

| Source-sampled ecological weather predictor | Original study IDs supporting slope | Equal-study mean slope of sunward GPS cosine | Descriptive 95% original-study block-bootstrap | Source signs |
|---|---:|---:|---:|---|
| ERA5 shortwave, per +100 W/m² | **10** | **−0.01966** | **[−0.03902, −0.00410]** | 7 negative / 3 positive |
| ERA5 2m temperature, per +5°C | 8 | +0.01492 | [−0.01366, +0.04144] | 5 positive / 3 negative |
| ERA5 100m wind speed, per +1m/s | 11 | +0.000579 | [−0.00415, +0.00467] | 9 positive / 2 negative |
| Weather wind-flow vs solar-azimuth cosine, per +1 | 11 | −0.03251 | [−0.07817, +0.02145] | 9 negative / 2 positive |

These FOUR separate original-weather univariate associations and study-block descriptive intervals were reported together, without selecting only the negative radiation outcome. No familywise correction or causal hypothesis conclusion was computed. The shortwave slope was negatively signed even after removing any **one** of the ten supported study sources: leave-one-original-study mean **[−0.02245, −0.01221]**. This is a positive, source-conditioned observational pattern, not evidence that animals actively move away from sunlight. Residual solar altitude within a four-hour bin, original geographic routes, weather-related foraging/migration, equipment observation timing and cloudiness may all create similar correlations.

### Ecological scale matters

The SAME 13 original study-source contexts with at least one weather-qualified siteyear were used to examine correlations between different source studies' mean solar-relative travel and their mean modeled environment, **without selecting a favorable subgroup**. Those *between-source* descriptive Spearman coefficients were weak and had broad source-bootstrap intervals:

- Mean solar-relative travel vs mean shortwave: rho **−0.0604** (13 studies; descriptive interval approximately [−0.653,+0.609]).
- Mean solar-relative travel vs mean 2m temperature: rho **+0.1648** (approximately [−0.439,+0.729]).
- Mean solar-relative travel vs mean modeled 100m windspeed: rho **+0.1758** (approximately [−0.535,+0.682]).

Thus the **within-individual source-weather covariance** is a different biological statistical question from **between-study mean climatic state**. The data do not show a simple, already-identified "hotter ecosystem means more sunward" or "windier site means more sunward" global law. The first observational shortwave pattern depends on actually observed tagged animal time×weather state, rather than species' original source papers' summarized activity estimates.

## Why this is still exploratory despite the source-bootstrap interval excluding zero

The original 24 source archives were previously chosen without solar effect sign but by archived header/animal and GPS study metadata; their animals, movement strategies and climate regions are NOT a probability sample of the world's independent populations. Original study-ID uniqueness is necessary but insufficient for geographic/sample independence. Solar azimuth and solar elevation both change with true solar time, and a **four-hour apparent-solar-clock block is too wide to exclude fine-scale changing illumination geometry**. One-year/modal-gridyear source selection and GPS measurement cadence can affect climate and movement outcomes. The "source-cluster bootstrap" describes stability among available original study archives, not a valid causal p-value or a familywise-corrected worldwide parameter.

The original ERA5 sampled shortwave values are gridded modeled *surface* radiation and may reflect cloudiness, not the incident solar flux at the animal's body, and wind at 100m is not the actual wind along a bird's flight path. Weather history and source processing may change upon later provider refetch; **43 original ERA5 raw-response SHA256s are retained, but raw hourly JSON response bodies are not frozen publicly**. The first results are preserved immutable, and numerical rerun drift should be diagnosed rather than silently rewriting results.

## Additional independent observation check, defined before its original source responses

On the basis of the old 10-study mean shortwave slope −0.01966, a *separate* 24-source previously unexamined original-GPS sample was fixed **before any of its original GPS movement-angle or ERA5 values were opened**. The previous source UUIDs/study IDs are excluded, one nonhuman species name per new archive, provider-original CSV header and byte band must meet the documented metadata criterion, with deterministic source UUID SHA ordering and no substitute for errors. The single signed primary expectation is a **negative** within-individual month/solar-clock radiation slope; preregistered source-block criterion requires >=6 new source IDs and a descriptive source-bootstrap upper 95% bound below zero. All nulls/failed sources count toward the 24-source denominator.

- [Pre-new-GPS frozen 24 independent-source UUIDs, sampling and sign criterion](../research/SOLAR_RADIATION_EXTERNAL_24_ORIGINAL_SOURCE_V0_CONTRACT.json).
- [Original file MD5 provider metadata frozen before new animal data](../research/SOLAR_RADIATION_EXTERNAL_24_PROVIDER_FROZEN_SOURCE_MANIFEST_20261025.json).
- First new original GPS/ERA5 directional observations are handled as an **external source sample**, not appended to the original exploratory study bootstrap retroactively.
- This additional direction check is still not a causally identifying experimental sunshine treatment nor a representative biome sample.

## Research claim ceiling

**Observed ecological result:** in the archived original 24-source frame, tagged animal sun-relative travel tended to become less sunward when gridded local hourly shortwave was higher **within month and four-hour solar-time matched individual observations**, with source-level heterogeneity, missingness and a ten-source descriptive bootstrap interval excluding zero.

**Not established:** a species-invariant solar compass or active light avoidance; direct selection on irradiance or wind; an effect independent of sun altitude, route, landscape and time; a population-representative global macroecological parameter; or supported wind/temperature effects of a common signed direction. The heldout original archive direction decision must remain separate.

All historical original ODSP seasonal/clock/prediction terminals and earlier PR #269/#270 sources are unchanged. This is a coherent first independent multi-source macroecological *observational programme*, not merely a collection of others' papers.
