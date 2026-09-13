from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_STATE_SPACE_GENERALITY_CONTRACT.json"


def test_state_space_generality_contract_freezes_common_estimand_and_geometries() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == "n2-state-space-generality-v1"
    assert contract["common_estimand"] == "E_heldout[log q_train(A|X) - log q0_train(A)]"
    spaces = [row["id"] for row in contract["validated_state_spaces"]]
    assert spaces == [
        "finite_discrete",
        "continuous_scalar",
        "circular_scalar",
        "continuous_x_circular_joint",
    ]
    implementation = contract["implementation"]
    assert implementation["generic_score_module"] == "odsp/distributional_gain.py"
    assert implementation["benchmark_module"] == "odsp/state_space_generality_benchmark.py"
    assert implementation["expected_check_count"] == 10
    assert implementation["absolute_tolerance"] == 2e-10


def test_state_space_generality_contract_does_not_reopen_frozen_empirical_chain() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = contract["scientific_boundaries"]
    assert boundary["empirical_endpoint_rerun"] is False
    assert boundary["frozen_decision_rule_modified"] is False
    assert boundary["bop_terminal_category_modified"] is False
    assert boundary["mh_terminal_category_modified"] is False
    assert boundary["n2_to_n3_promoted"] is False
    assert boundary["state_space_generality_is_biological_generality"] is False
    assert boundary["state_space_generality_implies_axis_representativeness"] is False
    assert boundary["state_space_generality_implies_causality"] is False
    assert boundary["state_space_generality_implies_transferability"] is False


def test_generic_layer_leaves_design_choices_explicit() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = contract["scientific_boundaries"]
    assert boundary["learner_is_fixed_by_generic_core"] is False
    assert boundary["comparator_is_fixed_by_generic_core"] is False
    assert boundary["independence_unit_is_fixed_by_generic_core"] is False
    assert "same reference measure" in contract["reference_measure_requirement"]
