from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_CORRECTION_CONTRACT_V2.json"
RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_CORRECTION_RECEIPT_V2.json"
SUPERSESSION = ROOT / "BOP_POPULATION_TRANSFER_V1_SUPERSESSION_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_bop_v2_corrects_few_cluster_inference_without_changing_frozen_gains():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    population = receipt["population_result"]
    total = population["total_gain"]

    assert contract["post_outcome_amendment"] is True
    assert receipt["post_outcome_amendment"] is True
    assert receipt["supersedes_inference_from_contract_id"] == (
        "bop-rodent-population-transfer-descriptive-amendment-v1"
    )
    assert population["group_count"] == 30
    assert population["cluster_count"] == 4
    assert population["uncertainty"]["few_resampling_unit_threshold"] == 10
    assert population["uncertainty"]["few_cluster_fallback_applied"] is True
    assert population["uncertainty"]["mean_interval_method"] == "cluster_robust_t_cr1"

    assert total["mean_gain"] == 0.5709102207418053
    assert total["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert total["mean_gain_lower"] < 0 < total["mean_gain_upper"]
    assert total["mean_gain_status"] == "uncertain"
    assert total["positive_group_count"] == 27
    assert total["positive_group_fraction"] == 0.9
    assert total["positive_fraction_wilson_lower"] > total[
        "positive_fraction_cluster_aware_lower"
    ]
    assert total["positive_fraction_lower"] == total[
        "positive_fraction_cluster_aware_lower"
    ]
    assert total["positive_fraction_lower"] < 0.71


def test_bop_v2_all_adjacent_population_mean_steps_are_uncertain():
    receipt = _read(RECEIPT)
    population = receipt["population_result"]
    species_step, context_step = population["steps"]

    assert species_step["mean_gain_status"] == "uncertain"
    assert species_step["mean_gain_lower"] < 0 < species_step["mean_gain_upper"]
    assert context_step["mean_gain_status"] == "uncertain"
    assert context_step["mean_gain_lower"] < 0 < context_step["mean_gain_upper"]
    assert population["population_mean_supported_ceiling"] == "pooled"


def test_bop_v1_is_preserved_as_history_but_not_valid_for_current_inference():
    supersession = _read(SUPERSESSION)
    assert supersession["historical_receipt_deleted_or_rewritten"] is False
    assert supersession["historical_v1_inference_should_be_used"] is False
    assert supersession["prospective_primary_endpoint_changed"] is False
    assert supersession["historical_v1_total_mean_interval"][0] > 0
    assert supersession["corrected_v2_total_mean_interval"][0] < 0
    assert supersession["corrected_v2_positive_fraction_lower"] < supersession[
        "historical_v1_positive_fraction_lower"
    ]


def test_bop_v2_uses_same_checksum_pinned_source_and_no_refit():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    assert receipt["source_evidence"]["workflow_run_id"] == contract["source_evidence"]["workflow_run_id"]
    assert receipt["source_evidence"]["artifact_id"] == contract["source_evidence"]["artifact_id"]
    assert receipt["source_evidence"]["artifact_digest"] == contract["source_evidence"]["artifact_digest"]
    assert receipt["source_evidence"]["artifact_id"] == 10310047790
    assert receipt["source_evidence"]["result_json_sha256"] == (
        "44a02f584b819a4af83c0d53684ed285cad322b1a3e5ef30aba605e5f3aff352"
    )
    assert receipt["model_refit_performed"] is False
    assert receipt["raw_source_data_reaccessed"] is False
    assert receipt["retuning_performed"] is False
