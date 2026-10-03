from __future__ import annotations

import json
from pathlib import Path

from scripts.build_n2_mee_reference_alignment_manuscript_v2 import (
    build,
    build_manuscript_text,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_REFERENCE_ALIGNMENT_MANUSCRIPT_V2_CONTRACT.json"
SUPERSESSION = ROOT / "N2_FAILURE_MODE_MANUSCRIPT_SUPERSESSION_RECEIPT_V2.json"
BUILDER = ROOT / "scripts" / "build_n2_mee_reference_alignment_manuscript_v2.py"


def test_reference_alignment_contract_is_positive_methodological_positioning():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    p = contract["positioning"]
    assert p["reference_to_claim_alignment_paper"] is True
    assert p["failure_mode_paper"] is False
    assert p["framework_paper"] is False
    assert p["odsp_is_primary_novelty_claim"] is False
    assert p["stage1_role"] == "known_truth_identification_and_power_test"
    assert p["penguins_role"] == "fresh_empirical_sign_reversal"
    assert p["serengeti_role"] == "semantic_boundary_control"
    assert p["published_literature_prevalence_claimed"] is False


def test_reference_alignment_manuscript_leads_with_positive_principle():
    text = build_manuscript_text()
    first_1200 = text[:1200]
    assert "Claim-aligned reference models" in first_1200
    assert "reference-to-claim alignment" in first_1200.lower()
    assert "failure-mode manuscript" not in first_1200.lower()
    assert "misidentify information transfer" not in first_1200.lower()


def test_reference_alignment_manuscript_preserves_all_scientific_evidence():
    text = build_manuscript_text()
    required = (
        "pooled-reference positive-declaration rate was 1.000",
        "conditioned context declaration rate was 0.000",
        "power was 0.959",
        "groupwise AUC",
        "0.062",
        "0.041",
        "Palmer Penguins",
        "+0.38946",
        "-0.08375",
        "Snapshot Serengeti",
        "reference-to-claim alignment",
        "three collection years",
        "t(2)",
    )
    for phrase in required:
        assert phrase in text


def test_reference_alignment_manuscript_states_claim_dependent_boundary():
    text = build_manuscript_text()
    assert "not a rule to condition every reference" in text
    assert "species identity itself was the claimed information" in text
    assert "the comparator defines the predictive information increment being measured" in text


def test_reference_alignment_builder_does_not_import_provenance_hardening_stack():
    source = BUILDER.read_text(encoding="utf-8")
    forbidden = (
        "untouched_external",
        "confirmatory_environment_lock",
        "confirmatory_implementation_lock",
        "upstream_model_artifact",
        "method_route",
    )
    for token in forbidden:
        assert token not in source


def test_failure_mode_v1_is_preserved_but_superseded_for_submission():
    receipt = json.loads(SUPERSESSION.read_text(encoding="utf-8"))
    assert receipt["historical_failure_mode_v1_preserved"] is True
    assert receipt["historical_failure_mode_v1_submission_authorized"] is False
    assert receipt["replacement_contract"] == "N2_MEE_REFERENCE_ALIGNMENT_MANUSCRIPT_V2_CONTRACT.json"
    assert receipt["stage1_result_rerun"] is False
    assert receipt["stage2_result_rerun"] is False


def test_reference_alignment_draft_is_full_length_and_no_new_inference(tmp_path: Path):
    output = tmp_path / "manuscript.md"
    manifest = tmp_path / "manifest.json"
    result = build(output, manifest)

    assert result["abstract_within_ceiling"] is True
    assert result["abstract_word_count"] <= 350
    assert result["word_count"] >= 3800
    assert result["reference_alignment_positioning"] is True
    assert result["failure_mode_primary_positioning"] is False
    assert result["stage1_result_modified"] is False
    assert result["stage2_result_modified"] is False
    assert result["new_inference_added_by_manuscript_builder"] is False
