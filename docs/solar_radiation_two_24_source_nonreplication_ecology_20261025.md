# Two original-GPS source cohorts: what the failed solar radiation replication really tells us

**ODSP original-data solar azimuth macroecology, 2026-10-25.**  
**Status: post-result ecological audit of two independently fixed original source lists. The previously preregistered external negative-direction decision remains NOT REPLICATED.**

This is a comparison of *derived effects computed from source-original Movebank tagged-animal GPS events and ERA5 hourly weather*, not a meta-analysis of ecological effects published in original papers. The new diagnostic does **not** reopen original GPS source selection or change the earlier source reports.

## 1. Original sampling frame and distinct estimands

Original public Movebank universe: 437 published data packages (2026-10-19 snapshot), 259 GPS/GNSS sensor-labelled packages, 159 original source CSVs with timestamp/tagged-animal/latitude/longitude headers. A first original source set of 24 archive files was fixed from a sensor/header registry without selecting on biological effect sign; a second, mutually disjoint 24 archive set and its NEGATIVE photic-radiation direction test were fixed before their GPS/ERA5 observation endpoints were opened.

Both original source sets have 24 unique study archive labels, but only **10 per set** had enough valid source individuals, month×four-hour solar-clock block support and ERA5 shortwave variation to estimate the source radiation slope. The remaining **14 per set are missing/undefined in this estimand, not zero**.

The shared observational outcome is the coefficient of original GPS travel relative to instantaneous Sun bearing,
\(Y=\cos(B-A)\), on gridded ERA5 shortwave power, per **+100 W/m²**. This is obtained by centering tagged-animal GPS samples within that original animal's calendar month×4-hour apparent solar-time bin. Original 1° grid×year contexts are averaged within taxon, and taxa within source, before assigning **one equal unit per archived study ID**.

The coefficient does not directly measure animal body-facing orientation, irradiance at the individual's skin/feathers, thermoregulatory choice, a Sun compass, or physically distinct independent study populations. It remains vulnerable to solar altitude and fine-scale time-of-day change within the four-hour clock bins.

## 2. The two source means really differ numerically; the difference itself is not established

| Source-original statistic | Original first 24-source set | Unseen external 24-source set |
|---|---:|---:|
| Fixed original archives | 24 | 24 |
| Source studies with identified radiation effect | 10 | 10 |
| Estimated source-equal radiation slope | **−0.019659** | **−0.003361** |
| Per-study descriptive bootstrap 95% CI | [−0.039023, −0.004099] | [−0.024097, +0.017406] |
| Negative/positive source signs | 7 / 3 | 7 / 3 |

A **separate post-result comparative test** of the means of these two original source sets yields original minus external **−0.016298 per 100 W/m²**, with 20,000-stratified-original-study-bootstrap descriptive 95% **[−0.045283,+0.010442]**. The interval spans zero. A 20,000-shuffle unpaired original-study label permutation gives approximate reference tail fraction **0.2974**, but the two original source-selection frames (multi-taxon vs unique taxon, regions, original animal tagging and ecological guilds) are **not exchangeable randomized field designs**, so this is not a valid world-population effect p-value. The total 20-observable-source mean is **−0.011510**, source bootstrap [−0.026157,+0.002756], also including zero.

**Important scientific result:** the earlier negative directional association was NOT independently replicated under its frozen criterion. Yet failure of the new source interval to exclude zero does **not** establish statistically different sample means or biologically stronger/wider sunlight avoidance in the original source set.

The earlier study mean −0.019659 and the exact frozen external decision are unchanged, linked in [the first 24 original source study response](../research/SOLAR_AZIMUTH_24_SOURCE_WEATHER_SOURCE_BLOCK_MACRO_FIRST_RESULT_20261025.json) and [the first 24 new original GPS study decision](../research/SOLAR_RADIATION_EXTERNAL_24_STUDY_SIGNED_TEST_FIRST_RESULT_20261025.json).

## 3. Post-outcome ecological descriptions: taxa, latitude and within-source geography

Taxonomic class is assigned from only the original source-native scientific names attached to supported study radiation estimands. The former 24-source sample includes mixed-guild studies (but all native supported taxa in each source belong to a single class); the external 24-source selection explicitly selected unique species names. Class/flight type is therefore **confounded by the two different original archive sampling designs**, climate and habitat.

| Exploratory guild | First sample supported sources | External sources | Mean per +100 W/m² across pooled sources | Source bootstrap 95% |
|---|---:|---:|---:|---:|
| Birds | 6 | 5 | −0.018022 | [−0.036134, −0.003605] |
| Mammals | 3 | 5 | −0.004679 | [−0.030878,+0.024404] |
| Reptiles | 1 | 0 | +0.005473 | insufficient independent source studies |

These post-result *descriptive* differences are not a new prospectively selected bird-specific effect, species-general law, or evidence of bird flight behavior in sunshine. The two bird subcohorts separately have means −0.028716 (n=6) and −0.005188 (n=5). The external source bird mean is less negative and its confidence interval is not established as a replicated class effect. In particular, "11 birds produce negative source bootstrap CI" is **not a heldout test of a bird-specific prediction**: grouping was done after original results.

**Within-study original calendar/space also matters:** of the 20 studies yielding a source radiation slope, **four** contained two or more qualifying original source grid×year or native-taxonomy contexts whose signed radiation slopes disagreed; six had only negative source context slopes, two only positive, and eight had only one or no separately identifiable source context. The four sign reversals are repeated biological/measurement contexts *within the same original study*, not four independent field biomes. These observations motivate testing vegetation, topography, clouds, weather, annual movement strategy and sampled latitude/solar elevation; they do not identify their cause.

Every original study, even the 28 without a radiation coefficient, original taxon labels, source-derived 15° latitude bands (never GPS grid coordinates) and context sign status is saved in the [48-source machine-readable diagnostic](../research/SOLAR_RADIATION_TWO_24_SOURCE_NONREPLICATION_DIAGNOSTIC_FIRST_RESULT_20261025.json). All raw GPS coordinates, individual IDs and exact UTC observation events remain in the ephemeral original-file analysis and are not republished.

## 4. Ecological conclusion and next mechanistic falsification

**Supported:** A globally uniform negative observational association of gridded shortwave with sun-relative GPS travel has NOT been demonstrated by two independently assembled source samples. The first negative archive-sample mean is not enough to claim avoidance of bright sunlight or solar heat stress as universal across animal ecology; observed source-level heterogeneity and lack of qualified GPS support are material.

**Unresolved:** A genuine physical daylight response may still be present in subsets of species/regions, but the present source samples are non-probability spatial/taxonomic samples, and meteorological shortwave and the Sun's geometric altitude covary within the 4-hour sampling windows. The original east/west migration corridor can also alter cos(B−A) when both sunlight geometry and cloud cover follow the time-of-day/season. Neither source-group contrast, lat-band description nor posthoc bird/mammal classification identifies a causal mechanism.

**Next physical-biological test:** On the same original GPS steps and ERA5 hours, separate **radiation variation beyond the variation expected from actual Sun elevation and the residual fine-scale solar clock position**. A within-animal source analysis can residualize modeled shortwave and GPS sun-relative heading on geometric solar elevation/solar time and then assess whether weather-associated shortwave variation is still related to travel direction. This must be an explicitly **NEW POST-RESULT sensitivity route** with its own locked original input frame, unchanged first outcomes, clear estimability thresholds, and full null/unavailable outputs—not a revised version of the failed negative preregistration.

This is ecological direction/niche research, not a solar prediction-model benchmarking exercise.
