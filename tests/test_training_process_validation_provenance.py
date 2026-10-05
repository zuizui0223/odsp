from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


def _manifest(tmp_path: Path):
    (tmp_path / "roster.csv").write_text(
        "unit,stratum\n"
        "u1,a\n"
        "u2,a\n"
        "u3,b\n"
        "u4,b\n",
        encoding="utf-8",
    )
    (tmp_path / "train.dat").write_bytes(b"training\n")
    (tmp_path / "fit.py").write_text("def fit(x): return x\n", encoding="utf-8")
    plan = {
        "schema_version": 1,
        "training_process_id": "p",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [{"role": "training", "path": "train.dat"}],
        "implementation_artifacts": [{"role": "fit", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {},
        "refit_ids": [f"r{i}" for i in range(8)],
        "master_seed": 10,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    create_training_process_freeze_manifest(plan_path, manifest)
    return manifest, tmp_path / "roster.csv"


def test_entire_source_frame_disjointness_is_checked(tmp_path):
    manifest, roster = _manifest(tmp_path)
    result = audit_training_process_validation_frame_separation(
        manifest,
        roster,
        ("v1", "v2", "v3"),
        row_identity_namespace="global-observation-id-v1",
        roster_format="csv",
        unit_id_column="unit",
        stratum_column="stratum",
    )
    assert result.training_source_frame_validation_disjoint is True
    assert result.overlapping_unit_count == 0
    assert result.entire_training_source_frame_checked is True
    assert result.realized_refit_memberships_only is False
    assert result.validation_outcomes_required is False
    assert result.overlapping_row_ids_emitted is False


def test_any_source_frame_overlap_is_detected_even_if_not_known_to_be_realized(tmp_path):
    manifest, roster = _manifest(tmp_path)
    result = audit_training_process_validation_frame_separation(
        manifest,
        roster,
        ("v1", "u3"),
        row_identity_namespace="global-observation-id-v1",
        roster_format="csv",
        unit_id_column="unit",
        stratum_column="stratum",
    )
    assert result.training_source_frame_validation_disjoint is False
    assert result.overlapping_unit_count == 1
    assert result.separation_category == "training_source_frame_validation_leakage"
    assert "u3" not in str(result.as_dict())


def test_roster_bytes_must_match_frozen_manifest(tmp_path):
    manifest, roster = _manifest(tmp_path)
    roster.write_text(
        "unit,stratum\nu1,a\nu2,a\nu3,b\nu5,b\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="file bytes"):
        audit_training_process_validation_frame_separation(
            manifest,
            roster,
            ("v1", "v2"),
            row_identity_namespace="global-observation-id-v1",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
        )


def test_validation_ids_must_be_unique_and_namespace_explicit(tmp_path):
    manifest, roster = _manifest(tmp_path)
    with pytest.raises(ValueError, match="unique"):
        audit_training_process_validation_frame_separation(
            manifest,
            roster,
            ("v1", "v1"),
            row_identity_namespace="global-observation-id-v1",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
        )
    with pytest.raises(ValueError, match="row_identity_namespace"):
        audit_training_process_validation_frame_separation(
            manifest,
            roster,
            ("v1", "v2"),
            row_identity_namespace="",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
        )
