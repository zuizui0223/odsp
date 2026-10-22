# Ecological result: warmer date-pair contrasts reallocate sampled DAY and NIGHT movement differently

**2026-10-22 · ODSP PR #267 · Source-verified original Movebank GPS × canonical ERA5 result. Exploratory AFTER original six-group GPS/ERA5 seasonal and within-individual temperature-slope findings.**

## Biological question

In the source-selected six mammalian recruitment cohorts, the original falling-minus-rising *night relative to day* GPS straight-line displacement at near-equal daylength was heterogeneous, and the previously reported within-original-animal-year paired-date OLS association with modelled regional temperature was positive in some deer cohorts and negative among Connecticut black bears. A relative day/night effect alone does **not** reveal whether the larger temperature contrast accompanies a **decrease in absolute DAY displacement**, an **increase in absolute NIGHT displacement**, both, or a greater DAY response in the opposite direction.

This is biologically relevant to distinguishing **daytime movement suppression** from **nighttime opportunity** under changing ecological conditions. But GPS displacement cannot directly measure foraging, behavioral activity budgets or heat exposure. Coarse source-region modelled temperature is not a causal thermoregulation experiment.

## Frozen source replay before new absolute component outcomes

[**Source-exact six-GPS-cohort climate-component workflow, CI 39722587356, SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/39722587356): all **five** known-truth tests passed BEFORE original data values. The prior source-authenticated six-cohort, **197** GPS-individual sample, relative NIGHT/DAY mean movement differences, original sample date-pair lists and canonical daily scientific ERA5 arrays were all checked before new absolute DAY/NIGHT climate slopes were computed.

The publicly published native ORIGINAL Movebank bitstreams were reacquired from the **identical original source UUIDs**, their provider MD5 and original whole-file byte counts were verified. Unmodified `locked_pairs()` was run once; a **separately named** DAY/NIGHT component reader independently replayed the SAME original 0.5–2h GPS-step validity, original within-solar day/night period, ≥3 step/date/zone support, astronomy ≤5-minute 1:1 date pairs separated by ≥30d and ≥10 pairs per admitted individual year, then demanded **date-by-date exact equality of original source pair dates and each original relative NIGHT−DAY effect** (tolerance 1e−10). The underlying 197 original animal recruitment samples stayed unchanged, as did all previously accepted/source-held cohort statuses.

