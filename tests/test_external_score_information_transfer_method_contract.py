from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_score_method_contract_keeps_modelling_outside_odsp():
    contract = json.loads(
        (ROOT / "ODSP_EXTERNAL_SCORE_INFORMATION_TRANSFER_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["schema_version"] == 1
    assert contract["command"] == "odsp transfer --contract ENDPOINT.json"
    assert "learner kind" in contract["forbidden_contract_roles"]
    assert "learner hyperparameters" in contract["forbidden_contract_roles"]
    assert contract["score_rules"]["orientation"] == "higher_is_better"
    assert contract["score_rules"]["same_heldout_rows_across_levels"] is True
    assert contract["confirmatory_rules"]["filtration_frozen_before_outcome_scoring"] is True
    assert contract["scientific_boundaries"]["upstream_model_fitted_by_odsp"] is False
    assert contract["scientific_boundaries"]["upstream_model_refit_uncertainty_included"] is False
    assert contract["scientific_boundaries"]["chain_decomposition_claimed_as_novel"] is False
