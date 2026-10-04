from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_confirmatory_contract_v2 import (
    certify_frozen_training_process_positive_information_transfer_v2,
)
from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_generation_receipt import (
    create_training_process_generation_receipt,
)


def _fixture(tmp_path: Path):
    (tmp_path/"roster.csv").write_text(
        "unit,stratum\n"+ "".join(f"t{i},a\n" for i in range(20)),
        encoding="utf-8",
    )
    (tmp_path/"train.dat").write_bytes(b"train\n")
    (tmp_path/"fit.py").write_text("def fit(seed): return seed\n",encoding="utf-8")
    plan={
        "schema_version":1,
        "training_process_id":"p-v2",
        "training_roster":{
            "path":"roster.csv","format":"csv",
            "unit_id_column":"unit","stratum_column":"stratum",
        },
        "training_data_artifacts":[{"role":"train","path":"train.dat"}],
        "implementation_artifacts":[{"role":"fit","path":"fit.py"}],
        "fit_entrypoint":"fit.py:fit",
        "fit_parameters":{},
        "refit_ids":[f"r{i:02d}" for i in range(8)],
        "master_seed":1234,
        "resampling":{
            "kind":PROCESS_KIND,
            "replacement":True,
            "within_stratum_draw_size":"original_stratum_size",
        },
    }
    plan_path=tmp_path/"plan.json"
    plan_path.write_text(json.dumps(plan),encoding="utf-8")
    manifest_path=tmp_path/"manifest.json"
    create_training_process_freeze_manifest(plan_path,manifest_path)
    manifest=json.loads(manifest_path.read_text())

    refits=[]
    artifacts=[]
    for row in manifest["refit_schedule"]:
        model=tmp_path/f"{row['refit_id']}.model"
        model.write_bytes(f"model:{row['refit_id']}\n".encode())
        refits.append({
            "refit_id":row["refit_id"],
            "resample_seed":row["resample_seed"],
            "fit_seed":row["fit_seed"],
            "bootstrap_membership_sha256":row["bootstrap_membership_sha256"],
            "model_artifacts":[{"artifact_id":"model","path":model.name}],
        })
        artifacts.append({
            "refit_id":row["refit_id"],
            "artifact_id":"model",
            "path":model.name,
        })
    declaration=tmp_path/"generation.json"
    declaration.write_text(json.dumps({
        "schema_version":1,
        "training_process_id":"p-v2",
        "refits":refits,
    }),encoding="utf-8")
    receipt=tmp_path/"generation-receipt.json"
    create_training_process_generation_receipt(
        manifest_path,declaration,receipt
    )

    groups=tuple(g for g in ("g0","g1") for _ in range(8))
    blocks=tuple(f"{g}-b{i}" for g in ("g0","g1") for i in range(8))
    validation_ids=tuple(f"v{i}" for i in range(16))
    training={rid:tuple(f"t{i}" for i in range(20)) for rid in manifest["refit_ids"]}
    pooled=np.zeros((8,16))
    coarse=np.full((8,16),0.5)
    fine=coarse+0.4
    levels=(
        RefitInformationLevelScores("pooled",(),pooled),
        RefitInformationLevelScores("coarse",("species",),coarse),
        RefitInformationLevelScores("fine",("species","context"),fine),
    )
    return manifest_path,receipt,artifacts,manifest,groups,blocks,validation_ids,training,levels


def test_high_level_process_contract_binds_manifest_models_and_separation(tmp_path):
    (
        manifest,receipt,artifacts,meta,groups,blocks,
        validation_ids,training,levels,
    )=_fixture(tmp_path)
    result=certify_frozen_training_process_positive_information_transfer_v2(
        levels,
        groups,
        blocks=blocks,
        score_refit_ids=meta["refit_ids"],
        validation_row_ids=validation_ids,
        training_row_ids_by_refit=training,
        process_manifest_path=manifest,
        generation_receipt_path=receipt,
        upstream_model_artifacts=artifacts,
        bootstrap_draws=500,
    )
    assert result.process_manifest_verified is True
    assert result.generation_receipt_verified is True
    assert result.model_artifact_bytes_verified is True
    assert result.training_validation_separated is True
    assert result.certification.process_mean_certified_transfer_ceiling=="fine"
    assert result.process_freeze_preceded_validation_outcome_access_verified_here is False


def test_high_level_process_contract_rejects_validation_leakage(tmp_path):
    (
        manifest,receipt,artifacts,meta,groups,blocks,
        validation_ids,training,levels,
    )=_fixture(tmp_path)
    bad=dict(training)
    bad[meta["refit_ids"][0]]=bad[meta["refit_ids"][0]]+(validation_ids[0],)
    with pytest.raises(ValueError,match="leakage"):
        certify_frozen_training_process_positive_information_transfer_v2(
            levels,groups,blocks=blocks,score_refit_ids=meta["refit_ids"],
            validation_row_ids=validation_ids,training_row_ids_by_refit=bad,
            process_manifest_path=manifest,generation_receipt_path=receipt,
            upstream_model_artifacts=artifacts,bootstrap_draws=500,
        )


def test_high_level_process_contract_rejects_model_byte_substitution(tmp_path):
    (
        manifest,receipt,artifacts,meta,groups,blocks,
        validation_ids,training,levels,
    )=_fixture(tmp_path)
    (tmp_path/"r00.model").write_bytes(b"substituted\n")
    with pytest.raises(ValueError,match="snapshot mismatch"):
        certify_frozen_training_process_positive_information_transfer_v2(
            levels,groups,blocks=blocks,score_refit_ids=meta["refit_ids"],
            validation_row_ids=validation_ids,training_row_ids_by_refit=training,
            process_manifest_path=manifest,generation_receipt_path=receipt,
            upstream_model_artifacts=artifacts,bootstrap_draws=500,
        )
