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
| Kruger, South Africa | *Loxodonta africana* | **13** | **-0.02889** | [-0.04336, -0.01172] | 2 positive / 11 negative |

**254 admitted individual animals across ten original source-specific cohorts (nine taxa).** This count does NOT imply 254 independently sampled populations, a random global mammal sample, or replication of a physiological mechanism. The rows are cohorts, not species-wide parameter estimates; the bootstrap interval quantifies source-animal sampling conditional on its original observation context.

**Observation-architecture exception: elephants.** The provider-MD5-verified original Etosha elephant ZIP contains ~2.93 million GPS fixes at a cadence incompatible with the original 30–120-min *adjacent*-fix rule (only 413 eligible original adjacent steps and no eligible animal-year). This v0 insufficiency stays unchanged. Elephant's estimate above belongs to a separately frozen **v1**, created only after that cadence limitation was observed, which selects **one original fix per UTC clock hour by timestamp alone** (no displacement-based selection), then applies the unchanged 30–120-min GPS and Southern photoperiod rules. It is a different observational estimand. [MD5/source-only ZIP audit](https://github.com/zuizui0223/odsp/actions/runs/39207207985) · [original v0 result](https://github.com/zuizui0223/odsp/actions/runs/39207354970) · [time-only elephant v1](https://github.com/zuizui0223/odsp/actions/runs/39207964106).

