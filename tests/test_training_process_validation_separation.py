from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_validation_separation import (
    SEPARATION_RECEIPT_TYPE,
    create_training_process_validation_separation_receipt,
)


def _freeze(tmp_path: Path):
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
    manifest_path = tmp_path / "manifest.json"
    create_training_process_freeze_manifest(
        plan_path,
        manifest_path,
    )
    return plan_path, manifest_path


def test_process_support_disjoint_receipt_is_stronger_than_realized_refits(
    tmp_path: Path,
):
    plan, manifest = _freeze(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nv2\nv3\n",
        encoding="utf-8",
    )
    out = tmp_path / "separation.json"
    result = create_training_process_validation_separation_receipt(
        manifest,
        plan,
        validation,
        out,
    )
    receipt = result["receipt"]

    assert receipt["receipt_type"] == SEPARATION_RECEIPT_TYPE
    assert receipt["overlap_count"] == 0
    assert receipt["process_support_disjoint"] is True
    assert receipt["consequence"][
        "every_possible_refit_draw_from_frozen_roster_is_validation_disjoint"
    ] is True
    assert receipt["consequence"][
        "realized_refit_enumeration_required"
    ] is False
    assert receipt["boundaries"]["validation_outcomes_read"] is False
    assert receipt["boundaries"]["row_ids_emitted"] is False
    assert "t1" not in out.read_text(encoding="utf-8")
    assert "v1" not in out.read_text(encoding="utf-8")


def test_overlap_hard_stops_before_receipt_is_written(tmp_path: Path):
    plan, manifest = _freeze(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nt3\n",
        encoding="utf-8",
    )
    out = tmp_path / "separation.json"
    with pytest.raises(ValueError, match="overlaps"):
        create_training_process_validation_separation_receipt(
            manifest,
            plan,
            validation,
            out,
        )
    assert not out.exists()


def test_validation_roster_cannot_include_outcomes(tmp_path: Path):
    plan, manifest = _freeze(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id,outcome\nv1,1\nv2,0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one"):
        create_training_process_validation_separation_receipt(
            manifest,
            plan,
            validation,
            tmp_path / "separation.json",
        )


def test_modified_training_roster_cannot_reuse_frozen_manifest(
    tmp_path: Path,
):
    plan, manifest = _freeze(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nv2\n",
        encoding="utf-8",
    )
    (tmp_path / "training.csv").write_text(
        "unit,stratum\n"
        "t1,a\n"
        "t2,a\n"
        "CHANGED,a\n"
        "t4,b\n"
        "t5,b\n"
        "t6,b\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="do not match"):
        create_training_process_validation_separation_receipt(
            manifest,
            plan,
            validation,
            tmp_path / "separation.json",
        )


def test_separation_receipt_never_overwrites(tmp_path: Path):
    plan, manifest = _freeze(tmp_path)
    validation = tmp_path / "validation.csv"
    validation.write_text(
        "row_id\nv1\nv2\n",
        encoding="utf-8",
    )
    out = tmp_path / "separation.json"
    create_training_process_validation_separation_receipt(
        manifest,
        plan,
        validation,
        out,
    )
    with pytest.raises(FileExistsError, match="will not be overwritten"):
        create_training_process_validation_separation_receipt(
            manifest,
            plan,
            validation,
            out,
        )
