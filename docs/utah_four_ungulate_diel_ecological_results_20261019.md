# Species-specific diel GPS displacement within one public ungulate survey

**Results manuscript component | ODSP ecology, 2026-10-19 | Exploratory observational research**

## Biological question

Within the same broad landscape and calendar window, do different ungulates reallocate GPS-observed movement toward daytime or nighttime at different magnitudes, and is this explained by greater daylight or reduced nocturnal displacement? Does longer photoperiod have the same within-animal-year association in four species?

These questions are ecological, not detector-adjustment or prediction-score research. The comparisons are on **observed straight-line displacement speed** from valid GPS intervals; do not equate with actual movement *duration*, intensity of foraging, predator exposure, species competition, or total daily energetic output.

## Results

Original Movebank Utah UDWR 2019–2020 telemetry DOI [10.5441/001/1.711](https://doi.org/10.5441/001/1.711), provider ORIGINAL ZIP checksum MD5 `08200c9dbdf7989fb5a35467213b7e5a`, one file for all four taxa. From provider-verified source recording and timestamp-only selection (one original fix/UTC-clock hour), **2,618 individually qualified animals** contributed to four equal-animal source-level night-minus-day GPS speed summaries. Pronghorn, wapiti, mule deer and bighorn all had lower observed nighttime than daytime source GPS speed; group means were **−0.11717, −0.03189, −0.02185 and −0.06576 log1p(km/h)**, respectively. In within-individual-year regressions of observed night-minus-day displacement against astronomical daylength, pronghorn, wapiti and mule deer showed positive source-average slopes **+0.00490, +0.00960 and +0.00562 per daylight hour** (source-animal 95% bootstrap intervals above zero), while bighorn's mean slope **−0.00341** had an interval overlapping zero. These slopes do not identify causal light entrainment.

### Result 2: comparison on common geographic and calendar support

The original six pairwise comparisons required a source taxon to have **at least three animals**, each with **at least three admitted days**, in the same **1° latitude × 1° longitude × calendar year-month** observation window. All six taxon pairs had data. A later post-outcome sensitivity study then counted distinct geographic cells independently of their repeated months/years. **All original six estimates were reproduced exactly before opening the new components or cluster summaries.** [Source + six-test workflow](https://github.com/zuizui0223/odsp/actions/runs/39218494366).

| Paired taxa A−B | Common cell-months | Distinct geographic blocks | Equal-block relative NIGHT−DAY contrast A−B | Daytime component A−B | Nighttime component A−B | Geographic-block bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pronghorn−wapiti | 16 | 3 | −0.11397 | **+0.09130** | −0.02267 | unavailable (3 blocks) |
| Pronghorn−mule deer | 50 | 7 | **−0.09837** | **+0.09649** | −0.00187 | [−0.11505, −0.08192] |
| Pronghorn−bighorn | 27 | 5 | **−0.04846** | **+0.09196** | +0.04350 | [−0.05477, −0.04358] |
| Wapiti−mule deer | 76 | 10 | +0.00956 | +0.01065 | +0.02021 | [−0.00419, +0.02478] |
| Wapiti−bighorn | 24 | 6 | +0.04682 | −0.00447 | +0.04235 | [+0.00939, +0.08352] |
| Mule deer−bighorn | 92 | 13 | +0.03635 | −0.01070 | +0.02565 | [+0.01772, +0.05296] |

**Central new observational ecological insight:** Pronghorn's comparatively dayward GPS movement in shared Utah space-time is **primarily a daytime displacement amplification, rather than a detectable deficit in night movement compared with mule deer**. These distinct component architectures cannot be deduced from a species' single "diurnal/nocturnal" label or its relative-night score alone.

Likewise, wapiti and mule deer have very similar q values on their common cells, despite both different from pronghorn. Differences between bighorn and the other species can arise from differences in nighttime speed even when daytime speeds are similar. This supports describing **multiple axes of movement-rate organization**, not a fixed taxon ranking inferred from pooled civil clock timestamps.

## Interpretation: meaningful, but not overclaimed

At least in one large mammal movement public database, temporal movement-rate contrasts among ungulates are **structured by taxonomy under partially matched geographic/month context**. The classically daylight-associated pronghorn shows especially high daylight displacement relative to other ungulates. The sampled patterns are not a global ecological universal law, proof of distinct foraging niches, causal heat avoidance, or actual resource competition; daytime movement could reflect travel and habitat use rather than active foraging.

Crucially, the **source never supported the stricter within-individual rising-versus-falling season comparison at equal daylength** for any of the four taxa. Source quality prevented testing that separate seasonal asymmetry question; the present supported diel/daylength observations cannot be falsely rebranded as a positive photoperiod-hysteresis result.

The spatial bootstrap resamples geographically defined 1-degree cells, of which some pairs only have **five to seven**. Adjacent cells, original animals, collared populations, calendar seasons, and source environmental conditions remain dependent. The cell-block interval is therefore **descriptive for this source's geographic distribution**, not a confidence interval for a universal species or evolutionary trait effect.

## Next ecological test

The strongest next question is whether the same spatial-month source contrasts covary with **experienced daytime heat, vegetation phenophase and water availability**, and whether particular forms of movement (travelling vs daily foraging) create the observed daytime amplification. Connect independent ERA5 thermal data and QA-screened satellite vegetation/water proxies to the already selected original cell-month or starting positions, avoiding post-outcome selection of climate products or only positive taxa. The primary scientific product is an ecology-side environmental and guild-conditioned contrast, **not a held-out prediction benchmark**.

## Public data/provenance

- [Versioned derived database](../research/utah_four_taxa_diel_20261019/README.md): 4 taxa with individual-cluster intervals; all six source-matched comparisons; [block/day/night component CSV](../research/utah_four_taxa_diel_20261019/spatial_block_day_night_components.csv).
- Provider original Movebank DOI 10.5441/001/1.711 (source metadata CC0). First qualified diel run [39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610).
- Post-first-outcome source and six test replays, spatial block and day/night decomposition [39218494366](https://github.com/zuizui0223/odsp/actions/runs/39218494366).
- Reproduction: [original ZIP and taxon extraction](../scripts/movebank_utah_four_taxa_solar_20261019.py), [four source outcome](../scripts/movebank_utah_diel_photoperiod_20261019.py), [spatial study](../scripts/movebank_utah_shared_spatial_20261019.py).
