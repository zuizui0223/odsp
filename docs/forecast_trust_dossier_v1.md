# Forecast trust dossier

`ForecastTrustDossier` is a high-level interpretability layer over existing ODSP trust evidence. It does **not** create a new confidence score.

The dossier keeps three domains separate:

1. **Validation gates** — point transfer, group-wise empirical coverage, and block-bootstrap transfer uncertainty.
2. **Deployment warnings** — in-domain, environmental novelty, or strict extrapolation for new forecast rows.
3. **Model-selection status** — recommended, Pareto member, robust-trusted but dominated, not robust-trusted, or not compared.

Example:

```python
from odsp.forecast_trust_dossier import build_forecast_trust_dossier

report = build_forecast_trust_dossier(
    robust_candidate,
    deployment_novelty_rows=query_novelty,
    selection=robust_selection,
)
```

A robustly validated model remains historically admitted even if a new query row is a strict extrapolation; the dossier adds a deployment warning instead of rewriting validation history. Conversely, an in-domain query cannot rescue a model whose transfer interval crosses zero or whose group-wise coverage fails.

`blocking_reasons` explain validation failures such as `transfer_uncertain`, `transfer_unavailable`, `transfer_nonpositive`, `point_transfer_failure`, or `groupwise_coverage_failure`. Deployment warnings are stored separately and never enter the validation blocker list.

The dossier is therefore presentation and decision-traceability infrastructure over already-computed evidence. It is not new statistical evidence, novelty is not an error probability, and no status implies biological mechanism or guaranteed future performance under distribution shift.