Instead of refetching weather from the evolving API, the environment was read from the **separately archived, source-scientific-only v1 actual Open-Meteo ERA5 daily arrays** (source run [CI 39220116497](https://github.com/zuizui0223/odsp/actions/runs/39220116497), official source snapshot artifact; complete prior snapshot SHA256 `8b637760b9199e6e7f9f85e647b74658827525ed42d400bc06d44c6a4a14f05e`). All existing original daily-content SHA256s per chunk, provider grid and date sequence, variables and model units were independently verified; the original regional mean matched-date ΔT and previous-30d Δ(P−ET0) values were recovered to ±1e−9 for **all six cohorts**. This avoids misinterpreting the volatile `generationtime_ms` API envelope as climate revision, without retroactively changing the original first-route source SHA/HOLD.

The new ecological estimands were **frozen after prior relative results but before new absolute slopes**, in `research/MOVEBANK_SIX_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022.json`. For each ORIGINAL marked individual×calendar year and identical matched source date-pairs, separate centered OLS *univariate* temperature-slopes were fit to:

```
  DAY  = falling − rising log(1 + median daytime GPS straight-line km/h)
  NIGHT= falling − rising log(1 + median nighttime GPS straight-line km/h)
  REL  = NIGHT − DAY
  βREL = βNIGHT − βDAY  (same source X, dates and year, identically)
```

Require original ≥10 valid paired dates per individual year and SD(ΔT)>0.5°C; also report the separately univariate 30-day climate water-balance association per Δ(P−ET0)/100mm only when source SD>10mm. Equal years within animal then equal animal weights within cohort; no p-values, weather-pair pseudoreplication or inflated independent source count. All previously archived relative OLS βT and βwater coefficients are recovered within 1e−9, and the six identities `βrelative=βnight−βday` hold to floating-point precision. Original exact animal IDs, GPS locations, date-time or per-individual slopes are NOT exported.

All **six of six** source cohorts passed with **zero new source-HOLD**. Source artifact `movebank-six-gps-thermal-day-night-components-20261022`, artifact **12401078719**, scientific original result JSON SHA256 `cf886ef3448132ae52e577a8ae832197fef71463b2a39f598a108be66797f41f`, complete per-cohort support and source fingerprints in that JSON.

## NEW original result: temperature-associated DAY/NIGHT GPS movement components

All coefficients are **an equal-original-individual-weighted mean within-original-year observed OLS slope**, in `log(1 + minimum original GPS displacement km/h)` per +1°C increase in the *matched original date-pair regional ΔT*. They are NOT animal physiology, individual temperature response causal parameters or percentage activity.

| Original Movebank mammal cohort | Individuals | Original daylength-matched source date pairs | βDAY / °C | βNIGHT / °C | **βNIGHT−βDAY / °C** |
|---|---:|---:|---:|---:|---:|
| Wapiti, Canada | 12 | 436 | **+0.000864** | **+0.001968** | **+0.001103** |
| Mule deer, Wyoming | **118** | **20,991** | **−0.002802** | **+0.000590** | **+0.003391** |
| American black bears, Connecticut | 20 | 962 | **+0.003869** | **+0.000966** | **−0.002903** |
| Wild pigs, Florida | 5 | 321 | −0.000105 | −0.000257 | −0.000153 |
| White-tailed deer, Virginia | **33** | **8,700** | **−0.001101** | **+0.000373** | **+0.001474** |
| Wolves, Alberta/BC | 9 | 220 | −0.010064 | +0.004940 | +0.015004 |

### Ecological interpretation without causal overreach

- **Wyoming mule deer**: Most of the *positive relative NIGHT–DAY thermal co-trend* arises from the **negative DAY component** (βDAY=−0.002802) rather than a large positive NIGHT component (βNIGHT=+0.000590). Of 118 original GPS-marked animals, **100** had negative original individual-average DAY association slopes, while **60** had positive NIGHT slopes (58 negative), and **107** positive REL slopes. Saying this cohort “moves more at night when warmer” hides an observed stronger *daytime decrease*.
- **Virginia white-tailed deer**: Original population-mean seasonal relative displacement was almost zero (−0.00319), yet date-pair regional thermal association remained positive for 31/33 individuals. **All 33/33** original animals had a negative DAY slope; 21/33 positive NIGHT slopes. The source-mean βDAY=−0.001101 explains a substantial part of the relative-positive co-trend βREL=+0.001474, even when the original seasonal mean nearly cancels. Thus **weak average change does not mean weak environmentally conditioned observation**, but this could reflect a common season trend shared across deer.
- **Connecticut black bears**: The regional warmer-date pair was associated with **greater GPS displacement in both zones**, but more strongly for DAY (βDAY=+0.003869) than NIGHT (βNIGHT=+0.000966). Therefore βREL is negative (−0.002903): a “dayward relative thermal pattern” does NOT entail declining nighttime observed displacement. This is distinct from the original unconditional branch mean, which had original DAY+0.06685 and original NIGHT−0.01032. Mean branch differences and pairwise climate co-trends are different biological questions.
- **Wapiti**: Both source βDAY and βNIGHT are positive with βNIGHT larger, giving positive βREL. This is unlike the mule deer/white-tailed deer case, where DAY declines.
- **Alberta wolves**: Both a DAY negative and NIGHT positive coefficient are observed, but only **nine** original collared animals and high sensitivity of prior total association; cannot establish a wolf-population thermal strategy. **Florida pigs**: near-null source βREL, both DAY and NIGHT slightly negative, five individuals.
- All source animals share coarse calendar-related climate conditions, many with repeated matched date pairs. The **100/118 or 33/33 individual slope signs are not 100 or 33 independent climate experiments**. In addition, individual GPS data sample one recruitment region/study design per source and original time-series movement intervals are autocorrelated.

### Secondary modeled 30-day climate-water balance: observational, not simultaneous mediation

| Original cohort | βDAY per +100mm Δ30d(P−ET0) | βNIGHT per +100mm | Original βREL per +100mm |
|---|---:|---:|---:|
| Wapiti | −0.01011 | −0.01117 | −0.00106 |
| Mule deer | **+0.07618** | +0.00405 | **−0.07213** |
| Black bear | **−0.05996** | −0.00340 | **+0.05657** |
| Wild pig | +0.00829 | +0.00934 | +0.00104 |
| White-tailed deer | +0.00740 | −0.00934 | −0.01674 |
| Wolf | −0.11538 | +0.02490 | +0.14028 |

Every βwater is **separately univariate** and may share underlying source calendar/climate trends with βT. For wolves only 7/9 marked animals meet the prior original water-contrast SD criterion, and its source-individual leave-one-out βREL span crosses zero. The water proxy `Σ(P−ET0)` is neither measured soil moisture nor wildlife forage or accessible water, and cannot be interpreted as causal water-mediated night movement.

## Updated ecological claim ceiling and specific next discriminating evidence

**The data support this observational distinction:** similar positive mean regional temperature contrasts under matched photoperiod do not entail one nightward displacement response, and even a positive NIGHT-relative thermal co-trend can reflect mainly **reduced daytime sampled GPS displacement** (mule deer and white-tailed deer), while negative relative contrasts can reflect **a stronger daytime increase** (black bear). This is a more specific ecological pattern than a “no common sign” statement, though still exploratory.

**Not demonstrated:** a heat-avoidance adaptation, a confirmed daytime refuge behavior, stronger nocturnal foraging, actual locomotor active-time budgets, thermoregulatory mechanism, rainfall or vegetation mediation, an endogenous season-memory/clock effect, or a taxon-general predictive law. Weather is one *public coarse regional grid* per source, not animal microclimate; animal calendar, climate, reproductive season and tag schedule are confounded. Source-cohort contrasts cannot estimate species-specific effects independently of geography.

**Highest-value empirical next step**, if pursuing a causal ecological claim: in multiple independent **same-species** population cohorts, compare fully source-verified GPS step interval and microclimate context and actual on-animal temperature or validated activity/foraging telemetry; calculate absolute daytime and nighttime state probabilities/distance separately and evaluate a previously named environmental window and between-population transfer. Do not initiate a new unrestricted threshold/model search in these six already exposed source outcomes.

## Reproducibility

- Code: `scripts/movebank_six_gps_thermal_day_night_component_20261022.py`.
- New original known-truth tests: `tests/test_movebank_six_gps_thermal_day_night_component_20261022.py`.
- Frozen post-prior-result contract: `research/MOVEBANK_SIX_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022.json`.
- Source-checked first run and downloadable aggregate artifact: [GitHub Actions 39722587356](https://github.com/zuizui0223/odsp/actions/runs/39722587356).
- Previously source-complete six-mammal GPS × regional ERA5 comparative ecology: [six group result](movebank_six_original_cohort_matched_era5_complete_ecological_result_20261019.md).
- Previous within-individual relative-night temperature and water slopes: [six source original ecological report](movebank_six_source_within_animal_era5_thermal_water_ecology_20261019.md).
- No prior six source original GPS results, ERA5 original source v0/v1 artifacts, negative source-HOLDs, or earlier Serengeti camera/NDVI/duck studies were altered. **PR #267 remains DRAFT.**
