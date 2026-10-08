# ODSP N2 ecological follow-up: Does wildlife activity track the sun or the clock?

**Status:** new public-data ecological prediction study, not a qualified
ODSP inference route or a re-analysis/reclassification of the closed
Snapshot Serengeti terminal endpoint.

## Biological question

A species can appear seasonally plastic in human civil-clock time for
at least three different reasons:

1. its daily detections follow sunrise/sunset while the photoperiod shifts;
2. its timing is approximately fixed relative to local civil time;
3. it actively reorganizes behaviour across seasons beyond astronomical
   phase alignment, potentially in response to thermoregulation, prey,
   human activity or other ecological interactions.

Existing camera-trap research already documents seasonal timing shifts
and corrects daylength-dependent biases. Vazquez et al. (2019,
Methods in Ecology and Evolution, DOI 10.1111/2041-210X.13290)
compared single, equinoctial and average solar anchoring and favored
average anchoring for estimating activity distributions in their tests.
That work DOES NOT make any empirical positive prediction for this
new ODSP site-and-year-heldout experiment.

Here the new falsifiable ecological endpoint is **predictive transport**:
does a species' solar-phase organization learned from 2018–2021
predict which CIVIL clock-hour bin a camera detects it in during
2022–2023 at PHYSICALLY unobserved camera sites?

Unlike merely overlaying smoothed activity curves, both candidate
models predict exactly the SAME clock-hour target at every heldout row,
so their heldout log scores are directly comparable proper scores.

## Source and prospective separation

Frozen input: Mayer et al. (2025), Rhode Island wildlife camera trap
survey 2018 to 2023, Ecology 106:e70094 (DOI 10.1002/ecy.70094).
Public Zenodo record 14508932, v3, DataS1.zip pinned by MD5
c66943e6c2a9aab0abce2a1eba8ce02e.

Source summary: 249 sites, 12 seasonal survey periods and 39
terrestrial vertebrate taxa. Surveys originally targeted suitable
forest/forested wetland habitats for bobcats and fishers. From 2019
onward most sites used two cameras, sometimes 50–100 m apart.
The version 3 archived detection file contains IMAGE-level rows,
not necessarily statistically independent ecological visits.

This study was frozen in
ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json before any archive
detection row outcomes were read through this new lane. The public
dataset and articles were already published; complete historical
non-access is not claimed. Accordingly it is **exploratory** and
not an authenticated untouched-external endpoint.

Whole physical site IDs are hashed to five stable folds using
SHA256('odsp-ri-solar-v0|site'). One fold (0) is held out from the
entire training roster. Fitting uses early years 2018–2021 on the
other four folds only. Evaluation uses late 2022–2023 seasons on
the heldout site fold only. NO individual camera, photo row or
site-year is treated as an independent geographic site.

Species are admitted using only training rows: >=120 30-minute
deduplicated events across >=8 training sites, and winter and
summer each with >=25 events across >=3 sites. The heldout
summer and winter need >=100 scored events and >=8 different
physical heldout sites or the endpoint is unavailable.

The archive's calendar time zone may not be externally verified,
so America/New_York wall-clock semantics are a declared
hypothesis and the observational inference remains exploratory.

## Models and the physically testable mechanism

Outcome Y: one of six frozen four-hour bins (00–04 through 20–24)
for a retained CAMERA DETECTION, NOT the true activity-time
probability of undetected animals.

M0 clock: species-specific six-bin local-clock probability.

M1 solar: species-specific six-bin EQUINOCTIAL two-anchor phase
with sunrise mapped to 06:00 and sunset to 18:00.
At each heldout camera site/date, the stored solar-phase
distribution is **exactly pushed forward** through the
piecewise-linear sunrise/sunset transformation to SIX CIVIL
clock bins. Log probabilities are then scored on the same
heldout observed Y used by M0.

M2 clock×season: six-bin distribution conditioned on species
and season (more flexible secondary control).

M3 solar×season: six-bin solar distribution conditioned on
species and season, projected to the same clock target (secondary
test for residual seasonal rearrangement beyond solar phase).

