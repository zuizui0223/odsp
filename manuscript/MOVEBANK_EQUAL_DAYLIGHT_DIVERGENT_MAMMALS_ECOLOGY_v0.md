# Equal daylight, divergent mammalian movement
## A source-verified public-telemetry comparison of seasonal diel displacement across six cohorts

**Ecology manuscript candidate v0.2 — 2026-10-19. Exploratory observational Results, not yet submission-ready.**  
**DO NOT merge raw camera photographs, animal movement, inferred continuous activity or official animal source coordinates into one endpoint.**

### Abstract

Daylength is a powerful organizing signal for animal temporal activity, but similar hours of sunlight on opposite annual seasonal branches need not coincide with the same weather, resources or internal biological state. We constructed a provenance-tracked comparison from the complete **437-package public Movebank Data Repository discovery frame**, resolved its **1,677 native ORIGINAL file entries** across all fixed package IDs, and analyzed original checksum-confirmed GPS trajectories in a prospectively fixed three-source pilot followed by an explicitly exploratory eight-source extension. The same observation rule used individual-specific paired dates separated by at least 30 days and matching modeled photoperiod within five minutes, adjacent original GPS locations at 30–120-minute sampling intervals, and adequate observed daylight and night sampling on both branches. The registered response was falling-minus-rising `[log(1+median night minimum straight-line displacement km/h) − log(1+median day displacement km/h)]`, with individual and annual repeated measures aggregated before source-level uncertainty assessment.

Six study cohorts from the initially tested eleven native source packages yielded **197 eligible individual animals**. The source-observed mean diel displacement response was positive among 12 Canadian wapiti (+0.0450, source-individual bootstrap 95% percentile [+0.0241,+0.0619]) and 118 Wyoming mule deer (+0.0311, [+0.0247,+0.0371]), negative among 20 Connecticut black bears (−0.0772, [−0.0888,−0.0659]), approximately null in five Florida wild pigs (−0.0010, [−0.0401,+0.0335]) and 33 Virginia white-tailed deer (−0.0032, [−0.0092,+0.0043]), and inconclusive among nine Alberta wolves (+0.0284, [−0.0960,+0.1862]). The two cervid positive responses each combined less recorded daylight displacement and greater nighttime displacement, whereas the bear response was dominated by more daylight displacement. All six source populations were subsequently linked *post-outcome* to ERA5 at their actual source-selected matched GPS dates, without refitting earlier movement effects. Declining-daylight regional mean-air-temperature contrasts were positive in all six original-source cohorts (+1.79 to +9.87°C), but GPS displacement responses varied in sign and magnitude. Particularly, Wyoming mule deer (+9.27°C; antecedent 30-day regional P−ET0 −82.6 mm) showed a positive relative NIGHT shift (+0.03115 log1p km/h), whereas Connecticut black bears (+9.87°C; P−ET0 −66.5 mm) showed a negative one (−0.07717). This does not establish or negate a conditional temperature mechanism, because species, geography, year, recruitment and tag schedules differ.

The results demonstrate heterogeneous observed seasonal diel displacement at approximately equal daylength **within the source-selected North American tracking cohorts**; they do not identify direct light entrainment, latent 24-hour animal activity budgets, causal heat avoidance, species-wide patterns or globally representative response frequencies. Future independent population cohorts with source-verified duty cycles, used-location thermal and phenology exposures, and within-species replication are essential to explain the heterogeneity.

**Keywords:** seasonal ecology; mammal telemetry; photoperiod; diel movement; environmental calendars; seasonal plasticity; public biological databases; sampling effort.

### Introduction

The daily alternation of light and darkness constrains opportunities for animal movement, while temperature, vegetation, food supply, reproductive state and human exposure vary over the longer seasonal calendar. Solar daylength repeats on two dates on opposite sides of a solstice, often under different ecological conditions. This makes the two calendar branches a physically motivated setting for examining the seasonal organization of recorded movement, independently of whether animals respond to astronomical daylength itself.

A simple prediction of photoperiod-only timing would be that an individual's daytime and nighttime displacement allocation is similar when nominal daylength is held close. Competing ecological explanations predict that environmental history and life stage can lead to differences. Those differences need not share one sign across taxa: a summer heat-sensitive population might reduce midday travel; a predator's spatial sampling or reproductive ecology could produce quite different changes; shifting ranges can alter both ambient exposure and its own observed time niche.

Seasonality and solar adjustment are not new methods or biological discoveries. Prior research has already shown mammalian season-dependent day/night activity and documented state-dependent photoperiod hysteresis in laboratory and field contexts. The question addressed here is **the empirical heterogeneity of same-individual GPS displacement contrasts under a fixed astronomy/effort filter across independently published terrestrial mammal tracking archives**, not a novel method for representing a clock.

