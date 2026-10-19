# Biological generality of ODSP descendants — preregistration draft v1

Date: 2026-10-19
Repository: zuizui0223/odsp
Branch: `prospective/biological-generality-20261019`
Status: **prospective hypothesis and source-feasibility protocol; no new ecological outcome examined**

## Decision and provenance

The fact that BATTER (flying mammals) and MINA (flightless birds) were both motivated by ODSP does **not** make them a matched two-taxon experiment. Their current strongest endpoints are different:
- BATTER: repeatable *individual* vertical-use distributions/centered shape among tracked bats, with counterexamples and unresolved behavioural/central-place mechanisms.
- MINA: excess concentration of *breeding counts* among monitored subcomponents during penguin population decline, conditional on population totals and counting noise.

ODSP's niche-thickness and state-prediction machinery can be applied across taxa, but this is methodological portability, **not** demonstration of a universal ecological law. Both descendants have biologically important central-place contexts (roost/colonial-breeding anchoring), which may reflect (i) real constraint, (ii) differential detectability/data availability, or (iii) neither. Do not infer a common cause from that coincidence.

**Core distinction:** flying vs flightless is a misleading 2-case contrast when ecological endpoint, movement medium, phylogeny, instrument and sampling scheme also differ.

## Scientific programme: two distinct falsifiable extensions

### A. Individual vertical-use organization beyond bats — primary NEW test

**Question:** Are repeatable, individual-specific distributions of vertical movement states a recurrent property across *different movement guilds*, and does central-place dependence predict their magnitude beyond locomotion mode and study context?

Competing explanations (not proven):
- H_A1, taxonomically recurrent: same-individual vertical profiles transfer across independent sessions in at least two independent **non-bat** species under an appropriately matched species/site/season reference, beyond whole-session individual-label permutations.
- H_A2, central-place constraint: within eligible species, a pre-outcome *independently defined* breeding/roost/colony-attached state is associated with stronger repeatability than matched non-central-place periods; contrasts must be within species and where possible within the same tracked individual. This is a **candidate association**, not assumed mechanism.
- H_A3, taxon/mode specificity: repeatability occurs for bat flight but fails among non-bat aerial taxa despite adequate power/measurement; alternatively, diver depth-maxima replicate while aerial non-bats fail. Such contrasts indicate endpoint/mode boundary, not proof of evolutionary uniqueness.
- H_A0, context or artefact: after equal coarse horizontal occupancy, biological state, stage, tag effects and session-label nulls are respected, identity-related gain is absent or heterogeneous.

**Common estimand for GPS altitude data (same measurement semantics only):** within-species, within-station/season held-out session mean log-score gain of the same individual's OTHER-session vertical distribution over the contemporary equal-individual conspecific reference, using identical coarse horizontal cells and identical evaluation weights. Calibrate against whole-session label exchangeability. An independent secondary test evaluates *distributional shape after additive within-session vertical centring*; this is a session-normalized shape comparison, NOT an operational prediction of absolute altitude when held-out session centring requires its own observations.

**Different semantic stratum, separate headline:** diver *dive-event maximum depths* with individual ID, location and time (penguins, seals). Maximum dive depth is not instantaneous underwater occupancy and cannot be pooled numerically with bat/gull GPS height. Evaluate the same question of cross-session identity at the **dive-event** level, with separate nulls and effect estimates. Report heterogeneity across the two observation regimes, not a universal pooled magnitude.

**Selection and eligibility rules before examining new vertical values:**
1. Fix one archival version / identity crosswalk per independent source; overlapping records published on Movebank/Zenodo/GBIF are one source, never independent replications.
2. Require timestamped individual identity, horizontal position and a truly **animal-borne vertical state** (not site elevation / sea-floor depth / instrument installation depth), with traceable native units, source QA and a predeclared availability/quality filter.
3. For a prospective species panel, require at least **10 different animals** with at least **2 biologically independent comparable sessions** and at least **50 eligible events per session**. Session rules must be defined from timestamps, x-y/known trips or metadata *before inspecting vertical values*. This is a power/coverage screen; a below-threshold panel is unavailable, not ecologically negative.
4. Match self and other predictions to exactly the same supported coarse x-y cells; choose horizontal grain from x-y support + location error **before** viewing vertical values. Report primary and predeclared grain sensitivity rather than choosing the best result.
5. Preserve sex, age, site, calendar context, tracked season, flight/dive behavioural state where externally identified, and instrument model when possible; avoid treating serial fixes as independent biological replicates.
6. Flights: use source-defined movement state or a **pre-vertical** GPS-speed/acceleration rule. Do not allow resting/roost fixes to masquerade as individual flying-height shape. In dives, retain only valid dive events and track location-to-dive interpolation uncertainty.
7. Separate absolute altitude offset, centered shape, horizontal patch fidelity, and departure/arrival effect. Session centring addresses additive height bias only, not tag error variance or behavioural mixtures.
8. Retain all qualifying failures. For non-bat generality, require separately supported positives in at least two independent non-bat species datasets, with a declared multiple-comparison correction, and report the complete denominator. Do not define success as 'at least one positive somewhere.'
9. For the proposed central-place association, use known external breeding/roost metadata or a predeclared x-y-only classification, then test matched within-species (ideally within-animal) periods. If this is unavailable, the central-place mechanism remains **untested**, regardless of the outcome in (8).

