from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json"


def test_v6_contract_freezes_distributional_scope() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == "n2-mee-state-prediction-manuscript-v6"
    assert contract["base_manuscript"] == "n2-mee-state-prediction-manuscript-v5"
    assert contract["common_prediction_target"] == (
        "q(A|X) on a scientifically declared ecological state space"
    )
    assert contract["common_primary_transfer_score"] == (
        "G_j = E_heldout,j[log q_train(A|X) - log q0_train(A)]"
    )
    assert contract["validated_state_space_geometries"] == [
        "finite_discrete",
        "continuous_scalar",
        "circular_scalar",
        "continuous_x_circular_joint",
    ]


def test_v6_contract_preserves_closed_empirical_endpoints() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    empirical = contract["empirical_endpoint_preservation"]
    assert empirical["mh_terminal_category"] == "empirical_state_prediction_unavailable"
    assert empirical["bop_terminal_category"] == "empirical_state_prediction_mixed"
    assert empirical["bop_positive_log_gain_individuals"] == 27
    assert empirical["bop_eligible_individuals"] == 30
    assert empirical["bop_post_outcome_species_decomposition_preserved"] is True
    assert empirical["empirical_endpoint_rerun"] is False
    assert empirical["primary_comparator_changed"] is False
    assert empirical["terminal_reclassification_allowed"] is False


def test_v6_contract_does_not_overgeneralize_discrete_information_quantities() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = contract["claim_boundary"]
    assert boundary["state_space_generality_is_biological_generality"] is False
    assert boundary["continuous_differential_entropy_claimed_coordinate_invariant"] is False
    assert boundary["effective_state_count_exp_entropy_claimed_for_continuous_states"] is False
    assert boundary["finite_discrete_brier_and_top1_claimed_universal"] is False
    assert boundary["joint_coupling_gain_interpreted_causally"] is False
    assert boundary["joint_coupling_gain_interpreted_as_symmetric_dependence"] is False
    assert boundary["learner_fixed_by_framework"] is False
    assert boundary["comparator_fixed_by_framework"] is False
    assert boundary["independence_unit_fixed_by_framework"] is False
    assert boundary["n2_to_n3_promoted"] is False
