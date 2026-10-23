# Four sympatry-eligible Utah ungulates: observed diel displacement and astronomical daylength

**2026-10-19 | First ORIGINAL GPS source-backed ecological findings | ODSP PR #268 (draft).**

## Biological result in one independently published multi-species source

The full fixed **437-package** Movebank registry was previously enumerated. The Utah UDWR source [DOI 10.5441/001/1.711](https://doi.org/10.5441/001/1.711) contains four tagged ungulate species in one original archived GPS file, **4,916,617 source records from 2,694 source-qualified animal IDs**, all four retained without effect selection. Provider ORIGINAL source UUID `9c4aaf76-7476-4305-8b14-9a6d8886e39a`, MD5 `08200c9dbdf7989fb5a35467213b7e5a` was verified before opening ecological outcomes.

**First strict equal-photoperiod opposite-season route:** all four taxa had **ZERO** eligible animal-year matches under the fixed 5-minute daylight/date/daypart rules; this previous result remains **UNAVAILABLE**, not a biological null. [Original source run 39212935666](https://github.com/zuizui0223/odsp/actions/runs/39212935666).

**Separately specified, new ecology question:** how different are their *daily NIGHT-minus-DAY minimum GPS-step displacement rates*, and how does this observed contrast change along naturally varying astronomical daylight duration? This does not ask to predict new individuals and does not reinterpret the unavailable old route. The new experiment used one actual GPS fix per UTC clock hour selected solely by source timestamp, valid real 30–120-minute within-solar-daypart steps, no location interpolation, >=3 qualified NIGHT and DAY steps on an individual-local-solar-day. An individual calendar year required >=10 eligible dates; an individual-year daylength slope required at least a 0.5-hour span of astronomical daylength. Animals were weighted equally, with 2,000 animal-cluster bootstrap replicates. Original source and six synthetic controls passed [GitHub Actions 39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610).

### 1. Across 2,618 admitted source animals, all four taxa have greater **daytime** observed GPS displacement

The endpoint below is source animal-equal mean `q = log(1+median NIGHT GPS-step km/h) - log(1+median DAY GPS-step km/h)`. A negative value indicates that, on admitted observed intervals, the animal's *night* speed is lower than its *day* speed. It is **NOT** a percentage of 24-hour activity time or a night/day movement probability.

| Taxon | Original individuals | Eligible animals | Mean night−day (log1p km/h) | Animal-bootstrap 95% interval | Animals q>0 / q<0 |
| --- | ---: | ---: | ---: | --- | --- |
| Pronghorn, *Antilocapra americana* | 222 | **215** | **−0.117167** | [−0.121751, −0.112589] | 0 / 215 |
| Wapiti, *Cervus elaphus* | 349 | **337** | −0.031889 | [−0.035765, −0.027631] | 58 / 279 |
| Mule deer, *Odocoileus hemionus* | 1,771 | **1,723** | −0.021849 | [−0.023210, −0.020468] | 319 / 1,404 |
| Bighorn sheep, *Ovis canadensis* | 352 | **343** | **−0.065761** | [−0.069022, −0.062728] | 1 / 342 |

The strongest descriptive daytime bias is seen in pronghorn, followed by bighorn sheep, then wapiti and mule deer. These reflect observed original source GPS displacements *conditioned on recording opportunity*. The original recruitment and tags are not experimentally standardized across taxa even within the same archive.

### 2. Solar-daylength associations are **not identical across the four taxa**

Each animal-year's slope of `q` on observed astronomical daylight hours was estimated before pooling animals. A **positive** slope means the night-relative *speed difference becomes less negative* during days with longer photoperiod; it does **not** mean animals become predominantly nocturnal.

| Taxon | Animals with sufficient daylength range | Mean within-animal-year slope (q per hour daylength) | Animal-bootstrap 95% interval | Individual slopes + / − |
| --- | ---: | ---: | --- | --- |
| Pronghorn | 213 | **+0.004900** | [+0.001561, +0.008013] | 133 / 80 |
| Wapiti | 332 | **+0.009599** | [+0.007141, +0.011945] | 209 / 123 |
| Mule deer | 1,683 | **+0.005619** | [+0.004387, +0.006921] | 1,164 / 519 |
| Bighorn sheep | 339 | −0.003412 | [−0.006520, +0.000612] | 123 / 216 |

Thus three taxa are relatively **less day-biased when days are longer**, despite remaining day-biased in their overall observed speed distribution; bighorn sheep has no clearly resolved directional slope. The slopes are observational seasonal associations and may reflect variation in temperature, habitat/resource calendars, migration stage, field recruitment and device exposure rather than direct solar entrainment.

### 3. Coarse common geography and month retain source-specific taxon contrasts

A predeclared support condition required each species to have >=3 distinct qualified animals, each with >=3 admitted source days, within each **1-degree grid cell × source calendar year-month**. All six species pairs had some supported common spatiotemporal cells; this is a coarse landscape stratum, NOT same habitat patch, proof of species interaction, or actual co-encounter. Below the contrast is **species listed first minus species listed second** in their equal-animal mean q, then equally averaged across cells-months.

| Compared taxa | Qualified common 1° cells × months | First − second diel log1p speed contrast |
| --- | ---: | ---: |
| Pronghorn − wapiti | 16 | **−0.110396** |
| Pronghorn − mule deer | 50 | **−0.105041** |
| Pronghorn − bighorn sheep | 27 | −0.049881 |
| Wapiti − mule deer | 76 | +0.003194 |
| Wapiti − bighorn sheep | 24 | +0.053506 |
| Mule deer − bighorn sheep | 92 | +0.038533 |

The strongest common-cell differences again put pronghorn toward **more daytime-dominated observed displacement** than wapiti or mule deer. Wapiti and mule deer have very similar common-cell diel speed contrasts. Repeated cells-months are NOT independent regions and have no source-level uncertainty intervals for these pairwise values. The support threshold is based on observation coverage, not biological effect sign.

## Ecological questions now sharpened

1. Does **open-habitat feeding exposure** versus cover, heat load or predator risk explain the especially strong pronghorn day bias at comparable year-month and coarse Utah landscape?
2. Why are wapiti, mule deer and pronghorn less day-biased along the long-day part of the solar calendar, but bighorn sheep does not show the same resolved slope?
3. Is the apparent long-day association mediated by local air/ground temperature, foliage/forage phenology or animal migration/reproductive state, rather than solar-daylight hour duration itself?

The result supports the **existence of source-measured group differences** but not these causal answers. Coarse cells, different animal capture areas, original collar fix schedules and missing observation periods remain potential confounds.

## What follows without turning this into a methods paper

The next ecological integration is to join original animal start-of-step location/date to actual grid/date **thermal stress and vegetation phenophase**, before summarizing by individual/source/cell, and estimate their associations *conditional on astronomic daylight*. Include contrasting/null results for every original taxon. Crucially, a mixed daylength–environment relationship can be informative even when strict two-season daylength matching is impossible.

This is a **database-derived, comparative ecological pattern** from one independent source. It does not recover the four failed historical equal-photoperiod comparisons, establish species-wide generality, reconstruct continuous movement budgets or identify a physiological photoperiod response. Raw original GPS positions, dates, tagged animal IDs and per-animal effects are not published.

**Reproducible result:** [Source-verified Actions run](https://github.com/zuizui0223/odsp/actions/runs/39216810610) and archived full four-taxon grouped JSON artifact `utah-solar-diel-original-four-taxa-20261019`. [Protocol](../research/MOVEBANK_UTAH_DIEL_PHOTOPERIOD_V0_20261019.json) · [source-specific Python](../scripts/movebank_utah_diel_photoperiod_20261019.py) · [independent fixtures](../tests/test_movebank_utah_diel_photoperiod_20261019.py).
