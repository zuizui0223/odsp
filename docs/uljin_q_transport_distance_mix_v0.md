# Does detector calibration transport across animal approach distance?

**Synthetic, post-PR250 methodological route. No EcoBank wildlife observations.**

## A problem even exact Clopper–Pearson intervals cannot solve

An external detector calibration can have correctly computed, very
narrow binomial intervals and still be WRONG for the wildlife passage
population if the opportunity conditions differ. Let a reference setup
show 50% near and 50% far independent passages. Camera detection
probability is q_near=.9 and q_far=.3 in ALL 4 frozen
rising/falling × early/late solar-phase cells. The calibrated
reference pooled effective q is .6 in each cell, detector OR=1.

Now suppose the actual independently defined animal passage mix near
is (.2,.8,.8,.2) over rising-early, rising-late, falling-early,
falling-late. The true detector q is (.42,.78,.78,.42), giving detector
season×phase OR = (.78/.42)^2 ≈ 3.45, even though EVERY
distance-stratum-specific camera q is CONSTANT in time, and the
animal encounter-rate OR may be exactly 1. This can falsely look like
a photoperiod-dependent animal activity adjustment.

This is selection/transport bias of the **opportunity distribution**,
not a malfunction of CP confidence interval mathematics, or a
previously unknown general causal inference theorem. A perfectly
estimated q for the 50/50 reference population remains nonportable
when near/far mix changes.

## A more defensible calibrated analysis

Externally measure (not infer from focal camera detections):
- 8 independent binomial reference detector-q values =
  2 independently specified passage-distance strata × 4
  season×phase cells;
- 4 independent binomial target opportunity near-distance MIX
  proportions in the corresponding 4 cells.

Use exact two-sided CP with Bonferroni for both families:
alpha_q=.0125/8 q cells (two tails alpha_q/16 per cell);
alpha_mix=.0125/4 mixture cells (two tails alpha_mix/8).
Animal site-pair preselected two-bin noncentral Fisher spends
alpha_animal=.025. The union-bound total = .05 **only when the
external reference opportunities and target-mix labels are
independent correct samples under the declared model**.

For each season×phase cell, transform q and near-weight confidence
intervals to a lower/upper effective target q:
q_eff=w*q_near+(1-w)*q_far.
The lower bound minimizes this expression over q and w endpoint
corners, the upper maximizes it. Then obtain the target detector
OR upper bound

  B = upper(q_Fearly)*upper(q_Rlate) /
      [lower(q_Rearly)*lower(q_Flate)].

HOLD if any denominator lower limit is zero. Otherwise exact
site-conditioned Fisher animal test at α=.025 and noncentrality B,
with independently known equal camera operating hours in these
synthetic examples. The naive pooled reference detector intervals
describe the WRONG population; comparing their animal test p-values
to the transport-corrected ones is an intentionally invalid-baseline
diagnostic, not a new calibrated 5% comparison.

## Frozen synthetic evaluation

Four truth worlds:
1. no season×phase or distance composition change;
2. animal encounter OR=1, but near-distance mix (.2,.8,.8,.2)
   induces false positive detector OR≈3.45;
3. reverse mix (.8,.2,.2,.8), inducing detector OR≈0.29;
4. true animal encounter OR=2 with the same confounded distance mix.

q_near=.9, q_far=.3 and reference mix 50/50 in every world.
Synthetic reference q calibration successes, independent target
distance-mix opportunities, and conditioned animal Poisson events
are drawn with frozen SeedSequence identities. 4 worlds × 3 n levels
(50,200,1000 per cell) × 200 draws = 2,400 source-free simulations.
For each n, 8n reference-q passage opportunities plus 4n independent
target-mix opportunities are required in the CORRECTED design; the
pooled baseline uses 8n q opportunities but has no target-mix data.
This is not an equal-total-cost comparison or a real field power
estimate.

## Ecological admission

A true q calibration needs **all passages**, including those
missed by the focal camera, and independent near/far/trajectory
annotations. Animal distance cannot be inferred solely from images
that exist only when the focal camera fired. For real work, expand
beyond two bins and near/far strata if angle, movement speed, group
size, vegetation and detector hardware interact, with independently
observed exposure and full original camera site/date roster. Two
Uljin regions and restricted site coordinates do not support
unconditional regional population claims. The original EcoBank
v1.1 source and real reference passages have NOT been accessed.
Existing ODSP primary inference and frozen clock/astronomy model
comparisons remain unmodified.
