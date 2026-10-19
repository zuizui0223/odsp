# A weak seasonal mean can hide within-animal climate–time relationships: six original Movebank cohorts

**2026-10-19 | ODSP PR #267 | Original-source authenticated observational Results. Exploratory after all six cohort mean-GPS outcomes and cohort mean-ERA5 climate contrasts were already opened.**

## Biological question

If the daylength-decreasing season is warmer at a cohort's regional reference grid, must individuals shift more of their observed displacement into night? Six independent publicly archived mammalian GPS cohorts already showed **mixed observed relative NIGHT−DAY movement shifts** despite **all six** regional modeled decreasing−increasing temperature contrasts being positive.

That cohort-level comparison confounds taxon, geography, field protocol and time. A more directly ecological question is **within a marked individual and the same original solar year, whether date pairs with a larger local-regional temperature difference also show a larger observed change in night-versus-day GPS displacement**, and whether that association differs by recruited study cohort.

This comparison probes a *measured temporal co-trend*, not thermoregulation causation or controlled environmental intervention; the same modelled regional weather days can be shared across many source animals, and breeding, vegetation and migration stages also vary with season.

## Independent provenance and frozen observation units

All six original Movebank native files were downloaded from their first-party ORIGINAL bitstream endpoints with provider-stored **MD5 checksum verification** and processed using the already frozen original `locked_pairs` GPS timing/data-quality design. Before ANY environmental source array was retrieved for the within-animal-slope test, the script checked the original source mean GPS effect and number of eligible animals EXACTLY against the original six source ledger.

Every original matched date pair is required to retain the source sampling rules: 30–120 minute original consecutive GPS fix intervals in a single mean-solar DAY or NIGHT zone, ≥3 good GPS steps in both zones per date, ≤5-minute daylength mismatch across paired dates, ≥30 days separation, a falling/rising zone-specific source sampling count ratio 0.5–2, no date reuse, ≥10 accepted date pairs for each original individual×year. The original 197 eligible source animals are unchanged.

The environmental covariates are the same previously predeclared **one public coarse source-region ERA5 grid**, model `era5`, checked original matched animal dates, `temperature_2m_mean` (°C) and previous-30-day `P−ET0` (mm). **No on-animal thermal exposure, microclimate, actual soil water or vegetation biomass was observed here.**

Post-first-result exploratory slope design was committed **before reading the new within-animal pairwise climate associations** at [the explicit six-cohort slope contract](../research/MOVEBANK_SIX_COHORT_WITHIN_ANIMAL_ERA5_SLOPES_V0_20261019.json). Each original animal-year with ≥10 weather-qualified original pairs and SD(ΔT)>0.5°C yields an individual-year *univariate* least-squares slope of its original paired GPS night-minus-day displacement outcome on the paired date's Δregional temperature. A separate slope uses SD(ΔP−ET0)>10mm and expresses units per 100mm. Years are averaged equally **within animal**, then each original eligible marked animal is weighted equally within source. All source animals with an unavailable slope stay explicitly undefined; no pseudo-counts, p-values, reused event fixes as independent animals, after-effect threshold changes or source selection.

Original [CI 39217223363 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/39217223363): **six known-truth tests passed**, all six provider MD5s verified, all six frozen GPS mean responses exactly reproduced prior to new climate extraction, and all original dates successfully linked to regional ERA5 without missing weather pairs. Machine-readable output artifact `movebank-six-source-animal-centered-matched-date-era5-associations-20261019` ID **12169473945**; no animal ID, original GPS positions or raw dates exported.

## New real source-backed pairwise climatic association

Slope units: **log(1+GPS km/h) relative NIGHT−DAY seasonal-difference per °C of regional date-pair temperature contrast**.

| Original GPS recruitment cohort | Eligible animals | Within-animal-year ΔT slope, equal-animal mean | Original marked animals with positive / negative ΔT slope | Mean original relative NIGHT−DAY seasonal movement outcome |
|---|---:|---:|---:|---:|
| Wapiti/elk, Canada | 12 | **+0.001103** | 7 / 5 | +0.045001 |
| Wyoming mule deer | **118** | **+0.003391** | **107 / 11** | +0.031148 |
| Connecticut black bear | 20 | **−0.002903** | 7 / 13 | −0.077168 |
| Florida wild pig | 5 | −0.000153 | 3 / 2 | −0.000977 |
| Virginia white-tailed deer | **33** | **+0.001474** | **31 / 2** | −0.003189 |
| Alberta wolves | 9 | +0.015004 | 6 / 3 | +0.028410 |

This introduces a **nontrivial ecological discrepancy between a calendar mean and date-level sensitivity**: the Virginia white-tailed deer source's overall seasonal relative NIGHT−DAY displacement is near zero, while its observed within-animal original date-pair temperature slope is positive for 31/33 GPS-supported animals. A near-zero **source mean branch difference** cannot be interpreted as absence of conditional seasonal environment–movement association. Yet **31/33 is not 31 independent climate manipulations**: animals share the same coarse-grid ERA5 dates and potentially systematic seasonal behavior and instrument schedules.

