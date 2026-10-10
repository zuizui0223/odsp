# Within-site seasonal detector drift can imitate animal seasonal timing

**A distinct SOURCE-FREE post-PR259 route; NO original animal data or
unverified hardware logs have been accessed.**

## Why site-specific detector calibration may not be enough

PR259 showed that a source camera q averaged across IID station types
does not necessarily transport to individual physical cameras even
when its source-population Binomial model and simultaneous
Clopper–Pearson intervals are valid. Yet q can also change over time
inside the SAME station because of seasonally changing vegetation,
temperature, sensor settings and visibility, despite identical
photoperiod. A physical site is an independent sampling unit for
site-majority tests; a year-long station q estimate is not necessarily
a valid target for early/late solar-phase predictions in both branches.

This route keeps the original 2022 41 matched rising/falling
daylength pairs, 82 original clock dates, common original 96 civil
15-minute animal event bins and original five time-anchoring candidate
models with 16 training+16 independent heldout PHYSICAL sites.

## Two synthetic detector worlds

Both worlds independently assign 32 camera station types A or B with
IID 50:50 probabilities. All q values are assumed constant INSIDE
each original six CIVIL 4-hour clock blocks and across the 41 dates
of EACH photoperiod branch, but may vary by station and branch.

- **Within-site seasonally STABLE q**, negative control:
  A q=(.95,.85,.35,.32,.60,.90), B=(.30,.43,.90,.91,.73,.35)
  in both rising and falling branches.
- **Within-site SEASONALLY DRIFTING q**, adversarial source world:
  A rising=(.95,.85,.35,.32,.60,.90),
  A falling=(.35,.40,.80,.90,.75,.40);
  B rising=(.30,.43,.90,.91,.73,.35),
  B falling=(.85,.80,.35,.40,.55,.85).
  Detector response can change even with invariant latent
  animal timing; no one specific weather or behavioral mechanism
  is claimed as the source of synthetic q seasonality.

## The exact reference-target population distinction

For each known TRUE passage reference opportunity at a particular
camera×civil-block, the **site-only source** independently draws
rising or falling photoperiod branch with probability .5,
then samples independent camera success with that branch's q.
Therefore its successes are IID Binomial(n,(q_rise+q_fall)/2)
and exact 96-source-cell CP confidence bands with alpha=.025
are correct FOR THIS BRANCH-AVERAGE detector estimand. They cannot
cover BOTH actual branch-specific target q values when seasonal
detector q differs. Thus all predeclared 48 season-drifting
site-only-reference paired model cases are HOLD, even if a favorable
model ranking appears or source interval correctly covers the
branch-AVERAGE q.

The **site×branch source** separately measures each physical camera
× 2 rising/falling branches × 6 civil 4-hour blocks, with
192-cell simultaneous CP alpha_q=.025. This correctly targets
the q of each physical site×season×clock block. It is valid
only when actual reference known-passage opportunities are
correctly labeled, independent of target detections, and
the detector q is stationary within each season branch and
clock block.

Equal gold-standard TRUE passage opportunities:
T=38,400: site-only 16×6×400 versus site×branch 16×2×6×200.
T=153,600: site-only 16×6×1600 versus site×branch
16×2×6×800. These are not proven equal camera/person-hour costs.

## The same 96 clock-bin predictive majority estimand

All five frozen original model families are trained ONCE on
16 physical training sites on actual synthetic q-distorted events.
Original model predictions retain common 96 local civil 15-minute
bins. The site-specific q is the SAME q for any two competing
time representations in a given physical site×date×civil clock
bin, so its event-level likelihood factors cancel.

For each of 16 independent heldout sites, calculate per-event
clock-model A−B logscore gap over all 82 original dates. Bound
the unknown detector-normalizer effect by exact 65-bisection
fractional-ratio extrema for six civil original 4-hour blocks,
with an independent q interval for each station×branch. Datewise
extrema summed over 82 dates are deliberately CONSERVATIVE
OUTER bounds because the actual q is shared across 41
dates within one branch (not new independently varying q per day).

Count heldout physical sites whose q-robust lower score gap >0.
Exact Binomial(16,.5) one-sided test, with Bonferroni .025/4
=.00625 for the four original ordered model pairs, requires
at least 14 of 16 robust-positive sites. Add source simultaneous
CP q noncoverage alpha=.025 for a per-design total union-bound
false-majority certification ≤.05 under IID site sampling,
independent correct reference opportunities, and the true q
temporal source model. Never inspect synthetic oracle q coverage
to decide whether to issue a certification; occasional legitimate
q interval noncoverage already belongs to the error budget.

## Prespecified full synthetic panel and result limits

Two q patterns×three animal time generating truths×20/200
animal detections per camera/date×two reference budgets×four
fixed model comparisons = 96 PAIRED CASES, each with both
site-only and site×branch q calibration results (192 method
arms); eight unique independent source calibration receipts.
The route reports the 48 seasonal-drifting site-only SOURCE-to-
TARGET HOLD cases, every source-reference validity diagnostic,
and all positive/negative site majority outcomes without selecting
the most favorable camera placement, date or clock bin.

The inference target is **P(new independent physical site:
fixed-trained A has larger DETECTED-EVENT score over the same
82 calendar dates than fixed-trained B)>.5**. Not true latent
animal activity, average population logscore, broader ecological
seasonal history, a unique solar zeitgeber, causal photoperiod
memory, or inference to unfamiliar regions.

If real q changes inside a 4-hour block, within a season over
its 41 dates, with passage distance/speed, or across cameras
beyond the two artificial types, additional evidence and
higher-resolution source confidence would be needed.

Original NIE EcoBank v1.1 wildlife events, independently
attested exact original camera operating hours, site-specific
gold-standard reference passages and coordinates are still
unavailable and unopened. Earlier PR245–259 frozen first
outcomes and qualified ODSP routes remain unchanged.
