from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_source_process_freeze_manifest import (
    INNER_PROCESS_KIND,
    OUTER_PROCESS_KIND,
    create_training_source_process_freeze_manifest,
)
from odsp.training_source_process_managed_generation import (
    RECEIPT_TYPE,
    run_managed_training_source_process_generation,
    validate_training_source_managed_generation_plan,
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
    (tmp_path / "source.dat").write_bytes(b"source-data\n")
    (tmp_path / "source_gen.py").write_text("SOURCE=1\n", encoding="utf-8")
    fit = tmp_path / "fit.py"
    fit.write_text(
        "import argparse,json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--source',required=True)\n"
        "p.add_argument('--outer',required=True)\n"
        "p.add_argument('--refit',required=True)\n"
        "p.add_argument('--inner',required=True)\n"
        "p.add_argument('--seed',required=True,type=int)\n"
        "p.add_argument('--output-dir',required=True)\n"
        "a=p.parse_args()\n"
        "outer=json.loads(Path(a.outer).read_text())\n"
        "inner=json.loads(Path(a.inner).read_text())\n"
        "payload={"
        "'source':a.source,'refit':a.refit,'seed':a.seed,"
        "'outer_total':sum(int(x['count']) for x in outer),"
        "'inner_total':sum(int(x['count']) for x in inner)}\n"
        "Path(a.output_dir,'model.json').write_text(json.dumps(payload,sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    freeze = {
        "schema_version": 1,
        "source_process_id": "source-v0",
        "source_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "source_data_artifacts": [{"role":"source_data","path":"source.dat"}],
        "source_generation_artifacts": [{"role":"source_generator","path":"source_gen.py"}],
        "fit_implementation_artifacts": [{"role":"fit","path":"fit.py"}],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {},
        "source_draw_ids": [f"s{i:02d}" for i in range(8)],
        "inner_refit_ids": [f"r{i:02d}" for i in range(8)],
        "master_seed": 20261018,
        "outer_resampling": {
            "kind": OUTER_PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
        "inner_resampling": {
            "kind": INNER_PROCESS_KIND,
            "replacement": True,
            "draw_size": "outer_source_draw_size",
        },
    }
    freeze_path=tmp_path/"freeze.json"
    freeze_path.write_text(json.dumps(freeze),encoding="utf-8")
    create_training_source_process_freeze_manifest(
        freeze_path,tmp_path/"manifest.json"
    )

    managed = {
        "schema_version": 1,
        "source_process_id": "source-v0",
        "manifest_path": "manifest.json",
        "source_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "working_directory": ".",
        "command": [
            "{python_executable}",
            "fit.py",
            "--source","{source_draw_id}",
            "--outer","{outer_membership_path}",
            "--refit","{inner_refit_id}",
            "--inner","{inner_membership_path}",
            "--seed","{fit_seed}",
            "--output-dir","{output_dir}"
        ],
        "command_artifacts": ["fit.py"],
        "timeout_seconds": 30,
        "environment_allowlist": [],
        "output_artifacts": [
            {"artifact_id":"primary_model","relative_path":"model.json"}
        ],
    }
    managed_path=tmp_path/"managed.json"
    managed_path.write_text(json.dumps(managed),encoding="utf-8")
    return managed_path


def test_managed_nested_generation_executes_balanced_8_by_8_tree(tmp_path):
    plan=_setup(tmp_path)
    result=run_managed_training_source_process_generation(
        plan,tmp_path/"outputs",tmp_path/"receipt.json"
    )
    receipt=result["receipt"]
    assert receipt["receipt_type"] == RECEIPT_TYPE
    assert receipt["source_draw_count"] == 8
    assert receipt["inner_refit_count_per_source"] == 8
    assert receipt["fit_execution_count"] == 64
    assert len(receipt["sources"]) == 8
    model_hashes=set()
    fit_seeds=set()
    for source in receipt["sources"]:
        assert len(source["outer_membership_semantic_sha256"]) == 64
        assert source["inner_refit_count"] == 8
        assert len(source["inner_executions"]) == 8
        for execution in source["inner_executions"]:
            assert execution["return_code"] == 0
            assert len(execution["inner_membership_semantic_sha256"]) == 64
            fit_seeds.add(execution["fit_seed"])
            model_hashes.add(execution["artifacts"][0]["sha256"])
    assert len(fit_seeds) == 64
    assert len(model_hashes) == 64
    assert receipt["boundaries"]["validation_outcomes_read"] is False
    assert receipt["boundaries"]["shell_used"] is False
    assert receipt["boundaries"]["outer_membership_verified_before_inner_generation"] is True
    assert receipt["boundaries"]["inner_membership_verified_before_fit"] is True


def test_managed_nested_generation_is_non_overwriting(tmp_path):
    plan=_setup(tmp_path)
    output=tmp_path/"outputs"
    receipt=tmp_path/"receipt.json"
    run_managed_training_source_process_generation(plan,output,receipt)
    with pytest.raises(FileExistsError):
        run_managed_training_source_process_generation(
            plan,output,tmp_path/"other-receipt.json"
        )
    with pytest.raises(FileExistsError):
        run_managed_training_source_process_generation(
            plan,tmp_path/"other-output",receipt
        )


def test_managed_nested_generation_rejects_manifest_membership_tamper(tmp_path):
    plan=_setup(tmp_path)
    manifest=tmp_path/"manifest.json"
    payload=json.loads(manifest.read_text(encoding="utf-8"))
    payload["nested_schedule"][0]["inner_refit_schedule"][0][
        "inner_membership_sha256"
    ]="0"*64
    manifest.write_text(json.dumps(payload),encoding="utf-8")
    with pytest.raises(ValueError,match="inner membership digest mismatch"):
        run_managed_training_source_process_generation(
            plan,tmp_path/"outputs",tmp_path/"receipt.json"
        )


def test_managed_nested_plan_requires_both_membership_placeholders():
    raw={
        "schema_version":1,
        "source_process_id":"p",
        "manifest_path":"m.json",
        "source_roster":{
            "path":"r.csv","format":"csv",
            "unit_id_column":"id","stratum_column":None
        },
        "working_directory":".",
        "command":[
            "python","fit.py","{source_draw_id}","{outer_membership_path}",
            "{inner_refit_id}","{fit_seed}","{output_dir}"
        ],
        "command_artifacts":["fit.py"],
        "timeout_seconds":30,
        "environment_allowlist":[],
        "output_artifacts":[{"artifact_id":"m","relative_path":"m.bin"}],
    }
    with pytest.raises(ValueError,match="inner_membership_path"):
        validate_training_source_managed_generation_plan(raw)
