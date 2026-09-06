# One-call forecast assessment

`odsp.forecast_assessment.assess_state_forecast` composes existing ODSP forecast-trust layers on one validation target.

Required validation inputs are the conditional and marginal held-out log densities, coverage indicator, independent group labels, dependence-block labels and prediction-region sizes. The same rows are routed through the point/groupwise coverage audit and the joint bias × block-uncertainty audit.

Optional layers are explicit:

- `weight_scenarios`: caller-supplied complete validation weights for sampling-weight sensitivity;
- `bounded_gamma`: deterministic bounded-reweighting stress audit;
- `radius_search_upper_gamma`: certified joint robustness radius search;
- `novelty_train_X` + `novelty_query_X`: environmental novelty and strict-extrapolation diagnostics;
- `selection`: an existing model-comparison result containing the candidate name.

Omitted layers are reported as `not_audited`. The wrapper does not silently invent sampling weights, fit a detection model, infer a true bias process or produce a scalar confidence score.

The returned `ForecastAssessmentResult` contains the raw component audits and a `ForecastTrustDossierV2`. Validation blockers, sensitivity warnings, deployment warnings and selection status therefore remain separate. In particular, a strict-extrapolation warning does not rewrite a previously admitted validation result, and a sampling-weight sensitivity warning does not become a retrospective validation failure.

The joint robustness radius is opt-in because it can require many repeated block-bootstrap stress audits. A finite radius is a sensitivity bracket relative to the declared block definition and reweighting envelope, not a probability of correctness.
