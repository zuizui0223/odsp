# Forecast Assessment v2

`odsp.forecast_assessment_v2.assess_state_forecast_v2` preserves the complete v1 one-call assessment and optionally adds evidence from three later ODSP audits on the same held-out target:

- simultaneous familywise group certification;
- model-refit transfer uncertainty;
- block-definition sensitivity.

The v1 result is returned unchanged as `base_assessment`. The new `extended_certification` is separate evidence: it does not rewrite the historical validation status, calibration result, novelty warning, robustness radius, or selection result.

Formal extended certification is based only on requested simultaneous-familywise and model-refit layers. If every requested formal layer is robust-generalizing, the extended certification is `certified`; uncertainty/failure gives `not_certified`; insufficient evidence gives `unavailable`; and omitting both gives `not_audited`.

Block-definition sensitivity is a design warning. A result can remain base-validation `admitted` while reporting `block_definition_sensitive`; ODSP does not infer the biologically correct block scale.

When a refit gain matrix is supplied, the declared reference member must match the base assessment's row-wise conditional-minus-marginal gain within the declared numerical tolerance (default `1e-12`). This guards against accidentally combining refit evidence from a different validation target or model with the current assessment.

Alternative block definitions are supplied in addition to the base `blocks`. The name `primary` is reserved for the base definition and cannot be replaced by an alternative.

No scalar aggregate confidence score is emitted. Extended certification is an explicit decision trace over caller-declared validation groups, blocks, refit ensembles and sensitivity designs; it is not a probability of correctness or a causal/mechanistic claim.
