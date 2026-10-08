from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_source_process_freeze_manifest import (
    OUTER_PROCESS_KIND,
    INNER_PROCESS_KIND,
    create_training_source_process_freeze_manifest,
)
from odsp.training_source_process_validation_provenance import (
    audit_training_source_process_validation_frame_separation,
)


def _freeze(tmp_path: Path):
    (tmp_path / "roster.csv").write_text(
        "unit,stratum\n"
        "u1,a\n"
        "u2,a\n"
        "u3,b\n"
        "u4,b\n",
        encoding="utf-8",
    )
    (tmp_path / "source.dat").write_text("source\n", encoding="utf-8")
    (tmp_path / "fit.py").write_text("def fit(x): return x\n", encoding="utf-8")
    plan = {
        "schema_version": 1,
        "source_process_id": "source-v0",
        "source_roster": {
            "path": "roster.csv",
            "format": "csv",
            "unit_id_column": "unit",
            "stratum_column": "stratum",
        },
        "source_data_artifacts": [{"role": "source", "path": "source.dat"}],
        "source_generation_artifacts": [{"role": "generator", "path": "fit.py"}],
        "fit_implementation_artifacts": [{"role": "fit", "path": "fit.py"}],
        "fit_entrypoint": "fit.py:fit",
        "fit_parameters": {},
        "source_draw_ids": [f"s{i:02d}" for i in range(8)],
        "inner_refit_ids": [f"r{i:02d}" for i in range(8)],
        "master_seed": 22,
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
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    create_training_source_process_freeze_manifest(plan_path, manifest)
    return manifest, tmp_path / "roster.csv"


def test_entire_original_source_frame_is_checked(tmp_path):
    manifest, roster = _freeze(tmp_path)
    audit = audit_training_source_process_validation_frame_separation(
        manifest,
        roster,
        ("v1", "v2"),
        row_identity_namespace="global-observation-id-v1",
        roster_format="csv",
        unit_id_column="unit",
        stratum_column="stratum",
    )
    assert audit.source_frame_validation_disjoint is True
    assert audit.entire_original_source_frame_checked is True
    assert audit.realized_outer_draws_only is False
    assert audit.nested_inner_refits_only is False
    assert audit.validation_outcomes_required is False


def test_overlap_in_unsampled_original_source_unit_is_still_leakage(tmp_path):
    manifest, roster = _freeze(tmp_path)
    audit = audit_training_source_process_validation_frame_separation(
        manifest,
        roster,
        ("v1", "u3"),
        row_identity_namespace="global-observation-id-v1",
        roster_format="csv",
        unit_id_column="unit",
        stratum_column="stratum",
    )
    assert audit.source_frame_validation_disjoint is False
    assert audit.overlapping_unit_count == 1
    assert audit.separation_category == "source_frame_validation_leakage"
    assert "u3" not in str(audit.as_dict())


def test_source_roster_bytes_must_match_manifest(tmp_path):
    manifest, roster = _freeze(tmp_path)
    roster.write_text(
        "unit,stratum\nu1,a\nu2,a\nu3,b\nu5,b\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="file bytes"):
        audit_training_source_process_validation_frame_separation(
            manifest,
            roster,
            ("v1", "v2"),
            row_identity_namespace="global-observation-id-v1",
            roster_format="csv",
            unit_id_column="unit",
            stratum_column="stratum",
        )
