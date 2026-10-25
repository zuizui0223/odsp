# Global variation in animal movement directions relative to the Sun: a source-wide original GPS macroecology

**ODSP manuscript v1 | 2026-10-25 | DRAFT / exploratory observational ecology**

**Evidence declaration.** This study computes NEW directional ecological indices from publicly archived, original animal GPS records. It is NOT a meta-analysis of reported findings from original publications. Source authors and file licenses remain credited by their original DOIs. It is not a causal field experiment and has not established a global biological response to solar azimuth.

## Abstract

Solar azimuth defines a global moving compass reference, yet animal travel headings can covary with Sun position because of diel schedules, migration corridors and landscape orientation rather than direct use of sunlight. We established a provenance-preserving observational database by enumerating all **437** public Movebank Data Repository packages in a fixed 2026-10-19 snapshot, including **259** packages carrying GPS/GNSS sensor metadata. A non-outcome original-file inventory resolved all 259 bundles; bounded original CSV-header examination identified **159** packages with the four necessary timestamp, animal ID and latitude/longitude columns. From progressively frozen, source-selected original files, **40** archives passed their provider checksum and contained **14,756,835** GPS observation rows. Of these, **29** archives yielded at least one source×taxon cohort meeting predefined directional-movement criteria, giving **41 qualified cohorts across 32 taxon-name labels**, **1,295,932** eligible daylight movement intervals, and **3,351** source-group-summed animal qualifications, which are not independent worldwide population sample sizes. Raw sun-relative travel cosines were positive in 16 and negative in 25 cohorts. We decomposed raw alignment into an exact geographic-compass×solar marginal term and a joint direction–Sun circular covariance, finding that the two terms had larger magnitudes in 20 and 21 cohorts, respectively. Mule deer showed a raw positive mean in Utah (+0.02339) but a negative mean in Wyoming (−0.04876), with different relative contributions from the two terms. To test shared ecological support rather than juxtaposing taxa across unrelated locations, an exploratory grid-month-solar-hour analysis of all ten predefined multitaxon source archives found one supported pair, two tropical vulture taxa, with a between-species sun-relative directional mean difference of +0.03366 over 45 common coarse cells, but it does not establish behavioral competition or distinct solar-cue use. The shared-cell initial source reread also encountered five provider-access/checksum holds and requires a separately documented strict technical replay. Our findings show empirically measurable, heterogeneous **observed sun-relative travel geometry**, but climatic, geographic, sensor and movement-strategy causes remain unresolved. Original-data source coverage and source-independent population attribution are prerequisites for a causal or generalized macroecological account of solar-directional niches.

## Introduction

### The ecological question, not a coordinate-conversion exercise

At any geographical location and instant, sunlight has a particular azimuth and elevation. Moving animals experience this directional field alongside terrain, wind, vegetation, habitat, their own orientation and migratory routing. A single universal prediction such as "animals move toward sunlight" is not required. A more discriminating macroecological question is whether the *relation* between travel directions and astronomical solar bearings is organized systematically by movement ecology, seasonal environment and habitat geometry, and whether repeatable patterns survive conditioning on mundane clock and compass composition.

Originally archived GPS observations permit the calculation of a single transparent comparison quantity for multiple species, field populations and biomes; published paper effect sizes cannot supply the same observation denominator or resolution. The scientific innovation sought here is **cross-environment organization of solar-relative movement niches**, not new sunrise formulas, prediction-model score improvement or a reference-paper synthesis.

### Three distinct levels of evidence

**Level I—observational geometry.** Is there repeatable raw solar-relative travel alignment within original GPS source populations?

**Level II—context dependence.** Does the same species or the same source's taxon pair differ in the components of this alignment when observation scale and common ecological opportunities are matched?

**Level III—mechanism and generalization.** Are independent field-population differences associated with landscape aspect, habitat shade, prevailing wind relative to solar azimuth, thermal/water histories, phenology and movement guild, after accounting for source cadence, solar-angle availability and geographical dependence? Level III requires independent environmental linkage and is NOT established by the current results.

## Materials and methods

### Registry and study inclusion

The primary registry is the complete archival catalog frozen 2026-10-19. It has 437 public data packages; 259 metadata-label GPS/GNSS. Public source packages are NOT statistically independent biomes, populations or even necessarily disjoint animal deployments. Three study-ID values occur on more than one GPS/GNSS package (six packages total); two GPS/GNSS packages lack study IDs. Every archive and species label must retain its DOI, study identity, original license, original checksum and all recorded source holds.

