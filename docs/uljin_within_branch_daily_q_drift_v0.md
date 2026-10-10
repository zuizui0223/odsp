# How much WITHIN-season detector drift can a solar-vs-clock prediction tolerate?

**Source-free post-PR260 method; real Uljin ungulate observations remain unavailable.**

The previous PR260 exactly calibrated q at each of 16 independent
heldout physical stations × rising/falling photoperiod branch ×
six original civil four-hour time blocks. But q was assumed
CONSTANT through each branch's 41 dates. That is a much stronger
claim than station-specific camera geometry: vegetation, weather,
motion-trigger sensitivity and hardware can change across dates.

## A valid source q mean need not be a valid target day q

Take the same IID physical camera type assignments and 32×2×6
station/photoperiod/clock q values as the branch-shifted q
world in PR260. Two new source-free daily truths:

- amp=0: genuinely stationary within each photoperiod branch.
  Exactly reuse PR260 first synthetic event and independent q
  reference RNG, trained predictions and 16 heldout sites, and
  REPLAY its 13/48 certified case result at the externally
  stipulated eps=0 limit.
- amp=.35: a cosine drift across the originally ordered 41
  rising/falling matched calendar pairs. For each physical
  station s, branch b, original civil four-hour block g and
  within-branch pair index j=0..40,

    q_s,b,g,j = qmean_s,b,g
        + .35 min(qmean_s,b,g,1-qmean_s,b,g)
          cos[2π(j+.5)/41 + gπ/6 + site_type_s π/3].

  The cosine averages EXACTLY 0 over 41 j, so reference qmean
  really is the correct branch mean; q_day remains (0,1).

For EACH independent gold-standard q reference passage at the
same station×branch×civil 4hour group, independently choose
ONE date uniformly across its 41 frozen dates, then independently
draw the camera detection Bernoulli(q_day). The observed reference
trigger is thus *genuinely iid Bernoulli(qmean)* after marginalizing
over the independently chosen date. Clopper–Pearson 192-cell joint
alpha_q=.025 is CORRECT for **qmean**, even in the daily drift
world—but does not directly measure the daily target q.

## External q drift attestation before animal observations

An independently attested bound of

    |q_site,day,block / qmean_site,branch,block − 1| <= eps

for EVERY original site×date×4hour cell, plus the SIMULTANEOUS
source CP confidence interval [L,U] for qmean, guarantees

    qday ∈ [max(0,L(1−eps)), min(1,U(1+eps))].

This is the ONLY meaning of robust q uncertainty here.
The external relative drift cap eps is NOT a statistically
estimated confidence interval and does not arise from the
animal event timing records. If eps itself is statistically
estimated, a SEPARATE coverage error budget is essential.

Four predeclared eps values are 0/.10/.20/.35. In amp=.35 world,
ONLY eps=.35 is guaranteed by the pre-frozen structural bound
(absolute cosine≤1 and min(q,1−q)/q≤1); eps<.35 is
HOLD_EXTERNAL_DAILY_DRIFT_CAP_NOT_ATTESTED in ALL cases,
regardless of favorable model score, CP source coverage,
or an accidentally small realized q oscillation. In amp=0
world, all four eps values are valid but progressively
conservative. This admission is dictated by PREDECLARED
external bound construction, never by looking at the synthetic
true q's realized confidence coverage.

## Same clock bins, site-majority and error budget

Fix the original 41 sunrise/sunset matched photoperiod date
pairs, all 82 dates, original 96 local civil 15min animal
observation bins, preexisting five clock/noon/sunrise-phase/
mean-anchor/branch-phase families, and 16 training/16 distinct
heldout physical sites. Do not rebin observations by model.

For each fixed trained ordered A/B pair, original physical site
s has detected-event per-site average score

    D_s(q) = Σ_{dates,k} y_s,date,k log(m_A/m_B)/N_s
      − Σ_{date} N_s,date log[(m_A,date·q_s,date) /
                               (m_B,date·q_s,date)]/N_s.

The per-event q cancels ONLY when both models receive the
SAME physical site/date/civil-clock q. Optimize the ratio
over the externally attested daily q boxes via original
65-bisection fractional-linear extrema for six 4-hour clock
groups, independently for each date. This is a CONSERVATIVE
OUTER set: the allowed q boxes across dates are not required
to arise from a single cosine trajectory or one branch mean.
No sharp joint seasonal profile is claimed.

Count the physical sites with a strictly positive q-robust
LOWER site score; exact one-sided Binomial(16,.5) majority
at alpha=.025/4=.00625 requires K>=14 robust sites. Source
192-cell independent CP qmean familywise alpha=.025; four
precommitted site majority comparisons joint alpha=.025.
A per-design false-majority certification bound ≤.05 follows
by union bound ONLY when source q reference labels, IID
physical heldout sites, event model, and **independently
attested external eps cap** are all truly valid.

The synthetic true q confidence-coverage outcome is an
ORACLE AUDIT only—NEVER a reason to compute or suppress
a statistical decision. Source q CP noncoverage is already
paid for in the .025 budget.

Two q drift amplitude worlds × four eps values × two
source reference budgets (38400,153600 independent known
passages) × three synthetic animal timing truths × two
event count levels 20/200 × four fixed model pairs =
**384 source-free records**. No post-outcome search of
better subwindows, stations, eps or season hypotheses.

This remains a fixed-model **new IID physical site majority
prediction** estimand, NOT the mean logscore, organism
internal circadian phase, true latent wildlife arrival rate,
temperature history, causal sunlight use or photoperiod memory.

Actual EcoBank camera animal events, independent operation
hours, reference-labeled true passages, original protected
station GPS and true daily q histories remain unopened.
All previously qualified ODSP processes and earlier
preregistered result ledgers remain unchanged.
