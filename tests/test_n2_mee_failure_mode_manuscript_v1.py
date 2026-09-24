from __future__ import annotations

import json
from pathlib import Path

from scripts.build_n2_mee_failure_mode_manuscript_v1 import (
    build_manuscript_text,
    build,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_FAILURE_MODE_MANUSCRIPT_V1_CONTRACT.json"


def test_failure_mode_contract_keeps_odsp_out_of_primary_claim():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["positioning"]["framework_paper"] is False
    assert contract["positioning"]["failure_mode_paper"] is True
    assert contract["positioning"]["odsp_is_primary_novelty_claim"] is False
    assert contract["development_freeze"]["new_certification_families_allowed"] is False
    assert contract["development_freeze"]["new_lattice_qualifications_allowed"] is False
    assert contract["development_freeze"]["new_primary_real_data_systems_allowed"] is False


def test_failure_mode_manuscript_contains_frozen_stage1_and_stage2_results():
    text = build_manuscript_text()

    required = (
        "Predictive skill can misidentify information transfer",
        "pooled-reference false-transfer rate was 1.000",
        "mean pooled positive-declaration rate was 0.896",
        "morphology-only random forest",
        "mean held-out log-score gain +0.38946",
        "mean was -0.08375",
        "Buteo buteo",
        "+0.27362",
        "-0.04331",
        "Snapshot Serengeti",
        "the reference should already contain every information layer",
    )
    for phrase in required:
        assert phrase in text


def test_failure_mode_manuscript_does_not_restore_framework_claims():
    text = build_manuscript_text()

    assert "It is not the central scientific claim" in text
    assert "not a blanket instruction to condition every reference" in text
    assert "Stage 2 contains empirical triangulation, not a survey of published-study prevalence" in text
    assert "ODSP as a model-agnostic framework" not in text
    assert "new prediction framework" not in text


def test_failure_mode_abstract_stays_under_frozen_ceiling(tmp_path: Path):
    output = tmp_path / "manuscript.md"
    manifest = tmp_path / "manifest.json"
    result = build(output, manifest)

    assert result["abstract_within_ceiling"] is True
    assert result["abstract_word_count"] <= 350
    assert result["framework_paper_positioning"] is False
    assert result["stage1_result_modified"] is False
    assert result["stage2_result_modified"] is False
    assert output.is_file()
    assert manifest.is_file()


def test_stage4_is_optional_not_a_gate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["stage4"]["required_for_submission"] is False
