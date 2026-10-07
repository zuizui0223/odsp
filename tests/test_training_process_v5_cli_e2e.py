from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path

import odsp.cli as cli


def _write_fixture(root: Path) -> None:
    (root / "train-roster.csv").write_text(
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
    (root / "train.dat").write_bytes(b"training-source\n")
    (root / "fit.py").write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id', required=True)\n"
        "p.add_argument('--membership', required=True)\n"
        "p.add_argument('--fit-seed', required=True, type=int)\n"
        "p.add_argument('--output-dir', required=True)\n"
        "a=p.parse_args()\n"
        "rows=json.loads(Path(a.membership).read_text())\n"
        "payload={'refit':a.refit_id,'seed':a.fit_seed,"
        "'n':sum(int(r['count']) for r in rows)}\n"
        "Path(a.output_dir,'model.json').write_text("
        "json.dumps(payload,sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    (root / "score.py").write_text(
        "import argparse, csv, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id', required=True)\n"
        "p.add_argument('--model-manifest', required=True)\n"
        "p.add_argument('--validation-data', required=True)\n"
        "p.add_argument('--scoring-spec', required=True)\n"
        "p.add_argument('--output', required=True)\n"
        "a=p.parse_args()\n"
        "mm=json.loads(Path(a.model_manifest).read_text())\n"
        "assert mm['refit_id']==a.refit_id\n"
        "model=json.loads(Path(mm['artifacts'][0]['path']).read_text())\n"
        "spec=json.loads(Path(a.scoring_spec).read_text())\n"
        "with Path(a.validation_data).open(newline='',encoding='utf-8') as h:\n"
        "    data=list(csv.DictReader(h))\n"
        "assert {r['row_id'] for r in data}=={r['row_id'] for r in spec['rows']}\n"
        "offset=(int(model['seed']) % 19)*0.0001\n"
        "rows=[]\n"
        "for row in reversed(spec['rows']):\n"
        "    rows.append({'row_id':row['row_id'],'scores':{"
        "'pooled':offset,'coarse':offset+0.60,'fine':offset+1.05}})\n"
        "Path(a.output).write_text(json.dumps({"
        "'refit_id':a.refit_id,'rows':rows},sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )

    refit_ids = [f"r{i:02d}" for i in range(8)]
    (root / "process-plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "training_process_id": "cli-e2e-process-v1",
                "training_roster": {
                    "path": "train-roster.csv",
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
                "fit_entrypoint": "fit.py:cli",
                "fit_parameters": {},
                "refit_ids": refit_ids,
                "master_seed": 20261006,
                "resampling": {
                    "kind": "stratified_unit_bootstrap_with_replacement",
                    "replacement": True,
                    "within_stratum_draw_size": "original_stratum_size",
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "managed-generation-plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "training_process_id": "cli-e2e-process-v1",
                "manifest_path": "process-manifest.json",
                "training_roster": {
                    "path": "train-roster.csv",
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
                    {
                        "artifact_id": "primary_model",
                        "relative_path": "model.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    lines = ["row_id,group_id,block_id,sample_weight"]
    for group in range(2):
        for block in range(8):
            lines.append(
                f"ext-{group}-{block},g{group},g{group}-b{block},1.0"
            )
    (root / "external-roster.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    (root / "external-freeze-plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "external_dataset_id": "cli-e2e-external-v1",
                "row_identity_namespace": "global-observation-id-v1",
                "roster": {
                    "path": "external-roster.csv",
                    "format": "csv",
                },
                "training_process_manifest_path": "process-manifest.json",
                "managed_generation_receipt_path": "managed-generation-receipt.json",
                "training_roster": {
                    "path": "train-roster.csv",
                    "format": "csv",
                    "unit_id_column": "unit",
                    "stratum_column": "stratum",
                },
                "score": {
                    "kind": "log",
                    "name": "log",
                    "orientation": "higher_is_better",
                    "common_scoring_rule": True,
                    "common_reference_measure": True,
                },
                "levels": [
                    {"name": "pooled", "information": []},
                    {"name": "coarse", "information": ["species"]},
                    {
                        "name": "fine",
                        "information": ["species", "context"],
                    },
                ],
                "certification": {
                    "component_one_sided_alpha": 0.05,
                    "minimum_refits": 8,
                    "minimum_blocks_per_group": 8,
                    "gain_tolerance": 0.0,
                },
                "scoring": {
                    "working_directory": ".",
                    "command": [
                        "{python_executable}",
                        "score.py",
                        "--refit-id",
                        "{refit_id}",
                        "--model-manifest",
                        "{model_manifest_path}",
                        "--validation-data",
                        "{validation_data_path}",
                        "--scoring-spec",
                        "{scoring_spec_path}",
                        "--output",
                        "{output_path}",
                    ],
                    "command_artifacts": ["score.py"],
                    "timeout_seconds": 30,
                    "environment_allowlist": [],
                    "validation_data_format": "csv",
                    "validation_row_id_column": "row_id",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_validation_after_freeze(root: Path) -> str:
    manifest = json.loads(
        (root / "external-freeze.json").read_text(encoding="utf-8")
    )
    frozen = str(manifest["frozen_at_utc"])
    stamp = datetime.fromisoformat(
        frozen[:-1] + "+00:00" if frozen.endswith("Z") else frozen
    )
    first_access = (
        (stamp + timedelta(seconds=1))
        .isoformat()
        .replace("+00:00", "Z")
    )

    lines = ["row_id,outcome"]
    for group in range(2):
        for block in range(8):
            lines.append(f"ext-{group}-{block},{(group + block) % 2}")
    (root / "external-data.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return first_access


def test_qualified_training_process_v5_cli_runs_full_external_chain(
    tmp_path, monkeypatch
):
    _write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert not Path("external-data.csv").exists()

    assert cli.main(
        [
            "experimental",
            "training-process",
            "freeze",
            "--plan",
            "process-plan.json",
            "--manifest-out",
            "process-manifest.json",
            "--out",
            "process-freeze-command.json",
        ]
    ) == 0
    assert Path("process-manifest.json").is_file()

    assert cli.main(
        [
            "experimental",
            "training-process",
            "generate",
            "--plan",
            "managed-generation-plan.json",
            "--output-root",
            "generated-refits",
            "--receipt-out",
            "managed-generation-receipt.json",
            "--out",
            "generation-command.json",
        ]
    ) == 0
    assert Path("managed-generation-receipt.json").is_file()

    # The external freeze is deliberately completed before the outcome-bearing
    # validation file exists.
    assert not Path("external-data.csv").exists()
    assert cli.main(
        [
            "experimental",
            "training-process",
            "external-freeze",
            "--plan",
            "external-freeze-plan.json",
            "--manifest-out",
            "external-freeze.json",
            "--receipt-out",
            "external-freeze-receipt.json",
            "--out",
            "external-freeze-command.json",
        ]
    ) == 0
    assert not Path("external-data.csv").exists()

    first_access = _write_validation_after_freeze(tmp_path)

    assert cli.main(
        [
            "experimental",
            "training-process",
            "external-score",
            "--freeze-manifest",
            "external-freeze.json",
            "--freeze-receipt",
            "external-freeze-receipt.json",
            "--external-roster",
            "external-roster.csv",
            "--external-roster-format",
            "csv",
            "--managed-generation-receipt",
            "managed-generation-receipt.json",
            "--generated-model-root",
            "generated-refits",
            "--validation-data",
            "external-data.csv",
            "--output-root",
            "external-score-runs",
            "--score-bundle-out",
            "external-score-bundle.json",
            "--scoring-receipt-out",
            "managed-scoring-receipt.json",
            "--out",
            "external-score-command.json",
        ]
    ) == 0

    (tmp_path / "external-run.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "external_freeze_manifest_path": "external-freeze.json",
                "external_freeze_receipt_path": "external-freeze-receipt.json",
                "managed_scoring_receipt_path": "managed-scoring-receipt.json",
                "score_bundle_path": "external-score-bundle.json",
                "validation_data_path": "external-data.csv",
                "external_roster": {
                    "path": "external-roster.csv",
                    "format": "csv",
                },
                "training_process_manifest_path": "process-manifest.json",
                "managed_generation_receipt_path": "managed-generation-receipt.json",
                "training_roster_path": "train-roster.csv",
                "external_outcomes_first_accessed_at_utc": first_access,
            }
        ),
        encoding="utf-8",
    )

    assert cli.main(
        [
            "experimental",
            "training-process",
            "external-run",
            "--contract",
            "external-run.json",
            "--out",
            "external-result.json",
        ]
    ) == 0

    result = json.loads(
        Path("external-result.json").read_text(encoding="utf-8")
    )
    assert result["receipt_type"] == (
        "odsp_untouched_external_training_process_v5_endpoint_v1"
    )
    assert result["freeze_precedes_declared_first_outcome_access"] is True
    assert result["score_tensor_derived_by_managed_scoring"] is True
    assert result["training_source_frame_validation_disjoint"] is True
    assert result["qualification_evidence_snapshot_verified"] is True
    assert result["implementation_source_snapshot_verified"] is True
    assert result["runtime_environment_snapshot_verified"] is True
    assert result["fixed_set_results_reclassified"] is False
    assert result["certification"]["certification"]["process_mean_certified_transfer_ceiling"] == "fine"
