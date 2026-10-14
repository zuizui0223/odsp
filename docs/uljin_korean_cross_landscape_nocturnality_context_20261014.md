# Is nocturnality a species constant? Independent Korean public-field-study context

**2026-10-14 | ecology-focused post-publication synthesis | ODSP PR #264**

## Biological question

Is the apparently greater nocturnal recording of Water deer versus Wild boar in the Uljin *pooled* camera data a fixed difference between the species, or do ecological contexts such as habitat, season and human access plausibly change the *observed* rank?

This report uses **three separately published studies**. Each field paper has its own camera network or published images; **independence of physical sites or event records has NOT been proven** and their reported time periods and sampling denominators are **NOT harmonized**. This is **NOT** a statistical meta-analysis, causal test, pooled-event analysis, or independent replication of the original predeclared 41 Uljin matched astronomical date pairs.

## Source-level authenticity and data-grain contract

| Study | Source DOI and evidence | Published sampling grain | Nighttime definition / period |
| --- | --- | --- | --- |
| Jeon & Lim (2026), Uljin, *Biodiversity Data Journal* | https://doi.org/10.3897/BDJ.14.e191556, Supplement 3 https://zenodo.org/records/21319408; **publisher MD5 verified** | Four ungulates, 82 reported physical cameras, 4,623 independent 30-minute events; **whole-year pooled 12-row table** | Day, civil twilight, night **outside civil twilight**; all observation periods pooled |
| Han et al. (2024), suburban South Korea, *Journal of the Korea Society of Environmental Restoration Technology* | https://doi.org/10.13087/kosert.2024.27.2.55; official public [KCI entry](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003076639) | 18 camera traps, Jan 2021–Nov 2022; **four diel classes and seasonal proportions** | Dawn, day, dusk, night; the report's autumn/winter numbers should not be equated with Uljin's pooled year |
| Jeong et al. (2025), Bukhansan National Park, *Journal of Agriculture & Life Science* | https://doi.org/10.14397/jals.2025.59.5.111; official public [KCI entry](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003260212) | 457 analyzed wild-boar and water-deer images from 2,529 photos; **forest and wetland habitat shares** | Reported day/night binary; twilight handling and photo sampling not shown to match either other source |

For the two public Korean journal abstracts, all numerical fields below were *independently re-checked against the KCI public article pages* via a scoped read-only GitHub Actions workflow. The Uljin values were recomputed from the *original* published Zenodo Supplement 3 ZIP and authenticated using its external checksum. **No new author-supplied raw dated event or camera-operation records have been accessed.**

## Observed nocturnality ordering and its non-universality

A within-report descriptive difference is defined as **Water deer nighttime-recording share minus Wild boar nighttime-recording share** (percentage points). Positive means Water deer has the higher reported share *within that report's own sampling and clock classification*.

| Publication / internal stratum | Water deer night | Wild boar night | Within-stratum Water deer − Wild boar |
| --- | ---: | ---: | ---: |
| Jeon & Lim Uljin, 2022–2023 pooled | 499/814 = **61.302%** | 172/684 = **25.146%** | **+36.156 points** |
| Han et al. suburban, **autumn only** | **61.9%** | **77.6%** | **−15.7 points** |
| Jeong et al. Bukhansan **forest** | **70.27%** | **70.85%** | **−0.58 points** |
| Jeong et al. Bukhansan **wetland** | **83.64%** | **77.03%** | **+6.61 points** |

A further context from Han et al. is Wild boar winter nocturnal capture share **78.0%**; corresponding Water deer winter share is *not established from the cited abstract*, so **do not invent a winter species difference**.

**Supported literature-level observation:** The *ordering of reported nighttime fractions* is **not universal** across independently published settings and subgroups. In Bukhansan's forest, the 0.58-point difference is **tiny and not statistically resolved by the information retrieved**; no ranking significance is claimed. The autumn suburban direction differs from the Uljin pooled-year direction, **but that is neither a matched-season nor harmonized detector comparison**.

## Within-publication habitat and trail clues, not causal evidence

Jeong et al. (2025), Bukhansan: relative to forest, the *published nocturnal image share* is **+13.37 points** for Water deer (83.64−70.27) and **+6.18 points** for Wild boar (77.03−70.85). The difference of these two *descriptive* habitat changes is **+7.19 points**. This is within a single article but still lacks habitat×camera effort, repeated animal identity and covariance; it is not a tested habitat×species interaction or behavioral plasticity.

Han et al. (2024), suburban study: the published **daytime photographic percentages** for Water deer are **12.1% near trails** versus **24.6% away** (far−near **+12.5 points**). Wild Boar is **3.4% near** versus **5.7% away** (far−near **+2.3 points**). These observations are compatible with a human-disturbance hypothesis, but trail proximity is not randomized and other site/habitat factors can differ. **No causation or significance is assigned to the difference of percentages.**

## Why this changes ODSP's ecological framing

The prior Uljin outcome cannot be summarized as “Water deer are nocturnal and Wild Boar are diurnal.” Instead it supports: **“At the sampled Uljin cameras during the published pooled period, Water deer events have a higher nighttime fraction than Wild Boar events.”** The independent Korean studies show that Wild Boar **can exhibit high reported nocturnal fractions** in different forest, wetland and season contexts, so species-level clock architecture is not a sufficient interpretation of the Uljin aggregate.

