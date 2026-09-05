from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from scripts.build_n2_mee_manuscript_v4 import build_manuscript_text
from scripts.build_n2_mee_review_bundle_v4 import build_bundle


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_MEE_STATE_PREDICTION_V4_FINAL_READINESS_RECEIPT.json"
V4_CONTRACT = ROOT / "N2_MEE_STATE_PREDICTION_V4_CONTRACT.json"
PREDICTION_RECEIPT = ROOT / "STATE_RESOLVED_PREDICTION_VALIDATION_RECEIPT.json"
MH_RECEIPT = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_RECEIPT.json"
BOP_RECEIPT = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"
GENERALITY = ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json"
V3_RECEIPT = ROOT / "N2_MEE_FINAL_SUBMISSION_V3_RECEIPT.json"
TITLE = ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE_v4.md"
COVER = ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v4.md"
DISCLOSURES = ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v4.md"
CHECKLIST = ROOT / "N2_MEE_STATE_PREDICTION_V4_SUBMISSION_CHECKLIST.json"
MH_WORKFLOW = ROOT / ".github" / "workflows" / "mh-antwerpen-state-prediction.yml"
BOP_WORKFLOW = ROOT / ".github" / "workflows" / "bop-rodent-state-prediction.yml"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _abstract(text: str) -> str:
    return text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]


def test_final_receipt_rebuilds_manuscript_and_anonymous_bundle(tmp_path):
    receipt = _read(RECEIPT)
    manuscript = build_manuscript_text()
    m = receipt["manuscript_v4"]
    assert hashlib.sha256(manuscript.encode("utf-8")).hexdigest() == m["sha256"]
    assert _word_count(manuscript) == m["word_count"] == 5443
    assert _word_count(_abstract(manuscript)) == m["abstract_word_count"] == 350
    assert "GPS tracking data of Western marsh harriers breeding in Belgium and the Netherlands" in manuscript
    assert "Dataset description associated with the MH_ANTWERPEN bird-tracking project" not in manuscript

    bundle_path = tmp_path / "review-v4.zip"
    built = build_bundle(bundle_path)
    b = receipt["anonymous_review_bundle_v4"]
    assert built["sha256"] == b["sha256"]
    assert built["bytes"] == b["bytes"]
    assert built["file_count"] == b["file_count"] == 64
    assert built["python_file_ai_annotation_count"] == b["python_file_ai_annotation_count"] == 48


