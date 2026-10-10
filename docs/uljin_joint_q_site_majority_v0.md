# Does a clock-vs-solar predictor win at a new physical site?

**Separate source-free route AFTER PR257's first calibration outcome.**
The parent PR257 simultaneously calibrated 82×6 or 82×96 source
detector q cells using independent reference passage opportunities
and bounded the heldout **sample mean** score order on identical
96 original civil bins. That is NOT a population-level predictive
confidence statement about independent NEW physical sites, even when
a 97.5% q calibration interval covers all true detector probabilities.

## Precisely different ecological inferential target

Condition on the original 16 training physical sites, fixed-trained
five time-coordinate model shapes/peak estimates, original 41 matched
photoperiod date pairs (82 original dates), species/detector model
and correctly specified temporal q calibration structure.

For one new independent physical camera site drawn from the same
site population, let D_s(q) be the **observed-event conditional**
clock 96-bin per-event predictive logscore gap of model A minus B,
summed over the same 82 days, for the TRUE common q. Define
p_site=P_new_site[D_s(q)>0]. Test one-sided

  H0: p_site ≤ 1/2 versus p_site > 1/2.

This is NOT a test that E[D_s(q)]>0, not transport to a new season or
geographic region, not a sign of endogenous photoperiod memory, and
not a latent animal encounter rate. Independence applies to the
16 whole physical heldout sites, NOT 16×82 dates, animal event
detections, reference camera q trials or 96 quarter-hour bins.

## Exact detector q and independent-site joint error budgeting

For each of four ORIGINAL preregistered pairwise model comparisons:
1. Take independent gold-reference Clopper–Pearson q intervals from
   PR257 at joint source-error alpha_q=.025 over all original
   82×6 or 82×96 cells. They must describe actual 15min q; pooled
   4h q source intervals are inadmissible when true detector q
   varies within the coarse clock block.
2. **DO NOT inspect if the true q is inside the confidence bands
   to decide whether to run the test.** Actual true q is unknown.
   The simulated true q coverage is a post-result AUDIT ONLY,
   not an operational admission gate or per-replicate guarantee.
3. Fix the A and B forecasts trained exclusively on 16 training
   physical sites. For every heldout site s, calculate the
   normalized 96clock-bin fixed-event logscore difference and
   its SHARP minimum D_s^-(q) over the **SAME q** shared by both
   forecasts and all heldout sites on each date. The event-specific
   q cancels; date-specific shared normalization ratios are
   optimized with the existing PR256 65-iteration fractional
   extrema, using 96 original bins or six genuine constant-q
   original civil 4-hour blocks.
4. Let K=sum_s 1{D_s^->0}. When all actual true q belong to the
   independent CP box, K is at most the number of sites whose
   true-q forecast gap is positive. Even under a new-site
   Bernoulli majority null p_site≤.5, the exact one-sided
   Binomial(16,.5) upper tail is a valid conservative site test
   on that calibration-coverage event.
5. Calibrate multiple pairwise checks: alpha_site_total=.025,
   alpha_site_each=.025/4=.00625; together with independent
   q-reference calibration alpha_q=.025 yields a 0.05
   false-certification **per preselected source/population
   design** by union bound, when the site independence and
   reference q sampling assumptions hold.

**Finite-site sharp threshold:** at least **14 of 16** heldout
independent physical sites must have q-robustly positive scores:
P[Binom(16,.5)>=14]=137/65536≈.00209. Thirteen sites are
INSUFFICIENT: P[X>=13]=697/65536≈.01064>.00625. This stringent
requirement is a scientific consequence of asking a genuinely
independent-site predictive question and Bonferroni-correcting
four candidate pairs; 82 calendar days are not 82 independent
animals or sites.

## 192 first diagnostic worlds, no outcome retuning

Replay EXACT parent PR257 artificial independent reference q
calibrations and 16+16 synthetic training/heldout site event data,
at three frozen behavioral truths (clock fixed, solar-phase, seasonal
phase), two event counts (20,200), two camera q patterns (constant
within six 4h civil blocks vs variable inside a block), two external
independent q-reference budgets (251904/1007616) and both
reference q granularities (82×6 vs 82×96), for all four original
paired model hypotheses: 3×2×2×2×2×4=192.

Freeze fail-closed outcomes for 48 invalid coarse q cases under
true within-block variability, and any positive-q-lower-zero case.
Report source q CP coverage of synthetic truth as an ORACLE
diagnostic only; it must NEVER cause a test to be run or skipped.
No post-hoc favorable model selection, no treating the 192
synthetic designs as one simultaneous inferential family, no
site-level mean-score confidence interval made from a site sign
test. The original 41 astronomy pairs, all previous per-PR
first result ledgers, parent ODSP refit/external evidence and
pretrained model likelihoods are untouched.

## Why this still does NOT prove Uljin animal activity adjustment

The genuine EcoBank v1.1 ungulate event rows, source-independent
hour-accurate original camera operation and truly independent
reference q passage labels have not been materialized. The model
also assumes a q time course shared across 16 heldout physical
cameras on the same date, independent sites from one site
population, and correctly specified source detector time
granularity. Site differences in vegetation, motion velocity,
animal size, camera height, true q, temporal autocorrelation
and taxon availability can violate these assumptions. A winning
solar or seasonal predictive class is not a unique biological
zeitgeber or endogenous seasonal photoperiod memory.

The method provides a different, explicit, auditable validation
route, not a reclassification of previous primary ODSP results.
