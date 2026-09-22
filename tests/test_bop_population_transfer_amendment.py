from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_CONTRACT.json"
RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_bop_population_transfer_amendment_is_explicitly_secondary_and_post_outcome():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)

    assert contract["post_outcome_amendment"] is True
    assert receipt["post_outcome_amendment"] is True
    assert contract["analysis_type"] == "descriptive_secondary_population_transfer"
    assert receipt["analysis_type"] == contract["analysis_type"]
    assert contract["frozen_primary_endpoint"]["must_not_be_reclassified_by_this_amendment"] is True
    assert receipt["frozen_primary_endpoint"]["terminal_decision_recomputed"] is False
    assert receipt["frozen_primary_endpoint"]["terminal_decision_changed"] is False


def test_bop_population_transfer_uses_individual_groups_and_species_clusters():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    estimand = contract["population_estimand"]
    population = receipt["population_result"]

    assert estimand["group"] == "heldout_individual"
    assert estimand["population_cluster"] == "species"
    assert estimand["equal_group_weight"] is True
    assert population["group_count"] == 30
    assert population["cluster_count"] == 4
    assert population["cluster_variable_declared"] is True
    assert population["familywise_confirmatory_claim"] is False
    assert population["uncertainty"]["mean_interval_method"] == "cluster_percentile_bootstrap"
    assert population["uncertainty"]["cluster_bootstrap_limitation"] is not None


def test_bop_total_transfer_is_positive_but_new_individual_uncertainty_remains():
    receipt = _read(RECEIPT)
    total = receipt["population_result"]["total_gain"]

    assert total["mean_gain"] == 0.5709102207418053
    assert total["mean_gain_status"] == "positive"
    assert total["mean_gain_lower"] > 0
    assert total["positive_group_count"] == 27
    assert total["positive_group_fraction"] == 0.9
    assert total["positive_fraction_lower"] > 0.79
    assert total["prediction_lower"] < 0 < total["prediction_upper"]
    assert total["empirical_p10"] > 0


def test_bop_total_transfer_and_stepwise_ceiling_are_not_conflated():
    receipt = _read(RECEIPT)
    population = receipt["population_result"]
    species_step, context_step = population["steps"]

    assert population["total_gain"]["mean_gain_status"] == "positive"
    assert species_step["lower_level"] == "pooled"
    assert species_step["upper_level"] == "species"
    assert species_step["mean_gain_status"] == "uncertain"
    assert context_step["lower_level"] == "species"
    assert context_step["upper_level"] == "species_context"
    assert context_step["mean_gain_status"] == "positive"
    assert population["population_mean_supported_ceiling"] == "pooled"


def test_bop_population_transfer_reuses_pinned_species_baseline_artifact():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    source = contract["source_evidence"]

    assert receipt["source_evidence"]["artifact_id"] == source["artifact_id"]
    assert receipt["source_evidence"]["artifact_digest"] == source["artifact_digest"]
    assert receipt["source_evidence"]["result_json_sha256"] == source["result_json_sha256"]
    assert receipt["model_refit_performed"] is False
    assert receipt["raw_source_data_reaccessed"] is False
    assert receipt["retuning_performed"] is False


def test_bop_population_transfer_validation_provenance_is_pinned():
    receipt = _read(RECEIPT)
    provenance = receipt["validation_provenance"]
    assert provenance["source_head_sha"] == "9923d2c6fda1eaf283e94e4ba46fe81d2bd395d7"
    assert provenance["workflow_run_id"] == 35686930897
    assert provenance["artifact_id"] == 10676618536
    assert provenance["artifact_digest"] == "sha256:4e9eaffa59cdd072e5efc05e22bb0a13946254814ce0ba5ab7a6688cb3f46674"
    assert provenance["result_json_sha256"] == "7e5f302e8346145ff60b3c53dae6fdf57d623299db7a094bad9896a6e8de8d8d"
