# Does exact CP camera calibration improve real randomized sensitivity?

**Separate source-free methodology route, not animal data.** The prior
Hoeffding calibrated 9,600 synthetic detector/animal draws (PR #248)
and a post-result deterministic CP improvement on representative
rounded calibration outcomes (PR #249). The latter is not a
probability or power comparison because true binomial successes
vary. We now prospectively freeze an ACTUAL paired random calibration
comparison, acknowledging parent outcomes were already seen.

## Identical samples and source lineage

Reuse the original 4 truths × 4 independent reference sample sizes
50/200/1000/5000 PER each of 4 q cells × 600 repeat worlds, **exactly**
the original NumPy SeedSequence mapping and the sequence: four
binomial calibration draws followed by conditional noncentral
hypergeometric animal counts. Both CP and Hoeffding receive the
very SAME independent reference successes and observed animal 2×2
table. Not merely similar populations: paired sample identities.

The first Hoeffding 16×600 scenario coverage, rejection rate,
HOLD incidence, and median detector-OR upper bounds **MUST match**
the original PR #248 first result ledger to numerical precision.
Any difference ends in failure. The original calendar, prior source
records, registered training/refit ODSP inference are untouched.

## Mathematical guarantees

Both methods build independent four-cell detector confidence bands
with familywise calibration miscoverage ≤.025:
- Hoeffding intervals from PR #248.
- Exact CP per-cell two-sided binomial intervals
  `[Beta^{-1}(.025/8; s,n-s+1), Beta^{-1}(1-.025/8; s+1,n-s)]`,
  with 0 and 1 at endpoints for s=0,n.

These four-cell bands feed the same detector interaction bound B.
If a lower denominator q interval reaches zero, report HOLD.
The same right-tail conditional exact Fisher test uses
alpha_animal=.025, yielding combined false certification ≤.05 by
union bound under independent labeled references, verified device
hours and Poisson animal encounter counts.

## Reporting and interpretation

For EACH 16 frozen scenario cells, report CP and Hoeffding
certification frequencies and paired Monte Carlo SE, numbers of
CP-only and Hoeffding-only selections, joint empirical q coverage,
zero-lower HOLD and median B. This tests expected efficiency, not
just representative rounded outcomes.

The n=50/200/1000/5000 calibration budgets include four separate
reference cells: 1,000 PER q cell means 4,000 independent known
passage opportunities total, not a study-wide sample size. This
power simulation is CONDITIONAL on fixed synthetic season and
phase-bin animal count margins and one physical study site/date pair.
It does not account for calibration camera false negatives in
the independent reference sensor, animal-specific trajectories,
individual detection dependence, seasonally varying vegetation
occlusion, many sites/taxa, sampling eligibility, or multiple
testing of unplanned time windows.

If CP is genuinely better, quantify the paired advantage and
uncertainty and still state that both methods are established
statistical intervals with known validity guarantees; there
is no new general theorem. If no advantage, report it
unchanged, without post-outcome scenario or threshold tuning.

The ecological scientific question remains: after checking
clock/noon/solar phase/season models on common temporal
observations, do calibrated station-specific detector
sensitivity and effort permit an inference about latent
encounter timing? No original EcoBank animal counts, physical
station metadata or original independent operation logs are
available yet; this experiment makes no new empirical claim.