Each uses the same Jeffreys pseudocount 0.5 per bin, with
training contributions weighted equally across physical
site×season-year within species.

If there is genuine solar phase tracking, M1 may transport
better than M0 at new sites after calendar years change.
If routines are clock-stationary, M0 can win instead.
If real season-specific timing persists after solar alignment,
M3 may predict better than M1, but without proving temperature,
predator or prey causality.

A frozen **wrong-season solar negative control** evaluates M1
using calculated sunrise/sunset from date+183 days instead of
the real observation date. Solar M1 must also beat this
deliberately incorrect astronomical predictor at heldout sites
in winter AND summer before asserting an exploratory
sun-alignment signal.

## Statistical endpoint

Primary paired loss difference per camera detection:

    G_solar = log P_M1(Y|species,site,date) - log P_M0(Y|species).

Secondary:

    G_remaining_season = log P_M3(Y) - log P_M1(Y).
    G_season_in_clock = log P_M2(Y) - log P_M0(Y).

Both M0 and M1 contain six parameters (before the sum constraint)
per species and have identical smoothing. Solar gives a physical
change of coordinates, not more learned per-species bins.

Aggregate event-level differences first within each
physical site×season-year, then equally across years within each
site×season, then equally across heldout sites in that season.
The same physical site's winter and summer outcomes are coupled.

Use a frozen 2,000-draw, seed-2026100803 **paired physical-site
exponential multiplier bootstrap** for exploratory uncertainty
summaries. The same positive random site weight is used for winter
and summer within a draw; this does not prove confidence interval
coverage with spatially nonrandom site selection.

An exploratory solar transport signal requires positive
one-sided 95% site-cluster bootstrap lower bounds on BOTH
winter and summer solar-over-clock contrasts, AND positive
lower bounds on correct-solar over wrong-season-solar in
both seasons. Nothing is retuned after the first source
outcomes.

## Essential caution

The original camera field survey was species-targeted and not
a probability sample of all Rhode Island habitat. Repeated
detections at a site can reflect placement, weather and detection.
Even if site-heldout and solar-aligned models score better, this
cannot demonstrate daylength causality, avoidance competition,
or activity rate in the absence of detection calibration.

Vazquez et al. (2019) showed that average anchoring may be
preferable to equinoctial anchoring for estimating whole diel
density. This experimental v0 tests a deliberately explicit
equinoctial astronomical predictor; superiority to alternative
solar transformations is NOT claimed. A separate version
would be necessary to compare average anchoring under the
same future site-year score.

The Rhode Island source's original clock timezone and any
DST edits require external documentation. Times around
ambiguous or nonexistent DST clock periods are rejected;
this does not rule out more general clock metadata errors.
An unrecognized archive schema, mismatched source MD5 or
unmatched camera deployments causes an **UNAVAILABLE** result,
never favorable retuning or replacement of the source.

## Why this is ecologically stronger than more reliability gates

The distinct scientific prediction is *what organizes animal
detected time across temporal and spatial boundaries*. It is
not whether another conservative all-component lower bound
can reach a target probability with a small number of sites.

- If M1 wins and its wrong-sun control loses: evidence
  consistent with transported astronomical organization
  of detected timing.
- If M0 wins: this equinoctial representation fails to
  outperform transportable clock-time schedules.
- If M3 adds much beyond M1: context/season-specific
  reorganization remains after accounting for sun geometry.
- If both models perform poorly: possible local behaviour,
  camera effort or detection variation; no mechanism
  is identified without targeted follow-up.

The exact public-data outcome is NOT YET available in this
document. The code contains known-truth synthetic controls
with solar-following and fixed-clock worlds and tests
exact probability conservation for the solar-to-clock map.
No closed empirical endpoint or active qualified inference
registry has been changed.

Primary literature:
- Mayer et al. 2025. Ecology 106:e70094.
  https://doi.org/10.1002/ecy.70094
- Vazquez et al. 2019. Methods in Ecology and Evolution.
  https://doi.org/10.1111/2041-210X.13290
