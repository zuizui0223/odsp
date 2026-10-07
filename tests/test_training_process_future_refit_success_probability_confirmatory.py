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
from odsp.training_process_future_refit_success_probability_confirmatory import (
    SURFACE_ID,
    certify_predeclared_training_process_future_refit_success_probability_v1,
)
from odsp.training_process_managed_generation import (
    run_managed_training_process_generation,
)


def _process(tmp_path: Path):
    (tmp_path / "roster.csv").write_text(
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
    (tmp_path / "train.dat").write_bytes(b"training-source\n")
    (tmp_path / "fit.py").write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--refit-id', required=True)\n"
        "p.add_argument('--membership', required=True)\n"
        "p.add_argument('--fit-seed', required=True, type=int)\n"
        "p.add_argument('--output-dir', required=True)\n"
        "a=p.parse_args()\n"
        "rows=json.loads(Path(a.membership).read_text())\n"
        "Path(a.output_dir,'model.json').write_text("
        "json.dumps({'refit':a.refit_id,'seed':a.fit_seed,'n':sum(r['count'] for r in rows)}, sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    refit_ids = [f"r{i:02d}" for i in range(8)]
    freeze = {
        "schema_version": 1,
        "training_process_id": "future-refit-probability-wrapper-test",
        "training_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [{"role": "training", "path": "train.dat"}],
        "implementation_artifacts": [{"role": "fit", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:cli",
        "fit_parameters": {},
        "refit_ids": refit_ids,
        "master_seed": 20261016,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    create_training_process_freeze_manifest(freeze_path, manifest)

    managed = {
        "schema_version": 1,
        "training_process_id": freeze["training_process_id"],
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
    managed_path = tmp_path / "managed.json"
    managed_path.write_text(json.dumps(managed), encoding="utf-8")
    generated = run_managed_training_process_generation(
        managed_path,
        tmp_path / "outputs",
        tmp_path / "managed-receipt.json",
    )
    return {
        "manifest": manifest,
        "roster": tmp_path / "roster.csv",
        "receipt": tmp_path / "managed-receipt.json",
        "receipt_sha": generated["receipt_sha256"],
        "refit_ids": tuple(refit_ids),
    }


def _validation():
    groups, blocks, row_ids = [], [], []
    for group_index in range(2):
        for block_index in range(8):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
            row_ids.append(f"validation-{group_index}-{block_index}")
    n = len(groups)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.5
    fine = coarse + 0.4
    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("coarse", ("species",), coarse),
        RefitInformationLevelScores(
            "fine", ("species", "context"), fine
        ),
    )
    return levels, tuple(groups), tuple(blocks), tuple(row_ids)


def _run(process, levels, groups, blocks, row_ids):
    return certify_predeclared_training_process_future_refit_success_probability_v1(
        levels,
        groups,
        blocks=blocks,
        validation_row_ids=row_ids,
        refit_ids=process["refit_ids"],
        training_process_manifest_path=process["manifest"],
        managed_generation_receipt_path=process["receipt"],
        managed_generation_receipt_sha256=process["receipt_sha"],
        training_roster_path=process["roster"],
        row_identity_namespace="global-observation-id-v1",
        roster_format="csv",
        unit_id_column="unit",
        stratum_column="stratum",
        bootstrap_draws=500,
    )


def test_probability_wrapper_verifies_process_generation_and_frame(tmp_path):
    process = _process(tmp_path)
    levels, groups, blocks, row_ids = _validation()
    result = _run(process, levels, groups, blocks, row_ids)

    assert result.surface_id == SURFACE_ID
    assert result.process_manifest_verified is True
    assert result.managed_generation_verified is True
    assert result.exact_refit_schedule_verified is True
    assert result.training_source_frame_validation_disjoint is True
    assert result.entire_training_source_frame_checked is True
    assert result.certification.audit.certified_success_count == 8
    assert result.certification.audit.future_refit_success_probability_lower_bound == pytest.approx(
        0.6305833524471807,
        abs=1e-14,
    )
    assert result.score_table_derivation_from_generated_models_independently_proven is False
    assert result.fixed_set_results_reclassified is False
    assert result.process_mean_v5_results_reclassified is False
    json.dumps(result.as_dict(), allow_nan=False)


def test_probability_wrapper_fails_closed_on_source_frame_overlap(tmp_path):
    process = _process(tmp_path)
    levels, groups, blocks, row_ids = _validation()
    bad_ids = list(row_ids)
    bad_ids[0] = "u3"
    with pytest.raises(ValueError, match="overlaps validation"):
        _run(process, levels, groups, blocks, bad_ids)


def test_probability_wrapper_requires_exact_managed_receipt_digest(tmp_path):
    process = _process(tmp_path)
    levels, groups, blocks, row_ids = _validation()
    with pytest.raises(ValueError, match="receipt bytes"):
        certify_predeclared_training_process_future_refit_success_probability_v1(
            levels,
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            refit_ids=process["refit_ids"],
            training_process_manifest_path=process["manifest"],
            managed_generation_receipt_path=process["receipt"],
            managed_generation_receipt_sha256="0" * 64,
            training_roster_path=process["roster"],
            row_identity_namespace="global-observation-id-v1",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
            bootstrap_draws=500,
        )


def test_probability_wrapper_rejects_refit_set_mismatch(tmp_path):
    process = _process(tmp_path)
    levels, groups, blocks, row_ids = _validation()
    bad = process["refit_ids"][:-1] + ("other",)
    with pytest.raises(ValueError, match="refit IDs"):
        certify_predeclared_training_process_future_refit_success_probability_v1(
            levels,
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            refit_ids=bad,
            training_process_manifest_path=process["manifest"],
            managed_generation_receipt_path=process["receipt"],
            managed_generation_receipt_sha256=process["receipt_sha"],
            training_roster_path=process["roster"],
            row_identity_namespace="global-observation-id-v1",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
            bootstrap_draws=500,
        )
