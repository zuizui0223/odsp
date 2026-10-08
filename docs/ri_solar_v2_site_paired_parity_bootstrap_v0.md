# Rhode Island v2 four-model conditional parity — paired-site uncertainty recovery

**Scientific status:** POST-OUTCOME EXPLORATORY, not a new preregistered
positive test. This new method runs against the same fixed public
2018–2023 RI camera ZIP, original v2 parser, training years and
whole-site heldout models. It does not change the initial empirical
decision or any ODSP qualified training/refit inference route.

## Reason for separate follow-up

The first result recorded these three heldout contrasts:

- solar minus clock, both season-POOLED, S-C;
- extra seasonal gain for solar, SS-S;
- extra seasonal gain for clock, CS-C.

The site-weighted season-conditioned model comparison
SS-CS = (S-C)+(SS-S)-(CS-C) is a direct algebraic identity.

Original first-result means give:

| Original heldout seasonal group | Pooled solar - clock | Conditional solar×season - clock×season |
|---|---:|---:|
| Winter | +0.02746 | -0.03866 |
| Summer | -0.03257 | -0.03818 |

The first artifact does not preserve the per-site scores or
joint bootstrap draws needed to estimate uncertainty for the
new combined contrast. Separate confidence limits cannot be
subtracted to make a valid interval.

## Exact physical-site original replay before new result

To address only this covariance gap, the new pipeline must replay
the EXACT first v2 scoring procedure and original bootstrap before
opening the new contrast:

1. Source MD5 pinned to
   c66943e6c2a9aab0abce2a1eba8ce02e;
2. Original literal camera site/station/device/season source schema,
   30-minute detection deduplication, 2018–21 models,
   2022–23 whole-site holdout and training-only species admission;
3. Exactly **19,916 scored events** and **43 physical heldout sites**;
4. Exactly winter +0.02745845931504319, summer
   -0.0325742873706785 as original equal-site seasonal means;
5. Exactly original one-sided 95% physical-site multiplier
   bootstrap lower points: winter +0.017686837094790103,
   summer -0.04153436486877643, with absolute tolerance 1e-10.

If ANY identity fails, stop with UNAVAILABLE. Do not tune source,
solar transform, model, group, weight or confidence method to
rescue a desired sign.

New row-wise season-conditional difference:
log P_solar_season(Y) - log P_clock_season(Y)
= (solar-clock)+(solar_season-solar)-(clock_season-clock).

Within each physical site and season, average events within each
heldout year, then average represented years. Each physical site
gets ONE weight in each seasonal mean. The bootstrap uses the
ORIGINAL 2000 draws, seed 2026100803, and a single positive
Exponential(1) multiplier PER WHOLE SITE, reused across both
seasons and every contrast. This preserves the covariance of
the new adjusted score difference.

The new 2.5% and 97.5% percentile endpoints are explicitly
selected **after seeing the first aggregate result** and are
DESCRIPTIVE sensitivity intervals, not a claim of independent
confirmatory 95% coverage. The site sampling design is not
an iid probability sample of all RI mammal habitats.

## Biological interpretation boundaries

The parity comparison asks whether an astronomical phase
coordinate carries useful predictive organization beyond
what a civil-clock histogram can learn once both models know
the season. It does not determine whether animals literally
respond to photoperiod or whether seasonal camera detection
effort creates apparent timing differences.

Different sunrise/sunset phase parameterizations, independent
camera operational logs, temperature, food supply, predator
pressure and true local animal activity would require a
new prospective scientific design.

The original source was previously exposed in v0/v1/v2, making
this clearly post-outcome exploratory work. The original
both-seasons-positive solar hypothesis stays NOT SUPPORTED.
The current outcome (before first workflow) is **not yet known**.

Frozen design:
RI_SOLAR_V2_SITE_PAIRED_SEASON_PARITY_BOOTSTRAP_CONTRACT.json.


## FIRST OFFICIAL post-outcome covariance recovery: completed

Run: https://github.com/zuizui0223/odsp/actions/runs/37767836871

The original source/model replay passed all hard gates, including the
19,916 original scored detections, 43 original heldout sites,
the original winter and summer pooled solar-versus-clock mean
log gains AND both original one-sided site-bootstrap lower bounds.
Synthetic site-resampling tests also passed.

The subsequently calculated SAME-site paired percentile bootstrap of
the season-conditioned four-model identity gave:

| Season | Mean adjusted solar minus clock (nats) | Exploratory 2.5%–97.5% paired-site interval |
|---|---:|---:|
| Winter | -0.03865692 | [-0.04826266, -0.02867377] |
| Summer | -0.03818343 | [-0.04656025, -0.02971341] |

Both interval endpoints are negative. This is meaningful internal
evidence that the season-conditioned CLOCK histogram predicts heldout
six-bin camera detection times more effectively under the specified
original site-weighting convention, not just because of an anomalous
single site. This interval remains POST-RESULT EXPLORATORY, and
spatial site-iid assumptions have not been validated. It cannot
be described as independent confirmatory significance or a
robustness proof for a new ecological population.

**Major substantive caveat:** The solar-phase six-bin model is
pushed forward via a 6x6 row-stochastic mixing matrix that can
restrict its representable civil-clock probabilities to a strict
convex hull. A direct clock histogram can be more expressive on
the SAME six-clock-bin target, despite an equal number of
nominal parameters. The paired interval does not distinguish
intrinsic ecological civil-clock organization from this
representation/regularization limitation, let alone seasonal
variation in photographic detection.

The correct new scientific hypothesis for independent validation is
not "winter mammals follow sunlight", but whether solar phase
supplies transportable *additional information* after season and
model class are controlled, with observability/effort independently
measured. The original both-season solar advantage remains NOT
SUPPORTED.

First immutable postoutcome artifact: ID 11546512179;
ZIP sha256:14aed4711e46fac93ffd3a505fb7f479dda970c74d02051c76aae33506a36640.
Machine-readable result ledger:
RI_SOLAR_V2_SITE_PAIRED_PARITY_FIRST_RESULT_LEDGER.json.
