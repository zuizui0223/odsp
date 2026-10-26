# Sunlight and movement direction: original-GPS macroecology of environmental heterogeneity

**ODSP — 2026-10-26. Post-outcome exploratory macroecology.** Uses the two independently fixed original Movebank GPS+ERA5 24-study source collections from PR #271 and PR #272. The preregistered external negative radiation–direction result remains **NOT REPLICATED**. This synthesis derives ecological patterns from original tagged-animal tracking data, not numerical re-analysis of effect sizes published in other ecological papers.

## Ecological hypothesis and distinct levels

*Does the association between the Sun's direction and observed animal travel depend on thermal state, wind relative to the Sun and the geography of the original study? Does a macro association also hold in two environments surveyed in the same taxon and original source study?*

The reused animal-level observational response is the previously calculated change in cos(GPS travel bearing − solar azimuth) per +100 W/m² of hourly modeled ERA5 shortwave, centered within original animal × calendar month × four-hour apparent-solar-clock bin. It is not animal-facing direction, solar compass use, microhabitat solar exposure or a causal weather response.

**Between sources**: relate each study's original shortwave–direction coefficient to observed mean meteorology and 15-degree coarse latitude. **Within source**: contrast the original same taxon in two source gridyear sampling contexts. Treat multi-species archives as one original study, not multiple independent worlds.

## First exploratory macro patterns from all registered originals

Original field study denominator: **48** sources. **20** estimate a signed radiation coefficient (10 from each 24-source set); **28** are genuinely undefined, not zero.

| Observed original-study covariate | All 20 Spearman rho | Earlier 10 | External 10 |
|:--|--:|--:|--:|
| Mean ERA5 temperature (2m) | **+0.4481** | +0.4182 | +0.3697 |
| Mean wind-flow-to direction versus solar azimuth, cosine | **+0.4992** | +0.2606 | +0.7455 |
| Absolute latitude, midpoint of coarse 15-degree bands | **−0.5637** | −0.8103 | −0.1573 |
| Mean ERA5 surface shortwave irradiance | +0.0752 | +0.3091 | −0.2485 |
| Mean ERA5 100m wind speed | −0.1263 | −0.5273 | +0.2606 |

These are directly calculated from the previously committed 48-source original GPS/ERA5 archives' derived summaries. All axes were examined **after** the earlier and independent radiation results were reported, so two cohort signs are not a preregistered confirmatory replication of moderators. The apparent latitude gradient varies greatly between cohorts; 15-degree latitude midpoints are geographic proxies rather than an independent measurement of daylight response.

**Negative specificity finding:** mean ambient irradiance is not itself monotonically associated with the strength of the original source shortwave-direction coefficient; its pooled rho is only +0.075 and its two cohorts have opposite signs. The naive macro proposition that generally brighter biomes have stronger same-signed direction effects is not supported here.

**Within the same original source/taxon:** there are 14 two-context pairs across 12 original studies; those 14 pairs are not 14 independent source populations. The source-equal higher-minus-lower radiation-context mean in the original signed radiation coefficient is **−0.00756 per +100 W/m²**, with 7 source differences positive and 5 negative. The original higher/lower source-context radiation averages differ by 42.70 W/m² (unmatched seasons, gridyears, repeated animals and routes remain). Higher-versus-lower temperature has source-equal radiation-coefficient contrast **−0.00647** (7 positive, 5 negative source means). Neither is consistent evidence that brighter or warmer conditions shift the within-taxon solar-relative bearing effect in one direction.

**Interpretation:** Study-macro meteorology, wind–solar geometry and coarse latitude are plausible organizing axes of *observed directional niche heterogeneity*, but they do not identify the causal mechanism. In particular, a source-level temperature or wind/Sun correlation cannot be transported to individual weather responses. Both positive, zero, unavailable, and opposite signed study sources remain part of this result.

## New physically meaningful hypothesis to test on untouched original GPS studies

Let B be the bearing of the GPS movement segment and A the instant Sun azimuth. Use both radial and tangential components of the animal movement relative to the Sun: Y_parallel = cos(B − A), Y_perpendicular = sin(B − A). A physically testable radiation hypothesis compares the **same original individual and route context** at matched solar altitude, fine apparent solar time, season, winds and temperature, using shortwave deviations beyond those predictable from sun geometry as a weather/cloud proxy. Then test original-study and taxon variation in this *residual* photic association.

A prospective cross-source ecological model can include migration/flying/terrestrial status, temperature, wind/Sun alignment, terrain aspect, shade and vegetation phenology, while retaining source and individual clustering and the entire eligible original registry (not selecting positive effects). The current source summaries **do not measure** solar-height-residualized radiation or actual habitat shade; causal solar orientation, thermoregulation, sun-mediated migration and habitat selection are all **unresolved**.

## Executable, inspectable artifacts

- Frozen scientific contract: research/SOLAR_IRRADIANCE_DIRECTION_MACRO_GRADIENT_V0_CONTRACT.json
- Analysis command: python -m scripts.analyze_solar_irradiance_direction_macro_gradient_v0
- Output: research/SOLAR_IRRADIANCE_DIRECTION_MACRO_GRADIENT_FIRST_RESULT_20261026.json
- Known-truth and fixed-original checks: python -m unittest discover -s tests -p test_solar_irradiance_direction_macro_gradient_v0.py -v

Source resampling intervals in the generated output are *descriptive conditional on the non-probability source archive sample*, not world-biome confidence intervals. Original raw animal GPS, exact coordinates/timestamps, and individual IDs are neither loaded into the new analysis nor written to outputs.
