from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from odsp.upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    snapshot_upstream_model_artifacts,
    verify_upstream_model_artifact_snapshot,
)


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _decls() -> list[dict[str, str]]:
    return [
        {"refit_id": "r01", "artifact_id": "fit", "path": "models/r01.bin"},
        {"refit_id": "r00", "artifact_id": "fit", "path": "models/r00.bin"},
        {"refit_id": "r00", "artifact_id": "metadata", "path": "models/r00.json"},
    ]


def test_snapshot_is_canonical_and_path_free(tmp_path: Path):
    _write(tmp_path / "models/r00.bin", b"fit-r00")
    _write(tmp_path / "models/r00.json", b'{"seed":1}\n')
    _write(tmp_path / "models/r01.bin", b"fit-r01")

    snapshot = snapshot_upstream_model_artifacts(
        _decls(), base_dir=tmp_path, refit_ids=("r00", "r01")
    )

    assert MODEL_ARTIFACT_LOCK_ID == "odsp-upstream-model-artifact-lock-v1"
    assert snapshot == (
        {
            "refit_id": "r00",
            "artifact_id": "fit",
            "sha256": hashlib.sha256(b"fit-r00").hexdigest(),
        },
        {
            "refit_id": "r00",
            "artifact_id": "metadata",
            "sha256": hashlib.sha256(b'{"seed":1}\n').hexdigest(),
        },
        {
            "refit_id": "r01",
            "artifact_id": "fit",
            "sha256": hashlib.sha256(b"fit-r01").hexdigest(),
        },
    )
    assert all("path" not in row for row in snapshot)


def test_runtime_verification_allows_artifacts_to_move_without_content_change(tmp_path: Path):
    original = tmp_path / "original"
    moved = tmp_path / "moved"
    for root in (original, moved):
        _write(root / "a.bin", b"aaa")
        _write(root / "b.bin", b"bbb")

    frozen = snapshot_upstream_model_artifacts(
        [
            {"refit_id": "r00", "artifact_id": "fit", "path": "a.bin"},
            {"refit_id": "r01", "artifact_id": "fit", "path": "b.bin"},
        ],
        base_dir=original,
        refit_ids=("r00", "r01"),
    )
    current = verify_upstream_model_artifact_snapshot(
        frozen,
        [
            {"refit_id": "r00", "artifact_id": "fit", "path": "a.bin"},
            {"refit_id": "r01", "artifact_id": "fit", "path": "b.bin"},
        ],
        base_dir=moved,
        refit_ids=("r00", "r01"),
    )
    assert current == frozen


def test_one_byte_model_mutation_hard_stops(tmp_path: Path):
    _write(tmp_path / "r00.bin", b"before")
    _write(tmp_path / "r01.bin", b"stable")
    declarations = [
        {"refit_id": "r00", "artifact_id": "fit", "path": "r00.bin"},
        {"refit_id": "r01", "artifact_id": "fit", "path": "r01.bin"},
    ]
    frozen = snapshot_upstream_model_artifacts(
        declarations, base_dir=tmp_path, refit_ids=("r00", "r01")
    )
    _write(tmp_path / "r00.bin", b"after")
    with pytest.raises(ValueError, match="upstream model artifact snapshot mismatch"):
        verify_upstream_model_artifact_snapshot(
            frozen, declarations, base_dir=tmp_path, refit_ids=("r00", "r01")
        )


def test_every_frozen_refit_requires_at_least_one_artifact(tmp_path: Path):
    _write(tmp_path / "r00.bin", b"r00")
    with pytest.raises(ValueError, match="missing artifacts for frozen refit"):
        snapshot_upstream_model_artifacts(
            [{"refit_id": "r00", "artifact_id": "fit", "path": "r00.bin"}],
            base_dir=tmp_path,
            refit_ids=("r00", "r01"),
        )


def test_unknown_refit_and_duplicate_logical_artifact_fail_closed(tmp_path: Path):
    _write(tmp_path / "a.bin", b"a")
    _write(tmp_path / "b.bin", b"b")
    with pytest.raises(ValueError, match="unknown frozen refit"):
        snapshot_upstream_model_artifacts(
            [
                {"refit_id": "r00", "artifact_id": "fit", "path": "a.bin"},
                {"refit_id": "r99", "artifact_id": "fit", "path": "b.bin"},
            ],
            base_dir=tmp_path,
            refit_ids=("r00",),
        )
    with pytest.raises(ValueError, match="duplicate upstream model artifact"):
        snapshot_upstream_model_artifacts(
            [
                {"refit_id": "r00", "artifact_id": "fit", "path": "a.bin"},
                {"refit_id": "r00", "artifact_id": "fit", "path": "b.bin"},
            ],
            base_dir=tmp_path,
            refit_ids=("r00",),
        )


def test_symlink_and_directory_artifacts_are_rejected(tmp_path: Path):
    _write(tmp_path / "real.bin", b"x")
    (tmp_path / "alias.bin").symlink_to(tmp_path / "real.bin")
    with pytest.raises(ValueError, match="symlink"):
        snapshot_upstream_model_artifacts(
            [{"refit_id": "r00", "artifact_id": "fit", "path": "alias.bin"}],
            base_dir=tmp_path,
            refit_ids=("r00",),
        )

    (tmp_path / "model-dir").mkdir()
    with pytest.raises(ValueError, match="regular file"):
        snapshot_upstream_model_artifacts(
            [{"refit_id": "r00", "artifact_id": "fit", "path": "model-dir"}],
            base_dir=tmp_path,
            refit_ids=("r00",),
        )


def test_machine_contract_freezes_model_artifact_content_boundary():
    payload = json.loads(
        Path("ODSP_UPSTREAM_MODEL_ARTIFACT_LOCK_V1.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == 1
    assert payload["lock_id"] == MODEL_ARTIFACT_LOCK_ID
    assert payload["freeze"]["all_refits_require_artifact"] is True
    assert payload["freeze"]["artifact_sha256_frozen"] is True
    assert payload["freeze"]["local_path_is_semantic"] is False
    assert payload["runtime"]["exact_logical_id_and_sha256_match_required"] is True
    assert payload["boundaries"]["proves_score_table_was_generated_by_frozen_models"] is False


def test_canonical_external_contracts_publish_model_content_lock_boundary():
    root = Path(".")
    generator = json.loads(
        (root / "ODSP_PREOUTCOME_EXTERNAL_FREEZE_GENERATOR_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    independent = json.loads(
        (root / "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json").read_text(
            encoding="utf-8"
        )
    )
    paired = json.loads(
        (root / "ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    lattice = json.loads(
        (root / "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )

    assert generator["manifest"]["upstream_model_artifact_content_frozen"] is True
    assert generator["manifest"]["model_artifact_local_path_is_semantic"] is False
    assert independent["runtime_exact_match_requirements"]["upstream_model_artifact_content"] is True
    assert independent["epistemic_boundary"]["score_table_derivation_from_frozen_models_proven"] is False
    assert paired["pre_outcome_freeze"]["upstream_model_artifact_content_frozen"] is True
    assert paired["external_validation"]["runtime_model_artifact_content_must_match_frozen_manifest"] is True
    assert paired["external_validation"]["score_table_derivation_from_frozen_models_proven"] is False
    assert lattice["pre_outcome_freeze"]["upstream_model_artifact_content_frozen"] is True
    assert lattice["external_validation"]["runtime_model_artifact_content_must_match_frozen_manifest"] is True
    assert lattice["external_validation"]["score_table_derivation_from_frozen_models_proven"] is False
