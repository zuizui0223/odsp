# Equal daylength, different mammal diel displacement despite similar regional thermal and water-season context

**2026-10-19 · ODSP PR #267 · FIRST SIX-COHORT ORIGINAL-DATE ERA5 LINK COMPLETE · Exploratory original-source mammal ecology.**

## Central biological result

Across six **source-MD5-authenticated**, original-tracking cohorts and **197 original admissible individual mammals**, the decline-daylength branch was **warmer on average** at the preselected broad ERA5 study-region reference in each source's individually admitted solar-daylength-matched GPS sampling dates, while the recorded relative night-versus-day **straight-line GPS displacement** response was not directionally universal. Most incisively, the Wyoming mule deer cohort and the Connecticut black bear cohort each experienced a similarly positive modelled mean air temperature contrast and negative previous-30-day modelled climate P−ET0, but displayed **opposing GPS diel displacement contrasts** (+0.03115 vs −0.07717 log1p km/h). This rejects only the *universal observational assertion* that warmer/drier declining-daylength calendar periods **always accompany more nighttime-relative movement in the sampled cohorts**; it cannot isolate thermoregulation, diet or a common effect modifier because population identity, taxon, geography, year, collar design and habitat differ.

## Existing complete 437-source frame, not six literature tables

The [original public Movebank Data Repository census](../research/seasonal_database_catalog/2026-10-19/movebank/README.md) found **437 public data package UUIDs** and **1,677 ORIGINAL bitstreams** (some are documentation). In the [source-locked initial pilot and eight-source extension](movebank_six_source_seasonal_ecological_synthesis_20261019.md), **eleven** archives were named in advance of their own original response inspection: **six** original GPS source files generated admissible within-animal ecological outcomes, **four** had provider ORIGINAL file MD5 mismatch (held as source integrity failures) and **one** moose source had no admitted matched-date animals. These 197 animals come from **six selected archives**, not 197 independent biomes or randomly selected mammalian populations. Do NOT use the 437 metadata package count as biological sample size.

Original unmodified target for all six was decrease-minus-increase of `[log1p(median solar NIGHT GPS straight-line displacement km/h) − log1p(median solar DAY displacement km/h)]`, using individual-admitted paired original dates with modeled daylength ≤5 minutes apart, original adjacent GPS steps 0.5–2h that do not cross a source mean-solar day/night zone, at least 3 good day and night steps, ratio of seasonal sample counts 0.5–2, 1:1 nonreused calendar pairs ≥30 days apart, and at least 10 paired dates for an individual year. Individual-year results averaged within the same marked individual, then source cohorts compared; original individual-bootstrap ranges are conditional to sampled individuals, NOT species-wide population inference.

### Six real original-source environmental contexts

