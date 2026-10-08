# Which wrong model selections are actually due to astronomical geometry?

**Synthetic intervention, not an empirical ecological causal estimate.**

V0 (PR #235) demonstrated that clock-based and solar-phase-based six-bin
predictors sometimes disagree even for invariant phase intensity.
Such a disagreement cannot itself be attributed to a date-specific solar
shift: different partitions of a *finite random sample* may disagree even
when neither is systematically biased.

## Frozen synthetic counterfactual and causal scope

For each of the exact same 1,800 synthetic worlds in V0, reuse the entire
site × original date pair × rising/falling branch × event phase roster with
the identical RNG seed. In addition to original clock and phase projections,
create one **branch-neutral clock** projection:

    t_neutral = phase_to_civil(phi, solar geometry of ASCENDING date)

for *both* rising and falling observations in each original pair.

No sample, event density, timestamp sampling order, model coefficient,
training/heldout site assignment or score denominator changes. Only the
falling-branch astronomical phase->clock mapping is replaced, as a synthetic
counterfactual intervention (not a claim about real time travel).

All three representations use the EXACT pre-existing v0 conditional fitter
and its lambda=2 and 41×6 cells/site scoring denominator. For every world,
let A be positive clock gain with original geometry and nonpositive solar
gain; let B be positive branch-neutral clock gain with nonpositive solar
gain. The paired contrast A-B estimates **incremental clock-only model
selection attributable to the original branch-specific solar geometry
relative to the neutralized synthetic control**, conditional on the modeled
point process and frozen decision procedure. Report mean(A-B) and paired
Monte Carlo SE, **even if negative**.

This is not a calibrated hypothesis test, real-animal false-discovery rate
or evidence of photoperiod memory. In particular, it does not estimate
unknown camera detector effort, individual heterogeneity, real station
astronomy or the distribution of actual ungulate activity.

The prior V0 known outputs are preserved in an immutable separate result
ledger. V1 must replay its clock-only fractions and mean gains exactly
before publishing a new counterfactual result. All 9 conditions are kept;
no window search or after-outcome threshold tuning.