First, all 259 original source bitstream lists were resolved; 670 data-container filename-suffix hints arose, but a suffix is not a verified original GPS schema. Bounded 8-KB original header-only screening found 159 canonical 4-column plain source CSVs; the remaining 100 were classified as multi-file/ambiguous (62), over original transfer cap (29), compressed (5) or missing required columns (4). No animal observations were read by that screen.

Next, a blinded registry metadata sample of 12 new sources was selected from 186 metadata-qualified candidates, in four combinations of species-label count × reported animal count, with three fixed SHA-hash ranks per combination and no source substitution on errors. It contributed seven checksum-verified usable source files, eight qualified cohort results, plus all source and animal-support holds. Subsequent header-supported sample was fixed at 24 further primary CSV original UUIDs (all ten remaining multi-taxon sources plus fourteen single-taxon SHA-ranked sources) before new GPS direction values were exposed. All 24 source original files passed integrity and original event analysis on the frozen first run; 20 source×taxon groups met the n>=5 independent tagged-animal descriptive threshold. Historic original nine-source pilots had already been analyzed for different temporal estimands and are labeled post-prior-outcome exploratory, never newly untouched validation.

### GPS and astronomy

Let B be the initial great-circle compass bearing, clockwise from geographic north, of an original same-tag 0.5–2h GPS displacement; let A be the approximate NOAA geometric solar azimuth at the original interval midpoint and its real location. Daylight moving intervals require original displaced distance >=100m, speed <=60km/h and solar elevation >=10° at original start, midpoint and end. No original sun-day crossing is allowed. Time-only nearest-UTC-hour-start selection was applied for certain existing sources and all new v1/v2 sources; historic source-specific cadence selection may differ, precluding naïve global effect pooling.

Define raw sunward *travel* mean R = E[cos(B−A)]. An axial alternative E[cos(2(B−A))] is stored; neither describes animal head/body orientation or sunlight exposure. The **exact circular identity** within an individual sample is

R = (E[cos B] E[cos A] + E[sin B] E[sin A])
  + (Cov(cos B, cos A) + Cov(sin B, sin A)),

which separates an expected projection from the independent observed geographic-compass/Sun marginals (G) and additional paired circular covariance (J). It is a statistical identity, not a causal mediation result. We compare source groups with animal-equal and year-equal weight.

A distinct conditional response estimates circular covariance only from within-animal, within-calendar-month, two-hour apparent-solar-clock strata with >=8 source GPS intervals, >=3 solar dates and >=5° original azimuth span. An eligible animal-year requires >=30 intervals over >=5 days, a source taxon generally >=5 eligible animals. The conditional response and the raw R use **different observational support**, therefore their ratio is NOT an attenuation estimate. A null/unsupported conditional cell is not absence of solar sensory behavior.

### Across-taxon ecological common support

After inspecting marginal source results, we separately froze a **post-exposure exploratory** common-support route for all ten v2 multi-taxon primary original sources. Species pairs compare solar-relative movement only within identical source × 1° latitude-longitude grid × calendar year-month × 4-hour apparent-solar-clock stratum. For each taxon and stratum require >=3 tagged animals, >=3 original solar dates and >=15 qualifying steps. Species pairs require >=3 common strata; mean per-species animal-equal solar alignment is compared equally over shared strata. All combinations failing common support remain undefined; grid locations, exact original dates and animal IDs stay inside the runner. This does not demonstrate fine-scale encounters, interactions or competition. Descriptive original-source animal bootstrap percentile intervals are not familywise or independent-region significance tests.

## Results

### Original-data universe and quantitative support

Provider checksums and original source analyses authenticated **40** original source files. Of those, **29** each supply at least one qualified taxon group, for **41** source×taxon effect rows over **32** literal scientific names. These represent **14,756,835** original GPS rows, with **1,295,932** daytime directional intervals in n>=5 admitted groups and summed **3,351** qualified source taxon animal records. Additional unsupported animal observations/source taxa and source technical holds remain in the [complete derived matrix](../research/GLOBAL_SOLAR_AZIMUTH_COMBINED_V2_ALL_ORIGINAL_SOURCE_TAXON_MATRIX_20261025.csv) and [full summary](../research/GLOBAL_SOLAR_AZIMUTH_COMBINED_V2_MACRO_SUMMARY_20261025.json). These sample totals are NOT n=41 independent ecosystems, nor 3,351 verified distinct biological individuals worldwide.

Among 41 source×taxon means, R was positive for **16** and negative for **25**; abs(G)>abs(J) in **20** and abs(J)>=abs(G) in **21**. Source-conditional exploratory animal-bootstrap percentile intervals exclude zero in 16/41 raw source groups and 5/41 conditional source groups. No multiple testing correction, phylogenetic regression, independent-population interval, causal environmental adjustment or probability of future study generalization has yet been established.

