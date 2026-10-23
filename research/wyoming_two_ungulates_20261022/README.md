# Two independent public ungulate studies: diel movement and astronomical daylight

**ODSP ecology-first comparative analysis, 22 October 2026.** The second original public GPS study was selected **before inspecting its new diel source outcomes**, using the previously frozen full 437-package Movebank catalogue. It contains exactly mule deer (*Odocoileus hemionus*) and bighorn sheep (*Ovis canadensis*) in Wyoming. The study is independent of the **Utah** field source, but may overlap other Wyoming archives. All two original taxa were retained, including an unsupported same-location result.

## New source evidence and original research question

In two independent field studies, does the **night-versus-day straight-line displacement-speed contrast** differ consistently between mule deer and bighorn sheep, and does their within-individual/year response to **astronomical daylength** show a repeatable pattern?

The original [Wyoming Movebank study, DOI 10.5441/001/1.703](https://doi.org/10.5441/001/1.703) was source-MD5 checked (ORIGINAL CSV, 98,724,772 bytes, provider MD5 `bd1c02734b6de3ddc9207fc1251edd66`; source declares CC BY-NC 4.0). The five synthetic tests and [source job 39723531890](https://github.com/zuizui0223/odsp/actions/runs/39723531890) succeeded. Original Utah survey is [10.5441/001/1.711](https://doi.org/10.5441/001/1.711) (CC0 metadata), source results [39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610).

The same solar day/night scheme, time-only hour GPS fix selection, original 0.5–2h step source rules, 3 day + 3 night intervals per source local day and 10 valid days per individual-year and 2000 animal-bootstrap draws were used for both. This is measured **GPS step displacement km/hour transformed as log1p**, NOT total daily locomotion time, actual activity occupancy, foraging time, body temperature or energy budget.

## Main original-data results

| Original source | Species | Qualified unique animals | Night−day log1p GPS displacement | Individual-bootstrap 95% interval | Daylength slope per additional daylight hour | Slope 95% interval |
| --- | --- | ---: | ---: | --- | ---: | --- |
| Utah | Mule deer | **1,723** | **−0.02185** | [−0.02321, −0.02047] | **+0.00562** | [+0.00439, +0.00692] |
| Utah | Bighorn sheep | **343** | **−0.06576** | [−0.06902, −0.06273] | −0.00341 | [−0.00652, +0.00061] |
| Wyoming | Mule deer | **119** | **−0.00446** | [−0.00578, −0.00309] | **+0.00554** | [+0.00410, +0.00697] |
| Wyoming | Bighorn sheep | **41** | **−0.01997** | [−0.02247, −0.01753] | +0.00022 | [−0.00585, +0.01098] |

**Replicated empirical pattern:** in each archived study, bighorn sheep source animals show a stronger **relative daytime displacement rate** than mule deer. The *source-group* mule-deer-minus-bighorn night−day difference is **+0.04391** in Utah and **+0.01551** in Wyoming. These numerical differences are **NOT co-located animal contrasts** outside Utah; they are descriptive differences between separately sampled source taxa in their respective studies.

**More informative replicated ecological association:** Mule deer show **positive within-individual-year associations between the length of the sunlit day and relative night−day GPS displacement**, with source means **+0.00562** Utah and **+0.00554** Wyoming and independently computed source animal-bootstrap intervals entirely positive. Bighorn's corresponding association is weak/uncertain in both studies. Therefore, **the sign and approximate scale of this mule-deer solar-calendar association recurs across two public original survey cohorts**. We do **not** infer photoperiod causation: vegetation, seasonal temperatures, migration, collar deployment and field observation schedules co-vary with daylight.

### Essential failure of the strict within-study sympatry comparison

The independent Wyoming source has **0 qualifying shared 1-degree cell × calendar year-month units** between its mule deer and bighorn, under the same predeclared minimum support. As a result **no common-space/month taxon contrast is identified** in Wyoming; it is not zero and no thresholds were relaxed to manufacture one. [Original Wyoming source log](https://github.com/zuizui0223/odsp/actions/runs/39723531890). The earlier Utah source has 92 shared cell-months in 13 distinct coarse geographic cells, with an observed source-block q difference **+0.03635** and descriptive source geographic-bootstrap interval **+0.01772 to +0.05296**. The Wyoming result supports a repeated source-group ranking, **not** repeated sympatric niche partitioning or true competition between the two species.

## Mechanism and next ecological question

The Utah GPS climate integration included modeled ERA5 temperature and monthly `P−reference ET0`; after within-cell daylight and thermal adjustment, its mule-deer-minus-bighorn q slope in *six* eligible geographic blocks remained negative versus P−ET0 (−0.01675 per 100 mm, exploratory block-bootstrap −0.02474 to −0.00794). The same-month between-year comparison was not clearly resolved (interval includes zero). **Wyoming source climate/resource responses have NOT yet been tested here.** Therefore it would be premature to interpret water balance as a mechanism shared across field populations.

The next biological priority is to ask whether the positive *mule-deer* individual daylength response is mediated by **weather and vegetation phenophase**, and whether bighorn are governed by a different environment-dependent trade-off. That requires experienced habitat, original sampling, and multiple independently documented populations. It is **not** a held-out prediction benchmark.

## Complete reusable source-derived database

- [Source and ecological summary CSV](two_source_mule_bighorn_diel_solar_comparison.csv) (all four source×taxon combinations, including individual-bootstrap intervals).
- [Wyoming original run aggregate JSON](wyoming_original_result.json), including both original source taxa and the **zero shared grid×month** finding.
- [Reproducible source contract](../MOVEBANK_WYOMING_TWO_UNGULATES_SOURCE_V0_20261022.json), [Python pipeline](../../scripts/movebank_wyoming_two_ungulates_20261022.py), [synthetic tests](../../tests/test_movebank_wyoming_two_ungulates_20261022.py).

These research outputs expose no GPS coordinates, individual IDs, raw event timestamps, or source telemetry files. The original Wyoming provider source carries **CC BY-NC 4.0** metadata and must retain source attribution and noncommercial-use restrictions for source material; Utah source metadata declares CC0. The observations are not a random sample of global ungulates, and the two studies do not independently establish a general species-level environmental mechanism.
