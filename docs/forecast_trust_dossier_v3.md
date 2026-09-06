# Forecast trust dossier v3

V3 preserves every validated section of ForecastTrustDossier v2 and adds a separate **joint robustness radius** layer.

The radius answers a narrow question: starting from the joint block-bootstrap × bounded-reweighting audit at `gamma=1`, how far can the row-reweighting envelope be widened before the baseline robust transfer-sign category is no longer certified?

The dossier reports:

- radius status;
- last passing `certified_gamma`;
- first failing `break_gamma` when finite;
- numerical boundary bracket width;
- the corresponding certified multiplier-ratio lower bound;
- limiting independent groups.

A finite radius creates a robustness warning but does **not** retroactively rewrite an already completed validation at another declared gamma. For example, a model can be admitted under a prespecified gamma=1.5 validation and separately show a certified joint radius near 1.73. The decision trace then reads `admitted_with_warnings` rather than `blocked`.

Likewise, a deployment `strict_extrapolation` warning remains separate from a finite-radius warning. Blocked or unavailable validation cannot be rescued by a large radius, in-domain deployment, or model-selection status.

The radius is not a confidence score, probability of correctness, biological threshold, detection probability, or causal-confounding parameter. It is a sensitivity radius relative to the declared blocks, bootstrap design, and bounded row-reweighting family.