### Within-species variation and decomposition

A contrast in two independent-source Utah and Wyoming mule deer original archives illustrates that the signed raw pattern is not a fixed species property: Utah R = **+0.023393** (1,652 eligible animals), decomposed G = +0.003049 and J = +0.020344; Wyoming R = **−0.048758** (110 animals), G = −0.042838 and J = −0.005920. In the distinct conditional solar-time-stratified estimand, Utah +0.000305 (animal-bootstrap interval −0.000071..+0.000623, n1509) and Wyoming −0.000743 (−0.002772..+0.001236, n106) each included zero. These data show *different observational decomposition*, not ecological seasonality or alternative sun compass mechanisms.

African elephant source cohorts similarly differ in raw signed means, +0.03314 (Etosha) versus −0.00903 (Kruger), but the Kruger bootstrap interval spans zero and the individual samples are small (15 vs14). Among two red fox sources, R was negative in both (−0.0430 vs −0.1053), and two barnacle goose sources were positive (+0.01355 vs +0.08280); raw magnitudes also include original study-year/device, sample-region and movement-route differences. The latter are examples of the current source matrix, not selected independent replication proof.

### Across-species within-common-stratum contrast

Among the ten frozen v2 original multi-taxon archives, the first common-cell analysis yielded 17 registered species-pair comparisons. In the FIRST workflow, five original archive rereads authenticated and five returned source HOLD (three provider checksum mismatches and two provider connection failures), even though those archives passed the earlier first v2 original-source verification. Among the original result's five usable archives, only **one** species pair passed prespecified common spatial-month-solar-time support: tropical vulture taxa *Cathartes melambrotus* versus *Sarcoramphus papa*, with equal-shared-cell R_A − R_B = **+0.033663**, 45 shared strata in 2 broad 1° grids and 15 year-months, five original individuals per species. No valid spatial-block/source independent interval was generated. The two fox taxa *Vulpes lagopus* and *Vulpes vulpes* had zero preselected matched cells despite opposite unconditioned raw signs; this forbids claims of co-occurring fox temporal solar-angle niche separation on these data.

The five repeat-read technical source holds remain historically frozen. A separate precontracted, single serial, unchanged ecological-input technical replay is being evaluated; its output cannot change the first results or imply independent new ecological confirmation. Details: [original first complete same-cell result](../research/GLOBAL_SOLAR_AZIMUTH_MULTI_SOURCE_SHARED_CELL_V0_FIRST_RESULT_20261025.json).

## Discussion

**Conservative positive ecological conclusion.** Animals across the registered source population sample show substantial *descriptive variation in the geometry of original daytime travel headings relative to astronomical solar azimuth*. This variation is neither invariably sunward nor antisunward and the relative marginal-compass and paired circular-covariance components can differ across independent original source recruitment contexts, including within a named species. A within-source shared-opportunity comparison is possible for at least one species pair; most proposed pairwise claims lack shared spatial/season/solar-clock support.

**Important negative identification finding.** A raw sun-relative cosine is not an animal sun-orientation mechanism, and common timestamps and angles alone cannot separate actual solar cue use from routes, migration corridors, terrain, diurnal seasonality, source GPS cadence and environmental history. Diel/clock-conditioned covariance uses reduced within-time azimuth contrasts and need not be the same biological estimand. The shared pair does not establish trophic avoidance, predator competition or partitioning of an observable sun-derived niche.

**Next macroecological test.** To move from the present multi-source descriptive database to broad ecological inference, separately enumerate independent geographically disjoint source populations and record measured environmental covariates at original sampling locations: surface solar flux and terrain-aspect interaction with Sun altitude/azimuth, wind vector relative to migration bearing, habitat canopy or vegetation seasonal phase, ERA5 temperature/water history, and behavioral movement guild. Then estimate whether source-population directional geometry co-varies with those environmental contexts, with nested individual/year/site/source terms and published original sample selection; retain all no-support and negative data. No new positive worldwide interaction effect is asserted yet.

## Data availability and study integrity

Source metadata census, original provider checksums, pre-outcome frozen source UUID selections and derived group-level observations are in ODSP's independent branch. Original GPS coordinates, exact time stamps, tracks and identifiable original animal IDs are not redistributed, and original source licenses (including noncommercial sources) remain attached through provider DOIs. Earlier ODSP seasonal activity/diel GPS and other terminal scientific decisions remain unchanged.

**Current decision:** exploratory independent original-data comparative ecology manuscript; NOT yet a confirmatory, biome-general, climatic-causal or source-independent inference paper.
