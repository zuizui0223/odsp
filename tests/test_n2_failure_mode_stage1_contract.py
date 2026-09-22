from __future__ import annotations

import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_STRATIFIED_CONTEXT_TRANSFER_FAILURE_MODE_STAGE1_CONTRACT.json"


def _read() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_stage1_contract_is_pre_result_and_failure_mode_first():
    contract = _read()
    assert contract["contract_id"] == "n2-stratified-context-transfer-failure-mode-stage1-v1"
    assert contract["status"] == "pre_result_frozen"
    assert contract["relationship_to_odsp"]["odsp_is_primary_scientific_claim"] is False
    assert contract["relationship_to_odsp"]["new_certification_family_introduced"] is False
    assert contract["relationship_to_odsp"]["lattice_used_in_stage1"] is False
    assert contract["relationship_to_odsp"]["all_group_unanimity_rule_used"] is False


def test_factorial_grid_has_exact_predeclared_size_and_structural_exclusions():
    contract = _read()
    design = contract["factorial_design"]

    factor_names = (
        "layer_effect_scale",
        "within_layer_context_effect",
        "group_count",
        "events_per_group",
        "layer_count",
        "context_layer_correlation",
        "focal_learner_layer_identity",
    )
    levels = [design[name] for name in factor_names]
    eligible = []
    excluded_pairs = set()
    for cell in itertools.product(*levels):
        row = dict(zip(factor_names, cell))
        if row["group_count"] >= 2 * row["layer_count"]:
            eligible.append(row)
        else:
            excluded_pairs.add((row["group_count"], row["layer_count"]))

    assert len(eligible) == 864
    assert design["eligible_factorial_cell_count"] == 864
    assert excluded_pairs == {(5, 4), (5, 10), (12, 10)}
    assert {tuple(x) for x in design["structurally_excluded_group_layer_pairs"]} == excluded_pairs
    assert design["replicates_per_factorial_cell"] == 64\n    assert design["population_interval_bootstrap_draws_per_world"] == 500


def test_bop_calibration_is_predeclared_and_in_realistic_window():
    contract = _read()
    calibration = contract["oracle_targets"]["bop_calibration"]
    observed = calibration["deterministic_oracle_layer_gain_nats_under_balanced_30_group_allocation"]
    lower, upper = calibration["predeclared_realistic_window_nats"]

    assert calibration["anchor_layer_count"] == 4
    assert calibration["anchor_group_count"] == 30
    assert calibration["anchor_layer_effect_scale"] == 2.0
    assert observed == 0.2664659336361246
    assert lower < observed < upper
    assert lower <= 0.27 <= upper
    assert calibration["must_fall_inside_realistic_window_before_stochastic_execution"] is True


def test_primary_inference_uses_group_cv_population_mean_not_unanimity():
    contract = _read()
    rule = contract["population_decision_rule"]
    methods = {row["method_id"]: row for row in contract["evaluation_methods"]}

    assert rule["group_unit"] == "independent simulated group"
    assert rule["group_weight"] == "equal"
    assert rule["confidence_level"] == 0.95
    assert rule["interval"]["switch_threshold_group_count"] == 10
    assert "Student t interval" in rule["interval"]["fewer_than_10_independent_groups"]
    assert "percentile bootstrap" in rule["interval"]["at_least_10_independent_groups"]\n    assert rule["interval"]["factorial_bootstrap_draws"] == 500\n    assert rule["interval"]["confirmatory_anchor_bootstrap_draws"] == 4000
    assert rule["positive_transfer"] == "lower confidence bound > 0"
    assert rule["unanimity_rule_used"] is False

    assert methods["group_cv_pooled_log_gain"]["inferential_role"] == "primary_failure_mode"
    assert methods["group_cv_layer_decomposed_context_gain"]["inferential_role"] == "primary_correction"
    assert methods["random_row_cv_pooled_log_gain"]["inferential_role"] == "diagnostic"
    assert methods["group_cv_auc"]["inferential_role"] == "diagnostic_nonadditive"
    assert methods["group_cv_accuracy"]["inferential_role"] == "diagnostic_nonadditive"


