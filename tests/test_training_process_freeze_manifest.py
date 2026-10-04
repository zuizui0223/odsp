from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    PROCESS_MANIFEST_TYPE,
    create_training_process_freeze_manifest,
    validate_training_process_freeze_plan,
)


def _plan(tmp_path: Path) -> Path:
    (tmp_path / "roster.csv").write_text(
        "unit,stratum\n"
        "u1,a\n"
        "u2,a\n"
        "u3,a\n"
        "u4,b\n"
        "u5,b\n"
        "u6,b\n",
        encoding="utf-8",
    )
    (tmp_path / "training.dat").write_bytes(b"frozen-training-bytes\n")
    (tmp_path / "fit.py").write_text(
        "def fit(seed): return seed\n",
        encoding="utf-8",
    )
    payload = {
        "schema_version": 1,
        "training_process_id": "bootstrap-process-v1",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [
            {"role": "training_data", "path": "training.dat"}
        ],
        "implementation_artifacts": [
            {"role": "fit_code", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {
            "penalty": 0.1,
            "standardize": True,
        },
        "refit_ids": [f"r{i:02d}" for i in range(8)],
        "master_seed": 20261005,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def test_freeze_manifest_binds_process_artifacts_seeds_and_memberships(tmp_path):
    plan = _plan(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    receipt = create_training_process_freeze_manifest(
        plan,
        manifest_path,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["manifest_type"] == PROCESS_MANIFEST_TYPE
    assert manifest["training_process_id"] == "bootstrap-process-v1"
    assert manifest["process_kind"] == PROCESS_KIND
    assert manifest["refit_count"] == 8
    assert manifest["training_roster"]["stratum_sizes"] == {"a": 3, "b": 3}
    assert len(manifest["refit_schedule"]) == 8
    assert len(
        {row["resample_seed"] for row in manifest["refit_schedule"]}
    ) == 8
    assert len(
        {row["fit_seed"] for row in manifest["refit_schedule"]}
    ) == 8
    assert all(
        len(row["bootstrap_membership_sha256"]) == 64
        for row in manifest["refit_schedule"]
    )
    assert len(receipt["manifest_sha256"]) == 64
    assert receipt["boundaries"]["independent_refit_draws_required"] is True
    assert (
        receipt["boundaries"][
            "arbitrary_supplied_refit_set_reinterpreted_as_process_sample"
        ]
        is False
    )


def test_freeze_manifest_is_reproducible_except_runtime_timestamp(tmp_path):
    plan = _plan(tmp_path)
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    create_training_process_freeze_manifest(plan, first_path)
    create_training_process_freeze_manifest(plan, second_path)
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))

    first.pop("frozen_at_utc")
    second.pop("frozen_at_utc")
    assert first == second


def test_freeze_manifest_never_overwrites(tmp_path):
    plan = _plan(tmp_path)
    manifest = tmp_path / "manifest.json"
    create_training_process_freeze_manifest(plan, manifest)
    with pytest.raises(FileExistsError, match="will not be overwritten"):
        create_training_process_freeze_manifest(plan, manifest)


def test_dependent_or_hand_picked_refit_process_is_rejected():
    payload = {
        "schema_version": 1,
        "training_process_id": "bad",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": None,
        },
        "training_data_artifacts": [
            {"role": "data", "path": "data.csv"}
        ],
        "implementation_artifacts": [
            {"role": "fit", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {},
        "refit_ids": [f"r{i}" for i in range(8)],
        "master_seed": 1,
        "resampling": {
            "kind": "kfold_partition",
            "replacement": False,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    with pytest.raises(ValueError, match="admits only independent"):
        validate_training_process_freeze_plan(payload)


def test_roster_cannot_smuggle_outcome_columns_into_process_definition(tmp_path):
    plan = _plan(tmp_path)
    (tmp_path / "roster.csv").write_text(
        "unit,stratum,outcome\n"
        "u1,a,1\n"
        "u2,a,0\n"
        "u3,a,1\n"
        "u4,b,0\n"
        "u5,b,1\n"
        "u6,b,0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must contain only unit"):
        create_training_process_freeze_manifest(
            plan,
            tmp_path / "manifest.json",
        )


def test_process_plan_has_no_caller_timestamp_field():
    payload = {
        "schema_version": 1,
        "training_process_id": "bad",
        "frozen_at_utc": "2000-01-01T00:00:00Z",
    }
    with pytest.raises(ValueError, match="unknown"):
        validate_training_process_freeze_plan(payload)
