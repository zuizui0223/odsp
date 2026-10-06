from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

from odsp.training_source_process_freeze_manifest import (
    INNER_PROCESS_KIND,
    OUTER_PROCESS_KIND,
    create_training_source_process_freeze_manifest,
)
from odsp.training_source_process_internal_freeze_v0 import (
    create_training_source_process_v0_internal_validation_freeze,
)
from odsp.training_source_process_managed_generation import (
    run_managed_training_source_process_generation,
)
from odsp.training_source_process_managed_internal_v0 import (
    MANAGED_INTERNAL_RECEIPT_TYPE,
    run_managed_internal_training_source_process_v0,
)
from odsp.training_source_process_managed_internal_scoring import (
    MANAGED_SCORING_RECEIPT_TYPE,
    run_managed_training_source_process_scoring_v0,
)


def _source_process(tmp_path: Path):
    (tmp_path / "source-roster.csv").write_text(
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
    (tmp_path / "source.dat").write_text("source\n", encoding="utf-8")
    (tmp_path / "fit.py").write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--source-draw-id', required=True)\n"
        "p.add_argument('--outer-membership', required=True)\n"
        "p.add_argument('--inner-refit-id', required=True)\n"
        "p.add_argument('--inner-membership', required=True)\n"
        "p.add_argument('--fit-seed', type=int, required=True)\n"
        "p.add_argument('--output-dir', required=True)\n"
        "a=p.parse_args()\n"
        "outer=json.loads(Path(a.outer_membership).read_text())\n"
        "inner=json.loads(Path(a.inner_membership).read_text())\n"
        "payload={'source':a.source_draw_id,'inner':a.inner_refit_id,"
        "'seed':a.fit_seed,'outer_n':sum(int(x['count']) for x in outer),"
        "'inner_n':sum(int(x['count']) for x in inner)}\n"
        "Path(a.output_dir,'model.json').write_text("
        "json.dumps(payload,sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    (tmp_path / "score.py").write_text(
        "import argparse, csv, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--source-draw-id', required=True)\n"
        "p.add_argument('--inner-refit-id', required=True)\n"
        "p.add_argument('--model-manifest', required=True)\n"
        "p.add_argument('--validation-data', required=True)\n"
        "p.add_argument('--scoring-spec', required=True)\n"
        "p.add_argument('--output', required=True)\n"
        "a=p.parse_args()\n"
        "mm=json.loads(Path(a.model_manifest).read_text())\n"
        "assert mm['source_draw_id']==a.source_draw_id\n"
        "assert mm['inner_refit_id']==a.inner_refit_id\n"
        "model=json.loads(Path(mm['artifacts'][0]['path']).read_text())\n"
        "spec=json.loads(Path(a.scoring_spec).read_text())\n"
        "with Path(a.validation_data).open(newline='',encoding='utf-8') as h:\n"
        "    rows=list(csv.DictReader(h))\n"
        "offset=(int(model['seed']) % 19)*0.0001\n"
        "out=[]\n"
        "for row in reversed(rows):\n"
        "    rid=row['row_id']\n"
        "    out.append({'row_id':rid,'scores':{"
        "'pooled':offset,'coarse':offset+0.5,'fine':offset+0.9}})\n"
        "Path(a.output).write_text(json.dumps({"
        "'source_draw_id':a.source_draw_id,"
        "'inner_refit_id':a.inner_refit_id,'rows':out},sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )

    source_ids=[f"s{i:02d}" for i in range(8)]
    inner_ids=[f"r{i:02d}" for i in range(8)]
    freeze_plan={
        "schema_version":1,
        "source_process_id":"source-v0-test",
        "source_roster":{
            "path":"source-roster.csv","format":"csv",
            "unit_id_column":"unit","stratum_column":"stratum",
        },
        "source_data_artifacts":[{"role":"source","path":"source.dat"}],
        "source_generation_artifacts":[{"role":"generator","path":"fit.py"}],
        "fit_implementation_artifacts":[{"role":"fit","path":"fit.py"}],
        "fit_entrypoint":"fit.py:cli",
        "fit_parameters":{},
        "source_draw_ids":source_ids,
        "inner_refit_ids":inner_ids,
        "master_seed":20261020,
        "outer_resampling":{
            "kind":OUTER_PROCESS_KIND,"replacement":True,
            "within_stratum_draw_size":"original_stratum_size",
        },
        "inner_resampling":{
            "kind":INNER_PROCESS_KIND,"replacement":True,
            "draw_size":"outer_source_draw_size",
        },
    }
    fp=tmp_path/"source-freeze-plan.json"
    fp.write_text(json.dumps(freeze_plan),encoding="utf-8")
    manifest=tmp_path/"source-process-manifest.json"
    create_training_source_process_freeze_manifest(fp,manifest)

    managed_plan={
        "schema_version":1,
        "source_process_id":"source-v0-test",
        "manifest_path":manifest.name,
        "source_roster":{
            "path":"source-roster.csv","format":"csv",
            "unit_id_column":"unit","stratum_column":"stratum",
        },
        "working_directory":".",
        "command":[
            "{python_executable}","fit.py",
            "--source-draw-id","{source_draw_id}",
            "--outer-membership","{outer_membership_path}",
            "--inner-refit-id","{inner_refit_id}",
            "--inner-membership","{inner_membership_path}",
            "--fit-seed","{fit_seed}",
            "--output-dir","{output_dir}",
        ],
        "command_artifacts":["fit.py"],
        "timeout_seconds":30,
        "environment_allowlist":[],
        "output_artifacts":[
            {"artifact_id":"primary_model","relative_path":"model.json"}
        ],
    }
    mp=tmp_path/"managed-plan.json"
    mp.write_text(json.dumps(managed_plan),encoding="utf-8")
    model_root=tmp_path/"generated-models"
    managed_receipt=tmp_path/"managed-receipt.json"
    run_managed_training_source_process_generation(
        mp,model_root,managed_receipt
    )
    return {
        "manifest":manifest,
        "managed_receipt":managed_receipt,
        "source_roster":tmp_path/"source-roster.csv",
        "model_root":model_root,
        "source_ids":source_ids,
        "inner_ids":inner_ids,
    }


def _validation_roster(tmp_path: Path, *, overlap: bool=False) -> Path:
    lines=["row_id,group_id,block_id,sample_weight"]
    for g in range(2):
        for b in range(8):
            rid="u1" if overlap and g==0 and b==0 else f"v-{g}-{b}"
            lines.append(f"{rid},g{g},g{g}-b{b},1.0")
    p=tmp_path/"validation-roster.csv"
    p.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return p


def _validation_plan(tmp_path: Path, process, roster: Path) -> Path:
    plan={
        "schema_version":1,
        "validation_dataset_id":"heldout-v1",
        "row_identity_namespace":"global-observation-id-v1",
        "roster":{"path":roster.name,"format":"csv"},
        "source_process_manifest_path":process["manifest"].name,
        "managed_nested_generation_receipt_path":process["managed_receipt"].name,
        "source_roster":{
            "path":process["source_roster"].name,"format":"csv",
            "unit_id_column":"unit","stratum_column":"stratum",
        },
        "score":{
            "kind":"log","name":"log","orientation":"higher_is_better",
            "common_scoring_rule":True,"common_reference_measure":True,
        },
        "levels":[
            {"name":"pooled","information":[]},
            {"name":"coarse","information":["species"]},
            {"name":"fine","information":["species","context"]},
        ],
        "certification":{
            "component_one_sided_alpha":0.05,
            "minimum_source_draws":8,
            "minimum_inner_refits_per_source":8,
            "minimum_blocks_per_group":8,
            "gain_tolerance":0.0,
        },
        "scoring":{
            "working_directory":".",
            "command":[
                "{python_executable}","score.py",
                "--source-draw-id","{source_draw_id}",
                "--inner-refit-id","{inner_refit_id}",
                "--model-manifest","{model_manifest_path}",
                "--validation-data","{validation_data_path}",
                "--scoring-spec","{scoring_spec_path}",
                "--output","{output_path}",
            ],
            "command_artifacts":["score.py"],
            "timeout_seconds":30,
            "environment_allowlist":[],
            "validation_data_format":"csv",
            "validation_row_id_column":"row_id",
        },
    }
    p=tmp_path/"validation-freeze-plan.json"
    p.write_text(json.dumps(plan),encoding="utf-8")
    return p


def _design(roster: Path):
    import csv
    with roster.open(newline="",encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    return (
        [r["row_id"] for r in rows],
        [r["group_id"] for r in rows],
        [r["block_id"] for r in rows],
        [float(r["sample_weight"]) for r in rows],
    )


def _freeze_and_score(tmp_path: Path):
    process=_source_process(tmp_path)
    roster=_validation_roster(tmp_path)
    plan=_validation_plan(tmp_path,process,roster)
    freeze_manifest=tmp_path/"validation-freeze.json"
    freeze_receipt=tmp_path/"validation-freeze-receipt.json"
    create_training_source_process_v0_internal_validation_freeze(
        plan,freeze_manifest,freeze_receipt
    )
    frozen=json.loads(freeze_manifest.read_text())
    frozen_at=datetime.fromisoformat(
        str(frozen["frozen_at_utc"]).replace("Z","+00:00")
    )

    row_ids,_,_,_=_design(roster)
    validation=tmp_path/"validation-data.csv"
    validation.write_text(
        "row_id,y\n"+"\n".join(f"{rid},1" for rid in reversed(row_ids))+"\n",
        encoding="utf-8",
    )
    score_bundle=tmp_path/"score-bundle.json"
    scoring_receipt=tmp_path/"scoring-receipt.json"
    run_managed_training_source_process_scoring_v0(
        freeze_manifest,freeze_receipt,roster,
        validation_roster_format="csv",
        managed_nested_generation_receipt_path=process["managed_receipt"],
        generated_model_root=process["model_root"],
        validation_data_path=validation,
        output_root=tmp_path/"score-outputs",
        score_bundle_out=score_bundle,
        scoring_receipt_out=scoring_receipt,
    )
    return {
        **process,
        "roster":roster,
        "freeze_manifest":freeze_manifest,
        "freeze_receipt":freeze_receipt,
        "validation":validation,
        "score_bundle":score_bundle,
        "scoring_receipt":scoring_receipt,
        "frozen_at":frozen_at,
        "managed_read_at": datetime.fromisoformat(
            json.loads(scoring_receipt.read_text(encoding="utf-8"))[
                "validation_data_first_read_by_odsp_at_utc"
            ].replace("Z", "+00:00")
        ),
    }


def test_managed_source_v0_chain_reaches_fine_ceiling(tmp_path):
    state=_freeze_and_score(tmp_path)
    row_ids,groups,blocks,weights=_design(state["roster"])
    access=state["managed_read_at"].isoformat()
    result=run_managed_internal_training_source_process_v0(
        state["freeze_manifest"],
        state["freeze_receipt"],
        state["scoring_receipt"],
        state["score_bundle"],
        state["validation"],
        groups,
        blocks=blocks,
        validation_row_ids=row_ids,
        sample_weight=weights,
        source_process_manifest_path=state["manifest"],
        managed_nested_generation_receipt_path=state["managed_receipt"],
        source_roster_path=state["source_roster"],
        validation_outcomes_first_accessed_at_utc=access,
    )
    assert result.receipt_type == MANAGED_INTERNAL_RECEIPT_TYPE
    assert result.freeze_precedes_declared_first_validation_outcome_access is True
    assert result.managed_validation_read_after_freeze is True
    assert result.declared_first_access_not_after_managed_validation_read is True
    assert result.semantic_use_of_model_and_validation_inputs_cryptographically_proven is False
    assert result.source_frame_validation_disjoint is True
    assert result.score_tensor_derived_by_managed_scoring is True
    assert result.evaluation.source_process_mean_transfer_ceiling == "fine"
    assert result.evaluation.process_audit.effective_training_cluster_count == 8
    assert result.evaluation.process_audit.inner_refits_pooled_as_independent_source_draws is False


def test_source_v0_freeze_rejects_original_source_frame_overlap(tmp_path):
    process=_source_process(tmp_path)
    roster=_validation_roster(tmp_path,overlap=True)
    plan=_validation_plan(tmp_path,process,roster)
    with pytest.raises(ValueError,match="overlaps"):
        create_training_source_process_v0_internal_validation_freeze(
            plan,tmp_path/"freeze.json",tmp_path/"receipt.json"
        )


def test_source_v0_scoring_rejects_nested_model_byte_tampering(tmp_path):
    process=_source_process(tmp_path)
    roster=_validation_roster(tmp_path)
    plan=_validation_plan(tmp_path,process,roster)
    freeze_manifest=tmp_path/"validation-freeze.json"
    freeze_receipt=tmp_path/"validation-freeze-receipt.json"
    create_training_source_process_v0_internal_validation_freeze(
        plan,freeze_manifest,freeze_receipt
    )
    target=process["model_root"]/"s00"/"r00"/"model.json"
    target.write_text('{"tampered":true}\n',encoding="utf-8")
    row_ids,_,_,_=_design(roster)
    validation=tmp_path/"validation-data.csv"
    validation.write_text(
        "row_id,y\n"+"\n".join(f"{rid},1" for rid in row_ids)+"\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError,match="bytes changed"):
        run_managed_training_source_process_scoring_v0(
            freeze_manifest,freeze_receipt,roster,
            validation_roster_format="csv",
            managed_nested_generation_receipt_path=process["managed_receipt"],
            generated_model_root=process["model_root"],
            validation_data_path=validation,
            output_root=tmp_path/"score-outputs",
            score_bundle_out=tmp_path/"bundle.json",
            scoring_receipt_out=tmp_path/"score-receipt.json",
        )


def test_source_v0_endpoint_rejects_nonprospective_access_timestamp(tmp_path):
    state=_freeze_and_score(tmp_path)
    row_ids,groups,blocks,weights=_design(state["roster"])
    with pytest.raises(ValueError,match="strictly predate"):
        run_managed_internal_training_source_process_v0(
            state["freeze_manifest"],
            state["freeze_receipt"],
            state["scoring_receipt"],
            state["score_bundle"],
            state["validation"],
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            sample_weight=weights,
            source_process_manifest_path=state["manifest"],
            managed_nested_generation_receipt_path=state["managed_receipt"],
            source_roster_path=state["source_roster"],
            validation_outcomes_first_accessed_at_utc=state["frozen_at"].isoformat(),
        )


def test_scoring_receipt_is_managed_source_v0_type(tmp_path):
    state=_freeze_and_score(tmp_path)
    receipt=json.loads(state["scoring_receipt"].read_text())
    assert receipt["receipt_type"] == MANAGED_SCORING_RECEIPT_TYPE
    assert receipt["fit_score_execution_count"] == 64
    assert receipt["validation_data_first_read_by_odsp_at_utc"]
    assert receipt["boundaries"]["shell_used"] is False
    assert receipt["boundaries"]["source_inner_nesting_preserved"] is True


def test_source_v0_endpoint_rejects_declared_access_after_managed_read(tmp_path):
    state=_freeze_and_score(tmp_path)
    row_ids,groups,blocks,weights=_design(state["roster"])
    future=(state["managed_read_at"]+timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError,match="must not occur after"):
        run_managed_internal_training_source_process_v0(
            state["freeze_manifest"],
            state["freeze_receipt"],
            state["scoring_receipt"],
            state["score_bundle"],
            state["validation"],
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            sample_weight=weights,
            source_process_manifest_path=state["manifest"],
            managed_nested_generation_receipt_path=state["managed_receipt"],
            source_roster_path=state["source_roster"],
            validation_outcomes_first_accessed_at_utc=future,
        )


def test_source_v0_validation_freeze_rejects_scoring_artifact_escape(tmp_path):
    process=_source_process(tmp_path)
    roster=_validation_roster(tmp_path)
    plan=_validation_plan(tmp_path,process,roster)
    payload=json.loads(plan.read_text(encoding="utf-8"))
    payload["scoring"]["command_artifacts"]=["../score.py"]
    plan.write_text(json.dumps(payload),encoding="utf-8")
    with pytest.raises(ValueError,match="safe relative path"):
        create_training_source_process_v0_internal_validation_freeze(
            plan,tmp_path/"freeze.json",tmp_path/"receipt.json"
        )
