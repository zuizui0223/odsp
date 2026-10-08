# Four-model season-parity audit: why the apparent winter solar advantage is not an astronomical mechanism

**Status: post-outcome algebraic audit of ONE ORIGINAL exploratory source.**
No additional camera records, taxa, sites, predictions, refits, time-zone
assumptions or significance tests are introduced here. The original
Rhode Island v2 first result (run 37747931559, first JSON SHA256
5d4bca0efc079ec3ae58d1062d4c1fb4c0b6476b64d56eead6d79e39ae83edab)
continues to say **EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE** for the
predeclared both-seasons-positive solar transfer hypothesis.

## The question missed by the first pooled model comparison

In the original experiment four *training-only* categorical models
predicted the same heldout local civil-clock detection-time bin Y:

- C: species-specific civil-clock six-bin probability, pooled over seasons.
- S: species-specific solar-phase six-bin probability mapped *back* into
  exactly the same heldout civil-clock bin Y, pooled over seasons.
- CS: species × season-specific civil-clock probability.
- SS: species × season-specific solar-phase probability, mapped back
  into the same heldout civil-clock bins.

S and C share per-species histogram capacity. CS and SS likewise share
per-species-and-season histogram capacity. The conditioned comparison
SS versus CS is therefore a better parity check for the specific
claim that an astronomical reference represents the *seasonal*
organization of detected daily time more effectively.

All models use the original training years, heldout whole-site split,
source rows, Jeffreys pseudocount and mean same-site-weighted log-score
target. These quantities were already stored in the FIRST result.

## Exact algebra, no new fitting or stochastic assumptions

Let l_M be the original per-observation log probability under model M.
Then, for any exact common weighting of the original heldout scores:

    mean(l_SS - l_CS)
      = mean(l_S - l_C)
        + mean(l_SS - l_S)
        - mean(l_CS - l_C).

Define A = pooled solar minus clock, B = extra solar gain from providing
season, D = extra clock gain from providing season.

The conditioned contrast is A+B-D. It is an algebraic identity, not
a model result selected after looking for favorable subsets.

| Contrast in heldout nats | Winter | Summer |
|---|---:|---:|
| Pooled solar - pooled clock, A | +0.02745846 | -0.03257429 |
| Solar×season - solar, B | -0.00701874 | +0.03357291 |
| Clock×season - clock, D | +0.05909665 | +0.03918206 |
| **Solar×season - clock×season, A+B-D** | **-0.03865692** | **-0.03818343** |
| Clock's advantage from seasonal conditioning relative to solar, D-B | +0.06611538 | +0.00560915 |

The **point means favor the season-conditioned clock model in BOTH
seasons**, even though the pooled solar model beat pooled clock in
winter. The winter flip is arithmetically explained by the fact that
letting the clock model vary with season added 0.05910 nats while
letting the solar-phase model vary with season actually lost
0.00702 nats for winter heldout detections.

This is not proof that the sun is uninformative: the original
correct-sun versus wrong-season-sun comparator also favored the
correct sun in winter and summer. Such an effect can coexist with
clock models performing better when granted the same seasonal
information, because a wrong-season sun is a deliberately poor
astronomical comparator, not a capacity-matched clock model.

## What this changes in the ecological interpretation

The earlier shorthand "winter mammals track sunlight but summer
mammals follow the clock" was TOO STRONG. The more defensible
statement for this dataset is:

> In this species-targeted camera survey, a solar-coordinate
> histogram improves over a season-POOLED clock histogram for
> winter detected times, but that advantage vanishes and reverses
> after BOTH models are allowed the same season label. Solar-phase
> reference is not uniquely supported as the mechanism of winter
> organization by these predictions.

This says nothing definitive about whether real animals adjust to
sunrise, sunset or photoperiod. A fixed two-anchor equinoctial solar
mapping may be an imperfect basis compared with an average-anchor
model; meanwhile the clock×season comparator can absorb the actual
seasonal shift. Camera placement, operational time, detectability,
temperature, prey, human disturbance and habitat can all matter.

It remains scientifically possible that some taxa truly follow
sunrise/sunset. The current pooled parity comparison is a model
criticism, NOT a causal test and NOT a universal rejection of solar
entrainment.


## Additional model-class confound: same six bins does NOT mean same clock-space flexibility

