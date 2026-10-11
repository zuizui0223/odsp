# Biological question: is annual overlap hiding season-specific rewiring of the four ungulates' temporal niches?

## A real published baseline, not a new matched-date discovery

Jeon & Lim (2026), *Biodiversity Data Journal* 14:e191556,
https://doi.org/10.3897/BDJ.14.e191556, reported a year-long
82-camera-station survey with **4,623 independent ungulate
detections**. Its main Table 4 estimates six pairs' original
local civil-clock overlap (KDE Delta4, B=1000 bootstrap):

| Pair | Published annual Delta4 | Published 95% CI |
|---|---:|---:|
| Goral—Roe deer | 0.840 | 0.803–0.872 |
| Goral—Water deer | 0.811 | 0.774–0.842 |
| Goral—Wild boar | 0.810 | 0.770–0.841 |
| Roe deer—Water deer | 0.799 | 0.746–0.829 |
| Roe deer—Wild boar | 0.757 | 0.706–0.789 |
| Water deer—Wild boar | 0.653 | 0.609–0.692 |

Original full-period species detection counts are
Goral 2,317; Water deer 814; Roe deer 808; Wild boar 684.
The six published Delta4 CIs are uncertainty intervals for
**annual pooled overlap**, NOT tests of the difference between
species pairs or any early-vs-midsummer effect.

The paper's average-year solar-time overlap estimates were
similar but not identical, ranging 0.633–0.819, again **not**
results for the frozen 82 original matched dates. The
original, fine-scale camera coordinates are deliberately
WITHHELD to protect goral, and no finer location is required.

## One biological question worth answering

**Can high YEAR-ROUND overlap hide opposite responses to early
versus later growing-season ecological conditions, even when
daylight length is held nearly constant?**

At a fixed camera, the photoperiod-matched pairs are
2022-05-01..06-10 (rising daylight) versus
2022-07-01..08-31 (falling daylight). This is **NOT**
spring-versus-autumn; both branches concern the early/
mid-growing season. Changing temperature history, plant
phenology, reproduction and disturbance timing are candidate
pressures, none isolated causally just by daylength matching.

In each of four ungulates, physically distinguish:

1. **Within-DAYLIGHT timing**: redistribution from the
   central daylight half to its first/last quarter (combined
   daylight edges). Core and combined edges each occupy the
   same duration by the defined solar geometry. A negative
   falling-minus-rising daylight CORE:EDGE log rate
   interaction is a candidate edge shift.
2. **Whole-day NIGHT shift**: redistribution from all
   daylight to time outside sunrise/sunset. A positive
   falling-minus-rising NIGHT:DAYLIGHT log rate interaction
   is a candidate nocturnal shift.
3. **Community reassembly**: if the two signatures differ
   among species despite an unchanged physical camera roster,
   a model assuming the four taxa share one seasonal timing
   adjustment is falsified.

These are three distinct ECOLOGICAL descriptions—not simply
“solar phase wins,” “peak activity shifts,” or “pairwise KDE
overlap is less than 1.”

## Predeclared alternatives after seeing published YEAR totals

E0: **Common response.** The four taxa shift their two
zone-allocation signatures in similar directions. A
source-valid estimate of a low species×branch×zone
interaction, not a non-significant p-value on inadequate
data, supports this interpretation.

E1: **Divergent temporal refuges.** Some taxa redistribute
core daylight toward the daylight edges; others toward
night; some may remain stable. This is the clearest
time-niche reassembly result; environmental mechanism
requires separately verified daytime temperature, shade,
vegetation and human presence series.

E2: **Annual pooling hides within-season reassembly.**
The high annual Goral/Roe-deer overlap (0.840) may coexist
with meaningful seasonal divergence of their respective
time-zone allocations. Conversely, a lower annual
Water-deer/Wild-boar overlap (0.653) may coexist with
more similar within-season changes. These are possible
patterns to examine, NOT predicted or claimed results.
Annual overlap extremes are published and known before
the fixed 82-day source outcomes; treating these
known pair rankings as newly preregistered confirmatory
outcomes would be invalid. Keep all six species pairs
instead of only two publication-selected extremes.

The behaviorally relevant test is not that annual overlap
exceeds seasonal overlap (nonlinear mixture calculations
do not justify that simple statement). Rather, quantify
species differences in effort-adjusted daylight core,
daylight edge and night allocation at an unchanged
physical station set, then describe how the six
species-pair comparisons change between the frozen
astronomical branches.

## Source and replication constraints that can change the answer

**Very important: a species need NOT be DETECTED on both
dates to be analytically eligible.** A camera that was
operating correctly on both matched dates contributes
valid ZERO counts for the species. Requiring an animal
event on both dates to include a station would
artificially select sites with high passage activity,
bias seasonal contrasts and exaggerate “replication.”

The existing original ZIP preflight's field
`station_x_matched_date_pair_both_dates_positive_event_cells`
is **ONLY a descriptive rarity/power diagnostic**,
NOT a filter for ecological rate estimates. The ecological
rates implementation `odsp/uljin_ecological_refuge_rate_signatures_v0.py`
correctly forms the site×paired-date roster only from
independently logged operation in all source dayparts
on both dates; all four taxa and **all zero-event**
site×date entries remain.

Without original hour-level camera ON/OFF data, even
perfect original event timestamps cannot identify
rates within daylight core/edge/night. Without independent
q calibration, verified rates are **detected animal
encounters**, not necessarily latent animal preference.
Two sampled regions UJ1/UJ2 do NOT become 82
independent geographic landscapes by treating their
cameras as fully independent site replicates.

No real original v1.1 event/operation member has yet
been authenticated. Hence no statement here is a new
observed species-season finding or a causal claim of
temperature avoidance, photoperiod memory, competition
or temporal coexistence.

## Research decision once original archive is actually obtained

First report 41-pair species×branch×dayzone event counts
(including zeros) and available identical-station
operation exposure. If the source temporal support
is sufficient, estimate the two predeclared zone
allocation contrasts per taxon and explicit
species×branch×zone differences, with clustered
uncertainty at genuine independent camera/site or
landscape units as source design permits.

If those source conditions are NOT met, report
an appropriately scoped inconclusive/low-support
result rather than searching new date windows or
inventing spring-autumn seasons.
