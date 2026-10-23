# Independent African elephant observations: same seasonal direction, different strength

**2026-10-19 | Cross-region, within-taxon ecological context from original Movebank GPS files; exploratory and post-prior-outcome.**

## Nontrivial ecological question

If an animal's solar branch by itself determined its day/night movement, near-equal photoperiod might imply invariant movement relative to daylight. Could a particular species show repeatable directional asymmetry across independent environments—even when the magnitude varies by habitat, meteorology, observation years or physiological state?

We compared **two independent original GPS source archives for the SAME taxon, African elephant (`Loxodonta africana`)**, with a consistent original-source observation rule (at most one GPS fix per UTC clock hour chosen using timestamps alone, same solar season branch matching, 30–120min valid step, and matching daylight/nights). The sources are Etosha National Park, Namibia and Kruger National Park, South Africa. This is much more informative for species-versus-geography questions than comparing an elk in one ecosystem with a bear in another, but **two cohorts cannot establish a species-wide rule**.

## Source-authenticated observations and exact effects

| Independent elephant source | Matched individual animals | Source-calibrated observation summary | Relative NIGHT/DAY GPS displacement seasonal change | Individual-bootstrap 95% (conditional source animals) | Animal directions |
|---|---:|---|---:|---|---|
| Etosha, Namibia — [Tsalyuk et al. 2018 public original](https://doi.org/10.5441/001/1.3nj3qj45_2) | **14** | 3,436 astronomy/date-paired observations; 251,278 timestamp-only hourly fixes from 2,930,268 original source GPS rows | **−0.15013** | [−0.20271,−0.10091] | **14/14 negative** |
| Kruger, South Africa — [Thermochron elephant tracking source](https://doi.org/10.5441/001/1.403h24q5) | **13** | 1,787 matched observation date-pairs; 154,857 timestamp-only hourly fixes from 283,688 original source GPS rows | **−0.02889** | [−0.04336,−0.01172] | **11/13 negative** |

The endpoint is falling-minus-rising `[log(1+median NIGHT straight-line GPS km/h)−log(1+median DAY GPS km/h)]`. Note the **southern-hemisphere annual daylight geometry**: increasing daylight after June, decreasing daylight after the December summer solstice. These are **independent cohorts and recruitment schedules**, not the same individuals or exact concurrent weather; *Etosha source 2008–2013 versus Kruger source 2007* in the published archives. Do not attribute the difference in magnitude to climate without comparable individual thermal/water exposures and telemetry protocol controls.

Both original files passed provider-declared MD5 checks and source-specific tests in these first real workflows:
- [Etosha elephant hourly source method first run 39207964106](https://github.com/zuizui0223/odsp/actions/runs/39207964106), original ZIP MD5 `dd6447d7d933e6bb10cd1eec1269eeb7`.
- [Kruger original first hour-thinned result 39210827847](https://github.com/zuizui0223/odsp/actions/runs/39210827847), original CSV MD5 `970ea06b9de69f1cc0d9f733d7f7e463`.

The `Etosha` first unthinned adjacent-step estimator was **not** considered source-inferentially admissible under its original high-frequency observation design; the hourly route is a separately named post-first-support estimator (not a silent upgrade of earlier evidence). Kruger reports its unthinned estimate separately **−0.03223** and its equally hourly-thinned one **−0.02889** on the same 13 animals, supporting the robustness of this sign to its own source-specific sampling representation; neither endpoint measures continuous time active.

### The temporal component matters

Etosha's −0.15013 relative night-minus-day seasonal change consists of falling-minus-rising **DAY +0.10664**, **NIGHT −0.04348** log1p km/h. Thus, on the descending daylength branch, observed daylight displacement increased while nighttime observed displacement fell. Kruger's smaller −0.02889 consists of **DAY +0.05238** and **NIGHT +0.02349**: both increased, but the daylight increase was larger. A shared **negative relative night/day sign therefore does NOT imply that absolute nighttime displacement necessarily decreased in both ecosystems**.

This is a concrete ecological motivation to retain the two absolute movement components rather than summarizing all change as simple “more diurnal” or “less nocturnal”. There is no original activity monitor calibration to infer what proportion of each day animals were active.

## Same-Etosha predator/scavenger context, independently checked

At Etosha, source-verified black-backed jackal (`Canis mesomelas`, independent original archive [10.5441/001/1.n1r7ds5r](https://doi.org/10.5441/001/1.n1r7ds5r)) was processed with the **same hourly source cadence rule**. Eight jackals had a mean relative night/day effect **+0.04479**, but an individual-bootstrap conditional source interval **[−0.00211,+0.11922]** spans zero (five positive, three negative). Thus it is NOT evidence that jackals robustly shift toward nights. More importantly, a separate common-calendar year inspection showed that in **2009** the two sources had **173 identical source-qualified date pairs**, 11 elephant individuals with effect **−0.26287** (source-bootstrap [−0.34969,−0.17352]) and seven jackal individuals with effect **+0.00926** (bootstrap [−0.00617,+0.02605]). The same fixed coarse Etosha ERA5 reference year had a falling-minus-rising previous-30-day `P−ET0` increase around **+118 mm** under their individual date supports. This is shared *region/year/date availability*, not synchronously observed contacts or equivalent individual habitats.

First common-calendar site/year source check: [Etosha year-stratified source CI 39210319995](https://github.com/zuizui0223/odsp/actions/runs/39210319995); the 2010 jackal cohort had only **one** eligible individual and remains INSUFFICIENT, while elephants had five with relative effect **−0.24226**. Do not claim a repeatable two-species interaction response in that second year.

## Within-elephant collar-temperature association: explicit failure to identify a mechanism

The Kruger source also contains GPS-associated `external-temperature` sensor values, unlike many telemetry datasets. The original source was exactly replayed and linked to the fixed solar-date pairs. On **13 elephants and 1,787 paired date pairs**, the exploratory individual-year-centered association slope between falling-minus-rising DAY-minus-NIGHT **collar thermal gradient** and the corresponding relative diel GPS speed shift was **+0.001172 log1p km/h per °C**, with descriptive animal-bootstrap 95% **[−0.00204,+0.00415]** spanning zero (eight positive vs five negative animal slopes). [Original sensor and source CI 39211773115](https://github.com/zuizui0223/odsp/actions/runs/39211773115). Collar electronic/external temperature is **NOT body temperature or independent ambient microclimate**, and this analysis does not support a definitive thermal mediation claim.

## Ecological interpretation

**Supported within these original datasets:** two separate African elephant cohorts showed a negative relative NIGHT-vs-DAY GPS displacement seasonal contrast under near-matched summer-solstice daylength. The effects differed in magnitude and component structure. In one ecological landscape (Etosha, 2009), an independent jackal cohort using overlapping source date pairs did not show a comparably large negative effect, but was limited to seven jackals and cannot identify an interaction.

**NOT supported:** a universal elephant species trait, direct predation/avoidance, heat avoidance, rainfall-resource causality, endogenous annual memory, identical sampling frames, globally representative effect, or even equal animal activity hours. Sex/age/recruitment/tags are not yet harmonized between independent elephant studies. The thermal association in Kruger is not strongly identified. The source cohort cannot be turned into two ecological replicates of an identical temperature intervention.

**Manuscript use:** a focused supplementary same-taxon cross-ecosystem comparison alongside the six independently original-source North American mammal cohorts. Do not pool separately calibrated camera PHOTO event-time odds, raw duck GPS fix-speed, and elephant minimum straight-line displacement on one numeric scale. All earlier ODSP frozen results and source HOLDs remain separate and unchanged.

### Source registers

- [Etosha hourly source contract](../research/MOVEBANK_ELEPHANT_HOURLY_V1_20261019.json)
- [Kruger independent source contract](../research/MOVEBANK_KRUGER_ELEPHANT_INDEPENDENT_V0_20261019.json)
- [Kruger thermal test contract](../research/MOVEBANK_KRUGER_THERMAL_DIEL_V0_20261019.json)
- [Etosha 2009–2010 common-year source contract](../research/ETOSHA_YEAR_STRATIFIED_ECOLOGY_V0_20261019.json)
