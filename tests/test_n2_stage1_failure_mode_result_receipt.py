from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_STAGE1_FAILURE_MODE_RESULT_RECEIPT_V1.json"


def _read() -> dict[str, object]:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_stage1_result_is_single_successful_frozen_execution():
    receipt = _read()
    run = receipt["one_shot_execution"]
    artifact = receipt["canonical_result_artifact"]

    assert receipt["contract_merge_sha"] == "05609e5a9fe4200d9cd7a1f46c807f9f682b1c72"
    assert receipt["execution_engine_merge_sha"] == "4932ecf2ffa8ae391ffcd0cf8cbb7f2cafbe272e"
    assert run["workflow_run_id"] == 35946823632
    assert run["run_attempt"] == 1
    assert run["conclusion"] == "success"
    assert run["job_count"] == 168
    assert run["all_jobs_successful"] is True
    assert run["rerun_same_v1_permitted"] is False

    assert artifact["artifact_id"] == 10787511129
    assert artifact["artifact_digest"] == "sha256:0308db85fca81e9699175eaf892e87007b1282a05a23a8ff9ef01edb5ba00744"
    assert artifact["result_json_sha256"] == "be9d594bb22f646129652091492e4ca01373dd443a069fcedb8fd8aad1b53a29"
    assert artifact["factorial_cell_count"] == 864


def test_all_predeclared_stage1_success_conditions_pass():
    receipt = _read()
    decision = receipt["frozen_decision"]
    anchors = receipt["confirmatory_anchors"]

    assert decision["full_claim_supported"] is True
    assert decision["decision_tree_matches"] == {
        "full_failure_mode_paper": True,
        "narrow_explicit_layer_only_paper": False,
        "diagnostic_only_rescope": False,
        "central_claim_withdrawn": False,
    }
    assert decision["post_result_threshold_changes_permitted"] is False

    assert anchors["A_explicit_layer_pooled_reference"]["pooled_reference_false_positive_rate"] == 1.0
    assert anchors["A_explicit_layer_pooled_reference"]["decomposed_context_false_positive_rate"] == 0.0
    assert anchors["B_context_proxy_for_layer"]["pooled_reference_false_positive_rate"] == 1.0
    assert anchors["B_context_proxy_for_layer"]["decomposed_context_false_positive_rate"] == 0.0
    assert anchors["C_proxy_negative_control"]["pooled_reference_false_positive_rate"] == 0.0
    assert anchors["C_proxy_negative_control"]["decomposed_context_false_positive_rate"] == 0.001
    assert anchors["D_context_power_correlated"]["decomposed_context_power"] == 0.959
    assert anchors["E_context_power_uncorrelated"]["decomposed_context_power"] == 1.0
    assert anchors["F_high_information_bias_correlated"]["absolute_mean_bias_nats"] < 0.001
    assert anchors["G_high_information_bias_uncorrelated"]["absolute_mean_bias_nats"] < 0.001


def test_bop_realistic_factorial_region_supports_failure_mode_and_correction():
    receipt = _read()
    bop = receipt["bop_reality_check"]
    summary = receipt["factorial_descriptive_summary"]["bop_realistic_layer_gain_cells"]

    assert bop["passed"] is True
    assert 0.2 <= bop["observed_oracle_layer_gain_nats"] <= 0.35
    assert summary["failure_relevant_cell_count"] == 54
    assert summary["mean_pooled_reference_positive_rate"] > 0.95
    assert summary["fraction_of_cells_with_positive_rate_gt_0_5"] > 0.94
    assert summary["mean_decomposed_context_positive_rate"] < 0.001
    assert summary["max_decomposed_context_positive_rate"] <= 0.015625
    assert summary["uncorrelated_layer_omitted_negative_control_mean_pooled_positive_rate"] < 0.01


def test_metric_diagnostic_does_not_turn_auc_into_primary_claim():
    receipt = _read()
    metric = receipt["metric_diagnostics_at_primary_null_anchors"]
    supported = receipt["scientific_interpretation"]["supported"]

    assert metric["A_explicit_layer_pooled_reference"]["group_cv_log_gain_positive_rate"] == 1.0
    assert metric["A_explicit_layer_pooled_reference"]["group_cv_accuracy_positive_rate"] == 1.0
    assert metric["A_explicit_layer_pooled_reference"]["group_cv_auc_positive_rate"] < 0.064
    assert metric["B_context_proxy_for_layer"]["group_cv_auc_positive_rate"] < 0.064
    assert any("reference-definition problem" in text for text in supported)
