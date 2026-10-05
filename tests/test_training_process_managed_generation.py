from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_managed_generation import (
    MANAGED_GENERATION_RECEIPT_TYPE,
    run_managed_training_process_generation,
    validate_managed_generation_plan,
)


def _setup(tmp_path: Path) -> Path:
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
    (tmp_path / "train.dat").write_bytes(b"training-source\n")
    fit_script = tmp_path / "fit.py"
    fit_script.write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id', required=True)\n"
        "p.add_argument('--membership', required=True)\n"
        "p.add_argument('--fit-seed', required=True, type=int)\n"
        "p.add_argument('--output-dir', required=True)\n"
        "a=p.parse_args()\n"
        "rows=json.loads(Path(a.membership).read_text())\n"
        "payload={'refit_id':a.refit_id,'fit_seed':a.fit_seed,"
        "'draw_count':sum(int(r['count']) for r in rows),"
        "'positive_units':sum(int(r['count'])>0 for r in rows)}\n"
        "Path(a.output_dir,'model.json').write_text(json.dumps(payload, sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    freeze_plan = {
        "schema_version": 1,
        "training_process_id": "managed-bootstrap-v1",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [
            {"role": "training", "path": "train.dat"}
        ],
        "implementation_artifacts": [
            {"role": "fit_code", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:managed_cli",
        "fit_parameters": {},
        "refit_ids": [f"r{i:02d}" for i in range(8)],
        "master_seed": 20261005,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    freeze_path = tmp_path / "freeze-plan.json"
    freeze_path.write_text(json.dumps(freeze_plan), encoding="utf-8")
    create_training_process_freeze_manifest(
        freeze_path, tmp_path / "manifest.json"
    )

    managed_plan = {
        "schema_version": 1,
        "training_process_id": "managed-bootstrap-v1",
        "manifest_path": "manifest.json",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "working_directory": ".",
        "command": [
            "{python_executable}",
            "fit.py",
            "--refit-id",
            "{refit_id}",
            "--membership",
            "{membership_path}",
            "--fit-seed",
            "{fit_seed}",
            "--output-dir",
            "{output_dir}",
        ],
        "command_artifacts": ["fit.py"],
        "timeout_seconds": 30,
        "environment_allowlist": [],
        "output_artifacts": [
            {"artifact_id": "primary_model", "relative_path": "model.json"}
        ],
    }
    plan_path = tmp_path / "managed-plan.json"
    plan_path.write_text(json.dumps(managed_plan), encoding="utf-8")
    return plan_path


def test_managed_generation_materializes_and_executes_all_frozen_refits(tmp_path):
    plan = _setup(tmp_path)
    result = run_managed_training_process_generation(
        plan,
        tmp_path / "outputs",
        tmp_path / "managed-receipt.json",
    )
    receipt = result["receipt"]
    assert receipt["receipt_type"] == MANAGED_GENERATION_RECEIPT_TYPE
    assert receipt["training_process_id"] == "managed-bootstrap-v1"
    assert receipt["refit_count"] == 8
    assert len(receipt["executions"]) == 8
    assert len(receipt["command_artifact_snapshot"][0]["sha256"]) == 64
    assert receipt["fit_environment_snapshot"]["python"]["implementation"]
    assert receipt["fit_environment_snapshot"]["distributions"]
    assert receipt["boundaries"]["validation_outcomes_read"] is False
    assert receipt["boundaries"]["shell_used"] is False
    assert receipt["boundaries"]["exact_membership_digest_verified_before_each_fit"] is True

    seeds = set()
    artifact_hashes = set()
    for row in receipt["executions"]:
        assert row["return_code"] == 0
        assert len(row["membership_semantic_sha256"]) == 64
        assert len(row["membership_file_sha256"]) == 64
        assert len(row["stdout_sha256"]) == 64
        assert len(row["stderr_sha256"]) == 64
        assert len(row["artifacts"]) == 1
        seeds.add(row["fit_seed"])
        artifact_hashes.add(row["artifacts"][0]["sha256"])
    assert len(seeds) == 8
    assert len(artifact_hashes) == 8

    json.dumps(receipt, allow_nan=False)


def test_managed_generation_is_non_overwriting(tmp_path):
    plan = _setup(tmp_path)
    output = tmp_path / "outputs"
    receipt = tmp_path / "receipt.json"
    run_managed_training_process_generation(plan, output, receipt)
    with pytest.raises(FileExistsError):
        run_managed_training_process_generation(
            plan, output, tmp_path / "other-receipt.json"
        )
    with pytest.raises(FileExistsError):
        run_managed_training_process_generation(
            plan, tmp_path / "other-output", receipt
        )


def test_managed_plan_requires_explicit_process_inputs():
    bad = {
        "schema_version": 1,
        "training_process_id": "p",
        "manifest_path": "m.json",
        "training_roster": {
            "path": "r.csv",
            "format": "csv",
            "unit_id_column": "id",
            "stratum_column": None,
        },
        "working_directory": ".",
        "command": ["python", "fit.py", "{refit_id}", "{fit_seed}", "{output_dir}"],
        "command_artifacts": ["fit.py"],
        "timeout_seconds": 30,
        "environment_allowlist": [],
        "output_artifacts": [
            {"artifact_id": "m", "relative_path": "m.bin"}
        ],
    }
    with pytest.raises(ValueError, match="membership_path"):
        validate_managed_generation_plan(bad)
