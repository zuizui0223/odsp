# What do ungulates do with the same amount of daylight, but a different ecological season?

## Biological question and correction to previous framing

This is an **ecological hypotheses** route, NOT another source-free
clock transformation or detector-q sensitivity PR. The original
frozen **41 photoperiod matched astronomical pairs** are not
spring-autumn pairs: the ascending daylight dates run **1 May to
10 June 2022**, while the descending dates run **1 July to
31 August 2022**. Hence the correct interpretation is **early
growing season versus midsummer at nearly matched DAYLENGTH**.
Do not relabel as a different longer-history spring-autumn dataset.

The original Korean Uljin source paper, Jeon & Lim (2026),
Biodiversity Data Journal 14 e191556,
https://doi.org/10.3897/BDJ.14.e191556, describes 4,623
ungulate detections over 82 stations across May 2022–May 2023.
The public NIE EcoBank original version 1.1 archive is at
https://doi.org/10.22756/ETC.20260000001022, but its original
event rows and true camera operation times have NOT been accessed
in this ODSP route. Only published aggregate metadata and the
original independent astronomical calendar freeze are available.

## The central hypothesis: changing a TIME REFUGE

**At effectively the same daylength and same physical camera
station, does the later ecological season redistribute the
detectable activities of these four taxa, and if so, where
does the displaced activity go?**

The four prespecified taxa are long-tailed goral, water deer,
Siberian roe deer and wild boar. Their distinct ecological
habitats and potential exposure pathways make different time
responses biologically plausible, without assuming which
species is guaranteed the biggest responder.

Three separately falsifiable causal-compatible signatures:

**H0, solar time invariance.** When the solar clock accounts
for daylength and original camera effort, detected time use is
unchanged between the rising and falling branches at matched
daylength. Compatible with light as an immediate timing cue,
but not proof of an endogenous clock.

**H1, early/late-daylight edge refuge.** On the later midsummer
dates, detected activity redistributes from the central HALF
of daylight to the two combined edge QUARTERS, without necessarily
moving to nighttime. This is consistent with avoiding exposed
bright/hot hours, but temperature must be measured independently
before a thermal interpretation is credible.

**H2, night refuge.** Detected events redistribute from overall
daylight to night on the later midsummer date, which is
different from H1. The core-to-edge and night-to-daylight
contrasts are therefore distinct, and neither response may be
identified from a single circular-mean event time when activity
is bimodal.

**H3, species-specific temporal niche REASSEMBLY.** The four
taxa do not all display the same H1/H2 branch effect. A
species×branch×time-zone interaction would indicate biological
diversity in within-day seasonal temporal allocation at
shared stations. It would NOT demonstrate direct competition,
fitness benefit, predator avoidance or temporal coexistence,
since marginal camera detections cannot identify any of those
mechanisms.

### Precisely predeclared physical day-zone categories

For each original local civil DATE using PUBLIC site-level
representative solar geometry and true external sunrise/sunset:

- **DAYLIGHT CORE**: [sunrise+.25×daylight, sunrise+.75×daylight),
  central 50% of actual daylight, solar-phase 09:00–15:00
- **DAYLIGHT EDGE**: first 25% plus last 25% of daylight
  (combined 50%), solar-phase 06:00–09:00 and 15:00–18:00
- **NIGHT**: outside actual sunrise/sunset

CORE and combined EDGE have **exactly equal astronomical
durations on a given date**. This avoids making edge avoidance
a trivial daylight-duration artifact; however source hourly
camera uptime and detection probability still need accounting.
Events are ALWAYS classified from original Asia/Seoul CIVIL
clock timestamps; date-specific solar boundaries are ecological
labels, never independent outcome bins for different model
families. The generalized public solar location is NOT
fabricated camera GPS; geographical timing sensitivity remains
a source limitation.

### Distinguishing the ecological mechanisms in advance

| Result in later growing-season matched-daylight branch | Consistent interpretation | What it does **not** prove |
|---|---|---|
| Core decreases, edge increases, night unchanged | Within-day daylight refuge reallocation (H1) | Thermal avoidance without measured temperatures |
| Night increases relative to all daylight | Shift into nocturnal time refuge (H2) | Human avoidance without time-resolved human disturbance |
| Species respond in opposing directions at the same stations | Divergent temporal guild reassembly (H3) | Causal competition or displacement |
| No detectable branch differences after effort adjustment | Solar-phase invariance not rejected | No ecological difference without precision/power |
| Branch effects track independent temperature or phenology observations | An environmental-history association | Causal effect of temperature or vegetation |

The novelty target is NOT a cold-vs-warm seasonal KDE or simple
species-pair overlap difference, both established in recent
ungulate camera-trapping work. It is distinguishing WHERE
species' time use shifts under a **light-matched natural
comparison** and whether taxa SHARE the shift direction,
without confusing site composition, operation hours and
detector q.

## Feasibility and inference audit BEFORE any ecological result

The initial source audit tests whether original v1.1 CSV member
records actually exist and were supplied, reports 8
species×branch case counts *including all zeros*, and inspects
source hourly operation chronology for the SAME stations and
dates. Existing 41 astronomy pair matches are NEVER refitted
to maximize event counts or seasonal effects.

An ecological statement about encounter *rates* must use
actual original positive operating HOURS in each of the three
ecological zones, including shutdowns. Daily 'functional
nights' or station-season summary effort does not establish
the hourly denominator. If these original source operation
records are unavailable or not independently authenticated,
the correct result is `HOLD_NO_HOURLY_OPERATION_DURATION`.

The software flags LOW_SUPPORT for a taxon when either
branch has fewer than 30 independent event records or when
fewer than 8 physical stations have independently verified
positive camera operating hours on BOTH original branches.
This is a descriptive feasibility threshold, NOT a power
calculation, a p-value threshold or a selective removal rule.
All four taxa must remain in the denominator and report.

Even a rate-normalized time-use result is conditional on
camera DETECTION. True latent animal preference would need
independent detector-q validation as identified by previous
ODSP methods. There are only TWO sampled study regions,
UJ1 and UJ2; there are not 82 independent landscapes.

Annual station `frequency_of_people` is an exploratory
site context covariate, NOT a time-resolved measurement of
human presence. Similarly, temporal overlap of two taxa
is algebraically determined by their marginal activity
distributions and does not independently prove interspecies
avoidance. Mechanistic attribution to temperature requires
a **separately acquired environmental series**, frozen
extracting rule and adequate source validity.

## A biologically meaningful empirical outcome

A strong positive paper would show that with unchanged
original station deployment, independent camera-hour
denominators and matched daylength, at least one species
exhibits a reproducible core→edge or daylight→night seasonal
shift, that different taxa have contrasting responses,
and that independent environmental or human covariates
distinguish their patterns. Negative results or missing
opportunity support must be reported and may be more
informative than claiming that clock-vs-solar 'wins'.

The current code produces ONLY original source-data
admission, detected event zone counts and verified
operational-hour support—not an invented ecological result
nor another calibrated detector-q benchmark. All previous
qualified ODSP inference routes and synthetic-first
ledgers are untouched.