New question (**hypothesis for future test**, not yet supported): *Do human exposure, habitat structure and seasonal context change the observed within-camera night/day allocation of Wild Boar more strongly than Water Deer, and does this alter their temporal overlap at matched astronomical daylength?*

**Design needed for an empirical answer:**

1. **Common physical station** and known camera ON/OFF operation by solar-zone and original paired date, independent of animal detection. Preserve all zero-event cells.
2. Report four-taxon, daylight-core / daylight-edge / night time allocations under original frozen May–early June vs July–August 2022 41 pairs, **NOT** the published civil twilight outside sunrise/sunset.
3. Match sampling calendar windows and explicitly predefine season / habitat / trail exposure as observational covariates, while modeling physical-station clustering and event count sparsity. No conclusion if usable stations/species/date support is inadequate.
4. Separate optical detection q, passage-distance composition and vegetation occlusion from genuine temporal allocation; treat trail proximity and annual people-frequency proxies as potential confounders unless actual hour-specific visitor data are obtained.
5. Require within-station, source-hour-calibrated **species×solar-zone×photoperiod-branch interaction** for an ecological reassembly claim. Without independent control of species-specific q, the strongest claim is still about **detectable time use**, not latent causal activity.

## Reproducibility / negative controls

- `ULJIN_INDEPENDENT_KOREAN_UNGULATE_CONTEXT_V0_CONTRACT.json`: DOI/source anchors, study-specific night definitions and mandatory source-HOLD flags.
- `scripts/run_uljin_independent_korean_context_v0.py`: **live revalidation** of KCI public English abstract numbers and the external-MD5-verified original published Uljin Supplement 3; no copyrighted text or sensitive coordinates reproduced.
- `tests/test_uljin_independent_korean_context_v0.py`: 5 tests for wrong DOI, changed published values, artificial preregistration, fabricated per-camera source, and numeric field comparisons.
- GitHub Actions: https://github.com/zuizui0223/odsp/actions/runs/38568648641 (source-linked same-publication comparison with CI).
- Separate **authentic NIE EcoBank Version 1.1 ZIP remains source-HOLD**, tracked at https://github.com/zuizui0223/odsp/issues/265.

**Maximum justified scientific conclusion:** *context-associated descriptive heterogeneity among three published Korean camera-trap datasets.* The design does not identify adaptive temporal flexibility, environment causation, direct competition, a quantitative between-study effect, or real season-specific Uljin matched-daylength ecology.


## Reassessment after exact twilight bounds and integer-photo inversion

**Important qualification to the first "not universal" description:** Different source-reported *strict night* percentages differ in sign, but a true **harmonized night-time rank reversal across populations is NOT yet established**, because the studies have different seasonal windows, observation grains, and dawn/dusk definitions.

The externally MD5-verified Uljin 4×3 published pooled table permits an exact category sensitivity: reassign every source-recorded **civil twilight** event arbitrarily to night or not-night, even using species-specific assignments. Water deer still span **61.302–67.568%**, while Wild Boar still span **25.146–30.556%**, so their **relative rank at Uljin persists** under any such twilight classification. Water exceeds Boar by at least **30.747 percentage points** for these actual observed year-long source counts; Goral and Roe Deer cannot be ordered this way. This says nothing about detector q, physical camera effort or station mix.

For Han et al. 2024 *autumn*, the abstract also reports **Water Deer daytime 13.9%** and **Boar daytime 0.7%**. *IF* the four dawn/day/dusk/night categories exactly partition source percentages, the unspecified dawn+dusk shares are **24.2% Water** and **21.7% Boar**. Species-specific twilight-as-night reassignment then gives **Water [61.9,86.1]%** and **Boar [77.6,99.3]%** night shares; these intervals overlap. Even the opposite observed autumn strict-night rank cannot be certified against every hypothetical new twilight definition without actual dawn/dusk sample fractions and timing. This is **not** proof that category differences caused the discrepancy; it limits inference.

Separately, Jeong et al. (2025) supply **457 focal analyzed photos** and exact two-decimal night percentages across four species×forest/wetland groups. Under the explicit **unverified** condition that all 457 unweighted photos exhaust those four groups and their percentages are rounded raw frequencies, there is **one** consistent integer 2×2×2 table (Water forest 22 day/52 night; Boar forest 58/141; Water wetland 18/92; Boar wetland 17/57). That conditional table implies that **55.68%** of the observed pooled PHOTO night-share species contrast is attributable to unequal forest/wetland photographic representation in one symmetric Kitagawa decomposition. This is **not** evidence of actual species habitat selection or an independently valid biological interaction test. A different photo table becomes feasible under the same percentages when as few as **seven of the 457 photos** are hypothetically outside the four groups. See [conditional inversion and twilight-bound audit](https://github.com/zuizui0223/odsp/blob/ecology/uljin-matched-daylength-temporal-refuge-v0/docs/bukhansan_public_457_photo_integer_inversion_and_uljin_twilight_bounds_20261014.md).

This strengthens the ecological target: need **original within-camera counts with the same solar-phase definitions and true camera on-time**, not stronger rhetoric based on incomparable aggregate nocturnal percentages.
