# Where should independent sensor time go: camera q or animal passage mix?

**Status:** distinct source-free pre-result synthetic research design,
following already published PR #251–#253 outcomes. This does NOT
recover actual original Uljin events or prove an endogenous zeitgeber.

## Why this is a different question

In PR #251 and #252, external calibration of **camera q** in near/far
distance strata and **animal opportunity composition w** across
rising/falling photoperiod and early/late solar bins protected a
within-site animal encounter-rate test from a 3.44898-fold
artificial detector-only seasonal contrast. PR #253 then asked how
tightly distance composition must be bounded, assuming its external
limit δ was CERTAIN.

The next field question is one of **resource allocation**: with
fixed independent verified passage opportunities, should a researcher
calibrate q more intensively or measure w more intensively? Both
have finite-sample uncertainty and both consume reference labor.

## Same external measurement budgets, unequal cell types

8 cells of external q = two distance strata (near/far) × four
rising/falling×solar early/late bins. In each, n_q independently
verified true animal passage opportunities are labeled with focal
camera success/failure. Four OTHER independent reference cells
supply n_w passage opportunities per season×phase, with
near-versus-far labels regardless of whether the focal camera
triggered. Total reference opportunity count:

    budget = 8*n_q + 4*n_w.

Every budget B=2400/6000/12000/24000 is compared with the following
three FULLY FROZEN allocations, using exactly that opportunity cost:

| B | Equal per cell (n_q,n_w) | q-heavy | w-heavy |
|---:|---:|---:|---:|
| 2400 | (200,200) | (250,100) | (100,400) |
| 6000 | (500,500) | (625,250) | (250,1000) |
| 12000 | (1000,1000) | (1250,500) | (500,2000) |
| 24000 | (2000,2000) | (2500,1000) | (1000,4000) |

These are equal COUNTS of gold-standard independently labeled passage
opportunities, not proven equal labor, total cost or placement access.
Neither scheme is an automatic optimal field program.

## Statistical coverage accounting

Use exact two-sided Clopper–Pearson with Bonferroni across 8 q cells,
alpha_q=.0125; across 4 w cells, alpha_w=.0125. A site/date-pair
preselected TWO-BIN exact one-sided Fisher test uses alpha_test=.025.
The union bound on false latent-season certification is
.0125+.0125+.025=.05 under independent true passage labels,
representative q/w sampling, an independently logged exposure
crossproduct, and conditional independent Poisson event counts.
Without these assumptions or with false reference labels, even
perfect binomial confidence intervals cannot identify true wildlife
encounter timing.

Monte Carlo case matrix: four frozen ecology truth worlds (no shift,
detector-only shift via target distance mix, genuine seasonal encounter
OR2 with stable distance mix, genuine encounter OR2 with confounded
distance mix) × 4 budgets × 3 allocations × 200 independent worlds =
9600 artificial q/w/animal experiments. Animal season and early/late
phase totals remain artificially fixed. All original source-free
negative and positive results reported. Compare robust positive
certification fraction, Monte Carlo SE, 12-cell simultaneous coverage,
zero-lower-q HOLD rate, and median finite conservative detector OR B.
A known-perfect-q-and-w ORACLE reference is reported for context only
and is NOT a fair equal-cost procedure.

## How this connects to clock time, solar time and seasons

All 41 original astronomy mirror DATE pairs remain frozen. The
early/late solar-phase two-bin target is a SMALL inference subtask,
not full-day clock-vs-solar model selection. The original fair
five-candidate full clock-bin prediction experiment PR #245 and its
misspecification findings PR #246 remain unchanged.

If the observer later wants to test multiple civil CLOCK versus SOLAR
phase windows on the same dataset, this q/w-calibrated one-sided test
cannot be reused without a new prespecified multiplicity/error
allocation and common civil-response clock-binning. Such an extension
would require authentic event timestamps, source camera-hour effort,
and q/w calibration in the targeted windows. Do not claim independent
photoperiod-memory or zeitgeber causality based only on seasonal
detector timing.

Source status is unchanged: genuine EcoBank original wildlife rows,
hardware deployment/downtime and independent known-passages/near-far
reference opportunities have NOT been authenticated or inspected.
No protected coordinates or qualified ODSP process routes altered.
