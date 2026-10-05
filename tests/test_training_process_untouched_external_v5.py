from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_external_freeze_v1 import (
    MANIFEST_TYPE,
    create_training_process_v5_external_freeze,
)
from odsp.training_process_freeze_manifest import (
    PROCESS_KIND,
    create_training_process_freeze_manifest,
)
from odsp.training_process_managed_generation import (
    run_managed_training_process_generation,
)
from odsp.training_process_untouched_external_v5 import (
    EXTERNAL_RECEIPT_TYPE,
    run_untouched_external_training_process_v5,
)


def _process(tmp_path: Path):
    (tmp_path / "train-roster.csv").write_text(
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
        "payload={'refit':a.refit_id,'seed':a.fit_seed,"
        "'n':sum(int(r['count']) for r in rows)}\n"
        "Path(a.output_dir,'model.json').write_text("
        "json.dumps(payload,sort_keys=True)+'\\n')\n",
        encoding="utf-8",
    )
    ids = [f"r{i:02d}" for i in range(8)]
    freeze_plan = {
        "schema_version": 1,
        "training_process_id": "external-process-v5-test",
        "training_roster": {
            "path": "train-roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "training_data_artifacts": [{"role": "training", "path": "train.dat"}],
        "implementation_artifacts": [{"role": "fit", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:cli",
        "fit_parameters": {},
        "refit_ids": ids,
        "master_seed": 20261005,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }
    fp = tmp_path / "training-freeze-plan.json"
    fp.write_text(json.dumps(freeze_plan), encoding="utf-8")
    manifest = tmp_path / "training-process-manifest.json"
    create_training_process_freeze_manifest(fp, manifest)

    managed = {
        "schema_version": 1,
        "training_process_id": "external-process-v5-test",
        "manifest_path": manifest.name,
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
            {"artifact_id": "primary_model", "relative_path": "model.json"}
        ],
    }
    mp = tmp_path / "managed-plan.json"
    mp.write_text(json.dumps(managed), encoding="utf-8")
    managed_receipt = tmp_path / "managed-receipt.json"
    run_managed_training_process_generation(
        mp, tmp_path / "generated-models", managed_receipt
    )
    return {
        "manifest": manifest,
        "managed_receipt": managed_receipt,
        "training_roster": tmp_path / "train-roster.csv",
        "refit_ids": tuple(ids),
    }


def _external_rows(tmp_path: Path, *, overlap: bool = False) -> Path:
    lines = ["row_id,group_id,block_id,sample_weight"]
    for g in range(2):
        for b in range(8):
            row_id = "u1" if overlap and g == 0 and b == 0 else f"ext-{g}-{b}"
            lines.append(f"{row_id},g{g},g{g}-b{b},1.0")
    path = tmp_path / "external-roster.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _external_plan(tmp_path: Path, process, roster: Path) -> Path:
    plan = {
        "schema_version": 1,
        "external_dataset_id": "external-dataset-v1",
        "row_identity_namespace": "global-observation-id-v1",
        "roster": {"path": roster.name, "format": "csv"},
        "training_process_manifest_path": process["manifest"].name,
        "managed_generation_receipt_path": process["managed_receipt"].name,
        "training_roster": {
            "path": process["training_roster"].name,
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "score": {
            "kind": "proper_score",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "levels": [
            {"name": "pooled", "information": []},
            {"name": "coarse", "information": ["species"]},
            {"name": "fine", "information": ["species", "context"]},
        ],
        "certification": {
            "component_one_sided_alpha": 0.05,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }
    path = tmp_path / "external-freeze-plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def _score_contract():
    return {
        "kind": "proper_score",
        "name": "log",
        "orientation": "higher_is_better",
        "common_scoring_rule": True,
        "common_reference_measure": True,
    }


def _runtime_scores():
    row_ids, groups, blocks, weights = [], [], [], []
    for g in range(2):
        for b in range(8):
            row_ids.append(f"ext-{g}-{b}")
            groups.append(f"g{g}")
            blocks.append(f"g{g}-b{b}")
            weights.append(1.0)
    n = len(row_ids)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.55
    fine = coarse + 0.45
    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("coarse", ("species",), coarse),
        RefitInformationLevelScores(
            "fine", ("species", "context"), fine
        ),
    )
    return (
        levels,
        tuple(groups),
        tuple(blocks),
        tuple(row_ids),
        tuple(weights),
    )


def _frozen(tmp_path: Path):
    process = _process(tmp_path)
    roster = _external_rows(tmp_path)
    plan = _external_plan(tmp_path, process, roster)
    manifest = tmp_path / "external-freeze-manifest.json"
    receipt = tmp_path / "external-freeze-receipt.json"
    frozen = create_training_process_v5_external_freeze(
        plan, manifest, receipt
    )
    return process, manifest, receipt, frozen


def test_external_freeze_is_outcome_free_and_binds_full_design(tmp_path):
    process, manifest_path, receipt_path, frozen = _frozen(tmp_path)
    manifest = frozen["manifest"]
    assert manifest["manifest_type"] == MANIFEST_TYPE
    assert manifest["external_row_count"] == 16
    assert manifest["positive_block_count_by_group"] == {"g0": 8, "g1": 8}
    assert manifest["training_source_frame_validation_disjoint"] is True
    assert manifest["boundaries"]["external_outcomes_read_by_freeze_generator"] is False
    assert manifest["internal_qualified_route"]["role"] == "primary_confirmatory"
    assert manifest["external_endpoint"]["canonical_surface"].endswith(
        "run_untouched_external_training_process_v5"
    )
    assert receipt_path.is_file()
    assert process["manifest"].is_file()


def test_external_freeze_rejects_source_frame_overlap(tmp_path):
    process = _process(tmp_path)
    roster = _external_rows(tmp_path, overlap=True)
    plan = _external_plan(tmp_path, process, roster)
    with pytest.raises(ValueError, match="overlaps"):
        create_training_process_v5_external_freeze(
            plan,
            tmp_path / "bad-manifest.json",
            tmp_path / "bad-receipt.json",
        )


def test_untouched_external_endpoint_runs_only_after_exact_semantic_match(tmp_path):
    process, manifest, receipt, _ = _frozen(tmp_path)
    levels, groups, blocks, row_ids, weights = _runtime_scores()
    result = run_untouched_external_training_process_v5(
        manifest,
        receipt,
        levels,
        groups,
        blocks=blocks,
        validation_row_ids=row_ids,
        sample_weight=weights,
        score_contract=_score_contract(),
        refit_ids=process["refit_ids"],
        training_process_manifest_path=process["manifest"],
        managed_generation_receipt_path=process["managed_receipt"],
        training_roster_path=process["training_roster"],
    )
    assert result.receipt_type == EXTERNAL_RECEIPT_TYPE
    assert result.freeze_manifest_semantics_verified is True
    assert result.external_design_exact_match_verified is True
    assert result.process_identity_exact_match_verified is True
    assert result.qualification_evidence_snapshot_verified is True
    assert result.implementation_source_snapshot_verified is True
    assert result.runtime_environment_snapshot_verified is True
    assert result.training_source_frame_validation_disjoint is True
    assert result.certification.certification.process_mean_certified_transfer_ceiling == "fine"
    assert result.fixed_set_results_reclassified is False
    json.dumps(result.as_dict(), allow_nan=False)


def test_runtime_weight_or_block_change_is_rejected_before_inference(tmp_path):
    process, manifest, receipt, _ = _frozen(tmp_path)
    levels, groups, blocks, row_ids, weights = _runtime_scores()
    changed_weights = list(weights)
    changed_weights[0] = 2.0
    with pytest.raises(ValueError, match="design"):
        run_untouched_external_training_process_v5(
            manifest,
            receipt,
            levels,
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            sample_weight=changed_weights,
            score_contract=_score_contract(),
            refit_ids=process["refit_ids"],
            training_process_manifest_path=process["manifest"],
            managed_generation_receipt_path=process["managed_receipt"],
            training_roster_path=process["training_roster"],
        )

    changed_blocks = list(blocks)
    changed_blocks[0] = "g0-posthoc"
    with pytest.raises(ValueError, match="design"):
        run_untouched_external_training_process_v5(
            manifest,
            receipt,
            levels,
            groups,
            blocks=changed_blocks,
            validation_row_ids=row_ids,
            sample_weight=weights,
            score_contract=_score_contract(),
            refit_ids=process["refit_ids"],
            training_process_manifest_path=process["manifest"],
            managed_generation_receipt_path=process["managed_receipt"],
            training_roster_path=process["training_roster"],
        )


def test_manifest_and_receipt_coedit_cannot_change_qualification_route(tmp_path):
    process, manifest_path, receipt_path, _ = _frozen(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["internal_qualified_route"]["qualification_registry_id"] = "posthoc-registry"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    import hashlib
    receipt["manifest_sha256"] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    levels, groups, blocks, row_ids, weights = _runtime_scores()
    with pytest.raises(ValueError, match="qualification route"):
        run_untouched_external_training_process_v5(
            manifest_path,
            receipt_path,
            levels,
            groups,
            blocks=blocks,
            validation_row_ids=row_ids,
            sample_weight=weights,
            score_contract=_score_contract(),
            refit_ids=process["refit_ids"],
            training_process_manifest_path=process["manifest"],
            managed_generation_receipt_path=process["managed_receipt"],
            training_roster_path=process["training_roster"],
        )


def test_freeze_manifest_and_receipt_are_non_overwriting(tmp_path):
    process = _process(tmp_path)
    roster = _external_rows(tmp_path)
    plan = _external_plan(tmp_path, process, roster)
    manifest = tmp_path / "freeze-manifest.json"
    receipt = tmp_path / "freeze-receipt.json"
    create_training_process_v5_external_freeze(plan, manifest, receipt)
    with pytest.raises(FileExistsError):
        create_training_process_v5_external_freeze(
            plan, manifest, tmp_path / "other-receipt.json"
        )
