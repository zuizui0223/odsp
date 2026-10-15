# Uljin: one shared crepuscular detection peak, contrasting nocturnal extension, and what pooled data cannot identify

**Date:** 2026-10-14 (Asia/Tokyo)  
**Scope:** Post-publication exploratory result from authentic, checksum-verified Supplement 3, not a new preregistered field observation.  
**Biological question:** Do four sympatric ungulates share an observed high-rate dawn/dusk window but differ in the extent of nighttime detections, and could the apparent difference be caused solely by observation or station composition?

## 1. Exact source and inclusion

Source: Jeon J-H & Lim A (2026), *Biodiversity Data Journal* 14:e191556, published Supplement 3 DOI https://doi.org/10.3897/BDJ.14.e191556.suppl3. The publisher-linked Zenodo release https://zenodo.org/records/21319408 contains `oo_1559451.zip`, independently attested MD5 `085afc8382ae5668edfa8ad74122a68e` and table `EA02_DielRate_Table_BySpecies.tsv`. The source-reading pipeline verifies the archive MD5, the exact 12 aggregate table rows, schema, all four species and all 4,623 event counts, and the published period-duration rate formulas. No physical camera station identifier, raw event timestamp, original NIE EcoBank Version 1.1 ZIP or original operation hours were read.

The three published zones are **daytime (sunrise to sunset)**, **civil crepuscular (dawn to sunrise plus sunset to dusk)** and **nighttime (civil dusk to civil dawn)**. This published **crepuscular** category is *outside* daytime and MUST NOT be conflated with the original ODSP PR #264 H1 **within-daylight edge** (first/last 25% of sunrise–sunset daylight). The authors' periods sum to 9288 calendar hours = 387×24 hours, not a demonstrated station×date independent ON-camera exposure denominator.

### Published pooled year-long detection counts and exposure-duration-scaled rates

| Species | Day n | Civil twilight n | Night n | Day detections/100 published period-hours | Twilight/100 h | Night/100 h |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Long-tailed goral | 1325 | 139 | 853 | 27.853 | **38.610** | 20.452 |
| Siberian roe deer | 463 | 73 | 272 | 9.733 | **20.277** | 6.522 |
| Water deer | 264 | 51 | 499 | 5.550 | **14.166** | 11.964 |
| Wild boar | 475 | 37 | 172 | 9.985 | **10.277** | 4.124 |

**Supported new pooled descriptive pattern:** All four species have their numerically largest detected-event intensity per published period hour during *civil twilight*; Water deer additionally extend numerically further into the post-twilight night than other species. But for **Wild boar**, the twilight rate is only **2.93%** above its day rate, and site-level uncertainty is absent—**do not** call this a confirmed twilight preference.

This is a description of **recorded events under published calendar-period normalization**, not evidence of equal station operating hours, equal physical movement availability or causal temporal segregation. The 30-minute event-independence rule does not make different records statistically independent animals or independent station replicates.

## 2. A three-part decomposition instead of the simplistic night/day binary

For two species A,B, let `R(A/B, z/y)` be their ratio of within-species detection count ratios `(n_Az/n_Ay)/(n_Bz/n_By)`. Because the source uses the same public period-duration denominator for each species, the time denominators cancel **exactly** in this cross-species ratio of period rate ratios. Therefore:

```text
R(A/B, night/day)
  = R(A/B, civil_twilight/day)
    × R(A/B, night/civil_twilight)
```

For **Water deer versus Wild boar** (largest absolute night/day comparison among all six available pairs):

| Comparison | Cross-species ratio | Ecological interpretation limit |
| --- | ---: | --- |
| Civil twilight/day | **2.480037×** | Relative recorded concentration in the externally-defined crepuscular window |
| Night/civil twilight | **2.104765×** | Relative recorded extension further into night |
| Night/day | **5.219895×** | Product of the two above, NOT a fivefold true activity or abundance difference |

Thus this observed pooled differentiation is not reducible to only a change at dawn/dusk: both the dawn/dusk-versus-day and the later-night-versus-dawn/dusk contrasts contribute. In log-ratio coordinates, 54.96% of the log night/day contrast comes from twilight/day and 45.04% from night/twilight, **an algebraic decomposition not attributable to independent causal drivers**.

For perspective, Water deer also have a higher night/crepuscular detected-period ratio than **Siberian roe deer** (species-comparison ratio **2.626**). Roe deer show high twilight/day detection but comparatively low night/twilight detection. This is a potential *two-axis temporal-niche structure* for future within-station study, not a confirmed niche mechanism.

## 3. How extreme must unmeasured *effective detector-q* differentiation be?

Let `R_obs=5.219895` be Water deer versus Wild boar's observed pooled night/day count-ratio contrast. **ONLY IF** the two species' events represent the same effective station/exposure population, and the only remaining observation distortion is the four positive effective detection multipliers `q_WN, q_WD, q_BN, q_BD`:

```text
R_obs = R_latent × B_q
B_q = (q_WN/q_WD)/(q_BN/q_BD).
```

