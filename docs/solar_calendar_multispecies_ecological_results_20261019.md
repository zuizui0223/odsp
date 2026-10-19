# Same sunlight, different movement schedules? A source-first mammal comparison

**2026-10-19 · ODSP ecology PR #267 · Empirical observational result and limitations**

## Central ecological question

Does an animal use the day and night in the same way at **nearly the same astronomical daylength** on the two branches of an annual solar cycle? If not, is the difference common across animals, or does it depend on environmental and biological context? The target is the **organization and seasonal redistribution of temporal movement niches**, not improved machine-learning prediction or camera calibration.

The public-data programme was organized before selecting its published source effects: [437 Movebank Data packages](../research/seasonal_database_catalog/README.md) and 26 GBIF Camtrap DP registry records were inventoried from their entire public discovery frames. The native original-file metadata for 437 Movebank packages and 1,677 bitstreams were independently checked ([run 39202214632](https://github.com/zuizui0223/odsp/actions/runs/39202214632)). Published original files for admitted mammal cohorts have provider original-bitstream MD5 checksums; no result-selected replacement sources are used.

## Currently admitted mammal cohort estimates

The original source endpoint uses consecutive GPS steps of **30–120 minutes**, with both endpoints/midpoint classified to the same local mean-solar daypart, species-individual date pairs from opposite branches of the summer solstice at **<=5 minutes of modeled daylength mismatch**, **>=30 days date separation**, and **>=10 matched pairs per individual-year**. At least three eligible GPS-step readings per solar day and night per date and a 0.5–2 observation count ratio across branches are required. Dates are paired without looking at displacement outcome. The outcome is the **decreasing-daylength minus increasing-daylength change in [log(1+median night GPS step speed km/h) − log(1+median day GPS step speed km/h)]**.

The same solar-branch definition follows **June summer solstice in the North** and **December summer solstice in the South**. These are minimum straight-line GPS displacements from one fix to the next, **not measured continuous activity, energetic cost or total travelled path distance**.

| Source and geography | Species | Eligible individuals | Relative night/day seasonal contrast | Animal-cluster bootstrap 95% interval | Within-source individual directions |
| --- | --- | ---: | ---: | ---: | --- |
| Banff, Canada | *Cervus elaphus* (wapiti) | **12** | **+0.04500** | [+0.02409, +0.06187] | 11 positive / 1 negative |
| Southern Florida, USA | *Sus scrofa* | 5 | -0.00098 | [-0.04009, +0.03354] | 3 positive / 2 negative |
| Connecticut, USA | *Ursus americanus* | **20** | **-0.07717** | [-0.08877, -0.06591] | 0 positive / 20 negative |
| Wyoming, USA | *Odocoileus hemionus* | **118** | **+0.03115** | [+0.02475, +0.03708] | 103 positive / 15 negative |
| Virginia, USA | *Odocoileus virginianus* | 33 | -0.00319 | [-0.00922, +0.00432] | 12 positive / 21 negative |
| Alberta, Canada | *Canis lupus* | 9 | +0.02841 | [-0.09597, +0.18617] | 5 positive / 4 negative |
| Southern Brazil | *Tapirus terrestris* | 22 | -0.00791 | [-0.02686, +0.01064] | 10 positive / 12 negative |
| Etosha, Namibia | *Canis mesomelas* | 8 | **+0.05485** | [+0.00724, +0.12713] | 6 positive / 2 negative |
| Etosha, Namibia | *Loxodonta africana* | **14** | **-0.15013** | [-0.20271, -0.10091] | 0 positive / 14 negative |

**241 admitted individual animals across nine original source-specific species/cohorts.** This count does NOT imply 241 independently sampled populations, a random global mammal sample, or replication of a physiological mechanism. The rows are cohorts, not species-wide parameter estimates; the bootstrap interval quantifies source-animal sampling conditional on its original observation context.

**Observation-architecture exception: elephants.** The provider-MD5-verified original Etosha elephant ZIP contains ~2.93 million GPS fixes at a cadence incompatible with the original 30–120-min *adjacent*-fix rule (only 413 eligible original adjacent steps and no eligible animal-year). This v0 insufficiency stays unchanged. Elephant's estimate above belongs to a separately frozen **v1**, created only after that cadence limitation was observed, which selects **one original fix per UTC clock hour by timestamp alone** (no displacement-based selection), then applies the unchanged 30–120-min GPS and Southern photoperiod rules. It is a different observational estimand. [MD5/source-only ZIP audit](https://github.com/zuizui0223/odsp/actions/runs/39207207985) · [original v0 result](https://github.com/zuizui0223/odsp/actions/runs/39207354970) · [time-only elephant v1](https://github.com/zuizui0223/odsp/actions/runs/39207964106).

**Cross-source robustness of the Etosha contrast:** Subjecting jackal GPS to the **same** outcome-blind hourly time selection as elephants gives **+0.04479** rather than the native +0.05485, for eight eligible jackals (5 positive/3 negative; 95% animal-bootstrap interval [-0.00211, +0.11922]). Thus the point-estimate direction of elephant (negative) versus jackal (positive) remains different under the same time selection scheme, but the jackal effect is less precise. The comparison is *post-outcome sensitivity*, not independent blinded confirmation. [Jackal hourly sensitivity run](https://github.com/zuizui0223/odsp/actions/runs/39208418314).

## Three positive biological observations, with strict scope

**A. Same astronomical photoperiod does not imply a universal diel movement response.** Multiple qualified Northern and Southern source cohorts show positive, negative, or very small seasonal changes. One simple claim—"animals uniformly shift toward night on the declining-daylight branch"—does not describe these nine sources. The question is now **which ecological contexts and biological traits are related to different reallocations**, not whether a model can predict the sign.

**B. Similar group seasonal means can hide different day/night components.** In Banff wapiti, relative nightward displacement (+0.04500) combines lower daytime log1p GPS speed (-0.02411) and higher nighttime log1p GPS speed (+0.02089). In Connecticut bears, the reverse contrast (-0.07717) combines higher daytime (+0.06685) and lower nighttime (-0.01032). In Etosha native-step jackals, the relative nightward contrast (+0.05485) includes **higher** daytime (+0.01638) as well as greater nighttime (+0.07123) displacement. Thus "more nocturnal" is an incomplete biological interpretation of this measured endpoint.

**C. Same broad ecosystem can contain opposite source-level directions.** Etosha elephants are negative under time-blind hourly selection, while Etosha jackals are positive under a matched hourly extraction sensitivity. This creates a tractable comparative problem—possibly physiological heat exposure, feeding ecology, trophic timing, or differences in seasonal resource dynamics—but it **does not yet distinguish species biology from noncontemporaneous study years, microhabitats, and source-specific GPS recording regimes**. Contemporary temporal interaction or competition is NOT established.

## Environmental status

A **separately registered, post-original-GPS-outcome** three-region ERA5 linkage reproduced the locked Banff wapiti (+0.04500), Florida pig (-0.00098), and Connecticut bear (-0.07717) movement means EXACTLY, then matched their original animal sampling dates to predeclared *coarse study-region* climate grids:

| Region | Falling−rising ERA5 regional mean T | Falling−rising 30-day P−ET0 proxy | Mammal relative night/day outcome |
| --- | ---: | ---: | ---: |
| Banff/elk | +9.751 °C | +5.577 mm | +0.04500 |
| Southern Florida/pig | +1.794 °C | +112.014 mm | -0.00098 |
| Connecticut/bear | +9.865 °C | -66.457 mm | -0.07717 |

All three group-average thermal differences were positive while the GPS response signs were not the same. It does **not** follow that local temperature is irrelevant: each climate source is a single coarse public ERA5 grid, not measured individual exposure, and species is confounded with study region, recruitment years and traits. The water index is **precipitation minus reference evapotranspiration demand**, not actual soil moisture. [Full three-source GPS+ERA5 result](movebank_gps_regional_era5_joint_ecological_result_20261019.md), [successful source run](https://github.com/zuizui0223/odsp/actions/runs/39203998039).

Further Southern Etosha matched-date region-climate integration is a **separate planned result**, not inferred from the Northern table. There is no tested vegetation phenophase/forage mediation or taxonomic trait coefficient as of this synthesis.

## Source failures and sample-selection limits

The eight-source Northern independent extension preselected new study archives from the complete repository metadata. Its **four provider original checksum mismatches** remain SOURCE HOLD, and one moose source yielded inadequate seasonal support; they are not replaced by studies selected on ecological outcome. Original hour-cadence mismatch in the elephant v0 route remains an independent endpoint failure. Camera-photo and GPS-step response variables are never pooled as though identical.

The present independent cohorts arise from an openly enumerated published-data frame, but **they are not representative of global animals, all environments, species phylogeny or abundance of different feeding guilds**. Public tracking studies are selected by funding, capture feasibility, researcher interest, tag battery schedules, and archive openness. Those selection effects must be accounted for before prevalence or universal trait claims.

## Biological next step: explanation rather than a prediction score

The candidate explanation is **ecological-calendar mismatch**: thermal, hydrological and vegetation phenophase contrasts at equivalent solar daylength may be related to relative nighttime movement, but the relationship could change with food guild, body size, breeding stage and spatial movement strategy. A stronger analysis needs source-specific **experienced** weather and remotely sensed vegetation at the actual matched GPS date and location, at least two cohorts per same species or documented movement guild, and population/recruitment hierarchy to separate within-individual, among-year and between-population responses.

The contribution will be which environmental/biological conditions accompany the observed changes—and counterexamples—not high cross-validation accuracy. As originally requested, ODSP retains its method/measurement safeguards in support of an **ecology-first paper built from a transparent public-source database**, not a paper about improving cameras.
