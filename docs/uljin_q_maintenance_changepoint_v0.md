# What if a camera's detection probability changes abruptly during a season?

**SOURCE-FREE methodology, not original Uljin wildlife observations.**

PR262 compared day/3day/7day/41day independent camera reference
calibration assuming station-branch q was stable or had a verified
smooth within-season Lipschitz bound. Real field cameras have
battery/hardware changes, camera repositioning, vegetation occlusion,
software updates and unknown downtime. Their detector sensitivity
may change abruptly, violating even a conservative q smoothness
bound. This proposal isolates *one independently documented camera
change date*, and never finds a break by searching wildlife detections.

## Original biological observation frame preserved

41 original 2022 mirrored photoperiod date pairs (82 CIVIL dates),
96 original 15-minute CLOCK event bins, 16 training/16 entirely heldout
physical cameras, five original fixed candidate clock/noon/solar/
mean-anchor/season timing mechanisms and four precommitted model pairs.
All artificial animal events and q reference observations remain
source-free. Actual EcoBank v1.1 station GPS, real animal events,
source camera operation logs or maintenance dates have NOT been read.

Freeze two camera q truths:
- **station-branch-stable**: original independent per-camera×season
  ×6 original civil 4-hour block q from the PR260 seasonally
  heterogeneous synthetic world, but no within-season hardware step.
- **externally-logged-maintenance-step** at original within-branch
  matched-pair index j=20: before step q=q_before; after q=.4+.2*q_before
  at each original camera×branch×4-hour civil clock cell. The logged
  break is ASSUMED known independently before any animal event
  inspection. All 41 date positions are retained. This is a
  constructed camera q shift, not an observed vegetation mechanism.

## Three reference source approaches, identical opportunity costs

For EACH camera site×rising/falling season branch×one of six original
CIVIL 4-hour blocks:
1. **1-day groups**: n true independent gold-standard passage references
   to EACH of the 41 dates.
2. **7-day groups UNADJUSTED**: original consecutive 7-day groups
   (last group shortened), with group reference success target the
   group mean q. If a true step occurs within the original 14..20
   seven-day group, source CP can legitimately cover that GROUP
   MEAN but cannot certify individual DAYS; all step-world
   unadjusted results HOLD.
3. **7-day groups SPLIT at independently known maintenance step**:
   intersect any group crossing j20 with j<20 and j>=20.
   Within every resulting group detector q is constant in BOTH
   predeclared q worlds, so source q confidence transfers to
   each original member date. Break dates are never chosen to
   maximize model log score or significance.

T=16 independent heldout cameras×2 original photoperiod branches
×6 original CIVIL four-hour detector-q blocks×41 original days×
n_day independent known TRUE reference animal opportunities,
with n_day=32 or 128. Totals T=251904 or 1007616.
These are opportunity-count budgets, NOT labor hours.

Every source reference opportunity INDEPENDENTLY chooses a date
UNIFORMLY among its own predeclared group dates, then samples a
focal-camera success Bernoulli(q_site,branch,day,clock).
That construction makes reference successes genuinely IID
Bernoulli(group mean q) even when the original group crosses a
maintenance step. CP simultaneous source noncoverage alpha_q=.025
(Bonferroni across every group×site×branch×clock cell) is valid for
source group mean. A correct source CI for the mean is not
automatically a confidence interval for daily target q.

A method can only issue q-robust forecast site-majority inference
when its group q is independently attested CONSTANT over dates.
Any q confidence lower bound zero triggers HOLD without pseudo-counts.
The comparison uses the SAME fitted training-only time models and
SAME original 96 clock event bins. Original event q cancels from
the fixed trained A-B logscore ratio, leaving the source-q-normalizer
uncertainty over the shared physical station/day q. Per-date
fractional-linear q bounds form a conservative OUTER site score
confidence envelope; q within a true maintenance segment is shared
across dates, but the conservative algorithm allows independent
nuisance extrema by date.

## Fixed exact site inference and source science limitation

Sixteen physically independent heldout camera sites are the
Bernoulli-sign units (not 82 dates or events). Count K whose
worst-case A-B site-normalized score lower bound is positive.
Exact one-sided Binomial(16,.5) with Bonferroni over FOUR
prior ordered predictor pairs allocates alpha_site=.025/4=.00625,
and requires K>=14 robustly positive sites. Joint source q
CP alpha=.025 plus exact four-comparison site alpha=.025 yields
per original selected source design false certification bound <=.05
under correct iid cameras, independent reference true-passage
gold labels, fixed training and accurate independent maintenance
logging. Source q synthetic oracle coverage NEVER gates the test;
any legitimate noncoverage probability is paid by calibration alpha.

All 2 camera q truths×2 matched reference budgets×3 animal-time
generators×2 per-station/date event counts×4 original model
comparisons =96 PAIRED cases with each of 3 external source
methods = **288** results and 12 separate external reference
calibration receipts. No post-outcome changepoint, event-window,
clock phase, camera or test threshold search is permitted.

This validation cannot prove a natural clock, solar zeitgeber,
endogenous photoperiod memory, true encounter activity or new
station population mean score superiority; it only checks
fixed-trained recorded-event predictor majority under an
explicitly verified source detector time scope. External
NIE EcoBank data are still unverified/unopened, and all earlier
qualified ODSP routes remain unchanged.