**Cross-source robustness of the Etosha contrast:** Subjecting jackal GPS to the **same** outcome-blind hourly time selection as elephants gives **+0.04479** rather than the native +0.05485, for eight eligible jackals (5 positive/3 negative; 95% animal-bootstrap interval [-0.00211, +0.11922]). Thus the point-estimate direction of elephant (negative) versus jackal (positive) remains different under the same time selection scheme, but the jackal effect is less precise. The comparison is *post-outcome sensitivity*, not independent blinded confirmation. [Jackal hourly sensitivity run](https://github.com/zuizui0223/odsp/actions/runs/39208418314).


## Independent second population of African elephants (Kruger, South Africa)

The complete 437-package Movebank census contained an independent **Kruger National Park** source for the **same species, *Loxodonta africana***, selected by taxonomy and original public GPS coverage independently of the new movement effect. Its original 43,776,326-byte GPS CSV (283,688 raw fixes, 14 female elephants drawn from different herds) passed the **provider-declared MD5**. Under the previously fixed time-only UTC-hourly and Southern daylength comparison, **13 animals** qualified for 1,787 GPS solar-matched date pairs. **11/13** had a negative relative night/day speed contrast, with elephant-equal mean **−0.0288937** and descriptive animal-bootstrap 95% interval **[−0.043357, −0.011718]**. With the original native 30–120-minute adjacent GPS fixes, the same source returned **−0.0322313** and 11/13 negative, independently of hourly thinning. Original grouped result: [Kruger source-confirmed run 39210827847](https://github.com/zuizui0223/odsp/actions/runs/39210827847). Provider DOI: [10.5441/001/1.403h24q5](https://doi.org/10.5441/001/1.403h24q5), original source CC0.

The direction of seasonal **relative daylight GPS displacement** is therefore shared by the **two geographically distinct, source-independent elephant cohorts**, Kruger and Etosha, although their magnitudes differ considerably. This provides replication at the level of independent study populations, but not a random continent-wide elephant sample nor a temperature-driven mechanism: the sources cover different years, habitats, sex compositions, tracking schedules and rainfall histories.

Importantly, the Kruger data originally belong to [Thaker et al. (2019)](https://doi.org/10.3389/fevo.2019.00004), which **already established** an association between collar thermal readings, elephant GPS movement and water shuttling. Re-demonstrating a generic temperature–speed association alone would not be a new ecological discovery. The source's public CSV additionally includes `external-temperature` (degrees Celsius), which the original authors explicitly caution measures a combination of ambient conditions, electronics heat and animal heat, albeit useful for relative ambient thermal variation. A newly fixed *separate* question is whether, **within the same elephant at matched astronomical daylength**, a seasonal change in its relative DAY-minus-NIGHT collar thermal gradient covaries with seasonal redistribution of NIGHT-minus-DAY displacement. The original Kruger GPS effect was source-verified **before** this thermal-difference outcome is inspected. Do not call the sensor animal body temperature or an uncalibrated absolute ambient temperature.

## Critical post-outcome year-stratified Etosha follow-up (2026-10-19)

**The apparent pooled elephant-vs-jackal sign opposition must be qualified.** After restricting to the two originally source-supported overlapping solar-year cycles (2009 and 2010) and then splitting **each year separately**, the source-matched results were:

| Southern solar cycle | Etosha elephants, hourly GPS | Etosha jackals, identical hourly GPS | Same regional matched-date water-balance proxy (elephant / jackal) |
| --- | --- | --- | --- |
| **2009** | **−0.26287**, 11/11 individuals negative; animal bootstrap 95% [−0.34969, −0.17352] | **+0.00926**, 4/7 positive; bootstrap [−0.00617, +0.02605], includes zero | **+118.31 / +116.29 mm** (30-day regional P−ET0) |
| **2010** | **−0.24226**, 5/5 negative; bootstrap [−0.30207, −0.18244] | Only **one** qualifying animal and 11 date pairs: **direction UNAVAILABLE**, not zero | +157.90 mm elephant; jackal one animal +48.73 mm, insufficient for a robust group comparison |

The 2009 observed solar calendar contains **173 distinct identical matched date pairs admitted somewhere in each species' dataset** (not 173 simultaneously collared co-located animal pairs). In 2010 only **9** such common date pairs were supported. Original provider checksums and the earlier pooled whole-source effects were reproduced **exactly before the new year-specific effects were opened**, all three source-blind tests passed, and the [GitHub Actions analysis succeeded](https://github.com/zuizui0223/odsp/actions/runs/39210319995).

**Biological conclusion now supported:** At near-equal photoperiod, Etosha elephants in these tracked cohorts consistently had **greater relative daylight movement on the decreasing-daylength side in both separate solar years**. The jackal population did not have a clearly detected analogous displacement; evidence for an *opposite, positive* jackal shift is weak after disaggregation by year. The robust result is therefore **elephant-specific repeated temporal redistribution in this source sample and heterogeneity of measured temporal response**, NOT a validated pair of opposing species-wide seasonal strategies.

In the **2009** observational windows for both source cohorts, the *same* coarse regional ERA5 grid shows a rising climatic P−ET0 proxy on the decreasing-daylight branch. This is a meaningful environmental context for the ecological calendar question, **not** a demonstration that rainfall or water availability caused the elephant movement shift. Environmental estimates are modeled coarse-region conditions, not animals' experienced vegetation, waterhole use or individual thermal exposure. Source individuals share years and region, but exact GPS dates, habitat and recruitment conditions are not held equal.

Original source attribution: Etosha elephant [10.5441/001/1.3nj3qj45_2](https://doi.org/10.5441/001/1.3nj3qj45_2) (source metadata CC BY-NC 4.0); Etosha jackal [10.5441/001/1.n1r7ds5r](https://doi.org/10.5441/001/1.n1r7ds5r) (CC0). This derived report republishes no coordinates, individual identities or raw trajectories.

## Three positive biological observations, with strict scope

**A. Same astronomical photoperiod does not imply a universal diel movement response.** Multiple qualified Northern and Southern source cohorts show positive, negative, or very small seasonal changes. One simple claim—"animals uniformly shift toward night on the declining-daylight branch"—does not describe these ten sources. The question is now **which ecological contexts and biological traits are related to different reallocations**, not whether a model can predict the sign.

**B. Similar group seasonal means can hide different day/night components.** In Banff wapiti, relative nightward displacement (+0.04500) combines lower daytime log1p GPS speed (-0.02411) and higher nighttime log1p GPS speed (+0.02089). In Connecticut bears, the reverse contrast (-0.07717) combines higher daytime (+0.06685) and lower nighttime (-0.01032). In Etosha native-step jackals, the relative nightward contrast (+0.05485) includes **higher** daytime (+0.01638) as well as greater nighttime (+0.07123) displacement. Thus "more nocturnal" is an incomplete biological interpretation of this measured endpoint.

**C. Same broad ecosystem can contain different magnitudes of response, but the earlier apparent sign opposition is not robust to year stratification.** Etosha elephants have a pronounced negative same-photoperiod night-relative shift in both 2009 and 2010. In 2009, jackals are near zero under the same timestamp-only hourly selection, while 2010 jackal data support just one animal. The resulting central ecological question is **why elephant temporal redistribution is repeatable across these wetting seasonal transitions while an analogous jackal shift is not clearly detected**. This is a source-specific association, not proof of species physiology, food, behavior-mediated water use, competitive displacement or direct contemporary interaction.

## Environmental status

A **separately registered, post-original-GPS-outcome** three-region ERA5 linkage reproduced the locked Banff wapiti (+0.04500), Florida pig (-0.00098), and Connecticut bear (-0.07717) movement means EXACTLY, then matched their original animal sampling dates to predeclared *coarse study-region* climate grids:

| Region | Falling−rising ERA5 regional mean T | Falling−rising 30-day P−ET0 proxy | Mammal relative night/day outcome |
| --- | ---: | ---: | ---: |
| Banff/elk | +9.751 °C | +5.577 mm | +0.04500 |
| Southern Florida/pig | +1.794 °C | +112.014 mm | -0.00098 |
| Connecticut/bear | +9.865 °C | -66.457 mm | -0.07717 |

All three group-average thermal differences were positive while the GPS response signs were not the same. It does **not** follow that local temperature is irrelevant: each climate source is a single coarse public ERA5 grid, not measured individual exposure, and species is confounded with study region, recruitment years and traits. The water index is **precipitation minus reference evapotranspiration demand**, not actual soil moisture. [Full three-source GPS+ERA5 result](movebank_gps_regional_era5_joint_ecological_result_20261019.md), [successful source run](https://github.com/zuizui0223/odsp/actions/runs/39203998039).

A **separate post-outcome Etosha ERA5 same-region result** now links the *actual admitted animal GPS date-pairs* to a common regional grid (19°S, 16°E), without modifying the earlier movement outcomes:

| Etosha source | Qualifying Southern solar cycles | Falling−rising ERA5 daily mean T | Falling−rising preceding-30d P−ET0 | Already measured GPS contrast |
| --- | --- | ---: | ---: | ---: |
| *Loxodonta africana*, hourly fix route | 2008–2013 | **−1.047 °C** | **+99.629 mm** | **−0.15013** |
| *Canis mesomelas*, same hourly sampling | 2009–2010 | **+0.091 °C** | **+107.850 mm** | **+0.04479** |

The original observed solar years overlap in **2009 and 2010**, but the older elephant full-source mean includes four additional solar cycles. The water proxy has a positive within-individual mean in all **14/14** eligible elephants and all **8/8** eligible jackals, but climatic P−ET0 is neither forage quality nor measured soil moisture. Temperature directions differ across their source-specific sets of sampled dates. [Original archive, solar-date and regional ERA5 combined run](https://github.com/zuizui0223/odsp/actions/runs/39208971379), whose source responses, hashes and zero climate-join losses are preserved. A **separately fixed 2009–2010-only GPS follow-up** is needed to address this remaining temporal confound. Neither temperature nor water has a causal coefficient in these figures. There is still no tested vegetation phenophase/forage mediation or cross-population taxonomic trait coefficient.

## Source failures and sample-selection limits

The eight-source Northern independent extension preselected new study archives from the complete repository metadata. Its **four provider original checksum mismatches** remain SOURCE HOLD, and one moose source yielded inadequate seasonal support; they are not replaced by studies selected on ecological outcome. Original hour-cadence mismatch in the elephant v0 route remains an independent endpoint failure. Camera-photo and GPS-step response variables are never pooled as though identical.

The present independent cohorts arise from an openly enumerated published-data frame, but **they are not representative of global animals, all environments, species phylogeny or abundance of different feeding guilds**. Public tracking studies are selected by funding, capture feasibility, researcher interest, tag battery schedules, and archive openness. Those selection effects must be accounted for before prevalence or universal trait claims.

## Biological next step: explanation rather than a prediction score

The candidate explanation is **ecological-calendar mismatch**: thermal, hydrological and vegetation phenophase contrasts at equivalent solar daylength may be related to relative nighttime movement, but the relationship could change with food guild, body size, breeding stage and spatial movement strategy. A stronger analysis needs source-specific **experienced** weather and remotely sensed vegetation at the actual matched GPS date and location, at least two cohorts per same species or documented movement guild, and population/recruitment hierarchy to separate within-individual, among-year and between-population responses.

The contribution will be which environmental/biological conditions accompany the observed changes—and counterexamples—not high cross-validation accuracy. As originally requested, ODSP retains its method/measurement safeguards in support of an **ecology-first paper built from a transparent public-source database**, not a paper about improving cameras.