**Candidate metadata screen already performed, without opening GPS heights:**
- `LBBG_SCHIERMONNIKOOG` Zenodo 20706447: reference CSV **29 animal IDs / 29 metadata rows**; 2017/2018 deployment starts. Frictionless schema contains `timestamp`, `location-long`, `location-lat`, `height-above-msl`, `individual-local-identifier`. Flight events, two-session support and tag accuracy remain **unverified**.
- `MEDGULL_ANTWERPEN` Zenodo 15685037: reference CSV **14 animal IDs / 14 metadata rows**; 2021/2022 deployment starts. Same required schema field family. Independent individual-session support remains **unverified**.
- `BOP_RODENT` Zenodo 10055071: reference CSV 35 animals (five species), and ODSP has already examined a subset for state prediction. **Historical/context comparator only**; cannot count reuse as prospective external replication, nor treat the updated 2026 Zenodo record as a second independent dataset.
- `USAP-DC 602035`: Adélie + gentoo GPS and dive depth, six published seasonal files (2018/19 to 2024/25, gap 2021/22). Individuals, dive-link quality and comparability not yet screened; page download currently requires reCAPTCHA. A dataset listing is not an admitted panel.
- `USAP-DC 601928`: 2022/23 Adélie GPS/TDR maximum-dive-depth event data; already advertises `DeployId`, `maxdep`, `Latitude`, `Longitude`, `Datetime_UTC` and interpolation time uncertainty `tdiff`. Animal/session counts and stable comparability remain unverified; reCAPTCHA required for website download.
- BAS PDC chinstrap TDR v2, DOI 10.5285/da13e049-be2b-4345-bbdd-ab960cb24731: 317 reported deployment CSV files, same-ID GPS references; join integrity and session availability must be checked. This is **not** a resuscitation of the closed Tawaki Gate-D failure.
- SO-ABBA seal dive dataset, Zenodo 19121676: 4,492,019 individually georeferenced dives from 1,394 seals (three species); individual, trip/block, event and interpolation details must be audited before endpoint admission.

### B. Breeding-component redistribution beyond penguins — a SEPARATE macroecological test

**Question:** Do declining breeding groups become disproportionately concentrated into fewer persistent breeding components *across non-penguin colonial taxa*, conditional on changing population total, count error and coverage?

Endpoint: inverse-Simpson effective monitored breeding-component number, compared against fixed composition simulations conditional on each observed annual total, with explicit missing-versus-zero distinction and stable roster/crosswalk. This is not a vertical-use individuality statistic and **must not be pooled with A**.

Status: MINA already has a three-island discovery + Adélie/chinstrap Signy replication (five units in total). The independent UK/Ireland BTO/JNCC SMP is the leading non-penguin data system. Its nested Master site → child Site identifiers and explicit nil returns make the test structurally plausible, but bulk longitudinal extracts require a separate data request and coverage/crosswalk audit. MINA's frozen feasibility contract requires at least 10 eligible Master-site×species networks across five seabird species before promotion; no SMP abundance outcomes have been opened. Do not request individual Plot-level data as interchangeable spatial components without a continuity crosswalk.

Do not interpret non-significant Antarctic-wide breeding-island architecture moderation (MINA integrated exploratory line) as a tested universal absence of habitat filtering.

## Possible shared ecology: hypothesis, not a combined answer

Central-place animals may face high state-space freedom while moving to forage but strong spatial constraints at breeding/roost sites. This can create a contrast between highly individualized movement use and non-proportional demographic redistribution. That sentence is a **conceptual bridge**, not a causal law, and it does not identify a common response variable.

The decisive question is **which ecological constraints predict the magnitude/organization of a *specified* heterogeneity endpoint**, not whether two striking clades happen to be both non-exchangeable.

## Stage ledger

- **Completed now:** origin comparison across ODSP/BATTER/MINA; public source catalogue; outcome-blind GPS metadata check for two gull studies; pre-outcome source ledger and falsifiable eligibility / claims plan.
- **Next allowed:** download immutable candidate metadata/event headers where lawful; assess GPS tag errors, flight-state definitions, independent sessions/animals and x-y overlap *without computing vertical shape or effect estimates*; freeze admissible taxa and corrections.
- **After admission freeze:** compute held-out self-vs-conspecific gain, correct label nulls and central-place moderation using independent validation groups; keep unsuccessful and unavailable sources in the denominator.
- **Separately later:** MINA seabird-SMP request / structurally gated macroecology; no retroactive change of the existing Ecology Report.

## Links to the independent record

- [ODSP empirical state matrix](https://github.com/zuizui0223/odsp/blob/main/N2_EMPIRICAL_STATE_MATRIX.json)
- [BATTER scientific status](https://github.com/zuizui0223/batter/blob/main/README.md)
- [MINA current ecological programme](https://github.com/zuizui0223/mina/blob/main/README.md)
- [MINA migration from ODSP](https://github.com/zuizui0223/mina/blob/main/docs/MIGRATION_FROM_ODSP.md)
- [MINA SMP structural audit](https://github.com/zuizui0223/mina/blob/main/docs/SMP_COMPONENT_FEASIBILITY_AUDIT_V1.md)
- [USAP-DC Palmer foraging 602035](https://www.usap-dc.org/view/dataset/602035)
- [USAP-DC Cape Crozier dives 601928](https://www.usap-dc.org/view/dataset/601928)
- [INBO gull 20706447](https://zenodo.org/records/20706447)
- [INBO Mediterranean gull 15685037](https://zenodo.org/records/15685037)
- [BAS chinstrap TDR v2](https://data.bas.ac.uk/full-record.php?id=GB/NERC/BAS/PDC/02020)
- [SO-ABBA seals](https://zenodo.org/records/19121676)
