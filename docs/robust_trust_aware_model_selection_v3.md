# Robust trust-aware forecast selection v3

This layer extends ODSP trust-aware model comparison by requiring uncertainty-supported transferability, not only positive point gains.

A candidate must pass three separate gates on untouched validation data:

1. every independent group has positive conditional-minus-marginal log-density gain;
2. every group has empirical coverage within the declared tolerance;
3. every group's block-bootstrap lower confidence bound on gain is above zero.

Only candidates passing all three gates enter the Pareto comparison. Pooled gain, pooled coverage, sharpness or a positive point estimate cannot rescue a failed or uncertain group.

The Pareto axes remain separate: higher mean held-out gain, higher minimum group bootstrap lower bound, lower worst-group coverage error and smaller mean prediction-region size. No aggregate confidence score is formed.

Use scientifically defensible blocks such as independent days, bouts, visits, deployments or sampling units. If too few blocks are available, robust transferability is `unavailable` rather than inferred from row count.

This is a predictive model-selection audit. It does not identify biological mechanism, provide an exact finite-sample bootstrap theorem, repair a poor block definition, remove observation bias or guarantee future distribution-shift performance.
