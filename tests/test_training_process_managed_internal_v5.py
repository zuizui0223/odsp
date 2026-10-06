from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_internal_freeze_v1 import (
    create_training_process_v5_internal_validation_freeze,
)
from odsp.training_process_managed_generation import (
    run_managed_training_process_generation,
)
from odsp.training_process_managed_internal_scoring import (
    run_managed_internal_scoring_v1,
)
from odsp.training_process_managed_internal_v5 import (
    MANAGED_INTERNAL_RECEIPT_TYPE,
    run_managed_internal_training_process_v5,
)


def _setup(tmp_path: Path) -> dict[str, object]:
    training_roster = tmp_path / "training-roster.csv"
    training_roster.write_text(
        "unit_id,stratum\n"
        "u1,a\nu2,a\nu3,a\nu4,a\n"
        "u5,b\nu6,b\nu7,b\nu8,b\n",
        encoding="utf-8",
    )
    (tmp_path / "training-data.csv").write_text(
        "unit_id,x\n"
        "u1,1\nu2,2\nu3,3\nu4,4\n"
        "u5,5\nu6,6\nu7,7\nu8,8\n",
        encoding="utf-8",
    )
    fit = tmp_path / "fit.py"
    fit.write_text(
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
    score = tmp_path / "score.py"
    score.write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id',required=True)\n"
        "p.add_argument('--models',required=True)\n"
        "p.add_argument('--validation-data',required=True)\n"
        "p.add_argument('--scoring-spec',required=True)\n"
        "p.add_argument('--output',required=True)\n"
        "a=p.parse_args()\n"
        "models=json.loads(Path(a.models).read_text())\n"
        "assert models['refit_id']==a.refit_id\n"
        "spec=json.loads(Path(a.scoring_spec).read_text())\n"
        "rows=[]\n"
        "for row in spec['rows']:\n"
        "    rows.append({'row_id':row['row_id'],'scores':{'pooled':0.0,'coarse':0.5,'fine':0.9}})\n"
        "Path(a.output).write_text(json.dumps({'refit_id':a.refit_id,'rows':rows},sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )

    refit_ids = [f"r{i:02d}" for i in range(8)]
    freeze_plan = {
        "schema_version": 1,
        "training_process_id": "managed-internal-test-v1",
        "training_roster": {
            "path": "training-roster.csv",
            "format": "csv",
            "unit_id_column": "unit_id",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [
            {"role": "training_table", "path": "training-data.csv"}
        ],
        "implementation_artifacts": [{"role": "fit_code", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:main",
        "fit_parameters": {},
        "refit_ids": refit_ids,
        "master_seed": 20261006,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    freeze_plan_path = tmp_path / "training-process-plan.json"
    freeze_plan_path.write_text(json.dumps(freeze_plan), encoding="utf-8")
    process_manifest = tmp_path / "training-process-freeze.json"
    create_training_process_freeze_manifest(
        freeze_plan_path, process_manifest
    )

    generation_plan = {
        "schema_version": 1,
        "training_process_id": "managed-internal-test-v1",
        "manifest_path": "training-process-freeze.json",
        "training_roster": {
            "path": "training-roster.csv",
            "format": "csv",
            "unit_id_column": "unit_id",
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
    generation_plan_path = tmp_path / "managed-generation-plan.json"
    generation_plan_path.write_text(json.dumps(generation_plan), encoding="utf-8")
    generated_root = tmp_path / "generated"
    generation_receipt = tmp_path / "managed-generation-receipt.json"
    run_managed_training_process_generation(
        generation_plan_path, generated_root, generation_receipt
    )

    validation_roster = tmp_path / "validation-roster.csv"
    validation_data = tmp_path / "validation-data.csv"
    roster_lines = ["row_id,group_id,block_id,sample_weight"]
    data_lines = ["row_id,outcome"]
    groups: list[str] = []
    blocks: list[str] = []
    row_ids: list[str] = []
    weights: list[float] = []
    for g in range(2):
        for b in range(8):
            row_id = f"v-{g}-{b}"
            group = f"g{g}"
            block = f"g{g}-b{b}"
            roster_lines.append(f"{row_id},{group},{block},1.0")
            data_lines.append(f"{row_id},{(g+b)%2}")
            row_ids.append(row_id)
            groups.append(group)
            blocks.append(block)
            weights.append(1.0)
    validation_roster.write_text("\n".join(roster_lines) + "\n", encoding="utf-8")
    validation_data.write_text("\n".join(data_lines) + "\n", encoding="utf-8")

    internal_plan = {
        "schema_version": 1,
        "validation_dataset_id": "heldout-validation-v1",
        "row_identity_namespace": "global-observation-id-v1",
        "roster": {"path": "validation-roster.csv", "format": "csv"},
        "training_process_manifest_path": "training-process-freeze.json",
        "managed_generation_receipt_path": "managed-generation-receipt.json",
        "training_roster": {
            "path": "training-roster.csv",
            "format": "csv",
            "unit_id_column": "unit_id",
            "stratum_column": "stratum",
        },
        "score": {
            "kind": "log",
            "name": "log_predictive_probability",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "levels": [
            {"name": "pooled", "information": []},
            {"name": "coarse", "information": ["identity"]},
            {"name": "fine", "information": ["identity", "context"]},
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
                "--models",
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
    internal_plan_path = tmp_path / "internal-freeze-plan.json"
    internal_plan_path.write_text(json.dumps(internal_plan), encoding="utf-8")
    internal_manifest = tmp_path / "internal-freeze.json"
    internal_receipt = tmp_path / "internal-freeze-receipt.json"
    create_training_process_v5_internal_validation_freeze(
        internal_plan_path, internal_manifest, internal_receipt
    )

    score_root = tmp_path / "internal-score-runs"
    score_bundle = tmp_path / "internal-score-bundle.json"
    scoring_receipt = tmp_path / "internal-scoring-receipt.json"
    run_managed_internal_scoring_v1(
        internal_manifest,
        internal_receipt,
        validation_roster,
        validation_roster_format="csv",
        managed_generation_receipt_path=generation_receipt,
        generated_model_root=generated_root,
        validation_data_path=validation_data,
        output_root=score_root,
        score_bundle_out=score_bundle,
        scoring_receipt_out=scoring_receipt,
    )

    return {
        "process_manifest": process_manifest,
        "training_roster": training_roster,
        "generation_receipt": generation_receipt,
        "generated_root": generated_root,
        "internal_manifest": internal_manifest,
        "internal_receipt": internal_receipt,
        "validation_roster": validation_roster,
        "validation_data": validation_data,
        "score_bundle": score_bundle,
        "scoring_receipt": scoring_receipt,
        "refit_ids": tuple(refit_ids),
        "groups": tuple(groups),
        "blocks": tuple(blocks),
        "row_ids": tuple(row_ids),
        "weights": tuple(weights),
    }


def _run(fixture: dict[str, object]):
    return run_managed_internal_training_process_v5(
        fixture["internal_manifest"],
        fixture["internal_receipt"],
        fixture["scoring_receipt"],
        fixture["score_bundle"],
        fixture["validation_data"],
        fixture["groups"],
        blocks=fixture["blocks"],
        validation_row_ids=fixture["row_ids"],
        sample_weight=fixture["weights"],
        refit_ids=fixture["refit_ids"],
        training_process_manifest_path=fixture["process_manifest"],
        managed_generation_receipt_path=fixture["generation_receipt"],
        training_roster_path=fixture["training_roster"],
        validation_outcomes_first_accessed_at_utc="2099-01-01T00:00:00Z",
    )


def test_managed_internal_chain_closes_model_to_score_provenance(tmp_path):
    fixture = _setup(tmp_path)
    result = _run(fixture)
    assert result.receipt_type == MANAGED_INTERNAL_RECEIPT_TYPE
    assert result.score_tensor_derived_by_managed_scoring is True
    assert (
        result.score_table_derivation_from_generated_models_independently_proven
        is True
    )
    assert result.generated_model_artifact_snapshot_verified is True
    assert result.implementation_source_snapshot_verified is True
    assert result.runtime_environment_snapshot_verified is True
    assert result.training_source_frame_validation_disjoint is True
    assert (
        result.certification.certification.process_mean_certified_transfer_ceiling
        == "fine"
    )
    assert (
        result.certification.score_table_derivation_from_generated_models_independently_proven
        is False
    )
    # The historical wrapper retains its own boundary; the new outer endpoint
    # supplies the independent operational proof.
    json.dumps(result.as_dict(), allow_nan=False)


def test_managed_internal_scoring_rejects_generated_model_byte_tampering(tmp_path):
    fixture = _setup(tmp_path)
    model = Path(fixture["generated_root"]) / "r00" / "model.json"
    model.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact bytes changed"):
        run_managed_internal_scoring_v1(
            fixture["internal_manifest"],
            fixture["internal_receipt"],
            fixture["validation_roster"],
            validation_roster_format="csv",
            managed_generation_receipt_path=fixture["generation_receipt"],
            generated_model_root=fixture["generated_root"],
            validation_data_path=fixture["validation_data"],
            output_root=tmp_path / "rerun-scores",
            score_bundle_out=tmp_path / "rerun-bundle.json",
            scoring_receipt_out=tmp_path / "rerun-receipt.json",
        )


def test_managed_internal_endpoint_rejects_nonprospective_declared_access(tmp_path):
    fixture = _setup(tmp_path)
    manifest = json.loads(Path(fixture["internal_manifest"]).read_text())
    with pytest.raises(ValueError, match="strictly predate"):
        run_managed_internal_training_process_v5(
            fixture["internal_manifest"],
            fixture["internal_receipt"],
            fixture["scoring_receipt"],
            fixture["score_bundle"],
            fixture["validation_data"],
            fixture["groups"],
            blocks=fixture["blocks"],
            validation_row_ids=fixture["row_ids"],
            sample_weight=fixture["weights"],
            refit_ids=fixture["refit_ids"],
            training_process_manifest_path=fixture["process_manifest"],
            managed_generation_receipt_path=fixture["generation_receipt"],
            training_roster_path=fixture["training_roster"],
            validation_outcomes_first_accessed_at_utc=manifest["frozen_at_utc"],
        )


def test_managed_internal_endpoint_rejects_tampered_scoring_execution_receipt(tmp_path):
    fixture = _setup(tmp_path)
    receipt_path = Path(fixture["scoring_receipt"])
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["executions"][0]["return_code"] = 1
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="nonzero return code"):
        _run(fixture)
