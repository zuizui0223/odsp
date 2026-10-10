# The camera may be calibrated correctly in the pooled source and still be wrong for each physical station

**Source-free new methods route; NOT an empirical Uljin ungulate analysis.
New prospective contract frozen after PR #258 first results.**

## Why this matters ecologically

A camera trap's ability to register a known true animal passage can
change with vegetation clutter, distance, movement direction, camera
height, trigger settings and hardware. PR #258 obtained
detector-calibrated 96 civil 15-minute site-majority predictions, but
assumed the SAME detector q time pattern for every physical site on a
date. That is different from assuming **sites themselves are iid**.

This route draws 32 physical camera sites independently, giving each
one of two persistent 6-block civil-clock q patterns. The same
original 41 matched astronomy date pairs, all 82 days, all 96 clock
15-minute event bins, and 16 training/16 completely heldout sites
remain fixed. Site q is deliberately constant across all original
dates and within original 4-hour CLOCK blocks, to isolate spatial
heterogeneity from previous source-time-resolution failure.

The two artificial camera worlds are a homogeneous negative
control (both camera types q=[.62,.66,.57,.60,.64,.67]) and
a heterogeneous world:
  A [.95,.85,.35,.32,.60,.90]
  B [.30,.43,.90,.91,.73,.35].

Each physical site type is drawn iid with probability 1/2 and all
sites independently generate their recorded animal clock-time
events from an original frozen civil CLOCK, SOLAR PHASE or
SEASONALLY BRANCHED phase model times their site-specific q.

## Compare two VALID sources with different target scopes

**Pooled external reference.** For EACH independent gold-standard
reference opportunity and each of six civil four-hour blocks,
independently draw a source camera type A/B with probability 1/2,
then independently draw focal camera response with corresponding
q. Its trigger success is **genuinely iid Bernoulli((qA+qB)/2)**,
even in the heterogeneous world. Clopper-Pearson two-sided
Bonferroni six-cell simultaneous q intervals (alpha_q=.025)
are therefore statistically valid for this source *population
mixture*. But they do NOT necessarily cover q at any individual
sampled heldout physical station when A and B differ. All
24 such pooled source-to-site majority tests are predeclared
HOLD, independently of favorable site counts or synthetic oracle
coverage checks. The source calibration itself has not failed.

**Site-specific external reference.** Each of the SIX civil
four-hour clock q cells is independently calibrated for EACH of
the 16 actual heldout physical camera sites from its own
correctly labeled independent true passage opportunities (96
simultaneous CP cells, alpha_q=.025). The reference q is stationary
within each site across the original 82 days in this artificial
truth. These q confidence bounds target the correct site q.

Both methods spend EXACTLY the same total external independent
gold-standard true passage opportunities:
T=38400: pooled 6×6400 vs site 16×6×400.
T=153600: pooled 6×25600 vs site 16×6×1600.

No claim is made that these are the same human staffing or
camera deployment expenses. Pooling may be far more precisely
estimated but can have the WRONG per-camera target.

## Fixed-trained common-clock score and conservative 16-site test

Train all five original clock/noon/sunrise/average/season
candidate model peak parameters once using 16 training
physical sites. Every synthetic animal observation is recorded
in the SAME original 96 civil 15-minute clock bins. Do not
reclassify animal events separately for each model.

For a heldout site s, a competing forecast A/B has the exact
per-event clock-bin score gap at TRUE camera q_s:

  D_s(q_s) = Σ_d Σ_k y_sdk log[a_dk/b_dk] / N_s
             - Σ_d N_sd log[(Σ_k a_dk q_sk)/
                               (Σ_k b_dk q_sk)]/N_s.

Use the SAME q_s for both models in each original clock cell.
To bound a site-specific score under its external q_s Bonferroni
interval, the model's event log ratios cancel q_s; use the
existing 65-iteration fractional-linear optimizer over the
six civil clock four-hour groups. For computational simplicity,
the q interval is extremized SEPARATELY for each of the 82
dates, although the station true q_s is held CONSTANT across
dates: this is an **OUTER CONSERVATIVE** bound, not the exact
sharp joint-date optimization. If its lower score is positive,
the TRUE score is positive on the joint q-coverage event.

Then count among 16 fully independent heldout physical sites
the number K with positive q-ROBUST lower score. Exact
one-sided Binomial(16,.5) with alpha_site=.025/4=.00625
requires >=14 robust sites to support the probability that A
scores higher at a NEW independent site more often than B.
Source q familywise alpha_q=.025 plus all four independent
site-majority hypothesis tests alpha_site_total=.025 means
union-bound false-majority certification <=.05 under the
sampling model, correct reference labels, heldout site iid,
fixed training forecasts and correctly qualified source q.

**IMPORTANT:** Synthetic truth q-coverage is never inspected to
select inferential output. Source noncoverage risk is already
budgeted. The pooled heterogeneous source is known structurally
nontransportable to each station and is held independent of
whether its individual q happened to fall inside the reference
bands by chance.

## Scope and limitations

There are 2 camera q worlds×3 animal time worlds×2 event counts
per site-date×2 equal independent reference budgets×2 q reference
methods×4 fixed model pairs = **96** cases, plus eight unique
external q calibration receipts. All are source-free. The target
of the 16-site test is a positive **MAJORITY** of independent
new sites' fixed model predictive scores over the same 82 dates.
It is NOT a population mean score test, a test of intrinsic
circadian clocks or endogenous photoperiod memory, nor proof of
true latent animal passage/active-state differences.

Real cameras may also change q BY DATE, season, time of night,
near/far animal distance, angle, velocity, and weather. If so,
even the six-cell site-level calibration over 82 days would be
a wrong source temporal target unless those changes were
independently measured or bounded. Four q test comparisons
are familywise accounted PER original predeclared scenario,
not across 96 source-free simulator cells.

Authentic EcoBank v1.1 ungulate event records, source operation
and downtime, station-level camera q references, independently
labeled animal passages and protected camera GPS are not
materialized. All earlier frozen ODSP qualified inference routes
and PR257/258 first results remain unchanged.