If independent external calibration **were** to establish all four `q` between `q_min` and `q_max`, with `r=q_max/q_min`, then `1/r² ≤ B_q ≤ r²`. In this **hypothetical homogeneous, common-exposure model** the corrected contrast could lie between `R_obs/r²` and `R_obs×r²`. This is exact interval algebra conditional on the stated model. **No actual q, site-mix, real on-time or external calibration has been measured.**

| Hypothetical r = max(q)/min(q) | Lower possible latent ratio, if the model holds |
| --- | ---: |
| 1.20 | 3.625 |
| 1.50 | 2.320 |
| 2.00 | 1.305 |
| 2.25 | 1.031 |
| 2.30 | 0.987 |

The threshold for a possible corrected ratio of 1 is **sqrt(5.219895) = 2.284709**, under these strictly hypothetical conditions. **This does not establish the true activity difference even when r=1**, because the same-station/population assumption is itself unverified.

## 4. Constructive spatial-mixture alternative, EVEN if camera-q is perfect

The full 12-row table does not identify within-camera behavior. This can be made algebraically explicit without inventing empirical stations.

Define **two abstract groups** A and B, with **identical** within-group day/night detected-time distributions for **every** species: `P(night | A)=0.75` and `P(night | B)=0.15`. These probabilities are hypothetical, and dawn/dusk detections are excluded from this limited two-part demonstration. Let `w_species` represent the fraction of each species' **day+night detected events** contributed by hypothetical group A. Then

```text
P_pooled_species(night | day_or_night)
    = 0.75 * w_species + 0.15 * (1 - w_species)
w_species = [P_pooled_species(night) - 0.15] / 0.60.
```

Using ONLY the observed published day and night counts:

| Taxon | Observed pooled night fraction, excluding twilight | Hypothetical share of detected events from A |
| --- | ---: | ---: |
| Goral | 0.391644 | 0.402740 |
| Roe deer | 0.370068 | 0.366780 |
| Water deer | 0.653997 | 0.839996 |
| Wild boar | 0.265842 | 0.193071 |

All four mixing fractions lie strictly between zero and one and **exactly reproduce the observed pooled expected day/night fractions**, even though the species have **no within-group difference** in this mathematical counterexample. Fractional expected counts are allowed, so this is a genuine constructive identification argument, not a claim of exact integer station records. These hypothetical groups are **not** the actual UJ1/UJ2 study regions or any named camera site. The construction concerns ONLY the day+night two-way margin, not the entire three-zone table.

This shows a much deeper uncertainty than detector q alone: **perfect and equal camera detection cannot rule out pooled site-composition confounding**. The observations remain real; the causal/within-site explanation is not identified.

## 5. Ecological hypothesis after this audit

The strongest falsifiable question is now:

> At the SAME functioning physical camera and a fixed original matched-daylength pair, do Water deer and Wild boar retain different dusk-to-night versus daytime detection allocations *within each station*, and does their difference change between the original early-growing season and midsummer dates?

Distinguish competing alternatives before claiming mechanisms:

- If within-camera contrasts remain directionally consistent after independent hourly operation and detector calibration, that supports station-conditional detected-time differentiation (still not competition).
- If the pooled contrast vanishes in within-camera comparisons, site occupancy and camera placement may explain the aggregate.
- If station-conditional differentiation persists but does not change between the immutable 41 early-vs-midsummer photoperiod pairs, the supported biology is **stable temporal differentiation**, not seasonal temporal reassembly.
- A causal claim about human disturbance, heat, competition or environmental entrainment additionally requires relevant independent measurements and design.

Original 41 date-pair admission and protected original camera coordinates remain unchanged and **HOLD**; do not substitute the journal's civil twilight for PR #264's within-daylight edge.

## Reproducibility

- Published original journal summary: https://zenodo.org/records/21319408.
- Existing verified reader: `scripts/inspect_uljin_published_supp3_aggregate_v0.py`.
- Existing 4×3 genuine table validation: `scripts/run_uljin_published_supp3_daypart_signatures_v0.py`.
- This new post-source analysis contract: `ULJIN_PUBLISHED_SUPPL3_PHASE_IDENTIFIABILITY_V0_CONTRACT.json`.
- New reproducible all-six-pair analysis and model counterexample: `scripts/run_uljin_published_three_phase_identifiability_v0.py`.
- Tests: `tests/test_uljin_published_three_phase_identifiability_v0.py`.
- [Dedicated independently verified CI run 38565146617](https://github.com/zuizui0223/odsp/actions/runs/38565146617) tested the algebra and fail-closed source boundaries and **reloaded the genuine public Zenodo ZIP with the publisher's actual checksum**.
- Authentic original EcoBank 1.1 event/operation ZIP is still unavailable; tracked in https://github.com/zuizui0223/odsp/issues/265.

**Evidence tier:** verified **observed aggregate distribution**, **conditional** measurement-bias sensitivity and **mathematical** non-identifiability example. No new biological p-value, latent animal activity or mechanistic claim.
