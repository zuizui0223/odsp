#!/usr/bin/env python3
"""Fail-closed validator of the first source-only BOP v3-v2026 terminal.

Validation is REPLAY, not independent GPS prediction. Checks the original
pre-source contract, first GitHub Actions provenance and byte-identical
metadata-only result. Never permits later source drift to reclassify a
closed source-admission conclusion or substitute another source version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_CONTRACT.json"
FIRST = ROOT / "research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_FIRST_RESULT.json"
RECEIPT = ROOT / "BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_TERMINAL_RECEIPT.json"

EXPECTED_TERMINAL = "NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
EXPECTED_SPECIES_COUNTS = {
    "Asio flammeus": 2,
    "Buteo buteo": 1,
    "Circus aeruginosus": 6,
    "Circus pygargus": 1,
}


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


def validate_reference_only_terminal(
    result: dict,
    *,
    frozen_receipt: dict,
    contract_bytes: bytes,
    first_result_bytes: bytes,
) -> dict[str, object]:
    """Require exact first result plus stable counts/provenance/source hashes."""
    pinned = frozen_receipt["freeze_and_first_access"]
    evidence = frozen_receipt["source_verification"]
    science = frozen_receipt["first_terminal"]
    if sha256(contract_bytes) != pinned["contract_sha256"]:
        raise ValueError("original pre-source scientific contract drifted")
    if sha256(first_result_bytes) != pinned["first_result_json_sha256"]:
        raise ValueError("frozen source-only first-result bytes drifted")
    if git_blob_sha(first_result_bytes) != pinned["result_file_git_blob_sha1"]:
        raise ValueError("frozen Git source-first-result blob changed")
    original = json.loads(first_result_bytes)
    if result != original:
        raise ValueError("official source-only replay differs from frozen first result")
    if result.get("contract_sha256") != pinned["contract_sha256"]:
        raise ValueError("source-only result is not bound to original contract")
    if (
        result.get("contract_id") != "bop-v3-v6-reference-only-roster-gate-v1"
        or result.get("gps_event_data_accessed") is not False
        or result.get("only_reference_data_access_authorized") is not True
        or result.get("old_original_terminal") != "empirical_state_prediction_mixed"
        or science.get("category") != EXPECTED_TERMINAL
        or result.get("identity_audit", {}).get("scientific_status") != EXPECTED_TERMINAL
        or result["identity_audit"].get("original_empirical_BOP_terminal_changed") is not False
    ):
        raise ValueError("source-only terminal or no-GPS boundary has changed")
    if (
        pinned["first_workflow_run_id"] != 40270328971
        or pinned["first_official_probe_job_id"] != 121401647193
        or pinned["first_result_artifact_id"] != 12627019951
        or pinned["first_result_artifact_zip_sha256"] != (
            "a75379cd04409e316f3b05d3d193ccaaea6bac360bfc817179e9dbdc7c2811f5"
        )
    ):
        raise ValueError("first successful official source-evidence identity changed")
    references = result.get("references")
    if not isinstance(references, list) or len(references) != 2:
        raise ValueError("exactly two reference-only source versions are required")
    if (
        [v.get("distinct_animal_ids") for v in references] != [35, 45]
        or [v.get("reference_rows") for v in references] != [35, 46]
        or [v.get("reference_bytes_sha256") for v in references] != evidence["source_reference_sha256s"]
        or [v.get("identity_taxon_roster_sha256") for v in references] != evidence["source_roster_sha256s"]
        or result.get("source_md5s") != evidence["source_reference_md5s"]
    ):
        raise ValueError("source roster/count/checksum provenance drifted")
    new = result["identity_audit"]
    if (
        new.get("applied_known_alias_count") != science["corrected_alias_count"]
        or new.get("overlapping_corrected_animal_ids") != science["corrected_id_matched_old_to_new_count"]
        or new.get("old_removed_out_of_scope_count") != science["removed_old_id_from_reference_count"]
        or new.get("old_distinct_animals") != science["old_unique_individual_ids"]
        or new.get("new_distinct_animals") != science["new_unique_individual_ids"]
        or new.get("new_id_candidates_count") != science["novel_id_candidate_count"]
        or new.get("new_id_candidates_by_species") != EXPECTED_SPECIES_COUNTS
        or new.get("new_id_candidates_by_species") != science["novel_id_candidates_by_species"]
        or new.get("one_stratum_minimum_count") != 10
        or sum(EXPECTED_SPECIES_COUNTS.values()) != 10
        or max(EXPECTED_SPECIES_COUNTS.values()) >= 10
        or any(new.get("new_id_candidates_within_stratum_meet_min_count", {}).values())
    ):
        raise ValueError("frozen new-animal identity and 90% rank support decision drifted")
    if science.get("no_species_met_threshold") is not True:
        raise ValueError("source 90% rank gate incorrectly promoted")
    if (
        frozen_receipt["interpretation"].get("historic_BOP_terminal_changed") is not False
        or frozen_receipt["interpretation"].get("no_GPS_access") is not True
        or frozen_receipt["interpretation"].get("version_identity_not_equal_independent_biological_replication") is not True
    ):
        raise ValueError("scientific claim ceiling was bypassed")
    return {
        "source_only_terminal": EXPECTED_TERMINAL,
        "additional_animal_ID_candidates": 10,
        "maximum_per_species": 6,
        "old_to_new_corrected_ID_overlap": 35,
        "source_members": 2,
        "model_or_GPS_outcome_accessed": False,
        "historical_BOP_terminal_changed": False,
        "frozen_first_result_sha256": pinned["first_result_json_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result", type=Path, default=FIRST,
        help="Metadata-only result from exactly the two pinned reference CSVs",
    )
    args = parser.parse_args()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    output = validate_reference_only_terminal(
        json.loads(args.result.read_text(encoding="utf-8")),
        frozen_receipt=receipt,
        contract_bytes=CONTRACT.read_bytes(),
        first_result_bytes=FIRST.read_bytes(),
    )
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
