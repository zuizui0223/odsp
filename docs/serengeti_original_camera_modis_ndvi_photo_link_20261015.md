# NDVI across original Serengeti camera positions: photoperiod-matched vegetation change versus photo redistribution

**2026-10-15 | ODSP PR #267 | source-verified observational RESULT | Exploratory; not animal activity, occupancy, forage, migration or causality.**

## Research question

The first independent remote-sensing result found that one public Serengeti region sampling patch grew substantially greener on the descending-daylength side of the same near-astronomical-daylength natural comparison. That regional patch cannot establish whether the actual 186 original camera sites became greener, or whether their local vegetation change predicts changes in which cameras photograph zebra, wildebeest and other focal species.

We therefore checked the original same-camera/site-year observation roster against real MODIS vegetation pixels at the **source camera positions**. The outcome is *conditional photo count/time reweighting* under unknown hourly detector operation `q`, not animal population movement.

## Data provenance, fully replayed before ecological effect calculations

**[First original source camera×NDVI GitHub Actions CI 38744196749 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38744196749)**: five known-truth tests first, then the already archived 83-scene NASA MODIS/Terra original source receipt was retrieved from fixed prior [CI 38742381644](https://github.com/zuizui0223/odsp/actions/runs/38742381644) and its SHA256 verified as `e0e3c57de8d6a3ab9996412886e9733ea572cf9989f88a68b5c3ac5fb5557f11`. All original source 83 Terra composite dates/IDs and **every published coarse regional NDVI source-pixel result** were rechecked during new COG reads, before using camera-specific pixels. No new satellite dates, interpolation, MODIS Aqua composites, QA=1 marginal data or post-data threshold changes were introduced.

Original `consensus_data.csv` MD5 `5ed2d32fd09127c178cf9dca8ccfd623` and `search_effort.csv` MD5 `27cb42f3feaa0642b17cbde24ba15fbd` both verified. The camera original first pooled/photo result SHA256 `0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3` was also required. The original **38,792** matched-date photograph records, **24,290** station/calendar near-equal-daylength source pairs, and **186** public physical camera sites are unchanged. Original source public camera coordinates were used only to sample 3×3 of nearby 250-m pixels in an ephemeral CI process; exact IDs/GPS, individual satellite pixel values and photo datetimes **are not exported**.

Original 16-day quality/temporal rules retained: NASA MOD13Q1 Collection 6.1 Terra NDVI pixel reliability 0 only, at least 6 of 9 valid 250-m pixels; use only most-recent **fully completed** composite on or before each matching camera date (lag <=20 days), no future NDVI, no gap filling. For each site×year source camera geometry, require >=10 image-quality-good paired dates and >=60% of its original solar-match date pairs before estimating its camera-specific *mean* difference `NDVI_falling − NDVI_rising`. The NDVI-quality date inclusion is independent of animal photo outcomes, but subsequent species correlation eligibility is **photo-positive selected**.

## Real original camera-position NDVI result

| December-solstice cycle | Original source site×day pairs | Source camera site×days with two QA-good satellite values | Camera×years with adequate NDVI paired-date coverage | Across-camera mean NDVI falling−rising | Fraction of included camera×years with positive NDVI change |
|---|---:|---:|---:|---:|---:|
| 2010 | 4,718 | 4,125 (87.4%) | **98** | **+0.1646** | **100%** |
| 2011 | 9,769 | 7,476 (76.5%) | **112** | **+0.2727** | **100%** |
| 2012 | 9,803 | 8,177 (83.4%) | **112** | **+0.2224** | **100%** |

The **322 supported camera×year instances** are repeat observations of stations in ONE Serengeti survey region, not 322 independent landscapes or animals. Still, the measured local-pixel result is substantially stronger spatial context than the earlier one-patch proxy: under the fixed actual source site/calendar sample and strict QA, **all quality-eligible 322 site×year NDVI differences were positive**. This is a robust *descriptive sign* for original sampled/qualified camera environments. It says nothing directly about how much edible green grass, protein/nutrients or visible distance existed at an individual animal's passage. Cameras themselves were preferentially installed on trees and vegetation around them was managed, making camera visibility and MODIS green canopy complex ecological observables.

## Does more local greening predict which camera photographs more of a focal mammal?

The five previously disclosed focal source taxa are `zebra`, `wildebeest`, `buffalo`, `gazelleThomsons`, `hyenaSpotted`; all three 2010–2012 solstice cycles and ALL low-support results are retained. For a camera to contribute to a *taxon-specific association*, source species photo counts must be >=5 on BOTH NDVI-qualified original rising/falling photographed-day windows. A taxon×cycle descriptive association is displayed only with at least 15 distinct cameras plus >=50% of original species source photo count coverage on both seasonal branches; no pseudocounts, no animal-event significance tests.

**Photo-location proxy:** Spearman rho between each site's mean matched-date `NDVI_F − NDVI_R` and log ratio of `N_photo_F/N_photo_R` at the same original camera and NDVI-qualified dates. Even when matched dates have equal counts per branch, this photo ratio is NOT independently calibrated animal encounter rate without camera operation/q.

**Time distribution proxy:** Spearman rho between site NDVI difference and the site's `P_photo(NIGHT|F) − P_photo(NIGHT|R)`, again for photograph records only.

| Original taxon / year | Adequate both-branch camera sites | Rho NDVI delta vs photo-count log ratio | Rho NDVI delta vs within-site night-photo fraction change | Supports exploratory descriptive correlation? |
|---|---:|---:|---:|---|
| Zebra 2011 | 53 | **+0.1141** | **+0.1288** | YES |
| Zebra 2012 | 31 | **−0.0488** | **+0.3121** | YES |
| Wildebeest 2011 | 27 | **−0.0015** | **−0.0706** | YES |
| Zebra 2010 | 10 | undefined | undefined | **NO**: site count floor |
| All other 5 taxon×year outcomes (12 additional cells) | 0–9 | undefined | undefined | **NO**: insufficient site photo support |

Original full 15-row and all year QA support records are archived in GitHub artifact `serengeti-camera-pixel-ndvi-vs-photo-mix-source-v0` from **[CI 38744196749](https://github.com/zuizui0223/odsp/actions/runs/38744196749)**, source JSON SHA256 `b6ed0294d6e4c6277f07ef9327f536c564c33c79265570bf7b37197eb951c25f`. The non-qualification of the remaining 12 taxon×cycle comparisons must be carried forward; no substitution with photo-only sites or arbitrary pseudo-counts. All all-species source photo results remain original and unchanged.

For the qualified species/years, **NDVI greening magnitude did not show a strong consistent monotonic association with local PHOTO record-number reweighting**: ρ_photo_count is small, near zero, and changes sign across zebra years. By contrast, zebra nighttime fraction change was more positively associated with local greening in 2012 (ρ≈0.312), but much less so in 2011 (ρ≈0.129); this is *heterogeneous, observational, post-discovery and a single landscape*, not an established NDVI-triggered behavioral response. The 2012 zebra leave-one-camera-out descriptive range was ≈+0.244 to +0.391 (NOT a statistical CI); repeated photographs and unknown q remain.

### Interpretation / hierarchy of supported evidence

1. **The sun does not uniquely specify ecological season:** at same-daylength source camera dates, publicly retrieved independent meteorology and now original remote sensing document substantial rainfall history and vegetation greenness differences.
2. **The greener season need not determine photographed allocation by an easily monotonic local rule:** actual camera-specific NDVI variation was generally positive, while photo-count reweighting and original W/B photo-time changes varied across species and sites. Simple claims that each taxon follows local camera greenness are not demonstrated.
3. **Resource mechanism requires more than NDVI:** forage *nutritional* value, actual grass availability, off-site migration across the >1,000km² landscape, browsing ecology, predator/human pressure, camera detection probability and actual station hour operation are still missing. A lack of camera-scale rho does NOT rule out resource-mediated movements at 80–100+km scales, which are known from independent Serengeti ecology (Holdo et al. 2009 DOI 10.1086/597229).
4. **No transferable biological law yet:** 5 taxa×3 cycles source exploratory results are not cross-region independent replicate effects. Causal latent animal time allocation, diel refuge adaptation, intrinsic season memory and universal photoperiod hysteresis remain unidentified.

## Reproducibility and hard scientific stops

- Independent regional MODIS source: [CI 38742381644](https://github.com/zuizui0223/odsp/actions/runs/38742381644) with 83 scenes/75 QC-good composites and 435/522 regional mirror pairs.
- Camera-site linked MODIS and photo source: [CI 38744196749](https://github.com/zuizui0223/odsp/actions/runs/38744196749) with original ERA5 unrelated; source animal MD5s, original photo hash, all 83 scene IDs, raw central first probe NDVI, all site QA and 38,792 events replayed.
- Frozen exploratory protocol: `research/SERENGETI_SITE_MODIS_NDVI_PHOTO_REWEIGHT_V0_CONTRACT.json`; implementation `scripts/run_serengeti_camera_ndvi_photo_assoc_v0.py`; tests `tests/test_serengeti_camera_ndvi_photo_assoc_v0.py`; dedicated workflow in ODSP PR #267.
- Historical camera type/flash mode changed 2010–12 (Swanson et al. 2015 DOI 10.1038/sdata.2015.26), a specific uncalibrated time-detection confound. Observation year does not certify same hardware or independent ON-hours.

**Current defensible claim:** strong within-region *observed NDVI branch asymmetry* coupled with relatively weak/mixed source PHOTO-weight/greenness associations, all subject to explicit satellite/photo measurement and sample-selection limits. **No mechanism or general biological law established. PR #267 stays DRAFT.**
