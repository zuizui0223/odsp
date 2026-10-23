# Ecology-first manuscript protocol: solar phase, seasonal path and mammalian activity
**Version 0, 2026-10-15 — hypothesis- and source-readiness only. Issue #266.**

## One-sentence scientific thesis

At the **same astronomical daylength**, mammals may allocate their camera-detected encounters differently between the rising and falling photoperiod branches, and the variation in this *seasonal loop* may be predictable from thermal and phenological lag **across genuinely independent landscapes**, rather than from the astronomical time transformation itself.

This is a TESTABLE QUESTION, not an established ecological finding. Avoid implying biological *memory*, circadian entrainment, photoperiod causation, animal competition or ambient-temperature causation on purely observational evidence. Explicitly retain positive, zero, reversed and unavailable results.

## Novelty relative to existing ecology

- Astronomical sunrise/sunset normalisation and mammalian seasonal activity differences are existing methods and results. Northern Japanese mammals show species-specific seasonal activity peaks (Ikeda et al. 2016, https://doi.org/10.1371/journal.pone.0163602).
- Kays et al. 2020 (https://doi.org/10.1111/2041-210X.13370) studied 41 camera-trap datasets but **seasonality at only FIVE sites** with >=1-year design: Montana, North Carolina, China, Peru and Panama. The original seasonality outcome concerned occupancy/rate, not same-daylength diel allocation. Many temperate and tropical species vary by season; a new paper cannot claim to discover seasonality.
- Distinct ecological innovation: (i) equal photoperiod on opposite seasonal branches, (ii) distinguish within-day **core→daylight-edge** from **daylight→night** redistribution, (iii) test species/environment response rather than a universal direction, and (iv) truly held-out landscape-level prediction (not simply repeated camera images).
- Existing ODSP Rhode Island exploratory result: at 43 held-out physical sites, 19,916 scored events, pooled solar−clock log gain winter +0.02745846 / summer −0.03257429 (PR #225); when both model families get season information, solar×season−clock×season −0.03865692 / −0.03818343 nats (PRs #228–#229). The solar-pushforward predictor has a restricted attainable simplex relative to the direct clock histogram. **This is model performance under unequal geometry; it does NOT identify a seasonal circadian preference or sunlight irrelevance.** Preserve original v0/v1/v2 results and exploratory status.
- Uljin original matched-daylight 41 pairs (PR #264) are in **source HOLD** (issue #265), with no actual matched animal results. Published 4×3 yearwide summary and Bukhansan undated camera×hour table are separate, not confirmations.

## Pre-specified hypothesis hierarchy

**H0 — photoperiod-only activity allocation**: with daylength and observed solar phase matched, a mammal's *detected encounter rate ratio* of core / edge and day / night is stable between branches after measured camera effort.

**H1 — daylight-edge redistribution**: on falling-branch dates the ratio of early+late daylight-edge encounter intensity to central daylight-core encounter intensity increases, especially in places with independently measured warmer daytime thermal conditions. *Counterevidence:* zero or opposite point estimate with adequate support, or non-transfer to held-out areas.

**H2 — night redistribution**: falling-branch night relative to all daylight detection intensity increases, independently of whether the daylight-edge ratio changes. *Counterevidence:* preserved day/night proportion despite H1 shifts.

**H3 — taxa and environment**: cross-taxon branch effects vary with thermal exposure, body-size/activity guild and vegetation/rainfall lags, rather than one shared sign. Predictive patterns must be specified before unseen region outcomes. A site-period climate correlation is not a causal process identification.

**H4 — cross-landscape transfer**: a frozen effect model calibrated outside an evaluation landscape predicts the **held-out regional direction and effect magnitude** with useful proper-score/interval calibration. The number of independent *landscapes*, not photographs or cameras, determines this level of generality.

A near-equatorial wet/dry comparison tests environment-only seasonal organization under small changes in daylength; it must be a **separate estimand**, not mislabeled as a replicate of strong temperate photoperiod hysteresis.

## Physical definitions and expected observation outcome

For each source-verified civil date, site latitude/longitude (public generalized location if applicable), source time zone and sunrise/sunset:
- **DAYLIGHT CORE**: middle 50% of sunrise-to-sunset daylight.
- **DAYLIGHT EDGE**: first + last quarter of sunrise-to-sunset daylight (combined length = 50% of daylight).
- **NIGHT**: outside sunrise-to-sunset daylight. Civil twilight outside sunrise/sunset lies here, not in daylight edge.
- For the night contrast, combine core + edge to DAYLIGHT. No per-date redistribution of event UTC date is allowed without an explicit night-to-date assignment.
- Event counts are divided by **actual physical camera on-hours** for that station/date/zone; exposure must not be inferred from the first/last animal detections or from the astronomical period length alone.

For species s, independent site i and matched pair j, use positive exposure E(i,j,b,z) and event count Y(i,j,b,z), including observed zero events. Define detected encounter intensity r = Y/E descriptively. The preselected contrasts are:

`H_edge = log[(r_falling,edge/r_falling,core) / (r_rising,edge/r_rising,core)]`

`H_night = log[(r_falling,night/r_falling,daylight) / (r_rising,night/r_rising,daylight)]`

Zero counts do **not** justify deleting a site/zone; estimate the contrasts via a preregistered site-/pair-conditioned count likelihood and explicit zero support rather than adding opportunistic pseudo-counts. Report interval widths, coverage and support; with unidentified on-hour effort, do not compute a detected-rate H.

**An observational loop H≠0 does not establish genuine biological memory:** warmer weather, vegetation, reproduction, food availability and humans also differ between same-daylength dates.

## Source-admission first, before biological outcomes

The machine-readable candidate matrix is `research/solar_seasonal_hysteresis_source_feasibility_v0.json`. No candidate is declared Tier-A result-ready at this revision.

### Tier A: actual same-station, same-daylength counter-season comparisons
Require ORIGINAL timestamped animal event rows (no reconstruction from aggregate plots), station ID, documented time-zone/clock correction, known operations with downtime and device settings, BOTH rising/falling branches sampled at the SAME physical station, availability of independently observed zeros and systematic date matching. Selection of stations must depend on operation feasibility, **not detection counts**. Independent detector probability q is required before claims about latent animal activity rather than camera observations.

1. **Kays seasonal datasets**, 5 sites including **Montana and North Carolina** as top priority. The whole 41-study compilation is NOT 41 independent seasonal replications. Dryad `seasonal.zip` exists (source DOI 10.5061/dryad.p8cz8w9m2), but its member schema, actual event timestamps and camera uptime remain unverified here. Panama moved cameras every 7–12 days among positions *within* survey blocks: stationary-camera pairing may be impossible there even with >=1 year study coverage. Peru unequal sampling effort needs verified exposure denominators. Climate-specific published summer/winter vs wet/dry labels must not replace actual matched solar date comparisons.
2. **Uljin**: frozen original 41 date-pairs and four taxa remain blocked on authentic EcoBank Version 1.1 ZIP and source-independent camera operation log (#265). Rising 2022 May 1–June 10 versus falling 2022 July 1–Aug 31 is early growing season vs midsummer, not spring vs autumn; keep frozen date roster intact.

### Tier B: informative but different environmental seasonal contrasts
- **Serengeti**, public independent temporal organization across camera sites. Published `search_effort.csv` uses first/last *valid camera images* on each memory card, not an independently authenticated hourly camera ON/OFF chronology. A tropical dry/wet-season reallocation is a useful biological comparator conditional on this observation limitation; it is NOT source-certified photo-to-latent-animal activity.
- **Freiburg 2026**, 24 camera locations, ten mammal taxa; authors publish per-event timestamp and SeasonYear and state cameras operated continuously, but original site×date uptime and stable pair support remain unverified. Urban impervious-surface gradient is mechanistically interesting but confounded with site-level camera placement; evaluate source before classifying A or B.
- **Rhode Island**, winter/summer surveys with established exploratory predictive contrast but no authenticated match of rising/falling photoperiod at site×year and no independently calibrated detector q.

### Tier C: spatial transfer within falling photoperiod only
- **Snapshot USA** runs Aug–Dec; **Snapshot Japan 2023** mainly Sep–Oct and Aug–Dec overall. Their huge spatial coverage is NOT extra rising-vs-falling branch replication.
- New 2026 NEON standardized forest-subproject dataset covers *one ~month-long early-growing-season deployment per subproject*, not annual repeated sampling.

### Literature background, not outcome-bearing replication
- **Ikeda et al. 2016 Hokkaido:** 2012–2014 (30 cameras, 8 focal mammal species, 13,279 recorded events), strong seasonality but original event timestamp/camera-operation level has not been independently retrieved. The paper reports all relevant data within the publication; this is not enough to claim our newly matched dates.
- **Ya Ha Tinda elk Movebank**, GPS telemetry is a potentially complementary measurement source; duty cycles changed and later collars sampled about one location per 13 hours. GPS-fix frequency does not directly measure animal activity. Only if source-specific duty cycle and movement metrics allow should any corroboration proceed, as an explicitly different estimand.

## Minimal viable design and test sequence

1. **Inspect publication → source bytes → operation schema → time zone → eligible stations**, recording version, license, original-hash provenance and literal schema. Avoid sensitive GPS disclosure. No wildlife times should be interpreted before the observation/effort gate.
2. Freeze source-admitted site×year roster and same-daylength date matcher (site-specific astronomical calculations). Do NOT choose matching days based on biological effect; report matching tolerance and number of retained pairs. Keep original Uljin 41 pairs unchanged.
3. Fit a zero-retaining count model with station/pair dependence, fixed physical exposure offset and two predeclared branch×zone interactions. Check stability to station-level omission and predeclared physical effort uncertainty; never treat thousands of repeated events as independent animals.
4. If enough external covariates are independently sourced, regress site/species H estimates on **T_falling−T_rising**, independent vegetation greenness/rainfall measures and biologically justified guild features. Temperatures/NDVI must be matched to exactly the animal pair-date windows, not generic seasonal labels. Avoid causal language without interventions/instruments.
5. HOLD at least one **separate study landscape** as never-used external ecological evaluation. Report regional direction/magnitude prediction, proper scoring, random-effect heterogeneity and the **prediction interval for a new independent region**. Unseen sites inside the same region are not equivalent to an unseen region.
6. Keep failed species, signs reversing, q-ambiguous outcomes, and ineligible regions in a labeled evidence ledger. No post-hoc rescue by changing date pairs, bin widths, species filters or camera grouping.

### Null/negative controls

- Purely invariant solar-phase simulated observations with date-specific solar-time Jacobian must not create false seasonal claims.
- Wrong-season astronomy and random-date placebo should not yield stronger out-of-region model performance.
- Stable camera-specific but differing seasonal detection q and season-dependent station composition are separate known negative worlds; favorable score signs alone cannot resolve these nuisances.
- No-event and partial-operation cells must be explicitly retained/rejected based on source support, never filled from total camera nights.

## Draft Figure/Results order — not yet numerical evidence

**Fig 1** Matched increasing/falling date geometry, observed (not schematic) temperature and NDVI branch lag.
**Fig 2** All eligible species×region H_edge and H_night with original support and intervals; zeros and sign reversals visible.
**Fig 3** Environmental lag meta-regression and held-out landscape predicted-versus-observed effect sizes.
**Fig 4** Observation robustness to camera on-hours, q uncertainty and geometry/placebo controls.

**CURRENT REAL RESULTS FOR THIS NEW PAPER: NONE.** Existing RI scores are exploratory source findings. Kays has published multi-site seasonality but NOT a source-verified equal-daylength loop result. Uljin is source-held. Neither a test plan nor a draft can be represented as a confirmed new mammal seasonal finding.

## Sources

- Kays et al. (2020), https://doi.org/10.1111/2041-210X.13370 ; archive https://doi.org/10.5061/dryad.p8cz8w9m2
- Ikeda et al. (2016), https://doi.org/10.1371/journal.pone.0163602
- Jeon and Lim (2026), https://doi.org/10.3897/BDJ.14.e191556 ; official archive DOI https://doi.org/10.22756/ETC.20260000001022
- Moesch et al. (2026), https://doi.org/10.5061/dryad.73n5tb3bz
- Snapshot Serengeti, https://doi.org/10.5061/dryad.5pt92
- Snapshot Japan 2023, https://doi.org/10.3897/BDJ.13.e141168
- Snapshot USA 2019–2023, https://doi.org/10.5061/dryad.k0p2ngfhn
- US forest NEON 2026, https://doi.org/10.5281/zenodo.20826511
- Ya Ha Tinda elk Movebank, https://doi.org/10.5441/001/1.5g4h5t6c
- Prior ODSP frozen ecology PRs #221, #225, #227–#229, #233–#238, #264; #265 source gate remains independent.

## Editorial scope and stopping rule

An ecology-driven manuscript earns a broad-generalization title only if **independent admissible region-level same-daylength branch effects and external predictions** have genuinely been obtained. If they cannot, narrow to (a) a regional matched-daylength natural experiment when eligible, (b) a cross-biome **descriptive** comparison with explicitly non-equivalent seasonal estimands, or (c) a methodological caveat paper—never claim a universal seasonal hysteresis law from one region or reconfigured camera-probability simulations.
