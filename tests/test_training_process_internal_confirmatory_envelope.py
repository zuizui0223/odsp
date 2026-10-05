from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_generation_receipt import (
    create_training_process_generation_receipt,
)
from odsp.training_process_internal_confirmatory_contract import (
    run_training_process_internal_confirmatory_contract_v1,
)
from odsp.training_process_internal_freeze_manifest import (
    create_training_process_internal_freeze_manifest,
)
from odsp.training_process_validation_separation_receipt import (
    create_training_process_validation_separation_receipt,
)


SCORE = {
    "kind": "log",
    "name": "log",
    "orientation": "higher_is_better",
    "common_scoring_rule": True,
    "common_reference_measure": True,
}
LEVELS = [
    {"name": "pooled", "information": []},
    {"name": "coarse", "information": ["species"]},
    {
        "name": "fine",
        "information": ["species", "context"],
    },
]


def _setup(tmp_path: Path):
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
    process_plan = {
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
    process_plan_path = tmp_path / "process-plan.json"
    process_plan_path.write_text(
        json.dumps(process_plan),
        encoding="utf-8",
    )
    process_manifest = tmp_path / "process-manifest.json"
    create_training_process_freeze_manifest(
        process_plan_path,
        process_manifest,
    )
    process_payload = json.loads(
        process_manifest.read_text(encoding="utf-8")
    )

    generation_rows = []
    model_declarations = []
    for row in process_payload["refit_schedule"]:
        refit_id = row["refit_id"]
        model = tmp_path / f"{refit_id}.model"
        model.write_bytes(f"model::{refit_id}\n".encode("utf-8"))
        generation_rows.append(
            {
                "refit_id": refit_id,
                "resample_seed": row["resample_seed"],
                "fit_seed": row["fit_seed"],
                "bootstrap_membership_sha256": row[
                    "bootstrap_membership_sha256"
                ],
                "model_artifacts": [
                    {
                        "artifact_id": "primary_model",
                        "path": model.name,
                    }
                ],
            }
        )
        model_declarations.append(
            {
                "refit_id": refit_id,
                "artifact_id": "primary_model",
                "path": model.name,
            }
        )
    generation_declaration = tmp_path / "generation.json"
    generation_declaration.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "training_process_id": "process-v1",
                "refits": generation_rows,
            }
        ),
        encoding="utf-8",
    )
    generation_receipt = tmp_path / "generation-receipt.json"
    create_training_process_generation_receipt(
        process_manifest,
        generation_declaration,
        generation_receipt,
    )

    row_ids = []
    groups = []
    blocks = []
    weights = []
    metadata_lines = ["row_id,group,block,weight"]
    for group_index in range(2):
        for block_index in range(8):
            row_id = f"v-g{group_index}-b{block_index}"
            group = f"g{group_index}"
            block = f"g{group_index}-b{block_index}"
            row_ids.append(row_id)
            groups.append(group)
            blocks.append(block)
            weights.append(1.0)
            metadata_lines.append(
                f"{row_id},{group},{block},1"
            )
    validation_ids = tmp_path / "validation-ids.csv"
    validation_ids.write_text(
        "row_id\n" + "\n".join(row_ids) + "\n",
        encoding="utf-8",
    )
    validation_metadata = tmp_path / "validation-metadata.csv"
    validation_metadata.write_text(
        "\n".join(metadata_lines) + "\n",
        encoding="utf-8",
    )
    separation_receipt = tmp_path / "separation-receipt.json"
    create_training_process_validation_separation_receipt(
        process_manifest,
        tmp_path / "training.csv",
        validation_ids,
        separation_receipt,
        row_identity_namespace="global-observation-id-v1",
        training_roster_format="csv",
        training_unit_id_column="unit",
        training_stratum_column="stratum",
    )

    qualification_receipt = tmp_path / "qualification.json"
    qualification_receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "receipt_type": (
                    "odsp_training_process_positive_cv3two_iut_"
                    "v5_qualification_v1"
                ),
                "method_version": (
                    "training_process_positive_cv3two_iut_v5"
                ),
                "null_run": {"qualification_pass": True},
                "power_run": {"qualification_pass": True},
                "summary": {"qualification_pass": True},
            }
        ),
        encoding="utf-8",
    )

    freeze_plan = {
        "schema_version": 1,
        "analysis_id": "internal-process-analysis-v1",
        "process_manifest": process_manifest.name,
        "generation_receipt": generation_receipt.name,
        "validation_separation_receipt": separation_receipt.name,
        "qualification_receipt": qualification_receipt.name,
        "upstream_model_artifacts": model_declarations,
        "validation_dataset_id": "validation-v1",
        "validation_roster": {
            "path": validation_metadata.name,
            "format": "csv",
            "row_id_column": "row_id",
            "group_column": "group",
            "block_column": "block",
            "weight_column": "weight",
        },
        "score": SCORE,
        "levels": LEVELS,
        "certification": {
            "component_one_sided_alpha": 0.05,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }
    freeze_plan_path = tmp_path / "internal-freeze-plan.json"
    freeze_plan_path.write_text(
        json.dumps(freeze_plan),
        encoding="utf-8",
    )
    internal_freeze = tmp_path / "internal-freeze.json"
    create_training_process_internal_freeze_manifest(
        freeze_plan_path,
        internal_freeze,
    )

    n = len(row_ids)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.5
    fine = coarse + 0.4
    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores(
            "coarse", ("species",), coarse
        ),
        RefitInformationLevelScores(
            "fine", ("species", "context"), fine
        ),
    )
    return {
        "process_manifest": process_manifest,
        "generation_receipt": generation_receipt,
        "separation_receipt": separation_receipt,
        "qualification_receipt": qualification_receipt,
        "internal_freeze": internal_freeze,
        "model_declarations": model_declarations,
        "row_ids": tuple(row_ids),
        "groups": tuple(groups),
        "blocks": tuple(blocks),
        "weights": tuple(weights),
        "levels": levels,
        "refit_ids": tuple(f"r{i:02d}" for i in range(8)),
    }


