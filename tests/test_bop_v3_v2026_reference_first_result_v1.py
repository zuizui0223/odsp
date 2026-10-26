from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_bop_v3_v2026_reference_first_result_v1 import (
    CONTRACT,
    FIRST,
    RECEIPT,
    validate_reference_only_terminal,
)


def _source():
    return (
        json.loads(FIRST.read_text(encoding="utf-8")),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        CONTRACT.read_bytes(),
        FIRST.read_bytes(),
    )


def _validate(result, receipt, contract, original):
    return validate_reference_only_terminal(
        result, frozen_receipt=receipt,
        contract_bytes=contract, first_result_bytes=original,
    )


def test_official_first_result_is_locked_with_source_checksums():
    result, receipt, contract, original = _source()
    validated = _validate(result, receipt, contract, original)
    assert validated["source_only_terminal"] == (
        "NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
    )
    assert validated["additional_animal_ID_candidates"] == 10
    assert validated["maximum_per_species"] == 6
    assert validated["old_to_new_corrected_ID_overlap"] == 35
    assert validated["source_members"] == 2
    assert validated["model_or_GPS_outcome_accessed"] is False
    assert validated["historical_BOP_terminal_changed"] is False
    assert receipt["freeze_and_first_access"]["contract_commit_sha"] == (
        "cf8d1cc94cf78b128911b31c43ff096fe4b32fd2"
    )
    assert receipt["freeze_and_first_access"]["first_workflow_run_id"] == 40270328971
    assert receipt["freeze_and_first_access"]["first_result_artifact_id"] == 12627019951
    assert result["identity_audit"]["old_removed_out_of_scope_count"] == 0
    assert result["references"][1]["reference_rows"] == 46
    assert result["references"][1]["distinct_animal_ids"] == 45


@pytest.mark.parametrize(
    "mode, error",
    [
        ("source_contract", "contract drifted"),
        ("source_first_result", "first-result bytes drifted"),
        ("candidate_by_species", "source-only replay differs"),
        ("candidate_count", "source-only replay differs"),
        ("source_sha", "source-only replay differs"),
        ("source_md5", "source-only replay differs"),
        ("gps_access", "source-only replay differs"),
        ("rank_promoted", "source-only replay differs"),
        ("historic_terminal", "source-only replay differs"),
        ("receipt_terminal", "source-only terminal"),
        ("receipt_source_bytes", "source roster/count/checksum"),
        ("artifact_identity", "first successful official source-evidence"),
    ],
)
def test_immutable_source_admission_fails_closed(mode, error):
    original_result, original_receipt, original_contract, original_bytes = _source()
    result = copy.deepcopy(original_result)
    receipt = copy.deepcopy(original_receipt)
    contract = original_contract
    if mode == "source_contract":
        contract += b"\n"
    elif mode == "source_first_result":
        original_bytes += b"\n"
    elif mode == "candidate_by_species":
        result["identity_audit"]["new_id_candidates_by_species"]["Circus aeruginosus"] = 10
    elif mode == "candidate_count":
        result["identity_audit"]["new_id_candidates_count"] = 11
    elif mode == "source_sha":
        result["references"][0]["reference_bytes_sha256"] = "0" * 64
    elif mode == "source_md5":
        result["source_md5s"][0] = "0" * 32
    elif mode == "gps_access":
        result["gps_event_data_accessed"] = True
    elif mode == "rank_promoted":
        result["identity_audit"]["scientific_status"] = (
            "METADATA_ONLY_CANDIDATE_NEEDS_OUTCOME_BLIND_GPS_ELIGIBILITY"
        )
    elif mode == "historic_terminal":
        result["old_original_terminal"] = "empirical_state_prediction_generalizing"
    elif mode == "receipt_terminal":
        receipt["first_terminal"]["category"] = "EMPIRICALLY_GENERALIZING"
    elif mode == "receipt_source_bytes":
        receipt["source_verification"]["source_reference_sha256s"][0] = "0" * 64
    elif mode == "artifact_identity":
        receipt["freeze_and_first_access"]["first_result_artifact_id"] = 999
    with pytest.raises(ValueError, match=error):
        _validate(result, receipt, contract, original_bytes)


def test_first_result_has_no_animal_id_rows_and_old_ref_rows_are_distinguished():
    first, _, _, _ = _source()
    assert sorted(first["identity_audit"]["new_id_candidates_by_species"]) == [
        "Asio flammeus", "Buteo buteo", "Circus aeruginosus",
        "Circus pygargus",
    ]
    assert first["identity_audit"]["new_id_candidates_count"] == 10
    assert first["identity_audit"]["overlapping_corrected_animal_ids"] == 35
    assert first["references"][0]["reference_rows"] == 35
    assert first["references"][1]["reference_rows"] == 46
    assert "animal-id" not in json.dumps(first)
    assert "H197221" not in json.dumps(first)
    assert "H200701" not in json.dumps(first)
