from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json")


def test_independent_directional_lattice_contract_freezes_four_edge_scope():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-independent-directional-lattice-4edge-v1"
    assert payload["alternative"] == "greater"
    assert payload["qualified_information_block_counts"] == [2]
    assert payload["qualified_edge_counts"] == [4]
    assert payload["three_block_twelve_edge_lattice_qualified"] is False
    assert payload["validation_groups_independent"] is True
    assert payload["upstream_refit_uncertainty_included"] is False
    assert payload["untouched_external_validation_included"] is False


def test_independent_directional_lattice_contract_inherits_existing_four_contrast_calibration():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inheritance = payload["qualification_inheritance"]
    assert inheritance["new_null_simulation_claim"] is False
    assert inheritance["source_contract"] == "ODSP_ONE_SIDED_POSITIVE_BOOTSTRAP_T_CONTRACT.json"
    assert inheritance["required_contrast_count"] == 4
    assert inheritance["same_inference_core"] == (
        "odsp.positive_transfer_bootstrap_t.certify_independent_group_positive_transfer_v2"
    )


def test_lattice_rescues_are_prohibited():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["governance"]["best_path_can_override_failed_edge"] is False
    assert payload["governance"]["shapley_can_override_failed_edge"] is False
    assert payload["governance"]["total_gain_can_override_failed_edge"] is False
    assert payload["governance"]["historical_empirical_endpoint_reclassified"] is False