The four-model identity is exact, but the biological interpretation
requires another substantial qualification. The solar-phase histogram
is not merely an alternative *label* for the same six clock bins.

Let p be an arbitrary six-bin solar-phase probability distribution,
M(site,date) the 6×6 piecewise-linear phase-to-clock transport matrix,
and q the implied heldout clock-bin probabilities:

    q_j = sum_k p_k M_{kj},       p_k >=0, sum_k p_k=1.

Thus the set of solar-model predictions for a fixed site/date is the
CONVEX HULL of M's six rows, which may be a strict subset of the
six-dimensional clock probability simplex. For every clock category:

    q_j <= max_k M_{kj}.

A direct season-conditioned CLOCK histogram does not have this
particular restriction. Therefore CS and SS have the same nominal
histogram parameter count but generally **unequal expressivity in
the common civil-clock prediction space**. The adjusted clock
advantage can reflect not only ecological timing organization
but also the solar-phase histogram's forced probability mixing.

For an illustrative location 41.5° N, 71.5° W (not an observed
camera site) on the northern winter and summer solstices, the
original astronomical model yields approximately:

| Date | Maximum possible solar-projected probability in 16–20 clock bin |
|---|---:|
| 2022-12-21 | about 0.60 |
| 2022-06-21 | about 0.42 |

A direct clock histogram may put arbitrarily close to 1.0
there. At ideal sunrise 06:00/sunset 18:00, M is the identity
and the restriction disappears. These are DETERMINISTIC model
geometry demonstrations and not estimates of animal behavior.

The new code
odsp/ri_solar_phase_projection_capacity_v0.py
and tests/test_ri_solar_phase_projection_capacity_v0.py
prove the above convex-hull bound and verify it numerically for
illustrative RI solar geometry, without accessing any wildlife data.

**Important interpretation revision:** SS-CS < 0 in both seasons is
a descriptive prediction-performance finding for these FIXED model
families. It does not imply mammals use civil time rather than
sunlight, and it is not a clean equal-expressivity test of the
photoperiod mechanism. A future prospective head-to-head comparison
should use models that produce densities on the same continuous
clock domain (with a correct change-of-variables Jacobian), or
explicitly match effective binned representational capacity.


## The uncertainty-identification boundary

The first artifact provides site-bootstrap lower bounds for some
originally reported components but DOES NOT preserve the joint
site×contrast bootstrap draws or site-level scores needed to
estimate uncertainty for the NEW combined contrast A+B-D.
One may NOT create a nominal confidence interval for A+B-D by
adding or subtracting the separate component interval endpoints.

**Therefore, the new result is a sign and magnitude of descriptive
heldout means, NOT a statistically significant season-conditioned
clock superiority claim.**

The first original observational source is public and was already
parsed before this post-result study. The result lacks independent
site sampling-probability attestation and original camera-timezone
verification; it compares photographic detections, not unbiased
animal activity. Taxon/site-matched analyses in PR #227 address
composition support for the simpler pooled S-C contrast but do not
automatically validate the conditioned SS-CS contrast.

## Correct next discriminating experiment

One new untouched source should freeze *before* access:

1. physically independent camera operational times and known
   timestamp zone / daylight-saving-time logic;
2. site/taxon sampling design and both environmental seasons;
3. **capacity-matched same-outcome C vs S, CS vs SS** with a
   prespecified primary parity comparison;
4. direct or independently measured temperature, detection effort,
   light, prey or predator variables if mechanism is claimed;
5. an independent field/year/site holdout and covariance-respecting
   cluster-level uncertainty.

Do not relabel these post-result descriptive contrasts as a
confirmatory discovery. The earlier ODSP empirical terminals and
qualified process-mean/source-process routes are unchanged.

## Reproducibility

- Input original action: https://github.com/zuizui0223/odsp/actions/runs/37747931559
- Original JSON exact SHA256:
  5d4bca0efc079ec3ae58d1062d4c1fb4c0b6476b64d56eead6d79e39ae83edab
- Input is retrieved from the exact ORIGINAL artifact, not Zenodo.
- New code: odsp/ri_solar_v2_four_model_season_parity_v0.py
- Contract: RI_SOLAR_V2_FOUR_MODEL_SEASON_PARITY_AUDIT_CONTRACT.json
- All code refuses to qualify new ecological model significance,
  runs no bootstrap, and retains the negative original conclusion.
