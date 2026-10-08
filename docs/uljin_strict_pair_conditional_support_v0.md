# Strict conditional phase-shape tests need repeat detections: a source-free feasibility screen

**Status:** analytic synthetic support scenarios only; this is NOT a claim that
the actual camera dataset contains these numbers, or that the existing ODSP
pooled conditional Poisson regression cannot estimate a season-shape effect.

A novel within-station × paired-date phase-label permutation diagnostic would
condition on BOTH total events and branch totals for that site/date-pair to
eliminate arbitrary baseline phase activity and any branch-wide event-rate
shift. That strong nuisance control is attractive but needs overlap in the
two branches. With zero detections in one branch, no nontrivial reassignment
of phase labels is possible while conditioning on exact branch totals.

There are 82 published stations × 41 preselected mirror pairs = 3,362
possible station×paired-day groups. Jeon & Lim (2026) report 4,623
**year-wide** independent events for four ungulates:
goral 2,317; water deer 814; roe deer 808; wild boar 684
(DOI 10.3897/BDJ.14.e191556). This does NOT assert that these
events occur on the originally selected 82 2022 calendar days.

We model a purely hypothetical mechanism: N full-year events independently
enter the selected paired calendar with probability f and, conditional on
entry, go uniformly to one of 3,362 physical-site/date-pair groups and
independently to one of the two branches with probability 1/2.

The exact fixed-N expectation of groups with at least one event in each
branch is:

  G * [1 - 2 (1 - f/(2G))^N + (1 - f/G)^N],

for G=3362. Fractions f=1, 0.25, 0.10 are frozen illustrative
retention scenarios, NOT estimated camera coverage. Per-pair baseline
variation, seasonality, taxa non-detection, spatial clustering and actual
operation logs are NOT simulated. The formula is not a distribution-free
upper bound; event concentration may change the expected number of pairs.

Even having detections on both branches is **necessary but not sufficient**
for nontrivial within-pair six-bin label shuffling, since events may occupy
only one phase category. Scientific interpretation:

* Strict per-pair branch-count conditioning buys robustness to arbitrary
  nuisance branch intensity but discards many sparse site-date-pair groups.
* Original common-beta conditional Poisson can use one-sided count cells
  (provided both branch exposures are independently recorded positive).
  These support expectations must not be sold as power bounds for that model.
* Partial pooling across days/sites could recover precision but adds
  exchangeability/heterogeneity assumptions that require diagnostics and
  untouched validation.

Before any ecological claim, actual original operation logs and event
date/time source fields must be authenticated, site×pair×taxon support
tabulated without outcome-driven selection, and physical site/region
dependence respected. This entire module reads only the frozen public
aggregates and no source outcome row. Existing ODSP qualification untouched.