def test_final_receipt_matches_prediction_and_empirical_receipts():
    receipt = _read(RECEIPT)
    pred = _read(PREDICTION_RECEIPT)
    mh = _read(MH_RECEIPT)
    bop = _read(BOP_RECEIPT)
    generality = _read(GENERALITY)

    pv = receipt["prediction_validation"]
    summary = pred["finite_sample_benchmark"]["summary"]
    assert pv["known_truth_replicates_per_cell"] == pred["finite_sample_benchmark"]["replicates_per_cell"] == 128
    assert pv["tested_sample_sizes_per_base"] == pred["finite_sample_benchmark"]["sample_sizes_per_base"]
    assert pv["stable_positive_in_all_replicates_at_every_sample_size"] == summary["stable_positive_in_all_128_replicates_at_every_sample_size"] is True
    assert pv["shifted_negative_in_all_replicates_at_every_sample_size"] == summary["shifted_negative_in_all_128_replicates_at_every_sample_size"] is True
    assert pv["unorganized_mean_gain_converges_toward_zero"] == summary["unorganized_mean_gain_converges_toward_zero"] is True
    assert pv["probability_rmse_decreases_with_sample_size"] == summary["probability_rmse_decreases_with_sample_size"] is True
    assert pv["generality_property_obligations_passed"] == generality["result"]["check_count"] == 1873
    assert pv["generality_property_obligations_failed"] == generality["result"]["failed_count"] == 0
    assert pv["generality_maximum_absolute_error"] == generality["result"]["maximum_absolute_error"]

    r_mh = receipt["prospective_empirical_prediction"]["MH_ANTWERPEN"]
    assert r_mh["terminal_category"] == mh["terminal"]["category"] == "empirical_state_prediction_unavailable"
    assert r_mh["thinned_events"] == mh["data_flow"]["thinned_event_count"] == 193370
    assert r_mh["eligible_individuals"] == mh["terminal"]["observed_eligible_individuals"] == 3
    assert r_mh["frozen_minimum_individuals"] == mh["terminal"]["frozen_minimum_eligible_individuals"] == 4
    assert mh["terminal"]["primary_rf_folds_executed"] == 0

    r_bop = receipt["prospective_empirical_prediction"]["BOP_RODENT"]
    primary = bop["primary_random_forest"]
    assert r_bop["terminal_category"] == primary["terminal_category"] == "empirical_state_prediction_mixed"
    assert r_bop["eligible_events"] == bop["data_flow"]["eligible_event_count"] == 154655
    assert r_bop["eligible_individuals"] == primary["eligible_individual_count"] == 30
    assert r_bop["primary_positive_log_gain_individuals"] == primary["positive_individual_count"] == 27
    assert r_bop["primary_nonpositive_log_gain_individuals"] == primary["nonpositive_individual_count"] == 3
    assert r_bop["primary_positive_brier_improvement_individuals"] == primary["positive_brier_improvement_count"] == 30
    assert r_bop["mean_primary_log_gain_descriptive"] == primary["mean_gain_descriptive"]
    assert r_bop["mean_primary_brier_improvement_descriptive"] == primary["mean_brier_improvement_descriptive"]


def test_final_receipt_preserves_v3_and_v4_claim_boundaries():
    receipt = _read(RECEIPT)
    contract = _read(V4_CONTRACT)
    v3 = _read(V3_RECEIPT)

    assert v3["receipt_id"] == "n2-mee-final-submission-v3"
    assert receipt["historical_v3_preservation"]["v3_final_submission_receipt_present"] is True
    assert all(value is False for key, value in receipt["scientific_boundary"].items() if key not in ())
    contract_boundary = contract["scientific_boundary"]
    assert contract_boundary["bop_mixed_terminal_relaxed_to_generalizing"] is False
    assert contract_boundary["closed_mh_endpoint_rescued"] is False
    assert contract_boundary["n2_output_automatically_promoted_to_n3"] is False


def test_final_receipt_admin_layer_is_separate_and_author_gated():
    receipt = _read(RECEIPT)
    checklist = _read(CHECKLIST)
    new_title = receipt["target"]["manuscript_title"]

    for path in (TITLE, COVER, DISCLOSURES, CHECKLIST):
        assert path.is_file()
    assert new_title in TITLE.read_text(encoding="utf-8")
    assert new_title in COVER.read_text(encoding="utf-8")
    assert receipt["submission_administration_v4"]["kept_outside_anonymous_review_bundle"] is True
    assert receipt["submission_administration_v4"]["file_count"] == 4
    assert all(value is False for value in checklist["manual_author_confirmation_required"].values())
    assert receipt["readiness"]["author_metadata_completion_required"] is True
    assert receipt["readiness"]["ready_for_submission_without_author_metadata_completion"] is False


def test_closed_empirical_workflows_are_path_filtered():
    receipt = _read(RECEIPT)
    for path in (MH_WORKFLOW, BOP_WORKFLOW):
        text = path.read_text(encoding="utf-8")
        assert "paths:" in text
        assert "workflow_dispatch:" in text
    assert receipt["workflow_governance"]["closed_mh_and_bop_workflows_use_path_filters"] is True
    assert receipt["validated_main"]["workflow_count_for_main_commit"] == 4
    assert receipt["validated_main"]["mh_public_data_workflow_ran_for_this_commit"] is False
    assert receipt["validated_main"]["bop_public_data_workflow_ran_for_this_commit"] is False