### Public source selection and original-data provenance

A public archive query captured the **full 437-package 2026-10-19 Movebank Data Repository 'Data packages' collection**, not a collection of 437 independent wild mammal populations. Native ORIGINAL bitstream metadata were resolved for every package (**437/437**, **1,677** original bitstream entries including non-animal files) with original checksum and license provenance. The first source-only within-animal solar-date suitability pilot named three North American ungulate/omnivore/carnivore archives before opening movement values, then a separate expansion named eight additional source packages from the same frame after the initial ecological results were already known. The present six-source Results are therefore exploratory even though the *within-source original outcome rules* were not tuned to effect signs.

Every original trajectory used in the six analyzable cohorts was matched to its public provider ORIGINAL file UUID and provider-stored MD5. Four of the eleven originally named sources were retained as **SOURCE HOLD** because their returned bytes did not match stored MD5; one moose cohort had insufficient matched date-pair support. Neither source failure nor nonqualification was treated as a zero animal response. The six analyzed cohorts below were NOT drawn as a random subset of the world's mammalian species.

### Movement and astronomic comparison

Original UTC individual locations were time sorted, and the valid sampling unit was an original consecutive GPS position interval **30–120 minutes** long, fully classified as a single solar DAY or NIGHT within the same local mean-solar calendar date by both ends and midpoint. Great-circle displacement divided by elapsed time is a **minimum straight-line observed km/h**, not the animal's actual path length, energetics or locomotor activity time. A step was excluded if its source speed was not finite or exceeded the fixed plausibility threshold 60 km/h.

A source individual×year needed at least three valid displacement steps in each daypart on each candidate date. Pre/post June solstice dates in the Northern Hemisphere were then paired 1:1 on approximate daylength difference **≤5 minutes**, at least 30 calendar days apart, with day and night eligible step-count ratios across branches in **[0.5,2]**. Every source individual-year required **≥10** such paired dates. All date selection was source astronomy and observation quality based, never movement-effect based. Each animal's paired contrasts were averaged within year, then among available years, then individuals were weighted equally in cohort summaries. Individual-bootstrap percentile intervals (2,000 deterministic resamples) describe conditional sampled individuals, **not taxon-general or independent-population confidence intervals**.

All original GPS identifiers, exact fixes and individual effects remain restricted to ephemeral source-audited processing; source reports contain grouped provenance, counts, result effects, signs and uncertainty only.

### Results 1 — no single observed movement direction at comparable sunlight

