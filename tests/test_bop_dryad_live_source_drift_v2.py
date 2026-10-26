from __future__ import annotations

import copy
import json

import pytest

from scripts.classify_live_bop_dryad_source_drift_v2 import (
    CONTRACT, FIRST, RECEIPT, ORIGINAL_FIRST,
    classify_live_dryad_source_drift,
)


def _source():
    semantic_bytes = FIRST.read_bytes()
    original_bytes = ORIGINAL_FIRST.read_bytes()
    live_first = json.loads(original_bytes)
    semantic = json.loads(semantic_bytes)
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    return live_first, semantic, receipt, CONTRACT.read_bytes(), semantic_bytes, original_bytes


def _call(live, semantic, receipt, contract, semantic_raw, original_raw):
    return classify_live_dryad_source_drift(
        live, semantic, receipt, contract, semantic_raw, original_raw
    )


def test_actual_original_artifact_fully_restores_unmodified_sha256():
    live, semantic, receipt, contract, semantic_raw, original_raw = _source()
    assert len(semantic["official_metadata_api"]["versions"]["sha256"]) == 55
    assert len(live["official_metadata_api"]["versions"]["sha256"]) == 64
    out = _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    assert out["classification"] == "EXACT_FIRST_SOURCE_REPLAY"
    assert out["changed_field_paths"] == []
    assert out["first_result_verified_unchanged"] is True
    assert out["malformed_historical_semantic_copy_retained"] is True
    assert out["semantic_copy_digest_truncation_reconciled_not_overwritten"] is True
    assert out["original_actions_json_sha256_verified"] == (
        "10181566debf005c51d5a28f6d058a9134fddca33580621d1d9a2ce40b32669e"
    )
    assert out["candidate_admission"] == "NOT_ADMITTED"
    assert out["new_source_version_accepted_as_frozen_result"] is False


def test_latest_versions_api_byte_drift_is_explicit_not_false_first_replay():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    live["official_metadata_api"]["versions"]["sha256"] = "f" * 64
    out = _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    assert out["classification"] == "SOURCE_METADATA_DRIFT_HOLD"
    assert out["changed_field_paths"] == [
        "official_metadata_api.versions.sha256"
    ]
    assert out["new_source_version_accepted_as_frozen_result"] is False
    assert out["BOP_existing_mixed_terminal_reclassified"] is False
    assert out["original_BOP_RF_direct_external_transfer_status"] == (
        "ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
    )


def test_new_live_sidecar_availability_is_hold_and_not_auto_admission():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    sidecar = live["small_non_gps_file_checks"]["README.md"]
    sidecar.pop("error_code")
    sidecar.update(
        status="SOURCE_READ", bytes_verified=True, sha256="c" * 64,
        parsed_non_gps={"status": "READ"}
    )
    out = _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    assert out["classification"] == "SOURCE_ACCESS_CHANGED_HOLD"
    assert out["candidate_admission"] == "NOT_ADMITTED"
    assert "small_non_gps_file_checks.README.md.status" in out["changed_field_paths"]


@pytest.mark.parametrize("key,value", [
    ("candidate_admission", "EXTERNAL_CONFIRMED"),
    ("BOP_existing_mixed_terminal_reclassified", True),
    ("raw_gps_or_height_outcomes_accessed", True),
    ("original_BOP_RF_direct_external_transfer_status", "COMPATIBLE"),
    ("feature_compatibility", {}),
    ("contract_sha256", "0" * 64),
])
def test_illegal_source_promotion_or_frozen_contract_change_is_fatal(key, value):
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    live[key] = value
    with pytest.raises(ValueError, match="critical historical BOP"):
        _call(live, semantic, receipt, contract, semantic_raw, original_raw)


def test_historical_semantic_copy_and_original_artifact_are_both_immutable():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    with pytest.raises(ValueError, match="pre-source Dryad scientific contract drifted"):
        _call(first, semantic, receipt, contract + b" ", semantic_raw, original_raw)
    with pytest.raises(ValueError, match="first-result semantic-copy bytes drifted"):
        _call(first, semantic, receipt, contract, semantic_raw + b" ", original_raw)
    with pytest.raises(ValueError, match="original GitHub Actions source JSON checksum"):
        _call(first, semantic, receipt, contract, semantic_raw, original_raw + b" ")


def test_historical_first_semantic_copy_cannot_be_silently_substituted():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    with pytest.raises(ValueError, match="original GitHub Actions source JSON checksum"):
        _call(first, semantic, receipt, contract, semantic_raw, semantic_raw)
    wrong = copy.deepcopy(semantic)
    wrong["official_metadata_api"]["versions"]["sha256"] = (
        first["official_metadata_api"]["versions"]["sha256"]
    )
    with pytest.raises(ValueError, match="first-result semantic-copy bytes drifted|truncation"):
        _call(first, wrong, receipt, contract, semantic_raw, original_raw)


def test_live_report_must_stay_deidentified_and_validly_hashed():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    live["animal.global.identifier"] = "not allowed"
    with pytest.raises(ValueError, match="unauthorized fields"):
        _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    live.pop("animal.global.identifier")
    live["official_metadata_api"]["versions"]["sha256"] = "not-a-real-sha"
    with pytest.raises(ValueError, match="valid SHA256"):
        _call(live, semantic, receipt, contract, semantic_raw, original_raw)


def test_source_unavailable_after_first_api_read_is_not_success():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    v = live["official_metadata_api"]["versions"]
    v.clear()
    v.update(status="SOURCE_HOLD", error_code="HTTP_403", bytes_verified=False)
    out = _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    assert out["classification"] == "SOURCE_ACCESS_CHANGED_HOLD"
    assert out["candidate_admission"] == "NOT_ADMITTED"
    assert out["new_source_version_accepted_as_frozen_result"] is False


def test_posthoc_operational_classification_cannot_rewrite_first_science():
    first, semantic, receipt, contract, semantic_raw, original_raw = _source()
    live = copy.deepcopy(first)
    live["official_metadata_api"]["versions"]["sha256"] = "f" * 64
    out = _call(live, semantic, receipt, contract, semantic_raw, original_raw)
    serialized = json.dumps(out, allow_nan=False)
    assert "individual.global.identifier" not in serialized
    assert out["first_official_result_sha256"] == receipt[
        "first_official_execution"
    ]["artifact_raw_result_json_sha256"]
    assert out["changed_field_count"] == 1
