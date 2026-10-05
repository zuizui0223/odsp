from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_generation_receipt import (
    GENERATION_RECEIPT_TYPE,
    create_training_process_generation_receipt,
)


def _freeze(tmp_path: Path) -> tuple[Path, dict]:
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
    (tmp_path / "train.dat").write_bytes(b"training\n")
    (tmp_path / "fit.py").write_text("def fit(seed): return seed\n", encoding="utf-8")
    plan = {
        "schema_version": 1,
        "training_process_id": "process-v1",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [{"role": "training", "path": "train.dat"}],
        "implementation_artifacts": [{"role": "fit", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {"penalty": 0.1},
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
    create_training_process_freeze_manifest(plan_path, manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest_path, manifest


def _declaration(tmp_path: Path, manifest: dict) -> Path:
    refits = []
    for row in manifest["refit_schedule"]:
        model_path = tmp_path / f"{row['refit_id']}.model"
        model_path.write_bytes(f"model::{row['refit_id']}\n".encode())
        refits.append(
            {
                "refit_id": row["refit_id"],
                "resample_seed": row["resample_seed"],
                "fit_seed": row["fit_seed"],
                "bootstrap_membership_sha256": row["bootstrap_membership_sha256"],
                "model_artifacts": [
                    {
                        "artifact_id": "primary_model",
                        "path": model_path.name,
                    }
                ],
            }
        )
    path = tmp_path / "generation.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "training_process_id": manifest["training_process_id"],
                "refits": refits,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_generation_receipt_binds_exact_schedule_and_model_bytes(tmp_path):
    manifest_path, manifest = _freeze(tmp_path)
    declaration = _declaration(tmp_path, manifest)
    out = tmp_path / "generation-receipt.json"
    result = create_training_process_generation_receipt(
        manifest_path, declaration, out
    )
    receipt = result["receipt"]

    assert receipt["receipt_type"] == GENERATION_RECEIPT_TYPE
    assert receipt["training_process_id"] == manifest["training_process_id"]
    assert receipt["refit_count"] == 8
    assert receipt["refit_ids"] == sorted(manifest["refit_ids"])
    assert len(receipt["upstream_model_artifact_snapshot"]) == 8
    assert all(len(row["sha256"]) == 64 for row in receipt["upstream_model_artifact_snapshot"])
    assert receipt["checks"]["model_artifact_bytes_bound"] is True
    assert receipt["boundaries"]["training_validation_separation_verified_here"] is False
    assert (
        receipt["boundaries"][
            "receipt_cryptographically_proves_fitting_code_consumed_declared_membership"
        ]
        is False
    )


def test_generation_receipt_rejects_seed_or_membership_mismatch(tmp_path):
    manifest_path, manifest = _freeze(tmp_path)
    declaration = _declaration(tmp_path, manifest)
    payload = json.loads(declaration.read_text(encoding="utf-8"))
    payload["refits"][0]["fit_seed"] += 1
    declaration.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="does not exactly match"):
        create_training_process_generation_receipt(
            manifest_path, declaration, tmp_path / "receipt.json"
        )


def test_generation_receipt_rejects_missing_or_extra_refit(tmp_path):
    manifest_path, manifest = _freeze(tmp_path)
    declaration = _declaration(tmp_path, manifest)
    payload = json.loads(declaration.read_text(encoding="utf-8"))
    payload["refits"].pop()
    declaration.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="does not exactly match"):
        create_training_process_generation_receipt(
            manifest_path, declaration, tmp_path / "receipt.json"
        )


def test_generation_receipt_never_overwrites(tmp_path):
    manifest_path, manifest = _freeze(tmp_path)
    declaration = _declaration(tmp_path, manifest)
    out = tmp_path / "receipt.json"
    create_training_process_generation_receipt(manifest_path, declaration, out)
    with pytest.raises(FileExistsError, match="will not be overwritten"):
        create_training_process_generation_receipt(manifest_path, declaration, out)
