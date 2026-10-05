# Training-process directional transfer v5: qualified two-term CV3 jackknife IUT

V5 is the **qualified internal training-process method** for the current narrow
ODSP scope: one-sided positive transfer, independent validation groups, and an
ordered filtration with exactly two contrasts. It is a separate inferential route
from fixed-set all-refit robustness.

The estimand is the mean held-out directional gain over a prospectively frozen
training-resampling-and-fitting process, conditional on the frozen empirical
training source, and over the declared validation population. It is not the
minimum over refits, the probability that a future individual refit passes, or
uncertainty from sampling a new ecological training dataset.

## Component inference

For every group × ordered information contrast, V5 uses delete-one
training-refit and delete-one validation-block jackknife components:

    V_R = (R-1)/R * sum_r (theta_minus_r - theta_hat)^2
    V_B = (B-1)/B * sum_b (theta_minus_b - theta_hat)^2

The component variance is the existing two-term two-way cluster-jackknife
estimator

    V_CV3(2) = V_R + V_B.

No intersection variance is subtracted. The one-sided lower bound uses a
Student-t critical value with

    df = min(R, B) - 1.

The global non-skippable claim is an intersection-union test: every required
group × contrast component must reject its one-sided null. The component bounds
are not simultaneous confidence bounds and cannot be reused for arbitrary
post-hoc cellwise discovery.

## Why v5 rather than its predecessors

All candidates were frozen before their own qualification results were opened.

- v1 crossed max-t controlled the null but failed the frozen terminal-power gate.
- v2 studentized IUT restored most power but failed the component-size gate.
- v3 centered pigeonhole IUT passed the power gate but remained liberal in
  several small-cluster null worlds.
- v4 CV3max IUT passed the power gate but narrowly missed the frozen null gate
  (maximum component rate 0.065 versus 0.063784).
- v5 CV3(2) IUT passed both frozen gates.

The failed versions remain frozen failures; v5 does not retroactively rescue or
reclassify them.

## Prospective qualification

Across the six frozen base null scenarios, the largest component false-positive
rate was **0.056**, below the predeclared Monte Carlo acceptance limit
**0.06378404875209022**.

Across the six frozen power scenarios, the smallest terminal power at a
five-oracle-SE positive shift was **0.859**, above the predeclared minimum
**0.80**.

A separately frozen adversarial support envelope also passed all five scenarios:
strong right skew, contaminated normal tails, discrete Rademacher effects,
16-fold validation-block weight imbalance, and heteroskedastic interaction
noise. The largest component false-positive rate in that panel was **0.058**.

The canonical receipts are
`TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json` and
`TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json`.

## Primary surface and provenance

The raw numerical function
`certify_training_process_positive_information_cv3two_iut_v5` is not, by
itself, the primary confirmatory interface.

The canonical internal surface is

`odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5`.

It verifies the content-locked training-process manifest, exact managed refit
schedule, generated model artifacts, full frozen training-source-frame
separation from validation rows, and the qualified implementation/runtime
identity before running the numerical core.

Existing fixed-set refit routes and historical empirical endpoints are unchanged.

## Untouched external continuation

The qualified process-specific external surface is

`odsp.training_process_untouched_external_v5.run_untouched_external_training_process_v5`.

That route has its own pre-outcome freeze and managed external scoring chain.
The active route evidence registry is v6
(`ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json`) with content lock v4
(`ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V4.json`).

The process route remains unqualified for contrast_count=4, paired/shared-block
validation, complete lattices, claims about all possible refits, original
training-source-population generalization, and external distribution-shift
robustness.
