# How many days of independent camera-reference observations should be pooled?

**New source-free method after PR #261: original wildlife events, camera
operation and independent reference passages were NOT accessed.**

The parent route showed that season-branch mean detector q can be
perfectly calibrated yet too uncertain to attribute observed
animal clock/solar/season score differences when q may fluctuate
daily. This route isolates a practical ecological monitoring
tradeoff: finer q source time resolution preserves daily target
validity but spends scarce gold-standard true-passage labels
across many cells; coarser temporal pooling improves binomial
precision but risks hiding real changing detection.

## Four exactly equal external passage budgets

Original frame: 41 matched rising/falling daylength pairs, 82 date
records, 96 original civil 15minute animal detection bins per date,
32 independently simulated camera stations with 16 training/16
heldout physical sites, same five fixed-trained clock/noon/
sunrise/sunset phase/average anchor/season models.

At EACH heldout station×season branch×original six CIVIL 4h
detector clock blocks, partition the fixed ORIGINAL 41 within-branch
dates into consecutive NONOVERLAPPING groups of length at most
m=1,3,7,41. Tail groups have actual length <m when needed.
For each true reference passage opportunity in group g,
independently select date uniformly among that group's actual
original calendar dates, then sample focal camera success
Bernoulli(q_date). The resulting individual trigger successes
are **genuinely independent identically distributed Bernoulli
with p=MEAN q over that date group**, even when actual q differs
among its constituent days. Therefore exact Clopper–Pearson
intervals apply to the **group MEAN q**, without the invalid
Poisson-binomial assumption from fixing unequal detection
probabilities at deterministic numbers of each day.

Per original date q source passage labels:
n_daily=32 or 128. Source total reference cost for EVERY m:
T=16 heldout physical sites × 2 branches ×6 original civil clock
4h q blocks ×41 original date-pair indices×n_daily,
thus **251,904 or 1,007,616 independently known TRUE passages**.
No claim that this equals labor, camera placement or travel costs.

Simultaneous q calibration uses α_q=.025 over all site×branch×
date-group×clock source q cells (7872 cells when m=1; 2688
when m=3; 1152 when m=7; 192 when m=41). Individual two-sided
Clopper–Pearson intervals use the exact tail
α_q/(2×number of source cells). All pooled-source intervals
can be correct for their group MEAN even when their values do
NOT equal each day q.

## Exact time-scale transport with separately warranted smoothness

Assume a truthfully independently attested absolute per-adjacent-
within-branch-day q change limit L:

    |q_(j+1)-q_j| <= L

at each station, photoperiod branch and original 4h clock block.
For a consecutive group containing d original within-branch
dates, the absolute distance between any member q_j and its
group mean qbar_g is bounded by

    L * (d-1)/2

since the maximum *average* index distance from any group day
is (d-1)/2. Thus when the source group mean qbar_g is in its
simultaneous CP interval [CP_lower,CP_upper], every group's
individual day detector q falls in

    [max(0,CP_lower-L(d-1)/2),
     min(1,CP_upper+L(d-1)/2)].

The smoothness bound is a **structural EXTERNAL assumption in
these artificial worlds**, not an empirically measured L, and
is NOT inferred from the focal wildlife detection timestamps.
If the bound is statistically ESTIMATED, its coverage error
needs an additional explicit familywise alpha budget before
a 5% ecological certification claim is valid.

Two pre-frozen worlds replay the parent detector:
(1) within-branch STATIONARY camera q, amplitude0, L=0;
(2) within-branch COSINE camera drift, amplitude.35,
a predeclared conservative absolute Lipschitz L=.03/day,
derived only from the synthetic generator's `.35 *min(q,1-q)*
2sin(pi/41) <= .0268` upper bound, without inspecting
animal detections. The cosine zero-average property ensures
original season-branch q source mean matches the parent's q.

## Fixed-clock forecasting and independent-site test

For any one source q calibration/time scale, the five original
models are fit ONCE on 16 training sites using independent
synthetic detected-event records in the SAME original 96 civil
clock response bins. Hold all learned peak parameters fixed
across 4 time source q resolutions. For each of four original
ordered pairwise model comparisons A−B, optimize the identical
physically unknown camera q into both model normalizers.
Original per-event q cancels; exact 65-bisection fractional
extrema over six CIVIL 4hour groups are performed per date.
Summing datewise feasible ranges allows q more freedom than
the actual smooth trajectory, so resulting sitewise bounds
are **CONSERVATIVE OUTER**, not sharp over 82 dates.

Among 16 independent physical heldout sites, count q-robust
strict-positive lower A−B per-site detected-event score gap.
One-sided exact Binomial(16,.5) site-majority at alpha=.00625
after four-pair Bonferroni requires ≥14 robust-positive sites.
Add q source simultaneous familywise noncoverage alpha=.025
and the four site-majority tests' total alpha=.025 for
combined per-preselected-design 0.05 false-majority bound
under correct independent reference opportunities, iid sites,
true external L, fixed training and correct camera operation.

**No gating on synthetic oracle q interval coverage**: it is
a recorded diagnostic only. If a group lower q interval
reaches 0, the source-specific robust test FAILS CLOSED with
HOLD rather than adding pseudo-counts.

Frozen source-free study: 2 camera q temporal truths×2
independent reference budgets×3 animal time truths×2
animal event count levels×4 ordered clock/solar/season model
pairs =96 paired comparisons, each with all four temporal
pooling strategies =**384** scores, plus 16 source CP
calibration receipts. No additional source-independent
animal process uncertainty, site nesting, sensor false-
negative reference error or causal ecological zeitgeber
model is estimated.

## Site-ecological interpretation limits

With actual weather-driven sensor changes, q could vary
within four hours, among animal taxa/body sizes, in
movement speed/distance, with vegetation, or between
particular protected stations. It may not be Lipschitz with
any modest L across maintenance, battery outage or
camera setting changes; source-specific camera timelines
would then need a discrete change-point or missingness
admission route, not a smoothness guess.

The truth of per-day L cannot be inferred from animal
detection event counts without confounding q and animal
passage rates. This is a design exercise for future
independent video/thermal/overlap references, NOT original
EcoBank v1.1 Uljin wildlife observation. Prior
qualified ODSP inference and PR245–261 original frozen
results remain untouched.
