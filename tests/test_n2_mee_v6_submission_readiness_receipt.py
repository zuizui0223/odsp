from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_MEE_STATE_PREDICTION_V6_SUBMISSION_READINESS_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_submission_readiness_receipt_preserves_scientific_boundary():
    receipt = _read(RECEIPT)
    boundary = receipt["scientific_boundary"]

    assert receipt["manuscript_version"] == 6
    assert receipt["target_journal"] == "Methods in Ecology and Evolution"
    assert boundary["bop_prospective_terminal_category"] == "empirical_state_prediction_mixed"
    assert boundary["bop_prospective_positive_individual_count"] == 27
    assert boundary["bop_prospective_scored_individual_count"] == 30
    assert boundary["bop_population_summary_post_outcome"] is True
    assert boundary["bop_population_summary_descriptive_only"] is True
    assert boundary["bop_population_cluster_count"] == 4
    assert boundary["bop_total_mean_gain_lower"] > 0
    assert boundary["bop_new_individual_prediction_lower"] < 0
    assert boundary["bop_stepwise_population_ceiling"] == "pooled"
    assert boundary["primary_endpoint_reclassified"] is False
    assert boundary["empirical_endpoint_rerun"] is False
    assert boundary["model_refit_performed"] is False
    assert boundary["raw_source_data_reaccessed"] is False
    assert boundary["retuning_performed"] is False


def test_v6_submission_readiness_receipt_pins_exact_artifact_and_author_gate():
    receipt = _read(RECEIPT)
    artifact = receipt["submission_artifact"]
    validation = receipt["mechanical_validation"]
    state = receipt["submission_state"]

    assert artifact["workflow_run_id"] == 35688663685
    assert artifact["artifact_id"] == 10677921242
    assert artifact["artifact_digest"].startswith("sha256:")
    assert len(receipt["canonical_file_hashes"]) == 7

    assert validation["abstract_word_count"] == 333
    assert validation["review_docx_structural_validation_passed"] is True
    assert validation["review_docx_rendered_page_count"] == 28
    assert validation["review_docx_visual_qa_completed"] is True
    assert validation["review_docx_clipping_or_overlap_detected"] is False
    assert validation["review_bundle_identity_scan_passed"] is True
    assert validation["review_bundle_internal_workflow_or_artifact_provenance_included"] is False
    assert validation["final_author_visual_approval_completed"] is False

    assert state["scientific_and_mechanical_package_ready"] is True
    assert state["ready_for_author_metadata_completion"] is True
    assert state["ready_for_submission"] is False
    assert len(state["remaining_author_only_gates"]) >= 10