The *Wyoming mule deer versus Connecticut bears* is notable at both levels. Both originally sampled source populations were warmer and drier according to broad regional ERA5 during the decreasing-daylength calendar phase, but their group mean relative movement responses have different directions (+0.03115 deer vs −0.07717 bear). Their within-individual pairwise thermal co-trend directions also differ (**+0.00339** and **−0.00290 per °C**, respectively). This is a suggestive **source-specific ecological heterogeneity**, not an identified diet, cover, circadian physiology, migration or heat-stress cause. Importantly, the original source/GPS year and environment are different between the cohorts; no randomized thermal comparison or species-by-biome factorial sample exists.

The original animal-level leave-one-animal-out temperature slope mean ranges (not population confidence intervals): elk **[+0.000493,+0.001740]**, Wyoming mule deer **[+0.003329,+0.003456]**, bears **[−0.003524,−0.001585]**, Florida pigs **[−0.005375,+0.003686]**, Virginia white-tailed deer **[+0.001352,+0.001528]**, wolves **[+0.009183,+0.020521]**. These ranges diagnose whether one tagged animal dominates a *descriptive source average*. They do **not** correct correlated weather calendar data or justify population-level significant within-animal thermal coefficients.

### Does the modeled thirty-day water-balance proxy clarify the picture?

The separately frozen *univariate* within-animal temporal slope against Δ`P−ET0`, scaled per **100mm**, was:

| Source cohort | Animal-mean paired regional P−ET0 slope (log1p GPS km/h per 100mm) | Animals with positive / negative slope | Animals with slope defined |
|---|---:|---:|---:|
| Wapiti | −0.00106 | 6 / 6 | 12 |
| Wyoming mule deer | **−0.07213** | **16 / 102** | 118 |
| Connecticut black bear | **+0.05657** | **16 / 4** | 20 |
| Florida wild pig | +0.00104 | 3 / 2 | 5 |
| Virginia white-tailed deer | −0.01674 | 9 / 24 | 33 |
| Alberta wolves | +0.14028 | 3 / 4 | **7/9**, two insufficient water-contrast variation |

The large absolute estimated wolf water slope arises in a small **seven-animal** subset, with source mean leave-one-animal-out range **[−0.05697,+0.25468]**, crossing zero, and is NOT an independently validated wolf hydrological response. All other cohorts had weather-slope support for their originally qualified source animals. The air-T and water-balance slopes are **separately univariate**, not independent simultaneously adjusted effects; temperature and P−ET0 are seasonal co-trends and may be strongly collinear.

### Source conditioning and ecological conclusions

1. **Positive real observation**: at matched solar daylength, the SOURCE-SAMPLED mammal cohorts display environmental-calendar contrast and observed within-animal day/night GPS displacement associations that vary across original recruitment populations. Near-zero group-mean differences can coexist with nonzero pairwise environmental associations.
2. **No independent climate experiment**: regional ERA5 weather is reused by multiple animals on identical or nearby dates. The apparent positive/negative animal counts, source means and leave-one-animal-out ranges can overstate evidence for a unique climatic explanation if treated as independent weather histories. A future stronger association should use model terms for shared original calendar, terrain/collar state and individual/region selection.
3. **No causal conditional trait law**: species, habitat, geography, migration state, source tag, year and observation schedule confound; no season/method/landscape-matched replication of the SAME taxa occurs among these six. Two independent African elephant source cohorts (Etosha and Kruger) are a separate promising same-taxon source comparison, but neither provides a common matched day/time and actual observed climate intervention.
4. **No animal activity or energy budget**: the target is normalized **minimum straight-line original GPS displacement**, not time actually moving, short-term bout frequency, energy expenditure, physiological heat balance, photoperiod memory, clock entrainment or animal adaptation.
5. **Research direction**: ecological tests should relate original within-population thermal, antecedent-water and vegetation/habitat state to **both absolute DAY and NIGHT displacement**, and where possible physically matched independent observations in the same taxon and multiple regions. A six-source correlation of source mean weather versus movement would be statistically misleading and is deliberately NOT provided.

**This route is a source-complete, post-original-result explanatory ecological pilot.** It refines which ecological question is worth testing; it cannot justify a globally universal solar-seasonal animal response and is not an independently registered hypothesis confirmation.

## Reproducibility and archival honesty

- Prior six group GPS+ERA5 source complete [CI 39214116116](https://github.com/zuizui0223/odsp/actions/runs/39214116116), first three [CI 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039).
- New within-year source climate association [CI 39217223363](https://github.com/zuizui0223/odsp/actions/runs/39217223363), source-native [script](../scripts/movebank_six_source_within_animal_era5_date_slopes_20261019.py), [six known-truth tests](../tests/test_movebank_six_source_within_animal_era5_date_slopes_20261019.py), [contract](../research/MOVEBANK_SIX_COHORT_WITHIN_ANIMAL_ERA5_SLOPES_V0_20261019.json).
- All old Movebank v0 results, source HOLD for four original archives, no-eligible moose, Serengeti camera photo source and GPS duck instantaneous sensor results are untouched. Current PR #267 remains DRAFT; no source-animal tracks or raw event-level data committed.