def test_confirmatory_anchors_and_success_rules_are_frozen():
    contract = _read()
    execution = contract["confirmatory_anchor_execution"]
    anchors = {row["anchor_id"]: row for row in execution["anchors"]}
    rules = contract["success_rules"]

    assert execution["replicates_per_anchor"] == 1000
    assert execution["bootstrap_draws_per_population_interval"] == 4000
    assert execution["master_seed"] == 20260922
    assert set(anchors) == {
        "A_explicit_layer_pooled_reference",
        "B_context_proxy_for_layer",
        "C_proxy_negative_control",
        "D_context_power_correlated",
        "E_context_power_uncorrelated",
        "F_high_information_bias_correlated",
        "G_high_information_bias_uncorrelated",
    }

    assert anchors["A_explicit_layer_pooled_reference"]["within_layer_context_effect"] == 0.0
    assert anchors["A_explicit_layer_pooled_reference"]["focal_learner_layer_identity"] == "included"
    assert anchors["B_context_proxy_for_layer"]["within_layer_context_effect"] == 0.0
    assert anchors["B_context_proxy_for_layer"]["context_layer_correlation"] == "rho_0.7"
    assert anchors["B_context_proxy_for_layer"]["focal_learner_layer_identity"] == "excluded"
    assert anchors["C_proxy_negative_control"]["context_layer_correlation"] == "none"

    assert rules["monte_carlo_null_rate_ceiling_at_1000_replicates"] == 0.06378404875209022
    assert rules["full_claim_requires_all_rules"] is True
    failure_rules = rules["false_positive_failure_mode"]
    assert {row["anchor_id"] for row in failure_rules} == {
        "A_explicit_layer_pooled_reference",
        "B_context_proxy_for_layer",
    }
    assert all(row["acceptance"] == "wilson_95_lower_bound_gt" for row in failure_rules)
    assert all(row["threshold"] == 0.50 for row in failure_rules)


def test_contract_contains_real_withdrawal_paths_and_no_post_result_retuning():
    contract = _read()
    decision = contract["decision_tree_after_single_execution"]
    governance = contract["single_execution_governance"]

    assert "central_claim_withdrawn" in decision
    assert "narrow_explicit_layer_only_paper" in decision
    assert "diagnostic_only_rescope" in decision
    assert decision["no_post_result_threshold_changes"] is True
    assert decision["no_selective_anchor_deletion"] is True

    assert governance["contract_must_be_merged_before_simulation_result_exists"] is True
    assert governance["confirmatory_results_generated_once"] is True
    assert governance["seed_changes_after_result_access_forbidden"] is True
    assert governance["factor_level_changes_after_result_access_forbidden"] is True
    assert governance["success_threshold_changes_after_result_access_forbidden"] is True


def test_fit_failures_cannot_be_rescued_after_results_are_seen():
    contract = _read()
    learners = contract["learners"]

    assert learners["separation_rescue_allowed"] is False
    assert "unavailable" in learners["fit_failure_policy"]
    assert "do not add regularization" in learners["fit_failure_policy"]


def test_old_v6_submission_package_is_explicitly_superseded():
    receipt = json.loads(
        (ROOT / "N2_V6_SUBMISSION_SUPERSESSION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["v6_submission_authorized"] is False
    assert receipt["historical_readiness_receipt_deleted_or_rewritten"] is False
    assert receipt["replacement_stage"] == CONTRACT.name
    assert receipt["submission_state"]["old_v6_should_not_be_submitted"] is True
    assert receipt["submission_state"]["old_v6_exact_upload_artifact_should_not_be_used"] is True


def test_layer_allocation_is_deterministic_and_matches_bop_oracle_contract():
    contract = _read()
    allocation = contract["data_generating_process"]["layer_assignment"]
    assert "first group_count mod layer_count layers receive one extra group" in allocation
