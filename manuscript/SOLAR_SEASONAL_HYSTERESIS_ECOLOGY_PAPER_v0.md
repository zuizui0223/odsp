# Equal daylight, different animal time?
## Testing seasonal asymmetry in mammalian diel activity across landscapes

**Status:** Ecology manuscript v0 — Introduction and Analysis Plan, **NO NEW EMPIRICAL RESULTS**  
**Date:** 2026-10-15  
**Companion evidence:** [ecological protocol](../docs/solar_seasonal_hysteresis_ecology_paper_protocol_20261015.md) | [machine-readable source gates](../research/solar_seasonal_hysteresis_source_feasibility_v0.json) | [issue #266](https://github.com/zuizui0223/odsp/issues/266).

### Intended conceptual advance

Many mammals reallocate activity within the 24-hour cycle across seasons. Sunrise and sunset define an obvious periodic forcing, but the rest of an organism's seasonal environment—temperature, vegetation, reproductive state, resource supply and human exposure—does not necessarily follow daylength instantaneously. The sun can therefore occupy nearly the same astronomical state on two separate dates while the terrestrial ecological conditions differ.

This suggests a natural counterfactual question: **If daylength is held almost constant in the same landscape, does a given species use the central daylight hours, dawn/dusk-adjacent daylight and night in the same proportions on the increasing and decreasing photoperiod branches?**

We refer to a branch contrast at matched photoperiod as **observational seasonal asymmetry** (or an observational loop). This wording deliberately does not presume that individual animals encode or remember the direction of the annual light cycle. A stronger physiological photoperiod hysteresis mechanism would require experimental or otherwise independent evidence.

### Introduction (working draft)

Sunrise and sunset organize animal activity across the world, but time-of-day niches are not mechanically fixed to solar geometry. Species differ in whether they are active during the day, night or twilight, and changes in these distributions can alter encounter rates, resource access and patterns of potential interaction. Importantly, the observation of temporal shifts does not on its own identify competition: weather, food supply, habitat selection and detection processes also affect when wildlife cameras record animals.

Classical day-night classification poses a second problem. The astronomical duration of daylight varies across seasons and latitudes. A species with invariant behavior relative to the sun can appear to change its clock-time distribution, particularly near a fixed clock-bin boundary. Solar-time standardization partly addresses this geometrical discrepancy, but the comparison between one solar-transformed model and one direct civil-clock model is not necessarily fair if their attainable probability distributions differ. Solar phase is a useful *coordinate system*, not itself evidence of a causal zeitgeber.

Existing ecological evidence already documents strong seasonal differences in camera-trap encounter rates and in diel activity. For instance, Ikeda and colleagues (2016) described season-dependent activity peaks among mammals in Hokkaido, whereas Kays and colleagues (2020) found seasonality in occupancy or detection rates in temperate and tropical study sites. These studies provide a biological starting point but did not establish a cross-landscape law of within-species diel redistribution **at fixed photoperiod on both seasonal branches**.

We hypothesize that observed diel allocation contains information about seasonal ecological context beyond instantaneous astronomical daylength. We distinguish two biologically different possible responses: (i) a shift from midday-centered to dawn/dusk-adjacent daylight use, consistent with—but not proving—daylight thermal refuge, and (ii) a shift from all daylight to the night, potentially reflecting broader heat, resource or disturbance constraints. Different taxa need not respond in the same direction; the more general question is whether response heterogeneity can be predicted from environmental differences at matched daylength.

Testing this hypothesis requires a stricter unit of ecological replication than photographs. Events must be dated and linked to an identified physical site whose real camera operation is known at the relevant time of day, and rising and falling branch observations must be available without post hoc selection on sightings. Variation across cameras in one study region tests local reproducibility; independently sampled regions are necessary to test ecological generality.

We therefore separate source-admissibility checks from a predeclared biological analysis, and require new-region predictions for the strongest conclusions. Failure to acquire adequate simultaneous source effort is an identification limit rather than an ecological negative result.

### Predictions to test

**P1 (light-only null):** same physical site × same species × matched daylength implies no rising/falling branch contrast in the relative detected daylight-core, daylight-edge or night intensities after real operational effort adjustment.

**P2 (core-to-edge):** greater falling-branch heat exposure relative to rising dates predicts a positive edge/core seasonal contrast. Lower exposure, winter or differently timed rainfall may produce a null or negative effect.

**P3 (daylight-to-night):** night/daylight redistribution is partially distinct from P2. A species can use dawn/dusk-adjacent *daylight* more without increasing night use.

**P4 (ecological transfer):** environmental and guild variables predict the direction and magnitude of branch contrasts in an independent region held out before model selection. A pooled mean effect with strongly inconsistent regions is insufficient evidence of universality.

### Methods (registered intent; source admission pending)

**Unit of observation.** Event species, dated local time, physical station identity, solar boundaries and original independently sourced operating intervals. Report camera detection rather than unmeasured latent movement or activity. Explicitly check local time zone, daylight-saving changes and long nights crossing midnight. For multi-year designs match each year separately and preserve dates with verified camera uptime and zero records.

**Astronomical matcher.** Pair increasing and decreasing photoperiod dates by site-specific astronomical daylength only, before analyzing observed wildlife events. If original site/date pair freeze exists (Uljin, 41 pairs), use that frozen roster unchanged. Retain the absolute daylength mismatch as an audit variable and independently handle equation-of-time changes in civil solar noon.

**Time categories.** Central 50% of daylight = core; combined first/last 25% of daylight = edge; all outside sunrise/sunset = night. Compute zone operating-hours from hardware/deployment records with any verified downtime. Do not mistake the published Korean civil twilight period outside daylight for our daylight edge.

**Biological endpoints.** Estimate two separate site/species seasonal log-ratios, H_edge and H_night, through an exposure-offset count model with explicitly preselected pooling and zero-count rules. Cluster uncertainty at physical sites and independent landscapes. Treat the nested model's comparison as a conditional observational prediction, not evidence of intrinsic circadian memory.

**Environmental explanation.** On the same matched dates compute daily temperature, thermal exposure during daylight core, precipitation, vegetation greenness and their branch differences from separately sourced, versioned climate and remote-sensing products. Use environmental predictors as observational explanations and test lag associations, not as natural experiments that uniquely identify temperature causation.

**Cross-landscape replication.** Train in independently sampled study regions, then hold out a complete region and assess the predictive distribution of the observed log-ratios. Report a new-region prediction interval, heterogeneity and direction as well as average effects. Within-camera sites are clustered, not independent landscape replications.

**Sensitivity and falsification.** Stable-solar-phase source-free counterexample, station-composition shifts, seasonal camera detection probability q, timestamp uncertainties, partial on-hours, known alternative calendar windows, external species taxon variation and negative controls. Favor the source-level HOLD over a spurious precise confidence interval.

### Results (empty by design; not yet a tested paper)

**Figure 1: seasonal matching and ecological lag.** No source-admitted paired empirical figure computed.

**Figure 2: core→edge and day→night matched branch effects.** No source-admitted biological H available.

**Figure 3: guild/ecology drivers and held-out region prediction.** Not estimable; no admitted cross-region Tier-A result.

**Figure 4: robust-to-detection and astronomical placebo checks.** Historical ODSP *synthetic methods checks* are available but are not new mammalian ecological responses.

Published external ecological motivation: Kays et al. studied 41 total areas but only five year-long sites for their seasonal question, with two in temperate North America and three in tropical/subtropical regions; Ikeda et al. reported species-specific seasonal activity changes in one northern Japanese forest. Neither is a verified equal-daylength replication of the present hypothesis.

### What conclusions will be defensible?

- With matched date/site independent camera-hours but unknown q: differences in **detected encounter-time allocation** conditional on measurement constraints.
- With q reference that transports across stations and seasons: a better-constrained inference about actual activity timing; still not automatically causal.
- With multiple independently held-out regions and environment checks: portable predictive ecology, potentially a limited generality claim.
- With aggregate seasons, unverified site/date camera-hours or only falling-season recordings: descriptive/background evidence, NOT a direct positive or negative H test.

### Source acknowledgments / links

Kays et al. 2020 (https://doi.org/10.1111/2041-210X.13370); Ikeda et al. 2016 (https://doi.org/10.1371/journal.pone.0163602); Uljin original dataset (https://doi.org/10.22756/ETC.20260000001022), Jeon & Lim 2026 (https://doi.org/10.3897/BDJ.14.e191556); Freiburg (https://doi.org/10.5061/dryad.73n5tb3bz); Snapshot Serengeti (https://doi.org/10.5061/dryad.5pt92); Rhode Island (https://zenodo.org/records/14508932).
