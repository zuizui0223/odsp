from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from odsp.training_process_external_freeze_v1 import (
    create_training_process_external_freeze_manifest_v1,
)
from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_managed_generation import (
    run_managed_training_process_generation,
)
from odsp.untouched_external_training_process_v1 import (
    run_untouched_external_training_process_v1,
)


def _process(tmp_path: Path):
    (tmp_path / "training_roster.csv").write_text(
        "unit,stratum\n"
        "u1,a\n"
        "u2,a\n"
        "u3,a\n"
        "u4,a\n"
        "u5,b\n"
        "u6,b\n"
        "u7,b\n"
        "u8,b\n",
        encoding="utf-8",
    )
    (tmp_path / "training.dat").write_bytes(b"frozen-training\n")
    (tmp_path / "fit.py").write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id',required=True)\n"
        "p.add_argument('--membership',required=True)\n"
        "p.add_argument('--fit-seed',required=True,type=int)\n"
        "p.add_argument('--output-dir',required=True)\n"
        "a=p.parse_args()\n"
        "rows=json.loads(Path(a.membership).read_text())\n"
        "Path(a.output_dir,'model.json').write_text("
        "json.dumps({'refit':a.refit_id,'seed':a.fit_seed,'draws':sum(r['count'] for r in rows)},sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    refit_ids = [f"r{i:02d}" for i in range(8)]
    freeze_plan = {
        "schema_version": 1,
        "training_process_id": "external-process-v1-test",
        "training_roster": {
            "path": "training_roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [
            {"role": "training", "path": "training.dat"}
        ],
        "implementation_artifacts": [
            {"role": "fit", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:cli",
        "fit_parameters": {},
        "refit_ids": refit_ids,
        "master_seed": 20261005,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    freeze_plan_path = tmp_path / "process-freeze-plan.json"
    freeze_plan_path.write_text(json.dumps(freeze_plan), encoding="utf-8")
    manifest_path = tmp_path / "process-manifest.json"
    create_training_process_freeze_manifest(
        freeze_plan_path, manifest_path
    )

    managed = {
        "schema_version": 1,
        "training_process_id": "external-process-v1-test",
        "manifest_path": "process-manifest.json",
        "training_roster": {
            "path": "training_roster.csv",
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
    managed_path = tmp_path / "managed-plan.json"
    managed_path.write_text(json.dumps(managed), encoding="utf-8")
    managed_result = run_managed_training_process_generation(
        managed_path,
        tmp_path / "models",
        tmp_path / "managed-receipt.json",
    )
    return {
        "manifest": manifest_path,
        "receipt": tmp_path / "managed-receipt.json",
        "receipt_sha": managed_result["receipt_sha256"],
        "roster": tmp_path / "training_roster.csv",
        "refit_ids": tuple(refit_ids),
    }


def _external_roster(tmp_path: Path, *, overlap: bool = False, extra_column: bool = False):
    path = tmp_path / "external-roster.csv"
    fieldnames = ["row_id", "group_id", "block_id", "sample_weight"]
    if extra_column:
        fieldnames.append("outcome")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for g in range(2):
            for b in range(8):
                row = {
                    "row_id": "u3" if overlap and g == 0 and b == 0 else f"ext-{g}-{b}",
                    "group_id": f"g{g}",
                    "block_id": f"g{g}-b{b}",
                    "sample_weight": 1.0,
                }
                if extra_column:
                    row["outcome"] = 1
                writer.writerow(row)
    return path


def _external_freeze(tmp_path: Path, process: dict, roster: Path):
    plan = {
        "schema_version": 1,
        "external_dataset_id": "untouched-external-test-v1",
        "external_roster": {
            "path": roster.name,
            "format": "csv",
        },
        "training_process": {
            "manifest_path": process["manifest"].name,
            "managed_generation_receipt_path": process["receipt"].name,
            "training_roster_path": process["roster"].name,
            "row_identity_namespace": "global-observation-id-v1",
            "training_roster_format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "score": {
            "kind": "log_score",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "levels": [
            {"name": "pooled", "information": [], "score_column": "score_pooled"},
            {
                "name": "coarse",
                "information": ["species"],
                "score_column": "score_coarse",
            },
            {
                "name": "fine",
                "information": ["species", "context"],
                "score_column": "score_fine",
            },
        ],
        "certification": {
            "alternative": "greater",
            "component_one_sided_alpha": 0.05,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }
    plan_path = tmp_path / "external-freeze-plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    manifest = tmp_path / "external-freeze.json"
    receipt = create_training_process_external_freeze_manifest_v1(
        plan_path, manifest
    )
    return manifest, receipt


def _score_table(tmp_path: Path, process: dict, *, drop_last: bool = False, duplicate: bool = False):
    path = tmp_path / "external-scores.csv"
    rows = []
    for g in range(2):
        for b in range(8):
            row_id = f"ext-{g}-{b}"
            for refit in process["refit_ids"]:
                rows.append(
                    {
                        "row_id": row_id,
                        "refit_id": refit,
                        "score_pooled": 0.0,
                        "score_coarse": 0.5,
                        "score_fine": 0.9,
                    }
                )
    if drop_last:
        rows.pop()
    if duplicate:
        rows.append(dict(rows[0]))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_id",
                "refit_id",
                "score_pooled",
                "score_coarse",
                "score_fine",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def _runtime_contract(
    tmp_path: Path,
    process: dict,
    freeze_manifest: Path,
    freeze_receipt: dict,
    scores: Path,
):
    runtime = {
        "schema_version": 1,
        "freeze_manifest": {
            "path": freeze_manifest.name,
            "sha256": freeze_receipt["manifest_sha256"],
            "frozen_at_utc": freeze_receipt["frozen_at_utc"],
        },
        "score_table": {
            "path": scores.name,
            "format": "csv",
        },
        "training_process_runtime": {
            "manifest_path": process["manifest"].name,
            "managed_generation_receipt_path": process["receipt"].name,
            "training_roster_path": process["roster"].name,
            "training_roster_format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
    }
    path = tmp_path / "external-runtime.json"
    path.write_text(json.dumps(runtime), encoding="utf-8")
    return path


def test_end_to_end_process_external_freeze_and_certification(tmp_path):
    process = _process(tmp_path)
    roster = _external_roster(tmp_path)
    freeze, freeze_receipt = _external_freeze(
        tmp_path, process, roster
    )
    scores = _score_table(tmp_path, process)
    runtime = _runtime_contract(
        tmp_path, process, freeze, freeze_receipt, scores
    )
    result = run_untouched_external_training_process_v1(runtime)
    assert result.freeze_manifest_semantics_verified is True
    assert result.external_row_refit_cartesian_product_verified is True
    assert result.external_group_block_weight_design_from_freeze_only is True
    assert result.qualification_evidence_snapshot_verified is True
    assert result.implementation_source_snapshot_verified is True
    assert result.runtime_environment_snapshot_verified is True
    assert result.training_process_provenance_verified is True
    assert result.historical_no_prior_external_outcome_access_machine_proven is False
    assert result.certification.certification.process_mean_certified_transfer_ceiling == "fine"
    json.dumps(result.as_dict(), allow_nan=False)


def test_external_freeze_rejects_training_source_overlap(tmp_path):
    process = _process(tmp_path)
    roster = _external_roster(tmp_path, overlap=True)
    with pytest.raises(ValueError, match="overlaps"):
        _external_freeze(tmp_path, process, roster)


def test_external_freeze_rejects_outcome_column(tmp_path):
    process = _process(tmp_path)
    roster = _external_roster(tmp_path, extra_column=True)
    with pytest.raises(ValueError, match="exactly"):
        _external_freeze(tmp_path, process, roster)


@pytest.mark.parametrize("mode", ["missing", "duplicate"])
def test_external_runtime_requires_exact_row_refit_cartesian_product(tmp_path, mode):
    process = _process(tmp_path)
    roster = _external_roster(tmp_path)
    freeze, freeze_receipt = _external_freeze(
        tmp_path, process, roster
    )
    scores = _score_table(
        tmp_path,
        process,
        drop_last=mode == "missing",
        duplicate=mode == "duplicate",
    )
    runtime = _runtime_contract(
        tmp_path, process, freeze, freeze_receipt, scores
    )
    with pytest.raises(ValueError, match="Cartesian|duplicate"):
        run_untouched_external_training_process_v1(runtime)


def test_external_score_table_cannot_override_frozen_design_metadata(tmp_path):
    process = _process(tmp_path)
    roster = _external_roster(tmp_path)
    freeze, freeze_receipt = _external_freeze(
        tmp_path, process, roster
    )
    scores = _score_table(tmp_path, process)
    text = scores.read_text(encoding="utf-8")
    lines = text.splitlines()
    lines[0] += ",group_id"
    lines[1] += ",g999"
    for i in range(2, len(lines)):
        lines[i] += ",g0"
    scores.write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime = _runtime_contract(
        tmp_path, process, freeze, freeze_receipt, scores
    )
    with pytest.raises(ValueError, match="columns"):
        run_untouched_external_training_process_v1(runtime)
