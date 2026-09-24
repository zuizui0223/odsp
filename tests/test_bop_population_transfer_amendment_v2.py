from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_CONTRACT_V2.json"
RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"
LEGACY = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_supersedes_anti_conservative_v1_without_rewriting_history():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    legacy = _read(LEGACY)

    assert contract["schema_version"] == 2
    assert receipt["schema_version"] == 2
    assert contract["supersedes"]["v1_receipt_deleted_or_rewritten"] is False
    assert contract["supersedes"]["v1_population_inference_should_not_be_used"] is True
    assert legacy["population_result"]["uncertainty"]["mean_interval_method"] == "cluster_percentile_bootstrap"
    assert receipt["population_result"]["uncertainty"]["mean_interval_method"] == "cluster_robust_t_cr1"


def test_v2_four_cluster_total_mean_is_uncertain_and_wilson_fallback_is_descriptive():
    receipt = _read(RECEIPT)
    population = receipt["population_result"]
    total = population["total_gain"]

    assert population["cluster_count"] == 4
    assert population["uncertainty"]["small_cluster_threshold"] == 10
    assert total["mean_gain"] == 0.5709102207418053
    assert total["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert total["mean_gain_interval_df"] == 3
    assert total["mean_gain_lower"] < 0 < total["mean_gain_upper"]
    assert total["mean_gain_status"] == "uncertain"
    assert total["positive_group_count"] == 27
    assert total["positive_group_fraction"] == 0.9
    assert total["positive_fraction_lower"] == 0.7437891742081593
    assert total["positive_fraction_lower_method"] == "wilson_score_group_level_small_cluster_fallback"
    assert population["population_mean_supported_ceiling"] == "pooled"


def test_v2_adjacent_components_are_both_uncertain_under_four_cluster_correction():
    receipt = _read(RECEIPT)
    species_step, context_step = receipt["population_result"]["steps"]

    assert species_step["mean_gain_status"] == "uncertain"
    assert species_step["mean_gain_lower"] < 0 < species_step["mean_gain_upper"]
    assert context_step["mean_gain_status"] == "uncertain"
    assert context_step["mean_gain_lower"] < 0 < context_step["mean_gain_upper"]


def test_v2_does_not_change_frozen_primary_or_refit_any_model():
    receipt = _read(RECEIPT)
    primary = receipt["frozen_primary_endpoint"]

    assert primary["terminal_category"] == "empirical_state_prediction_mixed"
    assert primary["positive_individual_count"] == 27
    assert primary["eligible_individual_count"] == 30
    assert primary["terminal_decision_recomputed"] is False
    assert primary["terminal_decision_changed"] is False
    assert receipt["model_refit_performed"] is False
    assert receipt["raw_source_data_reaccessed"] is False
    assert receipt["retuning_performed"] is False


def test_v2_validation_provenance_is_pinned():
    receipt = _read(RECEIPT)
    provenance = receipt["validation_provenance"]

    assert provenance["source_head_sha"] == "8a2944ee08463a3b428954cd74da455fdf484324"
    assert provenance["workflow_run_id"] == 35988157400
    assert provenance["artifact_id"] == 10802594595
    assert provenance["artifact_digest"] == "sha256:19b13824cdc95c070c0b524bcf195c33857c0647e5aa7fc0709302c5d440a366"
    assert provenance["result_json_sha256"] == "de72da8f84db42963f6bcb7e56f9fd9f1bed02945cb3efd9740b5f51ae07d234"
