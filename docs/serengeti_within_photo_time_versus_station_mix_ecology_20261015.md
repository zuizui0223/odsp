# Same photoperiod, two distinct sources of changing PHOTO-record time: original Serengeti ecological decomposition

**2026-10-15 | ODSP PR #267 | Exploratory original-source ecological comparison**  
**Real published animal PHOTO data; NOT measured latent animal behavior, movement or causal season response.**

## Why this paper question matters

Prior original Serengeti matched-photoperiod photo-time comparisons suggested species-specific season differences in night-record share. Yet the published study landscape is a mosaic spanning substantial rainfall and productivity gradients, and the original ecosystem contains seasonal zebra/wildebeest migrations. A marginal increase in recorded nighttime proportion may reflect:

1. **Within-camera timing redistribution**: at a camera where a species is recorded in both branches, the night fraction of its photos changes.
2. **Among-camera photo-weight redistribution**: the relative share of that species' photos supplied by cameras with chronically high versus low night-photo shares changes.

The second is a shift in **where photographs are collected**, NOT independently established animal migration. Both can arise from changing detector sensitivity/uptime and unknown independent passage opportunities.

The distinction is an ecological estimand issue, not a new mathematical theorem. It is directly relevant to ODSP's "does marginalization hide the organization of state variables?" question, but **cannot be conflated** with ecosystem-wide niche thickness or interspecies competition.

## Immutable source and analysis receipt

