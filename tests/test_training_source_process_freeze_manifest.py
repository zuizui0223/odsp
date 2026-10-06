from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_source_process_freeze_manifest import (
    INNER_PROCESS_KIND,
    OUTER_PROCESS_KIND,
    SOURCE_PROCESS_MANIFEST_TYPE,
    create_training_source_process_freeze_manifest,
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
    (tmp_path / "source.dat").write_bytes(b"source\n")
    (tmp_path / "source_gen.py").write_text("SOURCE=1\n", encoding="utf-8")
    (tmp_path / "fit.py").write_text("FIT=1\n", encoding="utf-8")
    plan = {
        "schema_version": 1,
        "source_process_id": "source-v0",
        "source_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "source_data_artifacts": [
            {"role": "source_data", "path": "source.dat"}
        ],
        "source_generation_artifacts": [
            {"role": "source_generator", "path": "source_gen.py"}
        ],
        "fit_implementation_artifacts": [
            {"role": "fit", "path": "fit.py"}
        ],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {"penalty": 0.1},
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
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def test_source_process_manifest_freezes_nested_balanced_schedule(tmp_path):
    plan = _setup(tmp_path)
    result = create_training_source_process_freeze_manifest(
        plan, tmp_path / "manifest.json"
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_type"] == SOURCE_PROCESS_MANIFEST_TYPE
    assert manifest["source_process_id"] == "source-v0"
    assert manifest["source_draw_count"] == 8
    assert manifest["inner_refit_count_per_source"] == 8
    assert len(manifest["nested_schedule"]) == 8
    assert result["source_draw_count"] == 8
    assert result["inner_refit_count_per_source"] == 8

    outer_digests = set()
    fit_seeds = set()
    for source in manifest["nested_schedule"]:
        assert len(source["outer_membership_sha256"]) == 64
        outer_digests.add(source["outer_membership_sha256"])
        assert len(source["inner_refit_schedule"]) == 8
        for refit in source["inner_refit_schedule"]:
            assert len(refit["inner_membership_sha256"]) == 64
            fit_seeds.add(refit["fit_seed"])
    assert len(outer_digests) > 1
    assert len(fit_seeds) == 64


def test_source_process_nested_schedule_is_deterministic_given_setup(tmp_path):
    plan = _setup(tmp_path)
    create_training_source_process_freeze_manifest(
        plan, tmp_path / "m1.json"
    )
    create_training_source_process_freeze_manifest(
        plan, tmp_path / "m2.json"
    )
    one = json.loads((tmp_path / "m1.json").read_text(encoding="utf-8"))
    two = json.loads((tmp_path / "m2.json").read_text(encoding="utf-8"))
    assert one["nested_schedule"] == two["nested_schedule"]
    assert one["source_roster"] == two["source_roster"]
    assert one["fit_parameters"] == two["fit_parameters"]


def test_source_process_manifest_inner_draws_preserve_outer_draw_size_per_stratum(tmp_path):
    plan = _setup(tmp_path)
    create_training_source_process_freeze_manifest(
        plan, tmp_path / "manifest.json"
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_roster"]["stratum_sizes"] == {"a": 3, "b": 3}
    # Digests are over canonical rows including zero-count original units; exact
    # membership bytes are intentionally reconstructed later by managed execution.
    assert manifest["assumptions"]["inner_refits_nested_within_source_draw"] is True
    assert manifest["assumptions"]["inner_refits_are_not_independent_outer_source_draws"] is True


def test_source_process_manifest_is_non_overwriting(tmp_path):
    plan = _setup(tmp_path)
    out = tmp_path / "manifest.json"
    create_training_source_process_freeze_manifest(plan, out)
    with pytest.raises(FileExistsError):
        create_training_source_process_freeze_manifest(plan, out)


def test_source_process_plan_rejects_too_few_outer_or_inner_draws(tmp_path):
    plan = _setup(tmp_path)
    raw = json.loads(plan.read_text(encoding="utf-8"))
    raw["source_draw_ids"] = ["s0"] * 4
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        create_training_source_process_freeze_manifest(
            bad, tmp_path / "bad-manifest.json"
        )


def test_source_process_ids_must_be_safe_path_components(tmp_path):
    plan_path = _setup(tmp_path)
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["source_draw_ids"][0] = "../escape"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="safe single path component"):
        create_training_source_process_freeze_manifest(
            plan_path, tmp_path / "manifest.json"
        )

    plan_path = _setup(tmp_path)
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["inner_refit_ids"][0] = "bad\\name"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="safe single path component"):
        create_training_source_process_freeze_manifest(
            plan_path, tmp_path / "manifest-2.json"
        )
