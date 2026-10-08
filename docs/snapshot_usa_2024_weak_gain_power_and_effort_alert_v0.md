# Snapshot USA 2024: public-source semantic stop and weak-gain power ceiling

**Post-freeze scientific warning:** this analysis used only the PUBLIC
DATA PAPER (Rooney et al. 2026, Global Ecology and Biogeography,
DOI 10.1111/geb.70229, p. 11 of 28) and frozen method formulas.
No 2024 deployment CSV site row or species/time sequence record was
opened to derive the findings on this page.

## Two source constraints that matter more than the image count

1. The paper states that **77% of 184 camera arrays were Forest**.
   Treating 77% as a whole-number rounded percentage means the true
   forest share is at least 76.5%, so there are at most
   floor(184 * (1 - 0.765)) = **43 nonforest arrays**.
   Grassland is a subset of nonforest. Thus under the frozen
   forest-vs-grassland design, the grassland group cannot supply
   more than 43 *array-level* primary units from this 2024 census.
   The actual count may be considerably smaller. This is not a
   direct read of the deployment file.

2. The paper's Table 3 note specifically says reported camera
   trap-nights were computed from the first/last IMAGE timestamps
   per deployment. Thus Survey_Nights is partially derived from
   image-observation timing, even though it sits in the deployment
   metadata file. The frozen v0 screen may count sites filtered
   by Survey_Nights as a **retrospective source-structure diagnostic**,
   but must not call its selection strictly outcome-independent.
   It does not download sequences, but that is not enough to prove
   every metadata covariate was generated independently of images.

Neither finding licenses post-freeze changes to the original
ODSP_SNAPSHOT_USA_2024_DEPLOYMENT_SCREEN_V0_CONTRACT.json. A
future test using prospectively recorded installation/retrieval
dates instead of image-derived effort must use a NEW contract
version and a new sampling question. Selection on calendar span
also does not automatically imply an operating-hour effort
denominator.

## Exact upper bound on e-value certification POWER (not a p-value)

The frozen shared-validation e-IUT component test in PR #217 uses
four fixed betting fractions and rejects for a mixture e-value
E_mix greater than 1 / a, with a=0.002.

For a fixed model-refit required component with iid validation
blocks and true mean bounded above by mu, the exact alternative
expected e-value satisfies:

    E[E_mix]
      <= (1/4) sum_{lambda in {.25,.5,.75,1}}
           (1+lambda*(mu-tau)/(tau-L))^B

because the expectation of each factor depends ONLY on the mean;
iid block factors permit their product expectation to factorize.
Here L=-1, gain tolerance tau=0, and B is the independent BLOCK
count. No Gaussian or small-variance approximation is made.

By Markov's inequality:

    P(component certified) <= min(1,a E[E_mix]).

Since each refit succeeds in the IUT only if EVERY required
component certifies, if every future frozen-process model has at
least one mandatory cell with true mean <= mu, its certificate
probability obeys this upper bound u.

For R refits, even with a COMMON validation sample and highly
dependent certifications, E[K]<=R u. So for a certification
decision that requires at least K_min certificates:

    P(K>=K_min) <= min(1,R*u/K_min).

This latter bound needs no certificate independence (just the
fixed-model per-component bound) and is an upper bound on decision
POWER, not a confidence bound for ecological p_success.

## Frozen-design example: q=0.8, R=20, weak mean +0.05

Using the original frozen experimental a=.002, delta=.025,
process alpha=.025, and the original four e-betting fractions:

| Number of iid blocks B in weakest group | Maximum power to certify one weak-mean component |
|---:|---:|
| 12 | 0.293% |
| 20 | 0.383% |
| 42 | 0.848% |
| 43 | 0.881% |
| 50 | 1.153% |

For R=20 and the original target p_success>0.8, K_min=20:
ALL 20 observed refits must certify. If every refit has at least
one required cell of true normalized Brier score gain <=+0.05,
and the grassland validation population is sampled at the array
level, then the public-source maximum B=43 implies a **power
upper bound of about 0.88%** for declaring p_success>0.8.

This is substantially stronger than the earlier *constant-gain
illustration*: it is distribution-free over iid, bounded-below
block-gain distributions of the stated mean. It can rule out
80% decision power *in that conditional weak-effect scenario*
regardless of the within-block noise distribution.

The calculation is reproducible via
odsp/snapshot_usa_2024_weak_gain_power_ceiling_v0.py
and tests/test_snapshot_usa_2024_weak_gain_power_ceiling_v0.py.
These are post-calibration design-theory companions; the
qualified v5 route and v0 experiment are not changed.

### Crucial limits

- **+0.05 is a HYPOTHETICAL normalized Brier-score mean**, not
  an empirical estimate from Snapshot USA. Previously observed
  Serengeti +0.045 LOG-score gains cannot be inserted into
  the Brier model without changing scale.
- Every refit must have at least one weak mandatory cell for the
  uniform refit-certification bound. Refits with very large
  gains on every component need not satisfy this assumption.
- The source-paper 77% is rounded; 43 is an *upper bound on
  possible grassland arrays*, not an observed grassland count.
- Even one camera array might not be an iid validation draw.
  That unverified sampling assumption is explicit.
- The upper bound concerns ONLY the exact frozen betting-mixture
  test. A newly prospectively qualified and better-powered test
  could perform differently.
- It is not a claim that ecological transfer fails or that
  time-of-day niches lack structure.
- No sequence-level dates, animal labels, normalized Brier
  scores or empirical future-refit probability are opened here.

## Practical routing decision

Snapshot USA 2024 remains useful for **descriptive ecology** and
potentially for realistic cross-site prediction comparisons.
However, it is not yet a credible primary demonstration of the
strong stochastic **future-refit success probability >0.8**
claim for small bounded information gains.

Keep the deployment-only v0 structural count route distinct
and record its outcome when GitHub Actions finishes. Whatever
that count is, the iid sampling mechanism, non-image-derived
effort support and power restrictions must be resolved before
opening/qualifying a true external validation route.

Source: Rooney et al. (2026), DOI 10.1111/geb.70229,
page 11, Sections 3.1–3.2 and Table 3 note.
