# ODSP: systematic new-source solar azimuth ecology, first GPS outcomes

Date: 2026-10-25. Status: exploratory **original public GPS data** analysis, not published-effect meta-analysis or confirmatory population inference.

## Original sample chosen without new solar-bearing outcomes

The 2026-10-19 Movebank public registry contains **437** original data packages, including **259** GPS/GNSS-labelled archives. The prior nine analyzed archive IDs were excluded explicitly. Registry animal/position-count and nonempty species-label rules yielded **186** new metadata-qualified candidates. Four strata were fixed by source species-label richness (one vs multiple distinct taxon labels) × source registered animal count (5–29 vs >=30), with original stratum sizes 92, 13, 68 and 13 respectively. The three smallest SHA256 hashes per stratum were taken under one frozen public seed, without original GPS outcome or publication-effect access. All 12 remain in the sample forever, whether or not their GPS works.

- [Exact selection contract](../research/GLOBAL_SOLAR_AZIMUTH_INDEPENDENT_12SOURCE_V1_CONTRACT.json)
- [Selected original 12 UUIDs/files/provider checksums, frozen pre-effects](../research/GLOBAL_SOLAR_AZIMUTH_12_NEW_SOURCE_FROZEN_ORIGINAL_FILE_MANIFEST_20261025.json)
- [Metadata-only Actions](https://github.com/zuizui0223/odsp/actions/runs/40164002601)
- [First original-GPS effects and all failed/null source groups](../research/GLOBAL_SOLAR_AZIMUTH_12_NEW_SOURCE_FIRST_ORIGINAL_GPS_RESULT_20261025.json)
- [Original-data first Actions: 3/3 shards successful](https://github.com/zuizui0223/odsp/actions/runs/40164287129)

**Original sample fates:** 12 fixed, 8 original-file-metadata admissible, 4 file ambiguity or size HOLD, then 7 original provider-MD5-verified GPS files analyzed; one otherwise admissible baboon original ZIP exceeded frozen 300-MB *uncompressed* safety cap and remained HOLD (no substitute). Seven processed originals gave **1,568,073 GPS source rows**, **49,005 qualified daylight moving intervals across all original taxa** of which **48,246** belong to source×taxon groups with >=5 eligible animals. Eight original source×taxon groups qualified, comprising **103 source-summed qualified animals**, not independent field populations. Never count 5 source HOLD cases as zeros.

A previously unprocessed Washington coyote/bobcat original had 121,706 GPS rows but no 0.5–2h qualified daylight movement intervals. One greater spear-nosed bat archive had 253,968 rows, 140 time-only hourly fixes, and zero qualifying daytime intervals; sensor schedule and sunlight filtering cannot be interpreted as intrinsic bat activity behavior. A domestic livestock original included 135,264 records under taxon strings not matching the two fixed published archive labels; the Canis familiaris registered category is declared NO_SOURCE_TAXON_RECORDS by the original v1 parser, not retrospectively renamed.

## Source-verified exploratory ecological results

Mean raw sun-relative GPS movement cosine (R) and a DIFFERENT conditioned within-individual × calendar-month × two-hour apparent-solar-clock circular covariance (C):

| Source taxon | n qualifying animals | R | C |
|---|---:|---:|---:|
| Illinois coyote (Canis latrans) | 17 | −0.01844 | −0.00406 |
| Illinois bobcat (Lynx rufus) | 5 | −0.00532 | −0.00468 |
| Illinois white-tailed deer (Odocoileus virginianus) | 35 | −0.01465 | +0.00105 |
| Raptor Buteo rufinus | 10 | −0.00633 | −0.00300 |
| Raptor Circaetus gallicus | 5 | +0.00266 | −0.00308 |
| Great hornbill (Buceros bicornis) | 5 | −0.00060 | +0.00172 |
| Domestic sheep (Ovis aries) | 8 | −0.02975 | −0.00384 |
| Egyptian vulture (Neophron percnopterus) | 18 | −0.06493 | −0.00492 |

Illinois co-archived carnivores and deer have weak *marginal source-mean* raw sun-relative bearing preferences with all their respective source-animal bootstrap 95% intervals spanning zero. This **does not support a claimed predator/prey solar-direction niche partition** on marginal GPS time and does not yet check if species share the same grid-month/solar-hour cells. The two raptor species differ in raw sign, but within-clock conditional circular covariances are similarly small; only Circaetus 5-animal uncorrected source-animal conditional interval excludes zero, among several tested taxa. No replicated raptor solar compass specialization is demonstrated. Egyptian vulture raw R −0.06493, source-animal 95% [−0.11860, −0.00674], but C −0.00492 [−0.01132, +0.00142] contains zero. Routes, migration, GPS schedule, terrain and sunlight exposure can all confound source-level signs.

## Combined global source frame

The old 9 authenticated sources plus new 7 original GPS sources total **16 MD5-verified original files**, with **14** supplying at least one supported cohort. There are **21 qualified source×taxon rows** across **17 literal taxon names** and **12,466,431 rows of original GPS data processed**. Across all verified sources, **1,136,878 daytime movement intervals** met geometric filters; **1,136,119** belong to source×taxon groups with >=5 eligible animals. **3,038** is the sum of admitted source×taxon animal counts, NOT demonstrated unique animals or 3,038 independent environmental replicates. [Full combined source table with nulls and source holds](../research/GLOBAL_SOLAR_AZIMUTH_V1_ALL_SOURCE_GROUP_MATRIX_20261025.csv); [source-level summary with independent-unit cautions](../research/GLOBAL_SOLAR_AZIMUTH_V1_COMBINED_SOURCE_SUMMARY_20261025.json).

There are 7 positive and 14 negative raw source×taxon point means among the 21 source-qualified groups; source-specific animal-bootstrap intervals exclude zero in 8 raw groups and 4 conditioned groups. These are descriptive, uncorrected across taxa and cannot establish species-wide or biome-wide solar response. Nothing identifies actual animal body orientation, an evolved sun compass, use of shady refuges, or a direct thermal causal mechanism.

**Macro ecological question remains:** after systematic additional original-source admission and study-population deduplication, which ecology or environment (habitat structure, wind, slope aspect, vegetation season and independent climatic history) modifies observed solar-relative travel bearing? One should investigate within-study matched location×month×solar-hour contrasts before asserting species interactions, and then combine independent region populations rather than a handful of published examples.

Status: DRAFT, source-verified exploratory primary observations; historical ODSP model/prediction/season terminal results remain unchanged.
