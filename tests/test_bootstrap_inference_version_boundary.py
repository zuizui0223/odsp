from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_inference_version_boundary_prevents_v1_bootstrap_t_claim():
    contract = json.loads(
        (ROOT / "ODSP_BOOTSTRAP_INFERENCE_VERSION_BOUNDARY.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-bootstrap-inference-version-boundary-v1"
    v1 = contract["version_1"]
    v2 = contract["version_2"]
    assert v1["replicate_specific_studentizer_recomputed"] is False
    assert v1["classical_bootstrap_t_claim_allowed"] is False
    assert v1["historical_max_t_field_names_retained_for_compatibility"] is True
    assert v1["historical_empirical_receipts_rerun"] is False
    assert v1["historical_empirical_terminal_categories_reclassified"] is False
    assert v2["replicate_specific_studentizer_recomputed"] is True
    assert v2["classical_bootstrap_t_claim_allowed"] is True
    assert v2["known_null_operating_characteristics_required_for_declared_design"] is True


def test_bootstrap_inference_boundary_keeps_refits_as_sensitivity_by_default():
    contract = json.loads(
        (ROOT / "ODSP_BOOTSTRAP_INFERENCE_VERSION_BOUNDARY.json").read_text(
            encoding="utf-8"
        )
    )
    refit = contract["refit_ensemble_boundary"]
    assert refit["automatic_probability_sample_interpretation"] is False
    assert refit["automatic_95_percent_confidence_interpretation"] is False
    stops = contract["reporting_hard_stops"]
    assert all(value is False for value in stops.values())


def test_canonical_version_boundary_document_uses_correct_names():
    text = (ROOT / "docs" / "bootstrap_inference_version_boundary.md").read_text(
        encoding="utf-8"
    )
    assert "fixed-scale standardized max-deviation" in text
    assert "replicate-studentized cluster bootstrap-t" in text
    assert "not relabelled as a 95% bootstrap-t confidence guarantee" in text
