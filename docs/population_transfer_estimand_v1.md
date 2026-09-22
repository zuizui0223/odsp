# Population transfer estimand v1

## Purpose

The population summary answers a different question from ODSP's all-groups
simultaneous certification.

For adjacent information levels `C_(k-1) -> C_k`, let `delta_gk` be the
realized held-out score gain in independent group `g`. The population estimand is

```text
mu_k = mean_g(delta_gk)
```

with one equal-weight contribution per independent group.

The scientific question is therefore:

> Across the population of groups represented by the study, is adding this
> information expected to improve held-out predictive score?

It is not the stronger question:

> Is the gain simultaneously positive in every observed group?

## Reported quantities

For every adjacent information step, `odsp.population_transfer` reports:

- equal-weight mean group gain;
- percentile bootstrap interval for that mean;
- fraction of observed groups with gain above the declared tolerance;
- a lower bound for that positive fraction;
- between-group standard deviation;
- a normal-theory prediction interval for a new group, explicitly labelled with
  its distributional assumption;
- empirical 10th, 50th and 90th percentiles.

If no higher-level population cluster is declared, groups are the resampling
units and the positive-fraction lower bound is Wilson's score bound.

If `columns.population_cluster` is declared, complete clusters are resampled
and the positive-fraction lower bound also comes from the cluster bootstrap.
With few population clusters this uncertainty estimate can be unstable; the
receipt records that limitation rather than silently treating within-cluster
groups as independent.

## Non-skippable population ceiling

A population-supported ceiling advances only through consecutive steps whose
mean-gain interval lies entirely above `gain_tolerance`.

A positive later step cannot skip an uncertain or nonpositive earlier step.

## Relationship to existing certification

The existing familywise group-by-step certification is unchanged. Its
`certified_transfer_ceiling` remains the conservative endpoint requiring
simultaneous support across all independent groups.

The population summary does not replace or weaken that calculation. It changes
the estimand from the minimum-group/sign-unanimity target to the population of
group-level gains.

Receipts therefore retain both:

```text
certified_result
population_result
```

The two answers may legitimately differ.

## Claim boundary

Population transfer v1 is a descriptive secondary summary. It does not create a
new familywise confirmatory claim, does not propagate upstream learner-refit
uncertainty, and does not infer whether groups or population clusters were
scientifically sampled at random.

The contract accepts those scientific design declarations but cannot verify
them empirically.

No BCa, bootstrap-t, max-t, hierarchical random-effects model, or Bayesian
prevalence layer is introduced here. The purpose of this module is to change the
estimand, not add another interval family.
