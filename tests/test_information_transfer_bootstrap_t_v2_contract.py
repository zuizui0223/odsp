from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_information_transfer_bootstrap_t_v2_contract_boundaries():
    contract = json.loads(
        (ROOT / "ODSP_INFORMATION_TRANSFER_BOOTSTRAP_T_V2_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["schema_version"] == 2
    assert contract["contract_id"] == "odsp-information-transfer-bootstrap-t-v2"
    family = contract["family_definition"]
    assert "group x adjacent information step" in family["strict_filtration"]
    assert "group x directed lattice edge" in family["complete_lattice"]
    resampling = contract["resampling"]
    assert "shared across all contrasts" in resampling["within_group"]
    assert "recomputed inside every bootstrap replicate" in resampling["studentizer"]
    boundaries = contract["scientific_boundaries"]
    assert boundaries["validation_sample_uncertainty"] is True
    assert boundaries["upstream_model_refit_uncertainty_included"] is False
    assert boundaries["refit_ensemble_treated_as_probability_sample"] is False
    assert boundaries["frozen_v1_endpoint_rerun"] is False
    assert boundaries["frozen_v1_terminal_reclassification"] is False
