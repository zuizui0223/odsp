from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_t_v2_method_contract_is_prospective_and_non_refit():
    contract = json.loads(
        (ROOT / "ODSP_SIMULTANEOUS_GROUP_BOOTSTRAP_T_V2_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["schema_version"] == 2
    assert contract["contract_id"] == "odsp-simultaneous-group-bootstrap-t-v2"
    estimator = contract["estimator"]
    assert "recompute" in estimator["replicate_standard_error"]
    assert "se_star" in estimator["max_t_statistic"]
    boundary = contract["scientific_boundaries"]
    assert boundary["upstream_model_refit_uncertainty_included"] is False
    assert boundary["refit_ensemble_treated_as_independent_sample"] is False
    assert boundary["frozen_endpoint_rerun"] is False
    assert boundary["frozen_terminal_reclassification"] is False
