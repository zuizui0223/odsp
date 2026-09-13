from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_endpoint_cli_contract_keeps_design_choices_explicit():
    contract = json.loads(
        (ROOT / "N2_ENDPOINT_CONTRACT_CLI_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "n2-executable-endpoint-contract-cli-v1"
    assert contract["command"] == "odsp run --contract ENDPOINT.json"
    boundary = contract["scientific_boundaries"]
    assert boundary["column_roles_inferred"] is False
    assert boundary["independence_unit_inferred"] is False
    assert boundary["folds_inferred"] is False
    assert boundary["strata_inferred"] is False
    assert boundary["baseline_inferred"] is False
    assert boundary["training_weight_policy_inferred"] is False
    assert boundary["learner_selected_from_outcomes"] is False
    assert boundary["frozen_empirical_endpoint_rerun"] is False
    assert boundary["frozen_terminal_reclassification"] is False
    assert boundary["receipt_is_a_claim_of_causality"] is False