[New dedicated GitHub Actions workflow **38738580588 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/38738580588) ran SIX synthetic known-truth and observational-claim tests FIRST, then verified original source consensus MD5 `5ed2d32fd09127c178cf9dca8ccfd623` and camera photo-valid-date effort MD5 `27cb42f3feaa0642b17cbde24ba15fbd`. The source reader replayed the original [v0 first PHOTO result 38677521888](https://github.com/zuizui0223/odsp/actions/runs/38677521888) byte-exact SHA-256 `0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3`, then independently checked every source `taxon × branch × core/edge/night` count for all **43 source taxon labels**. All original **38,792** matched-date PHOTO records, **24,290** solar-day-length source calendar pairs and **186** source physical camera IDs were preserved; no unpublished station coordinate or raw event datetime was exported.

**Frozen new registered-after-original-outcomes** source contract `research/SERENGETI_WITHIN_STATION_VERSUS_SPATIAL_MIX_V0_CONTRACT.json` was committed BEFORE any new decomposition values were opened. An ecological result and visualization from this data remain **post-original-publication exploratory**, NOT a newly independent prospective animal-population test. Previous RI, Serengeti N2, Uljin, and PR267 original first-results unchanged.

## Exact, noncausal record-fraction decomposition (common camera support ONLY)

For taxon `s`, December-solstice cycle `y` and original physical camera `i` where at least one photo exists in BOTH seasonal branches, let `n_ib` be detected night photos, `d_ib` detected daylight photos, and `N_ib=n_ib+d_ib > 0`. On this source-PHOTO-positive common roster `C`, put:

`p_ib=n_ib/N_ib`, `w_ib=N_ib / sum_(j in C) N_jb`.

The seasonal common-camera night-photo fraction change satisfies the **exact symmetric identity**:

`ΔP_common = P_falling − P_rising = W + B`, where

- **W, within-camera photo-time change:** `sum_i ((w_iF+w_iR)/2) × (p_iF−p_iR)`.
- **B, among-camera PHOTO record mix change:** `sum_i ((p_iF+p_iR)/2) × (w_iF−w_iR)`.

The routine asserts the identity to `1e−12`; no fitting, outcome filtering, smoothing or per-cell pseudocounts are introduced. Independently, `TV_photo_sites = 0.5 sum_i |w_iF−w_iR|` reports the extent of PHOTO weight redistribution on the same common camera roster, **NOT migration distance**.

Crucially, cameras with zero PHOTO events in one branch are excluded from C **but retained** in source all-site counts and audit. Pooled changes from ALL cameras, including branch-only photographed cameras, **are NOT decomposed by W+B**. The fraction of original branch photo records retained in C is reported separately; failing coverage is NEVER concealed.

Prespecified DESCRIPTIVE attention requires >=20 physical cameras in C, >=50% original PHOTO-record coverage in EACH branch and >=100 original photo events per branch. These are **support filters for display, not evidentiary p-value gates**. All 43 source labels and all three original calendar cycles remain archived, including no support and undefined cells.

## New empirical result (site-positive photo sample, percentage points)

| Taxon | Solstice cycle | C cameras | W: within-camera PHOTO time | B: between-camera PHOTO mix | ΔP_common | Predeclared display support |
|---|---:|---:|---:|---:|---:|---|
| Zebra | 2010 | 54 | **+13.27** | **−5.32** | +7.95 | yes |
| Zebra | 2011 | 102 | **+6.10** | +0.69 | +6.79 | yes |
| Zebra | 2012 | 77 | **+6.50** | +1.16 | +7.67 | yes |
| Buffalo | 2010 | 20 | +2.96 | **−19.37** | −16.41 | **NO**: only 41.3% of falling original photos retained in C |
| Buffalo | 2011 | 48 | **+7.30** | **−9.16** | −1.86 | yes |
| Buffalo | 2012 | 50 | +5.41 | +7.11 | +12.52 | yes |
| Spotted hyena | 2010 | 26 | **+16.56** | +5.11 | +21.66 | yes |
| Spotted hyena | 2011 | 43 | +7.31 | +9.78 | +17.10 | yes |
| Spotted hyena | 2012 | 26 | +5.07 | −4.20 | +0.86 | **NO**: 36.7% rising original photo coverage |
| Wildebeest | 2010 | 2 | +63.76 | −11.76 | +52.00 | **NO**: only 2 shared cameras, falling coverage 5.4% |
| Wildebeest | 2011 | 67 | +0.27 | +4.40 | +4.68 | yes |
| Wildebeest | 2012 | 33 | +5.23 | +4.10 | +9.33 | yes |

All signed contributions in **percentage points** are derived from original archived full-precision values, with rounding only for publication. They add to the *common-camera* night PHOTO fraction Δ (tiny last-decimal differences are rounding). Zebra common-camera recorded PHOTO coverage in rising/falling seasons respectively was 95.0%/73.7% (2010), 91.4%/90.3% (2011), 83.5%/98.3% (2012). The common-camera effect is not dominated by a single site-year with negligible photo coverage in these three zebra cycles, but no valid confidence interval was computed.

Of all 43 source taxon labels × 3 solstice cycles (**129** original entries), **24 taxon-cycle cells** from **10 original taxon labels** satisfy the frozen descriptive photo-support rule (one is `guineaFowl`, so do not call all 10 mammals). Among those 24 qualified-for-display PHOTO comparisons:
- **17/24** have `|W| > |B|`, versus **7/24** with `|B| > |W|`.
- **10/24** have W and B in **opposite directions**, meaning one observational component masks some or all of the other.
- These numerators count taxon×year photo summaries within ONE landscape, not independent populations, sites, trials or globally sampled taxon-years. No binomial/p-value inference is valid from them.

**Main ecological observation:** Zebra's *within-camera PHOTO* nighttime fraction contribution is consistently positive on this common camera roster in all **three** annual cycles, despite camera photograph distribution reweighting being opposite in 2010. Buffalo's 2011 common-site PHOTO timing term +7.30 pp is almost cancelled by site record-mixture −9.16 pp, causing a small apparent common-camera total −1.86 pp. Wildebeest 2011 has nearly zero within-camera term but +4.40 pp PHOTO-weight term; this is intriguing given migration ecology, yet does not prove migration caused the mixture. Negative/no-support source cases are preserved.

## Why this changes the paper's interpretation

Previous pooling, or even source all-camera night/day odds, may obscure offsetting observational processes. In a seasonally migratory ecosystem, observed PHOTO-time distributions are joint consequences of **(site, recorded hour, species, seasonal branch)**, not merely a single "species chronotype". The same marginal night-photo trend can emerge from different combinations of site record reweighting and in-camera time change. This strengthens the argument for keeping explicit spatial and temporal axes in ODSP instead of inferring ecology from unqualified pooled statistics.

However this is **an algebraic descriptive decomposition**, not causal mediation, novel natural-law proof, inference of true animal migration, selection of nocturnal refuges, independent animal encounters or temperature/NDVI drivers.

## Strong inferential ceilings

1. The common roster C is **conditioned on detection** in both branches. It is not representative of all true occupied cameras or animals. Photo-unique camera losses and photo-coverage differences are explicitly reported. The all-camera population change is NOT W+B.
2. Original *search_effort.csv* reports first and last valid camera PHOTO dates per SD card, **not separately measured hourly on/off**, and the independent detection probability `q(camera, date, hour, species)` is unknown. W and B are about photographing, not latent behavior or population space use.
3. Seasonal vegetation and other movements may alter passage distances and time/day photo q. The station mixture term cannot be called verified space-use redistribution of animals.
4. The first experimental observation was post-publication and this decomposition was prospectively frozen only relative to its own new outputs, not an untouched new dataset.
5. Reused 2010–2012 solstice-year camera observations are spatially dependent within **one** sampled ecological landscape; `n=24` support cells is not n independent taxon populations.
6. The NDVI independent satellite source, ORNL DAAC MOD13Q1 C6/6.1 subset API, was checked via the official [TESViS web service](https://modis.ornl.gov/data/modis_webservice.html) ([DOI](https://doi.org/10.3334/ORNLDAAC/1600)), but the **Serengeti region/time extraction did not return verified pixel observations**. No NDVI number, forage coefficient or climate-mediated activity claim is invented or appended to the original result.
7. Published Serengeti authors documented rainfall/productivity gradients, seasonal wildebeest/zebra migrations and a real camera grid, but these **existing ecological facts** do not identify the W/B terms as those mechanisms. See Swanson et al. 2015, https://doi.org/10.1038/sdata.2015.26.

## Next most informative biological test

First seek **event-independent station×zone ON-hour camera metadata** and detector quality by season, or use independent true-passage/location devices. Without it, a new prediction of night encounter intensity is unidentified. If stronger measurements can be obtained, test whether remotely sensed greenness, rainfall, herd movement and vegetation map explain camera-specific rather than merely pooled differences, while preserving cross-region validation as a distinct endpoint.

## Files and checks

- Immutable contract: `research/SERENGETI_WITHIN_STATION_VERSUS_SPATIAL_MIX_V0_CONTRACT.json`.
- Source replay + analysis: `scripts/run_serengeti_photo_site_timing_mix_v0.py`.
- All six known-truth/zero tests: `tests/test_serengeti_photo_site_timing_mix_v0.py`.
- All source output frozen: [GitHub Actions 38738580588](https://github.com/zuizui0223/odsp/actions/runs/38738580588), artifact `serengeti-photo-time-vs-station-mix-v0`, source MD5 twice verified and original first photo SHA256 fully replayed.
- Original branch PR #267 remains **DRAFT**, no modification to original N2, Rhode Island, Uljin source holds or previous qualified statistical routes.