| Original recruitment/study region | Qualified **individual** GPS animals | Original matched GPS **date pairs** | Δ modelled regional daily mean T (°C) | Δ modeled preceding-30d P−ET0 (mm) | Δ relative NIGHT−DAY GPS displacement log1p km/h | Original animal-bootstrap 95% interval for GPS |
|---|---:|---:|---:|---:|---:|---|
| Elk / Wapiti, Canada, [DOI](https://doi.org/10.5441/001/1.5g4h5t6c) | 12 | 436 | **+9.7505** | +5.5772 | **+0.04500** | [+0.02409,+0.06187] |
| Mule deer, Wyoming, [DOI](https://doi.org/10.5441/001/1.708) | **118** | **20,991** | **+9.2692** | **−82.5958** | **+0.03115** | [+0.02475,+0.03708] |
| American black bear, Connecticut, [DOI](https://doi.org/10.5441/001/1.706) | 20 | 962 | **+9.8650** | **−66.4565** | **−0.07717** | [−0.08877,−0.06591] |
| Wild pig, southern Florida, [DOI](https://doi.org/10.5441/001/1.719) | 5 | 321 | +1.7937 | +112.0141 | −0.00098 | [−0.04009,+0.03354] |
| White-tailed deer, western Virginia, [DOI](https://doi.org/10.5441/001/1.718) | 33 | **8,700** | +7.9629 | **−65.2594** | −0.00319 | [−0.00922,+0.00432] |
| Wolf, Alberta/BC coarse reference, [DOI](https://doi.org/10.5441/001/1.662) | 9 | 220 | +6.3504 | +34.2841 | +0.02841 | [−0.09597,+0.18617] |

**All six coarse study-region temperature contrasts were positive** at the individually sampled dates. Three source cohorts had **decreased** antecedent regional P−ET0 (mule deer, black bear, white-tailed deer) and three had increased modeled P−ET0 (elk, pig, wolves). The wolf estimate's original individual-bootstrap interval spans zero. Florida pigs and Virginia deer have group estimates near zero; these are NOT species-level proof of season-invariant movement.

The *new* three cohort weather link is [original three-source extension ERA5 Actions 39214116116](https://github.com/zuizui0223/odsp/actions/runs/39214116116) — **SUCCESS**, five fixed source/arithmetic tests passed. Original per-file native Movebank MD5s were checked and source response group mean/eligible animal count reproduced exactly **before opening new climate data**:
- Wyoming `a8563f71fa6213919812dc0f2da30c26`, 948,632 source rows, original 118 animals, **20,991** individual date pairs, ERA5 1,125 daily values on one fixed grid with response hash `ce2da73d576892b91cf05d5de3fe3335873128eda7e6ed8418782ed2112aedc2`; **0** paired-weather-missing cases.
- Virginia `dcdaf661bbf7d4cb9364028999542629`, 559,830 source rows, original 33 animals, **8,700** date pairs, 1,090 daily weather values, SHA `6aba3d750a0e6ef12de7de9db61544f721b7d420c9c09902b5ae456652640037`; **0** paired-weather-missing cases.
- Alberta wolves `3a3a1b732e997c771943ae1151a76efd`, 174,454 source rows, original 9 animals, **220** pairs, 1,991 model weather days across 2 original date chunks, source SHA `968b7a504c776a853bf1c396a5acfcb47b271df17b67723935c2c72c82f6328a` and `85af05d3bf39b38b026cf304e8e2e32a428e927303acf06b86a3766e962e9c44`; **0** missing pairs.

The three previously linked initial source weather contexts [first source/ERA5 workflow 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039) remained original and **were not refitted**. Both source-run aggregate JSON receipts were separately downloaded/validated and are linked in their respective GitHub artifacts. New extension complete JSON artifact ID **12169881098**; first three group JSON artifact ID **12164677616**.

### Nontrivial biology, and a stronger alternative question

The six-source comparison separates two things:
1. **Astronomical seasonal exposure** is held approximately constant by matched daylight duration of sampled dates, but **hydrothermal calendar states are not constant**. The strongest local example is Wyoming deer and Connecticut bears, both +9...+10°C and previous-30d drier model water balances, with unlike diel displacement responses.
2. **Night-relative movement is a difference of two absolute movement processes**. Wyoming mule deer and Canadian wapiti show **both less DAY and greater NIGHT** observed displacement on the declining-daylength side. Connecticut black bear shows **greater DAY** and slightly lower NIGHT displacement. The Virginia deer and Florida pig near-zero relative mean do not identify absence of absolute movement variation.

Thus the biologically useful next question is **when the same climatic seasonal contrast maps to different DAY and NIGHT movement responses, controlling source population and individual where possible**, not simply which of "sun" and "clock" better predicts photographed times. Pre-register an **individual-year-centered association** of within-animal paired-date temperature and preceding-water contrast with observed DAY and NIGHT GPS displacement *within each archive*, and avoid a six-point cross-source climate regression confounded by taxon and geography. An individual-level slope can still be biased by temporally autocorrelated seasonal trends, annual phase, field protocols and coarse weather exposure; it must not be called a causal mechanism or habitat-specific generality without independent on-animal temperature/greenness.

### Critical observation/inference ceiling

- ERA5 `ΔT` and `Δ(P−ET0)` are **sampled at one manually chosen public coarse reference site per recruitment/source**, not at each individual original GPS position. They do **NOT** measure the actual animal experienced microclimate, water body, shaded operative temperature or edible forage.
- Water proxy is accumulated **P minus FAO reference ET0**, not measured shallow soil moisture, root-zone moisture, vegetation NDVI or the physical water balance directly experienced by animals. These two predictors cannot distinguish actual food resource allocation or predation.
- Reused climate dates and same source weather grid may induce strong dependence across animals; **20,991 mule-deer date pairs are NOT 20,991 independent ecological replicates**, nor 118 independent climate environments. Matching calendar dates and intervals does not fully remove source device observation-cadence selection.
- Across-source 6 rows, species, geography, local human pressure, vegetation, climate, tag hardware, year and migratory stage confound. No naive six-point correlation, pooled independent-pair p-value or species-level coefficient is warranted.
- Source years are historical and disjoint across studies; the matched **solar geometry**, not actual simultaneously shared climate or measured animal contacts, is what is common.
- Camera PHOTO records from Serengeti and 7-duck instantaneous GPS-speed reports are **different endpoints**. Do NOT numerically pool them with mammal GPS straight-line minimum step speed. The climate 21 fixed-point land-grid pilot is environmental-only, not 21 animal source effects.

## Source-to-result provenance

- Original complete Movebank 437-package registry/1,677 original bitstream files: [catalog](../research/seasonal_database_catalog/2026-10-19/movebank/README.md).
- Prior original GPS outcomes: [six-cohort ecological report](movebank_six_source_seasonal_ecological_synthesis_20261019.md), [first GPS source CI 39202860827](https://github.com/zuizui0223/odsp/actions/runs/39202860827) and [extra eight source CI 39203695999](https://github.com/zuizui0223/odsp/actions/runs/39203695999) (four integrity HOLDS and one insufficient moose).
- Old 3-source original ERA5 climate results: [CI 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039).
- NEW 3-source source replay and ERA5 climate: [contract](../research/MOVEBANK_EXTENSION_THREE_ERA5_DATE_CONTEXT_V0_20261019.json), [script](../scripts/movebank_extended_three_regional_era5_20261019.py), [known-truth tests](../tests/test_movebank_extended_three_regional_era5_20261019.py), [CI 39214116116](https://github.com/zuizui0223/odsp/actions/runs/39214116116), artifact `movebank-wyoming-virginia-alberta-matched-original-gps-era5-20261019`.
- **No original animal event-level IDs, GPS traces, photographs or source files were committed or uploaded. PR #267 remains DRAFT.**

**Current defensible conclusion:** The original six matched-solar-daylength mammal GPS sources show divergent seasonal relative diel displacement despite a common positive sign of *regionally modeled* same-date air warming; even similarly warmer/drier source environments have divergent observed movement outcomes. **It is an exploratory comparative pattern, not a general biological law, temperature-mediated causal effect or population-randomized study.**