| Source population and DOI | Qualifying animals | Change in relative nighttime log1p displacement | Source-animal bootstrap 95% range | Positive/negative animals |
|---|---:|---:|---:|---:|
| Wapiti, Ya Ha Tinda Canada — [10.5441/001/1.5g4h5t6c](https://doi.org/10.5441/001/1.5g4h5t6c) | 12 | **+0.04500** | [+0.02409,+0.06187] | 11/1 |
| Mule deer, Sublette Wyoming — [10.5441/001/1.708](https://doi.org/10.5441/001/1.708) | 118 | **+0.03115** | [+0.02475,+0.03708] | 103/15 |
| Black bear, Connecticut — [10.5441/001/1.706](https://doi.org/10.5441/001/1.706) | 20 | **−0.07717** | [−0.08877,−0.06591] | 0/20 |
| Wild pig, Florida — [10.5441/001/1.719](https://doi.org/10.5441/001/1.719) | 5 | −0.00098 | [−0.04009,+0.03354] | 3/2 |
| White-tailed deer, western Virginia — [10.5441/001/1.718](https://doi.org/10.5441/001/1.718) | 33 | −0.00319 | [−0.00922,+0.00432] | 12/21 |
| Wolves, Alberta — [10.5441/001/1.662](https://doi.org/10.5441/001/1.662) | 9 | +0.02841 | [−0.09597,+0.18617] | 5/4 |

The six groups add to **197** eligible GPS-marked individual animals, whereas the effective number of recruitment/source cohorts here is **six**, potentially with unverified geographic or recruitment overlap. An individual with repeated days/years is not counted as another independent ecological population. The source-specific effect cannot be interpreted as a standardized percentage of lifetime activity because the numeric transformation is `log(1 + km/h)` of source step speeds.

The original Wapiti mean comprises falling−rising **day −0.02411** and **night +0.02089** log1p km/h; the Wyoming mule deer is **day −0.01657**, **night +0.01457**. In contrast, the sampled Connecticut black bears had **day +0.06685** and **night −0.01032**, i.e. a negative relative night-vs-day seasonal change dominated by greater recorded daytime displacement. The Virginia deer and Florida pig group effects were close to zero at the available source level; wolves are too uncertain for a directional source-general claim. Mixed signs are not evidence for an individual's internal light-entrainment mechanism.

### Results 2 — warmer source-region calendar does not uniquely identify movement direction

A subsequent *post-outcome exploratory* ERA5 regional context was calculated using each original admitted individual/solar-year's paired GPS calendar dates, not arbitrarily selected equinox days. A **coarse public reference grid** was fixed for each of the first three source populations, with daily mean 2m air temperature and a previous-30-day proxy `Σ(precipitation − reference ET0)`. The model-derived water proxy is NOT measured soil water or edible forage, and source region grid temperature is NOT an elephant/elk's individual thermal exposure.

| Population | Original eligible animals | Regional falling−rising air T (°C) | Regional previous-30-day P−ET0 (mm) | Observed falling−rising relative NIGHT GPS displacement |
|---|---:|---:|---:|---:|
| Canada wapiti | 12 | +9.751 | +5.577 | **+0.04500** |
| Florida pig | 5 | +1.794 | +112.014 | −0.00098 |
| Connecticut bear | 20 | +9.865 | −66.457 | **−0.07717** |

Every admitted animal in each source had a positive *individual-averaged coarse-grid* thermal contrast on the declining-daylength branch, yet the signed diel displacement responses were not the same. This limits only the **overly strong description** that “a warmer season must lead to a positive nighttime-relative movement shift” for these cohorts. No ecological claim that heat *cannot* matter, nor a taxon-independent thermal slope, is warranted. These source group contrasts come from different populations, recruitment eras, study regions and devices.

The **three additional source population regional ERA5 date joins have now succeeded**: each of the Wyoming mule deer (118 animals, 20,991 source date pairs), Virginia white-tailed deer (33 animals, 8,700 date pairs) and Alberta wolves (9 animals, 220 date pairs) original Movebank source files passed provider MD5; all prior group GPS effect means and animal numbers were reproduced EXACTLY before any climate response was used. Their original-date regional mean-air-temperature contrasts were **+9.269, +7.963 and +6.350°C**, respectively. Their preceding-30d `P−ET0` differences were **−82.596, −65.259 and +34.284 mm**, respectively. All paired regional weather dates were present, with no missing values in this specific ERA5 source dataset. [Original successful five-test/source replay CI 39214116116](https://github.com/zuizui0223/odsp/actions/runs/39214116116).

### Results 3 — comparable warm/dry regional seasonal contexts do not entail the same within-population diel displacement result

All **six** original GPS recruitment cohorts with an eligible source-specific movement effect now have their individually paired original daylight-matched dates linked to independent *modelled* regional ERA5 air temperature and preceding-30-day `P−ET0` climate water-balance proxies. No additional source was added because of effect sign; the original six are the already fixed subset of the eleven pre-named Movebank archives that passed native MD5 and solar-time sampling conditions. The original six-source total remains **197 qualifying individually marked mammals**. Their source regions and modeled fixed reference coordinates are public but NOT GPS-estimated animal locations; one ERA5 grid point stands for an entire source recruitment region.

| Original mammal source cohort | Admitted animals | Decreasing−increasing regional 2m air T (°C) | Antecedent 30d regional P−ET0 change (mm) | Relative NIGHT−DAY original GPS displacement change (log1p km/h) |
|---|---:|---:|---:|---:|
| Canada wapiti | 12 | +9.7505 | +5.5772 | **+0.04500** |
| Wyoming mule deer | 118 | **+9.2692** | **−82.5958** | **+0.03115** |
| Connecticut black bears | 20 | **+9.8650** | **−66.4565** | **−0.07717** |
| Florida wild pig | 5 | +1.7937 | +112.0141 | −0.00098 |
| Virginia white-tailed deer | 33 | +7.9629 | −65.2594 | −0.00319 |
| Alberta wolves | 9 | +6.3504 | +34.2841 | +0.02841 (source-bootstrap interval spans zero) |

A central ecological observation is that Wyoming mule deer and Connecticut bears each experienced an approximately **+9–10°C regional warming on the decreasing-daylight seasonal branch** and **a lower preceding-30-day modelled water-balance proxy**, yet their *within-individual* observed diel displacement contrasts have opposing signs. Virginia white-tailed deer also belonged to this warmer/drier regional quadrant, yet had a near-zero source-group night-vs-day difference. The differences show **no universal observational direction forced by the SIGN of coarse hydrothermal change** in these selected source cohorts. They do NOT show that temperature is irrelevant or identify a direct resource/trophic mechanism: the taxon, field region, original source year and collar scheduling are confounded. Similarly, a positive thermal contrast in all six cohorts is a selection conditioned on geography and photoperiod comparison, not a global physical law about decreasing-daylength seasons.

The water term is `P−ET0`, not independently measured animal-accessible water, root-zone moisture, grazed vegetation or an experimental contrast. The group means are *selected individual averages of matched-day regional model fields*; repeated pair dates across animals are not independent climate observations. The individually bootstrapped movement intervals are conditional within each original cohort and cannot be combined as 197 independent cross-ecosystem replications. All six original GPS population-level effects were frozen before the environmental linkage. The environmental association analysis was designed and run **after the original displacement effects were observed**, so the six contrasts are exploratory, not an unseen independent confirmatory test.

Details and complete original provider MD5/weather-source receipts: [all six original GPS cohorts × ERA5 ecological result](../docs/movebank_six_original_cohort_matched_era5_complete_ecological_result_20261019.md), first 3-group weather [CI 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039), second three [CI 39214116116](https://github.com/zuizui0223/odsp/actions/runs/39214116116). Future decisive analysis requires **individual- or site-within-source hydrothermal exposure associations at the same paired dates**, not a regression across only six species–location-confounded source means.

### Discussion — what generalizes and what does not

Within the source-selected mammalian telemetry cohorts, similar daily sunlit duration on opposite annual branches does not fix the observed relative day-night displacement outcome. There are repeatable individual-sign tendencies within certain sampled source cohorts, but the overall directions differ across the studied groups. The finding is **population-level observational heterogeneity**, and does not yet identify its shared environmental drivers or the population of all terrestrial mammals.

Two specific ecological pathways remain to be tested in independently sampled populations: (1) time-use plasticity related to experienced daytime thermal burden, which might be expressed as **less daytime displacement, more nighttime displacement or both**; (2) resource or water-season context that changes the animal's range usage and encounters, which could alter both temporal allocation and where sensors find animals. A source with a near-zero relative day/night difference may still have large, offsetting changes in both absolute day and night movement.

The independently studied Serengeti camera/NDVI results provide **motivation**, not a numeric replication of the GPS estimand: under same-daylength photo-date matching NASA/Terra MODIS greenness rose in the original quality-eligible source cameras, but original camera-hour uptime and detection `q` were unknown. A separate sparse 21-land-grid ERA5 1/15/30d climate pilot shows heterogeneous warm/dry versus cool/wet histories even at similar endpoint solar photoperiod. Neither external strand supplies new animal population effects in the six GPS cohorts; mixing them into a single animal meta-analysis would be scientifically unjustified.

**Critical counterfactuals.** Matching daylength does not match weather, resource phenology, reproductive stage or human exposure. The initial eleven sources were selected for published source data availability and animal count, not randomly across taxa/geographies. Source selection and GPS duty cycle could differ systematically across time, species and habitat. Individual bootstrap intervals under the original qualified-source roster do not correct this source-selection or detection bias. No raw event timestamps or precise coordinates are redistributed.

### Conclusion and immediate empirical next test

The first genuinely source-verified public mammal GPS comparison reveals **nonuniform seasonal diel displacement reallocation at near-matched solar daylength**, with particular source cohorts shifting in opposing directions. The ecological explanation remains unknown. The highest-value immediate empirical test is to link **same matched animal dates** to independently sourced environmental conditions across the already qualified cohorts, then test *within-population* climate associations and replicate taxa across contrasting habitat contexts. A prediction-score benchmark is optional; transparent ecological effect sizes, absolute day/night components, nulls and unqualified sources are essential. The work should not be submitted with a “universal seasonal hysteresis law” claim.

### Source and reproducibility

- [All public Movebank 437-package provenance](../research/seasonal_database_catalog/2026-10-19/movebank/README.md), native original inventory [Actions 39202214632](https://github.com/zuizui0223/odsp/actions/runs/39202214632).
- Fixed first three source GPS results [Actions 39202860827](https://github.com/zuizui0223/odsp/actions/runs/39202860827); eight other source files, including all HOLDs [Actions 39203695999](https://github.com/zuizui0223/odsp/actions/runs/39203695999).
- First three original-date ERA5 regional context [Actions 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039).
- Full previous [six-source ecological synthesis](../docs/movebank_six_source_seasonal_ecological_synthesis_20261019.md), [three matched-date climate source Results](../docs/movebank_gps_regional_era5_joint_ecological_result_20261019.md).
- All original registered source movement effects, telemetry-time filters and prior codes remain unchanged in this separate GPS ecology manuscript draft; no post-hoc behavioral endpoint replacement.
