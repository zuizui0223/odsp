from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_validation_separation_receipt import (
    SEPARATION_RECEIPT_TYPE,
    create_training_process_validation_separation_receipt,
)


def _fixture(tmp_path: Path):
    (tmp_path / "training.csv").write_text(
        "unit,stratum\n"
        "t1,a\n"
        "t2,a\n"
        "t3,a\n"
        "t4,b\n"
        "t5,b\n"
        "t6,b\n",
        encoding="utf-8",
    )
    (tmp_path / "train.dat").write_bytes(b"training\n")
    (tmp_path / "fit.py").write_text(
        "def fit(seed): return seed\n",
        encoding="utf-8",
    )
    plan = {
        "schema_version": 1,
        "training_process_id": "process-v1",
        "training_roster": {
            "path": "training.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [
            {"role": "training", "path": "train.dat"}
        ],
        "implementation_artifacts": [
            {"role": "fit", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {},
        "refit_ids": [f"r{i:02d}" for i in range(8)],
        "master_seed": 20261005,
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
    return manifest, tmp_path / "training.csv"


def test_receipt_wraps_canonical_full_frame_audit_and_locks_validation_bytes(
    tmp_path: Path,
):
    manifest, training = _fixture(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nv2\nv3\n",
        encoding="utf-8",
    )
    out = tmp_path / "separation.json"
    result = create_training_process_validation_separation_receipt(
        manifest,
        training,
        validation,
        out,
        row_identity_namespace="global-observation-id-v1",
        training_roster_format="csv",
        training_unit_id_column="unit",
        training_stratum_column="stratum",
    )
    receipt = result["receipt"]
    assert receipt["receipt_type"] == SEPARATION_RECEIPT_TYPE
    assert receipt["training_source_frame_validation_disjoint"] is True
    assert receipt["entire_training_source_frame_checked"] is True
    assert receipt["realized_refit_memberships_only"] is False
    assert receipt["row_identity_namespace"] == "global-observation-id-v1"
    assert len(receipt["validation_roster_file_sha256"]) == 64
    assert len(receipt["validation_row_id_semantic_sha256"]) == 64
    assert receipt["canonical_audit"][
        "automatic_identity_crosswalk_inference"
    ] is False
    text = out.read_text(encoding="utf-8")
    assert "t1" not in text
    assert "v1" not in text


def test_overlap_hard_stops_and_does_not_write_receipt(tmp_path: Path):
    manifest, training = _fixture(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nt3\n",
        encoding="utf-8",
    )
    out = tmp_path / "separation.json"
    with pytest.raises(ValueError, match="not disjoint"):
        create_training_process_validation_separation_receipt(
            manifest,
            training,
            validation,
            out,
            row_identity_namespace="global-observation-id-v1",
            training_roster_format="csv",
            training_unit_id_column="unit",
            training_stratum_column="stratum",
        )
    assert not out.exists()


def test_validation_roster_must_be_metadata_only(tmp_path: Path):
    manifest, training = _fixture(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id,outcome\nv1,1\nv2,0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one"):
        create_training_process_validation_separation_receipt(
            manifest,
            training,
            validation,
            tmp_path / "separation.json",
            row_identity_namespace="global-observation-id-v1",
            training_roster_format="csv",
            training_unit_id_column="unit",
            training_stratum_column="stratum",
        )


def test_identity_namespace_is_mandatory(tmp_path: Path):
    manifest, training = _fixture(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text("row_id\nv1\nv2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row_identity_namespace"):
        create_training_process_validation_separation_receipt(
            manifest,
            training,
            validation,
            tmp_path / "separation.json",
            row_identity_namespace="",
            training_roster_format="csv",
            training_unit_id_column="unit",
            training_stratum_column="stratum",
        )


def test_receipt_never_overwrites(tmp_path: Path):
    manifest, training = _fixture(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text("row_id\nv1\nv2\n", encoding="utf-8")
    out = tmp_path / "separation.json"
    settings = dict(
        row_identity_namespace="global-observation-id-v1",
        training_roster_format="csv",
        training_unit_id_column="unit",
        training_stratum_column="stratum",
    )
    create_training_process_validation_separation_receipt(
        manifest,
        training,
        validation,
        out,
        **settings,
    )
    with pytest.raises(FileExistsError, match="will not be overwritten"):
        create_training_process_validation_separation_receipt(
            manifest,
            training,
            validation,
            out,
            **settings,
        )
