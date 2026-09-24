from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_STAGE2_REAL_DATA_RESULT_RECEIPT_V1.json"


def _read() -> dict[str, object]:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_stage2_result_is_bound_to_single_successful_one_shot():
    receipt = _read()
    execution = receipt["one_shot_execution"]
    artifact = receipt["canonical_result_artifact"]

    assert receipt["contract_merge_sha"] == "8a83079f395b7e22bf82d87a430d8169247bf996"
    assert receipt["few_cluster_fix_merge_sha"] == "6bc65a1a5575d61835838e711d6f0221af320034"
    assert receipt["execution_engine_merge_sha"] == "79570b6ddb7cf4cf8c56a077871fe90d36f2ac94"
    assert execution["workflow_run_id"] == 35992702616
    assert execution["run_attempt"] == 1
    assert execution["conclusion"] == "success"
    assert execution["workflow_dispatch_enabled"] is False
    assert execution["rerun_same_v1_permitted"] is False
    assert artifact["artifact_id"] == 10804873232
    assert artifact["artifact_digest"] == "sha256:f7383597df4b1d06f778533da8c4d1162c64be6d7d9aa79e562f44ad1546f6b2"


def test_fresh_penguins_has_predeclared_full_reversal():
    result = _read()["fresh_palmer_penguins"]
    naive = result["naive_pooled_gain"]
    corrected = result["audit_context_gain"]
    layer = result["audit_layer_component"]

    assert result["prepared_row_count"] == 342
    assert result["years"] == ["2007", "2008", "2009"]
    assert naive["mean_gain"] > 0
    assert naive["mean_gain_lower"] > 0
    assert naive["mean_gain_status"] == "positive"
    assert layer["mean_gain"] > 0
    assert layer["mean_gain_status"] == "positive"
    assert corrected["mean_gain"] < 0
    assert corrected["mean_gain_upper"] < 0
    assert corrected["mean_gain_status"] == "nonpositive"
    assert naive["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert corrected["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert naive["mean_gain_interval_df"] == 2
    assert corrected["mean_gain_interval_df"] == 2

    assert result["decision_components"] == {
        "point_sign_reversal": True,
        "inferential_downgrade": True,
        "strong_attenuation": True,
    }
    assert result["decision"] == "fresh_empirical_reversal"


def test_bop_is_not_counted_as_system_level_reversal_after_small_cluster_fix():
    bop = _read()["bop_rodent"]

    assert bop["population_v2_total_status"] == "uncertain"
    assert bop["population_v2_context_status"] == "uncertain"
    assert bop["system_level_point_sign_reversal"] is False
    assert bop["system_level_inferential_downgrade"] is False
    assert bop["system_level_strong_attenuation"] is False

    sentinel = bop["buteo_motivating_sentinel"]
    assert sentinel["mean_total_gain"] > 0
    assert sentinel["mean_species_component"] > 0
    assert sentinel["mean_context_within_species_component"] < 0
    assert sentinel["descriptive_point_sign_reversal"] is True
    assert sentinel["included_in_system_flip_denominator"] is False


def test_serengeti_prevents_blanket_anti_pooled_claim():
    control = _read()["snapshot_serengeti_semantic_control"]

    assert control["terminal_category"] == "temporal_partition_generalizing"
    assert control["transfer_category"] == "generalizing"
    assert all(value > 0 for value in control["heldout_gains"])
    assert control["pooled_reference_scientifically_appropriate"] is True
    assert control["included_in_system_flip_denominator"] is False


def test_stage2_counts_are_descriptive_and_failure_mode_position_is_supported():
    receipt = _read()
    counts = receipt["stage2_counts"]
    position = receipt["paper_position_after_stage2"]

    assert counts == {
        "system_count": 2,
        "point_sign_reversal_count": 1,
        "inferential_downgrade_count": 1,
        "strong_attenuation_count": 1,
        "prevalence_or_meta_analytic_rate_claimed": False,
    }
    assert position["stage1_known_truth_is_primary_mechanistic_evidence"] is True
    assert position["fresh_real_data_reversal_observed"] is True
    assert position["semantic_negative_control_observed"] is True
    assert position["framework_paper_positioning_should_not_be_restored"] is True
    assert position["failure_mode_paper_positioning_supported"] is True
    assert position["stage4_published_study_reanalysis_required_for_core_claim"] is False
