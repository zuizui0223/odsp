# Independent original-GPS solar azimuth macroecology: first complete source audit

**2026-10-25, first run successfully completed and source-original group results preserved.**  
**Status: exploratory primary data analysis, not cross-population generalization or causal proof.**

- First full source/known-truth workflow: [Actions 40162457020](https://github.com/zuizui0223/odsp/actions/runs/40162457020), four jobs succeeded, nine geometry/source known-truth tests passed.
- Frozen before first new azimuth outcome: [V0 original-response contract](../research/GLOBAL_SOLAR_AZIMUTH_MACRO_V0_CONTRACT.json).
- All nine groups, both negative and positive: [provider-MD5-qualified original-source results](../research/GLOBAL_SOLAR_AZIMUTH_V0_FIRST_ORIGINAL_GPS_RESULT_20261025.json).
- Source overlap: [independent audit of all 259 high-resolution sensor-labeled catalog entries](../research/GLOBAL_SOLAR_AZIMUTH_SOURCE_STUDY_OVERLAP_AUDIT_20261025.json).

## Directly observed original data, not paper effects

All FIVE provider original GPS file archives (three independent previously registered original pilots, one Utah four-ungulate archive, one separate Wyoming two-ungulate archive) had matching original provider MD5. In total: **7,330,427 original rows**, **915,783 new daytime directional qualified consecutive GPS steps**, **9 source×taxon groups**, **6 literal taxon names**, **2,844 sum of source×taxon eligible-animal counts** and **2,674 source×taxon eligible-animal counts for within-clock conditional estimand**. The sums are NOT necessarily unique individuals across all studies, independent ecosystems, or valid biological N for a pooled significance test.

Raw mean cosine of animal displacement direction relative to actual solar bearing A is a DESCRIPTION, not animal orientation to sun. The 'clock' column is an animal-year / month / apparent solar-time conditioned CIRCULAR COVARIANCE statistic, a DIFFERENT estimand with more restricted sun-azimuth variation. Never claim numerical attenuation ratio from comparing these two scales.

| Archive/cohort | N animals for raw outcome | Raw E[cos(travel−sun)] | Clock-restricted circular covariance (same-source N) |
|---|---:|---:|---:|
| Canada wapiti (*C. elaphus*) | 130 | −0.065289 | +0.000356 (128) |
| Florida wild pig (*S. scrofa*) | 10 | +0.005674 | −0.007599 (10) |
| Connecticut black bear (*U. americanus*) | 21 | +0.006369 | +0.000898 (21) |
| Utah pronghorn (*A. americana*) | 212 | −0.004511 | −0.000255 (209) |
| Utah wapiti (*C. elaphus*) | 327 | −0.030992 | −0.001506 (321) |
| Utah mule deer (*O. hemionus*) | 1,652 | +0.023393 | +0.000305 (1,509) |
| Utah bighorn (*O. canadensis*) | 341 | +0.020778 | −0.000289 (329) |
| Wyoming mule deer (*O. hemionus*) | 110 | −0.048758 | −0.000743 (106) |
| Wyoming bighorn (*O. canadensis*) | 41 | −0.005281 | −0.000179 (41) |

### Nontrivial descriptive ecology

**The mule deer raw sun-relative displacement association switches sign across two independently archived regional field populations:** Utah **+0.02339**, Wyoming **−0.04876**. Individual-cluster source bootstrap ranges are Utah **[+0.01626,+0.03067]**, Wyoming **[−0.06882,−0.03128]**. Distinct GPS study, landscapes/observational contexts; not yet a formal region-cluster causal or global interaction test. Wyoming has far fewer animals and possible other sample structure differences.

After restriction to within-animal/month/2h apparent-solar clock variation, the point estimates are Utah **+0.000305** (individual-bootstrap 95% [−0.000071,+0.000623]) and Wyoming **−0.000743** ([−0.002772,+0.001236]); both include zero. The adjusted contrast does NOT estimate the same quantity as raw sunward mean, and its solar-angle support may be small. It specifically does not justify an assertion that solar direction is irrelevant.

**Wapiti:** Canadian raw −0.06529 and Utah raw −0.03099, each individual-bootstrap interval excludes zero in that distinct sampled field population, whereas within-clock covariance is Canada +0.000356 (CI crosses zero) and Utah −0.001506 (descriptive CI [−0.002424,−0.000662]). Biological within-population mechanism not identified; differing sampling, migration, terrain and tracking gaps remain alternatives.

**Wild pig:** Florida within-clock covariance −0.007599 (descriptive animal bootstrap [−0.011684,−0.003865]) in TEN eligible individuals; do not treat as study-independent proof of active avoidance, ecological universal response, or multiple-comparison-corrected statistical discovery.

Across the nine source×taxon groups, 5 original raw alignment animal-bootstrap intervals exclude zero and 2 clock-restricted intervals do. These are unadjusted, within-source, post-previous-study exploratory intervals. Neither nine entries, thousands of animals, nor millions of GPS steps provide N=9 independent biomes or a cross-biome significance test.

## Entire original-data source frame integrity and overlap

The 2026-10-19 Movebank catalog has 437 packages and 259 whose archived sensor metadata explicitly list GPS or GNSS. The 259 contain 161 literal scientific-name strings, not 161 independent eligible species. Only 198 of 259 pass BOTH metadata-reported >=10k positions and >=5 animals, which is triage priority rather than true admission.

**Source study-ID duplication is already PRESENT in the original metadata**: 254 distinct repository study-ID labels; 3 are recorded on >1 package each; 6 package records are on those duplicate IDs, while 2 GPS/GNSS packages lack any study ID. Four lack a scientific-name label. Data-package DOI keys are distinct, so deduplication solely by DOI would miss sharing of study IDs. Sharing a study ID does not by itself prove that animal tracking events overlap, and distinct IDs do not guarantee field-population independence. This supports the need for source-unit provenance reconciliation **before** global meta-regression, rather than treating all 259/437 packages as independent source populations.

## Scientific target and claim ceiling

This provides original-data support for **geographic heterogeneity of observed solar-relative movement bearings** and for caution that raw sunward alignment does NOT equal directional solar cue use. It does not establish that solar azimuth causally structures animal ecological niches.

Prospective main response should estimate geographically, taxonomically and ecologically replicated sun-relative travel strategies with a rigorous time/route/season counterfactual. Predictor frame must include site-month environmental gradients and movement corridor/landscape orientation, observation cadence and solar azimuth variation; report source admission coverage across ALL catalogued packages. No post-result subgroup hunting in these nine outcomes. Include all remaining source holds, negative and undefined results.

**Next independent observation stage:** add all four separately pre-registered Southern GPS source archives (Etosha elephant, Brazil tapir, Etosha jackal, Kruger elephant) under newly frozen Southern azimuth source contract, without making the northern findings a directional prior. Treat Etosha elephant and jackal as the same ecological landscape—not independent ecosystem replicates. Later sample geographically and taxonomically stratified eligible original GPS/GNSS archives beyond this convenience source subset.

Existing ODSP daylength/GPS speed, original temporal N2, and solar/clock predictive model routes are unchanged.
