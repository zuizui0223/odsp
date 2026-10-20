# Cross-taxon biological generality — current state

## Latest boundary: independent stork cohorts do not show uniform vertical-shape individuality

The original Rotics 2013 migration-specific 50km test (Movebank study 150450794) showed an age/date-block null-relative gain +0.194850 nats/event (25 birds, 111 bird-days, 6,951 scored fixes, p_upper=0.001; archived run 39409175819). A deterministic rerun (39413456822) exactly reproduced all original JSON and CSV evidence members byte-for-byte.

A **different 2014 white-stork study** (Flack / Weinzierl, Movebank study 332044860, DOI 10.5441/001/1.bj96m274) was admitted before opening heights: 60 source reference birds (all labelled nestling), 59 birds with selected flight-speed GPS records, 50km comparable source roster **11 birds / 33 bird-days / 2,040 bins**, while 5km has **zero**; source preheight run [39415189033](https://github.com/zuizui0223/odsp/actions/runs/39415189033).

Its numerically identical, separately preregistered 50km D1-balanced centered-height-shape / 999 exact-date-stage session exchangeability test returned **NOT SUPPORTED** [run 39416255916](https://github.com/zuizui0223/odsp/actions/runs/39416255916): 11 birds, 33 bird-days, 2,039 scored GPS fixes, observed gain **−0.26989281**, null mean **−0.13523669**, observed-minus-null **−0.13465612**, all 999 null valid, one-sided p_upper **0.998**. Only **2 of 11** individual raw scores were positive. Native altitude completeness 58,959/58,971 = 99.980%.

Source reference animal IDs: 2013 122 and 2014 60 with **zero exact animal-ID overlap**. One GPS tag ID occurs in both full source reference archives, used on distinct birds in 2013/14, and is not among the 2014 final 11 birds. The two source populations are independently tagged at the literal tracked-bird ID level, but this is not a controlled experiment of cohort biology.

**Interpretation:** The original positive evidence in a mixed-age eastern-Germany migration cohort is not uniformly reproduced in an independent all-nestling southwestern-Germany tracking cohort under the same 50km test. Positive p=.001 vs p=.998 is not a formal significant cohort-by-context interaction. The latter is an unsupported positive hypothesis, **not proof of biological zero**: n=11 and 33 observed sessions, cohort/stage/site/tag differences, unadjusted topography and identification-via-tag limitations remain. Both null randomizations change the eligible-bird denominator (2013 observed25 vs null36–53, 2014 observed11 vs null13–28), limiting exchangeability interpretation.

**Ecological question newly sharpened:** What ecological conditions make individual vertical-use shape recur across days? Stable vs changing flight opportunities, wind and thermal uplift, juvenile experience, behavioural mode and geographic migration stage are candidates, not supported causal explanations. Gull 2016/2017 provides independent *regional wind predictive context* but does not prove individual-specific wind response. Do not reopen either stork archive with outcome-tuned alternative spatial grains to rescue the 2014 result.

Durable evidence:
- [Two-cohort biological synthesis](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/WHITE_STORK_2013_2014_CROSS_COHORT_BIOLOGICAL_SYNTHESIS_V1.md)
- [2013 source result receipt](https://github.com/zuizui0223/odsp/blob/prospective/stork2013-50km-vertical-identity-20261020/prospective/WHITE_STORK_2013_50KM_RESULT_EVIDENCE_RECEIPT_V1.json)
- [2014 source result receipt](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/FLACK_STORK_2014_50KM_RESULT_EVIDENCE_RECEIPT_V1.json)
- [Cross-guild claim map](https://github.com/zuizui0223/odsp/blob/prospective/biological-generality-20261019/prospective/CROSS_GUILD_VERTICAL_PROBABILITY_SYNTHESIS_V1.md)

---

## Latest evidence: wind-conditioned vertical shape recurs in two breeding years

The cross-taxon biological-generalization lane advanced from the previous 2021 DELTATRACK individual identity experiment to **two fixed yearly tests of environmental context**, in the distinct `LBBG_ZEEBRUGGE` Movebank tracking study (one species, `Larus fuscus`). Source 2016 and 2017 native GPS, CERRA regional 100m winds at four archival colony centers, exact-identifier site join, and all altitude-blind support screens were independently anchored before opening each year's height outcomes.

| Breeding year | Original altitude-blind wind candidates | Scored birds | Bird-days | GPS fixes | Wind-conditioned vs pooled raw gain | Mean null | Null-calibrated excess | p-upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 41 | 39 | 744 | 31,002 | +0.0110375 | −0.0234812 | **+0.0345187** | **0.001** |
| 2017 | 25 | 24 | 422 | 18,348 | +0.0217185 | −0.0210897 | **+0.0428082** | **0.001** |

Both years used the same frozen numerical algorithm: within-individual, same 5-km horizontal cell, different-day ten-bin height-shape distributions centered by each day's median; compare conditional same-regional-wind group vs wind-pooled reference on identical held-out GPS fixes. Within-grid and month whole-wind-day permutations (999 each) yielded **999/999 valid** and 0 null observations at least as high. Count bird-level, not GPS fixes, as biological replication; site/date null exchangeability remains observational.

The 39 and 24 birds share **11 exact animal IDs**. Unique union **52 birds** across both years. Individual-level raw gain is positive in 27/39 (2016) and 18/24 (2017); among the 11 reappearing birds, 7 have positive gains in both years. The year-specific raw gain rank of an individual is **not established** as stable across years (the shared 11 show only weak descriptive alignment). No combined or meta-analytic p value is calculated because same study sites, tags and partly the same birds.

**Biological statement:** This provides one species / one Movebank study / two consecutive years of evidence that the shape of individual-level vertical flight-use probabilities is **environment-context dependent rather than fully fixed by identity alone**. It does not establish causal wind-driven flight decisions; source wind is a regional 100m site measure, not actual 3D air flow at each GPS location. Speed-based filtering does not validate flapping or soaring, and tag-specific non-additive altitude noise remains unresolved. Penguin colony-count concentration in MINA remains a separate population-level endpoint.

**Auditable evidence:**
- [2016 biological result](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_BIOLOGICAL_RESULT_V1.md) — run [39401802547](https://github.com/zuizui0223/odsp/actions/runs/39401802547).
- [2017 temporal validation receipt](https://github.com/zuizui0223/odsp/blob/prospective/zeebrugge-2017-temporal-wind-test-20261020/prospective/ZEEBRUGGE_2017_CERRA_WIND_RESULT_RECEIPT_V1.json) — preregistered preheight run [39403638754](https://github.com/zuizui0223/odsp/actions/runs/39403638754), full test [39404195393](https://github.com/zuizui0223/odsp/actions/runs/39404195393).
- [Two-year ecological synthesis](https://github.com/zuizui0223/odsp/blob/prospective/zeebrugge-2017-temporal-wind-test-20261020/prospective/ZEEBRUGGE_2016_2017_WIND_HEIGHT_BIOLOGICAL_SYNTHESIS_V1.md).

**Next unique goal:** move beyond this single species/network. Prefer an independent taxon/study with externally derived flight/dive behavior and/or device-calibrated vertical state, prespecifying the identical conditional-probability transfer question. Do not continue source/year mining to amplify p values.

---

## New independent ecological context result: 2016 regional wind and height shape

A new, separately checksum-pinned `LBBG_ZEEBRUGGE` GPS source (2016) was joined to independently obtained 100m CERRA wind at four source-defined colony centers **before inspecting GPS heights**. Outcome-blind screening run 39391834277 passed 41 candidate birds. The frozen within-bird, same-5km-cell, held-out-day wind-context analysis run [39401802547](https://github.com/zuizui0223/odsp/actions/runs/39401802547) completed successfully.

- **Larus fuscus: 39 qualifying individuals, 744 bird-days, 31,002 target flight-height fixes.** Altitude quality 133,497/133,693 = 99.853%.
- Conditional same-individual/same-cell wind-regime shape vs that individual's wind-pooled profile: observed gain +0.01103752 nats/fix.
- Wind-regime date permutations within CERRA grid and month (999/999 valid): null mean −0.02348120, **observed minus null +0.03451872**, one-sided Monte Carlo **p=0.001**.
- Bird-level raw gain is positive in 27/39 birds. A **post-outcome descriptive** site join finds mean gain positive in all four colony groups (n=3, 8, 7, 21), but site-specific effects are not separate independent tests.
- Core ecological contribution: **A particular individual's vertical-use probability shape carries additional environmental context**; it need not be a single invariant shape. The wind regimen used here is regional colony-site weather, not personally experienced flight air-flow.
- Limits: observational association, no causal wind attribution, same-bird device error, within-cell micro-paths, accelerometer-defined flight mode missing for this archive, site-month/date exchangeability assumption. This is a new individual shape estimand, distinct from published studies of wind-linked habitat selection or flapping/soaring rates.

Auditable result and biological interpretation:
- [Wind-height outcome report](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_BIOLOGICAL_RESULT_V1.md).
- [Machine-readable result receipt](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_RESULT_RECEIPT_V1.json).
- [Frozen model](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_TEST_FREEZE_V1.json).

**Next independent-horizon question:** does this wind-context shape information transfer to the next consecutive archive year (2017) under a new year-level freeze, while explicitly accounting for shared individual tags and site/weather correlation? Do not try to improve 2016 p values by searching alternative weather grids, bin cutoffs or seasons.

---

## Latest completed next-step: matched flight–stationary individual comparison

A further **post-outcome exploratory** test has now linked the exact same birds' frozen flight (5-km) and low-speed 100-m individual ID score gains. It did **not** alter either original endpoint or re-run a new independent taxon replication.

- [Matched context workflow 39383667556](https://github.com/zuizui0223/odsp/actions/runs/39383667556): completed successfully; archived evidence artifact 12247305470 (ZIP SHA256 8f304f4709f9ae27ae49af5dbfbbc2c917a914efd7db622b9fee6780d76381bf).
- **33 birds** overlap the originally eligible flight (40) and stationary (46) sets. In these 33, flight raw bird scores are positive for 30 and stationary raw bird scores for 20.
- Rank concordance of bird-level raw gains across contexts is **weak**: Spearman rho **+0.10227**; 9,999 matched-bird random permutations, two-sided p **0.5672**; bird-level bootstrap 95% interval **−0.2641 to +0.4256**. An independent scipy calculation agrees (rho=0.10227).
- Original stationary 46 birds/590 bird-days/51,960 fixes/mean score +0.008155 was reproduced to machine precision; original flight numerical model/results were imported by pinned SHA256 without refitting. New synthetic tests passed.
- Raw gain levels are **not directly biologically comparable across 5-km flight and 100-m slow-motion contexts**. The two contexts' effects have descriptive associations with their own number of scored bird days (flight rho≈0.331, stationary rho≈0.433), so effort-related heterogeneity remains.
- **Interpretation:** a single shared bird/tag-related *ranked* propensity across both contexts has no positive empirical support here, but the broad confidence interval and context-dependent measurement errors prohibit claiming that the flight signal is free of instrument error. Both contexts separately retain ID-associated distributions; the 2021 bird-to-tag aliasing is still perfect.
- Cross-context correlation is exploratory and cannot identify the biological or instrumental fraction; not a second external replication, not a universal flying-animal law, and not directly comparable to MINA's penguin breeding-site concentration.

Durable report: [Flight–stationary matched synthesis](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-matched-context-20261020/prospective/DELTATRACK_2021_FLIGHT_STATIONARY_SYNTHESIS_V1.md).

Machine-readable receipt: [33-bird result ledger](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-matched-context-20261020/prospective/DELTATRACK_2021_MATCHED_CONTEXT_RESULT_RECEIPT_V1.json).

**Next scientific boundary:** An independent, non-constant vertical instrument or actual within-bird tag switch (or validated behavioural states/known perch microtopography) is required. Repeatedly reshaping this already opened source would not solve the causal identity problem.

---

Updated 2026-10-20. Latest completed step: a prospectively fixed external tracking-study test in DELTATRACK 2021. Prior MEDGULL exploratory results and unavailable original endpoints remain unchanged.

## Latest external-study result

Branch: `prospective/deltatrack-2021-identity-20261020`.

Using the unchanged MEDGULL D1 balanced estimator, **Larus fuscus: 40 individuals, 899 bird-days and 66,811 scored five-minute flight records** retain individual-label-associated cross-day centered altitude shape beyond exact-date session relabeling.

- Observed mean log-score gain: +0.0456739261.
- Null mean: -0.0278862764.
- Observed minus null: +0.0735602025 nats/record.
- 999/999 valid permutations; none at least as large as observed.
- One-sided Monte Carlo p=0.001; Holm p=0.002 across the TWO prespecified species.
- 37/40 positive individual point scores, not 37 significant individual tests.
- Null eligible birds 49–59 versus observed 40; full support re-estimation and this difference are retained.

Larus argentatus: 14 individuals had valid flight heights but only 1 individual / 7 bird-days / 449 records passed the full comparison support. Its endpoint is **unavailable**, not a negative biological result. It stays in the multiplicity family with placeholder p=1; no biological p-value is reported.

The dataset is an external study relative to MEDGULL, not an independent study for each DELTATRACK year. The two species share site/instrument context. The supported external result is one species, not two successful independent species.

## Frozen design and execution

Source DOI 10.5281/zenodo.22102508; DELTATRACK-gps-2021.csv.gz; MD5 1a3145234cccd1a48b280b0fb485d679. Target two-species raw count 3,637,037; valid thinned height count 216,407.

Plan saved before this 2021 height analysis: commit abd6416013cf8aedf0acff9b91782964ce947228. Successful run 39375585874, execution commit 089194d368ca43554d3ea681d008d01e5ce51008, artifact 12242743398.

First attempt failed at Numba cache loading after parsing heights but before emitting an identity statistic. The error was reproduced with synthetic data; only the production cache directory was separated. No year, model, threshold, seed, source or numerical kernel changed.

Durable report and receipt on the external-test branch:
- prospective/DELTATRACK_2021_IDENTITY_REPORT_V1.md
- prospective/DELTATRACK_2021_IDENTITY_RECEIPT_V1.json
- prospective/DELTATRACK_2021_IDENTITY_PLAN_V1.md
- prospective/DELTATRACK_2021_RUNTIME_RECOVERY_V1.json
- prospective/deltatrack_2021_identity.py
- prospective/test_deltatrack_2021_identity.py

The complete result JSON, all 999 null draws, all per-bird comparisons and executable code are saved in the verified run artifact and the conversation reproducibility package.

## Interpretation and remaining scientific boundary

Evidence now extends from the post-outcome MEDGULL discovery to a pre-specified test in a different gull study/species. The safest claim concerns **individual-label-associated vertical-use shape**, not biological personality or adaptive specialization free from instrumentation.

Tag-specific non-additive altitude errors, effort, unobserved behavioral mixtures, within-cell routes and the substantive exact-date exchangeability assumption remain limitations. Day medians use the heldout session itself; this is shape matching, not online absolute-height prediction. Do not compare raw calibrated-score magnitudes as directly comparable biological strengths across datasets.

No inference of resource partitioning, central-place causation or universal mammal–bird equivalence. MINA penguin breeding-component concentration is a different response variable; do not combine the two into one demonstrated law.

Next scientific boundary: measurement/context attribution and extension beyond a narrow colonial-flying comparison. Do not continue changing thresholds on already-viewed MEDGULL or treat the excluded L. argentatus panel as a biological negative.

## Preserved MEDGULL sensitivity

Branch sensitivity/medgull-donor-days-20261020. MEDGULL 2022 I. melanocephalus: 11 birds, 258 bird-days, 17,054 records under D1. D1 pooled observed -0.0296285 vs null -0.0945509; D1 balanced +0.0362684 vs null -0.0167478. Both Holm p=0.002 across those two exploratory comparisons. This remains post-outcome sensitivity, not an independent confirmation. Balanced uses different smoothing level as well as weighting.

Original D50 pooled reproduced: 9 birds, 241 days, 15,904 records, gain -0.014494591842618162. Its original minimum-10 primary stays closed as unavailable.

## Preserved structural diagnosis

MEDGULL 13 -> 11 after correcting the individual/cell Counter key; 11 -> 11 after same-date exclusion; 11 -> 9 after removing short donor days. Earlier attribution solely to same-date exclusion was wrong.

DELTATRACK 2020 stays below its original minimum-10 rule: L. argentatus 6, L. fuscus 9. Its code did not have the Counter-key defect. Schiermonnikoog 2018 had 6 correct shared-cell candidates, 4 after short-donor-day removal. These are support findings, not ecological negatives.

## Verification closeout

New and reused module tests: 15 passed, 1 optional source integration test skipped. Independent dictionary reference agrees in 96 irregular synthetic cases; max score difference 6.67e-16. Saved real-data individual aggregates, full null means/tail counts/p values and Holm adjustment rechecked independently; artifact file hashes verified.

Full default repository suite rerun in 39374955129: 1,514 passed, 2 failed, 1 skipped, 0 errors. The two unresolved historical failures are test_final_receipt_rebuilds_manuscript_and_anonymous_bundle and test_closed_empirical_workflows_are_path_filtered. They had previously been reproduced on the unchanged parent. Scientific job success does not mean the entire repository suite is green.


## 2026-10-20 measurement attribution and low-speed negative control (new)

Post-outcome diagnostic branch: [diagnostic/delta2021-device-context-20261020](https://github.com/zuizui0223/odsp/tree/diagnostic/delta2021-device-context-20261020). **The frozen DELTATRACK 2021 flying-height primary test remains unchanged.**

On the exact same 2021 GPS source, the 2021 flight panels have 64 L. fuscus birds/64 unique tags and 14 L. argentatus birds/14 tags, with zero within-year same-bird cross-tag replication. All paired `bar:barometric-height` values are constant zero (189,598 GPS-valid L. fuscus events; 26,809 L. argentatus), preventing an independent altitude-channel check. GPS HDOP is completely reported, median 1.2, but measures horizontal precision and cannot remove tag-specific vertical-error differences. Device-vs-animal causation is thus structurally unidentified.

A stationary/very-low-speed (0–0.5 m/s) GPS negative control was frozen after the flying outcome, with x-y modal 100 m cells, identical centered-altitude bins, unchanged balanced donor kernel and 999 date-matched session-label permutations. [Run 39380619623](https://github.com/zuizui0223/odsp/actions/runs/39380619623) completed.

- **Larus fuscus:** 46 eligible birds, 590 bird-days, 51,960 scored GPS events. Observed matched-vs-other centered shape score +0.008155; null mean -0.025646; excess **+0.033801 nats/record**; 999/999 valid draws, 0 exceedances, Holm p=0.002 across the two species.
- **Larus argentatus:** 8 eligible birds at final >=50 scored-bin/day criterion, below min 10. Remains **unavailable**, no null p. Descriptive score +0.01790 is not inferential.
- 63/12 birds had met an earlier less demanding 20-bin/day structural same-cell screen; this does not override the later 50-bin evaluation-day criterion.

**Biological implication:** The individually associated GPS-height distribution shape signal is detectable in low-speed records as well as flying records. Therefore, the positive flying result alone cannot be interpreted as a *flight-specific* individual strategy. Near-stationary signals could arise from tag-dependent error, bird-specific perches/nest microtopography, or both. The negative control **does not prove tag artifact**; the two context effect magnitudes are not directly comparable because sampling, states and conditioning differ. No new bat or penguin claim follows.

Durable receipts:
- [Device QC](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/DELTATRACK_2021_DEVICE_QC_RECEIPT_V1.json)
- [Stationary control](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/DELTATRACK_2021_STATIONARY_NEGATIVE_CONTROL_RECEIPT_V1.json)
- [Cross-project ecological generality boundary](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/ODSP_DESCENDANTS_BIOLOGICAL_GENERALITY_BOUNDARY_V1.md)

Next unique identification axis: same-bird different-device tracking or an actually variable independent altitude sensor, plus properly controlled within-bird movement-state/micro-perch data. Repeated mining of the same bird-tag observations cannot by itself estimate the biological versus device-origin fractions.
