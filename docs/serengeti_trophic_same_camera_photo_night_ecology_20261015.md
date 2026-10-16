# Does seasonal temporal reallocation differ between potential predators and prey at the SAME camera?

**2026-10-15 | ODSP PR #267 | New source-replayed ecology-first OBSERVATIONAL result — post-pooled-outcome exploratory.**

## Why this is not just another clock transformation

The earlier original Snapshot Serengeti analysis found 43 source taxon labels over **38,792** photo detections on **24,290** almost-equal-daylength photo-supported camera-date pairs. Species-specific PHOTO night/day odds in the falling versus rising branch could differ substantially. However, one taxon changing its aggregate detected timing more than another does not demonstrate temporal segregation between the two taxa when they actually occur at the same sites. Source cameras, animal abundances and seasonal migration can strongly alter the mixture of places sampled.

We therefore asked a more ecological and more falsifiable question: **At a physical camera that recorded both species on both annual branches, did the predator's *night-record fraction* change more than that of a candidate prey taxon?** The distinct 2010, 2011 and 2012 December solstice cycles were kept, with the exact source and solar dates inherited unchanged from the previous first source result.

Existing work already demonstrates Serengeti carnivore space-time avoidance (Swanson et al. 2015; https://doi.org/10.1038/sdata.2015.26; 2017 lion/hyena/cheetah https://pmc.ncbi.nlm.nih.gov/articles/PMC5167031/) and the influence of livestock on herbivore crepuscular time in adjacent conservancies (Guthmann et al. 2024 https://doi.org/10.1111/1365-2656.14034). This post hoc source exploration cannot claim discovery of predator-prey time partitioning.

## Exact measured object

Within an original source physical camera `i` and December-solstice year `y`, and retaining ONLY cases with at least one photograph of EACH comparison taxon on EACH season branch, let `p_{A,F,N}` be the **fraction of A's retained source photographs in night** on the falling branch (analogous `B,F`, `A,R`, `B,R`). Night = outside astronomical sunrise/sunset; day = full sunrise-to-sunset.

`D_{iy} = [p(A,F,N)-p(B,F,N)] - [p(A,R,N)-p(B,R,N)]`.

For the main reported result, compute each camera's mean `D` over its observed valid years and then give equal weight to each distinct original physical camera. This is a *difference in source-recorded night fractions*, in **percentage points**, NOT a night encounter rate, not a mammalian activity distribution and not a causal effect. Include all original source photo events/zeros, with no smoothing/pseudocount; if a taxon is not detected on a branch, `D` is undefined and contributes to an explicitly reported source support loss rather than an imputed value.

An additional narrower three-way log-odds interaction was calculated only when ALL eight source count cells (2 taxa × 2 branch × 2 time zones) were **strictly positive**. Under a VERY STRONG conditional camera detection model in which the species×season×night three-way term in `q` is absent, camera branch×time effort/detector effects cancel algebraically from this conditional relative comparison. This claim does **not** apply to the main photographed night-fraction `D`, and the assumption has not been independently verified in the field.

### Source+analysis verification (not a new observational independence guarantee)

- Original source `consensus_data.csv` MD5 `5ed2d32fd09127c178cf9dca8ccfd623` and `search_effort.csv` MD5 `27cb42f3feaa0642b17cbde24ba15fbd` independently verified AGAIN.
- Immutable previous first 43-taxon pooled source photo result JSON SHA256 `0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3` replayed byte for byte before computing new pair-specific values.
- Exactly **38,792** source quality-thinned photo records, **24,290** mirrored-day camera calendar pairs and **186** original source physical camera codes conserved. Across annual cycles **373 structural site×year candidates** had appropriate paired source astronomy/support (not 373 independent ecological regions).
- Four ecological pair comparisons FROZEN in `research/SERENGETI_SAME_STATION_TROPHIC_PHOTO_TIME_V0_CONTRACT.json` **AFTER** earlier source pooled and per-year species outcomes were visible. No result-based re-pairing, bin tuning, taxon substitution or null dropping.
- Dedicated source-preserving [GitHub Actions 38703238070 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38703238070): 5 synthetic known-truth guards passed; original source MD5, first result fingerprint and frozen count checks passed; aggregate-only artifact `serengeti-trophic-same-camera-record-only-v0`, ID 11957731940. No protected original camera coordinates, IDs or photo dates exported.

## All predeclared pair results

All values are from PHOTO-detected records, in **percentage points**. Positive `D` means the first taxon's night-record fraction increased more (or decreased less) than the second's between falling and rising branches. The mean is equal *physical CAMERA* weight, not event weight; within a camera, multiple year-cycles are averaged first.

| Fixed contrast (source exact taxon labels) | Both taxa recorded on both branches, site×year units | Distinct physical cameras | Camera-equal mean D | Camera-equal median D | Camera sign D >0 / <0 / =0 | Leave-one-original-camera-out camera-equal mean range | Strict all-8-positive source site×year units |
|---|---:|---:|---:|---:|---|---:|---:|
| Spotted hyena − zebra (`hyenaSpotted` / `zebra`) | **74** | **58** | **−1.53 pp** | −1.82 pp | 26 / 30 / 2 | **−4.10 to +0.46 pp** | **5** |
| Female lion − wildebeest (`lionFemale` / `wildebeest`) | **11** | **10** | **+26.88 pp** | +28.80 pp | 7 / 3 / 0 | +15.05 to +34.86 pp | **0** |
| Buffalo − zebra (`buffalo` / `zebra`) | **92** | **71** | **−2.11 pp** | +5.73 pp | 38 / 33 / 0 | **−4.00 to +0.28 pp** | **18** |
| Spotted hyena − female lion (`hyenaSpotted` / `lionFemale`) | **16** | **12** | **−14.29 pp** | −16.67 pp | 4 / 6 / 2 | −21.28 to −6.50 pp | **0** |

**No independent-site uncertainty interval** is estimated in this new source study. The leave-one-camera min/max ranges are sensitivity ranges, NOT confidence intervals; 58 or 71 camera sites are within only ONE ecological Serengeti landscape, and camera years may be correlated. Camera-codetection inclusion is explicitly **conditioned on species being photographed in both branches**—a distinct target, never a site-occupancy or latent encounter-rate analysis.

### Most informative ecological comparison: hyena versus zebra

The earlier study's *species-specific, differently pooled* photo night/day matched-date ORs were hyena ~2.63 and zebra ~1.41. That fact alone cannot establish that predators move relatively more nightward than prey at common physical camera sites. Those are different estimands and populations, so **do NOT subtract their ORs or claim a formal Simpson decomposition**.

In the actual co-photographed same-camera subset, the camera-equal change difference is only **−1.53 pp**, with 26 cameras positive, 30 negative and 2 tied; leave-one-camera range crosses zero. Per original solstice cycle, the separate site-cycle-equal `D` means are:
- **2010:** n=19 site-cycles, **−18.39 pp** (9 negative, 8 positive, 2 zero);
- **2011:** n=37, **+0.50 pp** (20 negative, 15 positive, 2 zero);
- **2012:** n=18, **+7.06 pp** (9 negative, 9 positive).

So even on recorded shared-camera supports, there is **no stable across-camera, across-year predator-greater-night-shift direction**. This is more biologically discriminating than calling both taxa nocturnal on the basis of a pooled source histogram. It does not prove the animals do not interact, that their times are equal or that no latent timing shift occurs.

The *strict count-complete* cross-season three-way log-odds is estimable for only **5/74** corresponding site-cycles and yields mean logOR **−0.667** in that tiny fully observed subset—insufficient for a general detector-cancelled ecological assertion. Do not use pseudo-counts to create more eligible cells.

### Other three predeclared pairs

- **Lion female / wildebeest**: +26.88 pp on ten cameras sounds ecologically interesting, but just 11 site-cycle units. 2010 has **zero** doubly detected site-cycles, and all years together have **zero** complete eight-cell units. The source cannot support a convincing species×season×time ratio adjusted for branch-specific detector effects.
- **Buffalo / zebra**: −2.11 pp on 71 camera sites, 38 positive vs 33 negative; more sites than the hyena–zebra comparison, but the equal-camera D range still crosses zero. Strict eight-positive observation cells only **18/92**, with mean three-way logOR **+0.0513** among those selected complete cells, not a significant ecological effect.
- **Hyena / female lion**: 12 sites, −14.29 pp observed, but the complete eight-cell source set is zero, and this is not evidence of avoidance/competition between these carnivores.

## What the experiment supports and what it refutes

**Supported photo-observation interpretation:** Comparing each taxon's temporal patterns separately and comparing species on common physical camera/solstice-year supports answer *different* ecological questions. Site-pair conditioning can greatly reduce the apparent stability of a simple predator-night-versus-prey narrative, and the present hyena–zebra common-camera sample contains mixed signs.

**NOT supported by this source:** a general predator-specific nocturnality increase in this observed setting; actual predator stalking/zebra risk; causal temperature/rainfall-mediated predator-prey encounter restructuring; endogenous circadian or photoperiod memory; calibrated latent animal activity; independent ecosystem replication; or a universal 5%-significant biological conclusion.

The original weather result established year-dependent falling-versus-rising heat and rain at equal daylength. It is ecologically useful competing context, but our new `D` analysis does not directly regress site photo differences on verified unique site weather/forage or perform causal mediation. Each species's migration, local habitat, visual detection q, animal size and camera operation may differ.

### Paper implication

Avoid the overly simple draft thesis **"mammalian nightward responses are universally caused by hot seasons or predator tracking"**. A stronger falsifiable ecological question is whether *community-level seasonal time reassembly* actually preserves, reduces or increases species-pair **relative time differentiation at common sites**, and under what resource/thermal/anthropogenic circumstances it transfers across independently sampled landscapes.

## Next independent data acquisition

Newly verified potential geographically distinct external **Mara conservancy** time-stamped camera source with 63 deployed cameras (Enonkishu 2018–22, plus expanded Ol Choro/Lemek 2021 onward): Guthmann et al. (2023/2024), [Dryad DOI 10.5061/dryad.79cnp5j28](https://doi.org/10.5061/dryad.79cnp5j28). Provider lists `Mara_Filtered.csv` with source SHA-256 `180d088846ca397c060fa174d8300d26b75127362830a3334aee74b14fd13b92` and camera `Mara_Metadata.csv` SHA-256 `e281cd77a7a2a4651048c6f00239617c158ae56a734b323568b066496f389ca4`. **Actual file-byte download returned HTTP 401**, so NO original Mara animal outcome or matched site effort examined. Camera location status can be MOVED/PULLED and paper describes daytime 3 photos versus nighttime 1 per trigger; these independently complicate cross-landscape detector q. Verify true station move chronology and actual ON hours before cross-site/ecoregion comparison. Mara lies within the broader Serengeti–Mara ecosystem and does not by itself represent a distinct biome.

## Reproducibility
- Contract: `research/SERENGETI_SAME_STATION_TROPHIC_PHOTO_TIME_V0_CONTRACT.json`.
- Source-immutable program: `scripts/run_serengeti_same_station_trophic_photo_time_v0.py`, original first replay check and source coordinate privacy boundary; tests `tests/test_serengeti_same_station_trophic_photo_time_v0.py`.
- [Source verified first focused CI 38703238070 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38703238070), uploaded aggregate artifact 11957731940.
- [Earlier original matched-date photo source](https://github.com/zuizui0223/odsp/actions/runs/38677521888) and [independent ERA5 temperature-rainfall joint context](https://github.com/zuizui0223/odsp/actions/runs/38700484637).
- No historical frozen ODSP original route or failed ecological endpoint reclassified. PR #267 remains **Draft**.
