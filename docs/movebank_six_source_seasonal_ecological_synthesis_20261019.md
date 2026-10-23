# ODSP: same daylength, different diel displacement — six-source synthesis

Date: 2026-10-19. Status: exploratory original raw GPS analysis, source-verified. Not an individual-behaviour/circadian mechanism or a species-level causal trait effect.

## Central ecological finding

**The direction of the night-versus-day movement displacement contrast between increasing- and decreasing-daylength dates was not shared across the first public-data source populations.** This is an ecological question about within-animal seasonal reallocation at comparable sunlight, not a prediction-method benchmark.

The same v0 endpoint was applied without outcome-dependent source selection to three initial source packages and eight further packages selected from the complete 437-package Movebank registry. Every original GPS file used for analysis was checked against its provider-declared checksum. Null, weak, insufficient and integrity-held entries are retained.

Estimated response: *decreasing − increasing* branch of [log1p(median NIGHT GPS straight-line km/h) − log1p(median DAY GPS straight-line km/h)], averaged equally over each source-admitted individual. Each individual-year required at least 10 opposite-branch 1:1 matched solar-date pairs (photoperiod mismatch ≤5min; ≥30d temporal separation), with ≥3 consecutive, 30–120min GPS displacement steps in day and night and a 0.5–2 observation-count ratio between seasons. Continuous animal activity was not measured.

| Source/taxon | Eligible animals | Relative night/day effect (log1p km/h scale) | Individual bootstrap 95% interval | Positive / negative animals |
| --- | ---: | ---: | --- | ---: |
| Canadian elk, *Cervus elaphus* | 12 | **+0.04500** | [+0.02409, +0.06187] | 11 / 1 |
| Wyoming mule deer, *Odocoileus hemionus* | 118 | **+0.03115** | [+0.02475, +0.03708] | 103 / 15 |
| Connecticut black bear, *Ursus americanus* | 20 | **−0.07717** | [−0.08877, −0.06591] | 0 / 20 |
| Florida wild pig, *Sus scrofa* | 5 | −0.00098 | [−0.04009, +0.03354] | 3 / 2 |
| Virginia white-tailed deer, *Odocoileus virginianus* | 33 | −0.00319 | [−0.00922, +0.00432] | 12 / 21 |
| Alberta wolves, *Canis lupus* | 9 | +0.02841 | [−0.09597, +0.18617] | 5 / 4 |

The six listed source populations contribute **197 eligible tracked individuals** (12 + 118 + 20 + 5 + 33 + 9). These are six source/recruitment cohorts, **not 197 independent populations**; all recruitment provenance must be checked for overlap. The point estimate and interval for an original source describe *only* animals with qualifying telemetry schedules. Do not interpret a six-source distribution as the population of global mammals.

## What is biologically interesting, and what does not follow

Elk and mule deer independently showed a positive night-relative displacement shift on the decreasing-daylength branch. In both, the source means combine **a reduction in daytime movement and an increase in nighttime movement**. The black bear population displayed the inverse relative contrast, primarily driven by increased daytime displacement. Wild pigs and white-tailed deer showed near-zero means; wolves are too uncertain for a directional biological narrative.

The response is a **difference in observed straight-line GPS displacement speed**, not a photoperiod-memory signal, a confirmed shift in true daily activity budgets, or evidence that any population specifically follows the sun rather than ambient temperature and forage. A reversal across elk/mule deer and bears cannot yet be attributed to diet, phylogeny, cover, thermoregulation, migration, hunting pressure or sex: source population, biome, field protocol and species are confounded, and the Canadian elk archive contains females only. A near-zero *relative* contrast also does not imply unchanged absolute activity.

A useful central study question is therefore **whether thermal and resource-season context, instead of a common direction of the astronomical calendar, accounts for this heterogeneity**. This is a testable ecological association, not a mechanism already identified. Directly compare each individual’s two matched-date thermal exposure, short-lag moisture and vegetation state, and the **absolute** daylight and night displacement components. Keep environmental estimands at the used *starting location*, quantify sampling conditions, and use independently documented feeding guild and movement strategy to assess heterogeneity when there are enough distinct populations. Additional populations within the same species are vital to separate taxon from habitat.

## Full source ledger and unavailability

Of **11 originally named source packages**, seven provider-verified files produced source analyses. The seventh (Wyoming Snowy Range moose) had **zero** eligible individuals under unchanged GPS segment criteria, so has **undefined**, not zero, movement effect. Four further sources—Jackson moose, Olympic cougar, Wyoming pronghorn and another Alberta elk archive—were **source HOLD** because the downloaded file did not reproduce the provider's stored MD5. No values from these four files were interpreted or “rescued” by changing eligibility rules. A vendor-archive checksum issue is a data-integrity observation, not biological absence of seasonality.

References:
- Initial prospectively fixed source and geometry contract: [three source cohort](../research/MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json), [movement estimand](../research/MOVEBANK_SOLAR_MOVEMENT_V0_20261019.json)
- Eight additional fixed source identifiers: [extension roster](../research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json)
- **Complete machine readable positive/null and HOLD outcomes**: [original result](../research/MOVEBANK_SOLAR_MOVEMENT_V0_RESULT_20261019.json), [extension result](../research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_RESULT_20261019.json)
- Fully executed workflow receipts: [first three](https://github.com/zuizui0223/odsp/actions/runs/39202860827), [extra eight](https://github.com/zuizui0223/odsp/actions/runs/39203695999)
- Method and source acquisition code: [native originals](../scripts/movebank_native_ecology_20261019.py), [unchanged ecological endpoint](../scripts/movebank_solar_movement_20261019.py), [extension](../scripts/movebank_solar_movement_extension_20261019.py)

Ecological endpoint next: observed matched-photoperiod thermal/vegetation contrasts joined to the eligible animal/date roster, with every source retained. Do not prioritize prediction scores; prioritize ecological coefficients, uncertainty, sign heterogeneity and competing climate/vegetation/anthropogenic explanations.

**Publication ceiling:** This is still an exploratory multi-source ecological pattern. Environmental covariates have NOT been joined to the movement-response contrasts and no causal claim is supported. Earlier observed Serengeti camera record timing and independently sampled geographic climate database are complementary motivation, not independent confirmations of the actual GPS movement mechanisms.
