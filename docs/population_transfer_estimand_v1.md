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

For the total first-to-final gain and for every adjacent information step, `odsp.population_transfer` reports:

- equal-weight mean group gain;
- an uncertainty interval for that mean, with the method determined by the declared resampling structure;
- fraction of observed groups with gain above the declared tolerance;
- a lower bound for that positive fraction;
- between-group standard deviation;
- a normal-theory prediction interval for a new group, explicitly labelled with
  its distributional assumption;
- empirical 10th, 50th and 90th percentiles.

If no higher-level population cluster is declared, groups are the resampling
units and the positive-fraction lower bound is Wilson's score bound.

If `columns.population_cluster` is declared and at least 10 independent
clusters are represented, complete clusters are resampled and the mean interval
uses the cluster percentile bootstrap.

For fewer than 10 declared population clusters, ODSP does **not** use the
cluster percentile bootstrap. The equal-group mean is retained as the estimand,
but its uncertainty is estimated with a CR1 cluster-robust standard error and a
Student t critical value with `G - 1` degrees of freedom. This avoids a
pathology of very small cluster bootstraps, where only a few distinct resamples
exist and percentile intervals can become spuriously narrow.

The positive-group fraction has no analogous reliable cluster-bootstrap lower
bound at very small `G`. In that case the cluster lower bound is treated as
unavailable and the receipt reports the ordinary group-level Wilson lower bound
only as a **descriptive fallback**. It must not be described as a cluster-robust
superpopulation confidence bound.

With only one declared population cluster, clustered mean uncertainty is
unidentified and the summary fails closed.

## Total transfer versus stepwise attribution

The total first-to-final gain is reported directly because it answers whether the
complete added information representation improves prediction over the declared
baseline. It is not blocked by an intermediate decomposition step.

The stepwise ceiling is a separate attribution question: whether every declared
increment on the path is itself supported at the population-mean level.

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
prevalence layer is introduced here. The CR1+t fallback is a narrow repair for
the finite-support failure of few-cluster percentile bootstrap, not a new
certification family. The purpose of this module remains to report the population
estimand without allowing uncertainty machinery to create artificial certainty.