def _run(fixture, tmp_path: Path):
    return run_training_process_internal_confirmatory_contract_v1(
        fixture["levels"],
        fixture["row_ids"],
        fixture["groups"],
        fixture["blocks"],
        freeze_manifest_path=fixture["internal_freeze"],
        process_manifest_path=fixture["process_manifest"],
        generation_receipt_path=fixture["generation_receipt"],
        validation_separation_receipt_path=fixture[
            "separation_receipt"
        ],
        qualification_receipt_path=fixture[
            "qualification_receipt"
        ],
        upstream_model_artifacts=fixture[
            "model_declarations"
        ],
        model_artifact_base_dir=tmp_path,
        refit_ids=fixture["refit_ids"],
        score_contract=SCORE,
        sample_weight=fixture["weights"],
    )


def test_full_internal_envelope_runs_only_after_all_evidence_matches(
    tmp_path: Path,
):
    fixture = _setup(tmp_path)
    result = _run(fixture, tmp_path)
    assert result.governance_verified is True
    assert result.upstream_model_artifact_bytes_verified is True
    assert result.validation_metadata_verified is True
    assert result.implementation_source_identity_verified is True
    assert result.runtime_environment_identity_verified is True
    assert (
        result.certification.process_mean_certified_transfer_ceiling
        == "fine"
    )
    assert result.historical_fixed_set_results_reclassified is False
    json.dumps(result.as_dict(), allow_nan=False)


def test_model_byte_change_hard_stops_frozen_execution(tmp_path: Path):
    fixture = _setup(tmp_path)
    (tmp_path / "r00.model").write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="artifact snapshot mismatch"):
        _run(fixture, tmp_path)


def test_runtime_validation_metadata_change_hard_stops(
    tmp_path: Path,
):
    fixture = _setup(tmp_path)
    fixture["groups"] = (
        "changed",
        *fixture["groups"][1:],
    )
    with pytest.raises(ValueError, match="metadata differ"):
        _run(fixture, tmp_path)


def test_qualification_receipt_change_after_freeze_hard_stops(
    tmp_path: Path,
):
    fixture = _setup(tmp_path)
    payload = json.loads(
        fixture["qualification_receipt"].read_text(
            encoding="utf-8"
        )
    )
    payload["power_run"]["qualification_pass"] = False
    fixture["qualification_receipt"].write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="bytes differ"):
        _run(fixture, tmp_path)


def test_freeze_refuses_unqualified_v5_receipt(tmp_path: Path):
    fixture = _setup(tmp_path)
    freeze = fixture["internal_freeze"]
    freeze.unlink()

    qualification = fixture["qualification_receipt"]
    payload = json.loads(
        qualification.read_text(encoding="utf-8")
    )
    payload["null_run"]["qualification_pass"] = False
    payload["summary"]["qualification_pass"] = False
    qualification.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    plan = tmp_path / "internal-freeze-plan.json"
    with pytest.raises(ValueError, match="null qualification"):
        create_training_process_internal_freeze_manifest(
            plan,
            freeze,
        )
    assert not freeze.exists()
