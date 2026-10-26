#!/usr/bin/env python3
"""Post-first-result Dryad live metadata drift classification (operational v2).

The archived first result is strictly validated by its UNCHANGED v1 validator.
The latest official source response is *not* presumed byte-identical to the
first observation: changed source metadata must be reported as a source HOLD,
not mistaken for an empirical model error or silently recast as a new result.

This is explicitly a POST-RESULT operational repair, not a prospectively
frozen new scientific endpoint or authorization to inspect GPS files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

if __package__:
    from .validate_bop_dryad_external_schema_first_result_v1 import (
        CONTRACT, FIRST, RECEIPT, validate_dryad_first_result
    )
else:
    from validate_bop_dryad_external_schema_first_result_v1 import (
        CONTRACT, FIRST, RECEIPT, validate_dryad_first_result
    )

ORIGINAL_FIRST = FIRST.parent / "BOP_DRYAD_V1_ORIGINAL_ACTIONS_ARTIFACT_JSON.json"
_EXPECTED_CORRUPTED_VERSIONS = "433835a643d6685935835df2ac3c5ff609ffd7f4a623b5083da5c9f"
_EXPECTED_ORIGINAL_VERSIONS = "433835a643d6685935835df2ac3fbb9070d331ff609ffd7f4a623b5083da5c9f"

_HEX = re.compile(r"^[0-9a-f]{64}$")
_SAFE_FIELDS = frozenset((
    "contract_id", "contract_sha256", "dataset_doi", "first_public_readme_date",
    "documented_species_total", "documented_common_BOP_taxa_total",
    "documented_data_1a_individuals", "documented_data_2a_individuals",
    "feature_compatibility", "official_metadata_api", "small_non_gps_file_checks",
    "metadata_source_status", "individual_cross_study_identity_overlap_status",
    "original_BOP_RF_direct_external_transfer_status",
    "new_model_prospective_freeze_required", "candidate_admission",
    "raw_gps_or_height_outcomes_accessed",
    "BOP_existing_mixed_terminal_reclassified",
    "BOP_2026_same_study_count_gate_reopened", "schema_version"
))
_HOLD_CODES = frozenset(("SOURCE_HOLD", "SOURCE_READ"))
_API = ("dataset", "versions")
_SIDECARS = (
    "README.md",
    "Study_areas_bounding_boxes.csv",
    "Complete_succesful_breeding_seasons.csv",
)


def _diff_paths(first: object, live: object, prefix: str = "") -> tuple[str, ...]:
    """Return changed *field paths* only; never publish provider values."""
    if type(first) is not type(live):
        return (prefix or "$",)
    if isinstance(first, dict):
        keys = set(first) | set(live)
        changed = []
        for key in sorted(keys):
            path = f"{prefix}.{key}" if prefix else key
            if key not in first or key not in live:
                changed.append(path)
            else:
                changed.extend(_diff_paths(first[key], live[key], path))
        return tuple(changed)
    if isinstance(first, list):
        if len(first) != len(live):
            return (prefix + ".length",)
        return tuple(
            path
            for i, (a, b) in enumerate(zip(first, live))
            for path in _diff_paths(a, b, f"{prefix}[{i}]")
        )
    return () if first == live else (prefix or "$",)


def _digest_proper(value: object, field: str) -> bool:
    return isinstance(value, str) and bool(_HEX.fullmatch(value))


def classify_live_dryad_source_drift(
    live: dict,
    first_semantic: dict,
    receipt: dict,
    contract_bytes: bytes,
    semantic_bytes: bytes,
    original_artifact_bytes: bytes,
) -> dict[str, object]:
    """Split archived first-result correctness from independent LIVE source drift.

    Original RF/BOP scientific terminal remains immutable. If current source
    content differs, report a source HOLD with the changed field paths.
    New metadata cannot independently admit the candidate or renew a claim.
    """
    # Historical v1 validator still verifies its immutable semantic copy.
    # It is not silently repaired: that copy contains one truncated digest.
    validate_dryad_first_result(
        first_semantic, receipt, contract_bytes, semantic_bytes
    )
    expected_raw_sha = receipt["first_official_execution"][
        "artifact_raw_result_json_sha256"
    ]
    if hashlib.sha256(original_artifact_bytes).hexdigest() != expected_raw_sha:
        raise ValueError("original GitHub Actions source JSON checksum mismatch")
    first = json.loads(original_artifact_bytes)
    if (
        _diff_paths(first_semantic, first)
        != ("official_metadata_api.versions.sha256",)
        or first_semantic["official_metadata_api"]["versions"]["sha256"]
        != _EXPECTED_CORRUPTED_VERSIONS
        or first["official_metadata_api"]["versions"]["sha256"]
        != _EXPECTED_ORIGINAL_VERSIONS
    ):
        raise ValueError("historical v1 semantic-copy truncation not uniquely verified")

    if not isinstance(live, dict) or set(live) - _SAFE_FIELDS:
        raise ValueError("live Dryad report contains unauthorized fields")
    # These constants are *not* allowed to change even when upstream
    # response hashes or small-file availability change.
    fixed = (
        "schema_version", "contract_id", "contract_sha256", "dataset_doi",
        "first_public_readme_date",
        "documented_species_total", "documented_common_BOP_taxa_total",
        "documented_data_1a_individuals", "documented_data_2a_individuals",
        "feature_compatibility",
        "individual_cross_study_identity_overlap_status",
        "original_BOP_RF_direct_external_transfer_status",
        "new_model_prospective_freeze_required", "candidate_admission",
        "raw_gps_or_height_outcomes_accessed",
        "BOP_existing_mixed_terminal_reclassified",
        "BOP_2026_same_study_count_gate_reopened",
    )
    for key in fixed:
        if live.get(key) != first.get(key):
            raise ValueError(f"critical historical BOP or model-compatibility field changed: {key}")
    if (
        live["candidate_admission"] != "NOT_ADMITTED"
        or live["original_BOP_RF_direct_external_transfer_status"]
        != "ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
        or live["raw_gps_or_height_outcomes_accessed"] is not False
        or live["BOP_existing_mixed_terminal_reclassified"] is not False
    ):
        raise ValueError("live source probe attempts to promote an unadmitted endpoint")

    current_api = live.get("official_metadata_api")
    initial_api = first.get("official_metadata_api")
    current_files = live.get("small_non_gps_file_checks")
    if (
        not isinstance(current_api, dict)
        or set(current_api) != set(_API)
        or not isinstance(initial_api, dict)
        or set(initial_api) != set(_API)
        or not isinstance(current_files, dict)
        or set(current_files) != set(_SIDECARS)
        or not isinstance(live.get("metadata_source_status"), str)
    ):
        raise ValueError("live source report missing required provider roster")
    for name in _API:
        item = current_api[name]
        if not isinstance(item, dict) or item.get("status") not in _HOLD_CODES:
            raise ValueError("invalid official API status")
        if item["status"] == "SOURCE_READ":
            if not _digest_proper(item.get("sha256"), name):
                raise ValueError("API read without valid SHA256")
            if item.get("bytes_verified") is not True or item.get("json_status") != "VALID_JSON":
                raise ValueError("API read not validated as JSON")
        elif item.get("bytes_verified") is not False:
            raise ValueError("API source HOLD masquerading as read")
    for name in _SIDECARS:
        item = current_files[name]
        if not isinstance(item, dict) or item.get("status") not in _HOLD_CODES:
            raise ValueError("invalid sidecar read/HOLD status")
        if item["status"] == "SOURCE_READ":
            if not _digest_proper(item.get("sha256"), name) or item.get("bytes_verified") is not True:
                raise ValueError("sidecar read without valid source digest")
        elif item.get("bytes_verified") is not False:
            raise ValueError("sidecar source HOLD masquerading as read")

    observed = set(_diff_paths(first, live))
    source_access = any(
        current_api[name].get("status") != initial_api[name].get("status")
        for name in _API
    ) or any(
        current_files[name].get("status") != first["small_non_gps_file_checks"][name].get("status")
        for name in _SIDECARS
    )
    if source_access:
        status = "SOURCE_ACCESS_CHANGED_HOLD"
    elif observed:
        status = "SOURCE_METADATA_DRIFT_HOLD"
    else:
        status = "EXACT_FIRST_SOURCE_REPLAY"
    # Never emit source keys beyond approved path metadata; the detector does
    # not attempt to infer why version JSON changed.
    return {
        "schema_version": 2,
        "role": "post_result_live_source_drift_audit",
        "first_result_verified_unchanged": True,
        "original_actions_json_sha256_verified": expected_raw_sha,
        "malformed_historical_semantic_copy_retained": True,
        "semantic_copy_digest_truncation_reconciled_not_overwritten": True,
        "first_official_result_sha256": receipt["first_official_execution"][
            "artifact_raw_result_json_sha256"
        ],
        "classification": status,
        "changed_field_count": len(observed),
        "changed_field_paths": sorted(observed),
        "new_source_version_accepted_as_frozen_result": False,
        "candidate_admission": "NOT_ADMITTED",
        "original_BOP_RF_direct_external_transfer_status":
            "ORIGINAL_RF_PREDICTOR_INCOMPATIBLE",
        "raw_gps_or_height_outcomes_accessed": False,
        "BOP_existing_mixed_terminal_reclassified": False,
        "external_biological_validation_performed": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    semantic_bytes = FIRST.read_bytes()
    answer = classify_live_dryad_source_drift(
        json.loads(args.result.read_text(encoding="utf-8")),
        json.loads(semantic_bytes),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        CONTRACT.read_bytes(), semantic_bytes,
        ORIGINAL_FIRST.read_bytes(),
    )
    result = json.dumps(answer, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        if args.out.resolve() in (
            CONTRACT.resolve(), FIRST.resolve(), RECEIPT.resolve()
        ):
            raise ValueError("frozen first scientific evidence cannot be overwritten")
        args.out.write_text(result, encoding="utf-8")
    print(json.dumps({
        "classification": answer["classification"],
        "changed_field_paths": answer["changed_field_paths"],
        "original_BOP_terminal_changed": False,
        "candidate_admission": answer["candidate_admission"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
