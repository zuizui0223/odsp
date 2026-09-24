from __future__ import annotations

import json
from pathlib import Path

from scripts.aggregate_n2_stage2_real_data import aggregate


def test_stage2_aggregator_keeps_semantic_control_outside_flip_denominator(tmp_path: Path):
    penguins = {
        "schema_version": 1,
        "result_id": "n2-stage2-palmer-penguins-v1",
        "contract_id": "n2-pooled-reference-failure-mode-stage2-real-data-v1",
        "contract_merge_sha": "8a83079f395b7e22bf82d87a430d8169247bf996",
        "system_id": "PALMER_PENGUINS",
        "fresh_outcome": True,
        "source": {
            "upstream_commit": "8957207b78d6ccd1b4654a9dd9c9041b657478ab",
            "raw_csv_sha256": "fixture",
            "prepared_row_count": 100,
            "years": ["2007", "2008", "2009"],
            "species": ["Adelie", "Chinstrap", "Gentoo"]
        },
        "naive_pooled_gain": {
            "mean_gain": 0.20,
            "mean_gain_status": "positive"
        },
        "audit_context_gain": {
            "mean_gain": -0.01,
            "mean_gain_status": "uncertain"
        },
        "decision_components": {
            "point_sign_reversal": True,
            "inferential_downgrade": True,
            "strong_attenuation": True
        },
        "decision": "fresh_empirical_reversal"
    }
    path = tmp_path / "penguins.json"
    path.write_text(json.dumps(penguins), encoding="utf-8")

    result = aggregate(path)

    assert result["counts"]["system_count"] == 2
    assert result["systems"]["PALMER_PENGUINS"]["point_sign_reversal"] is True
    assert result["semantic_negative_control"]["system_id"] == "SNAPSHOT_SERENGETI"
    assert result["semantic_negative_control"]["included_in_system_flip_denominator"] is False
    assert result["semantic_negative_control"]["pooled_reference_scientifically_appropriate"] is True

    sentinel = result["buteo_motivating_sentinel"]
    assert sentinel["mean_total_gain"] > 0
    assert sentinel["mean_context_within_species_component"] < 0
    assert sentinel["descriptive_point_sign_reversal"] is True
    assert sentinel["included_in_system_flip_denominator"] is False


def test_bop_system_level_result_is_not_overclaimed_after_few_cluster_fix(tmp_path: Path):
    penguins = {
        "schema_version": 1,
        "result_id": "n2-stage2-palmer-penguins-v1",
        "contract_id": "n2-pooled-reference-failure-mode-stage2-real-data-v1",
        "contract_merge_sha": "8a83079f395b7e22bf82d87a430d8169247bf996",
        "system_id": "PALMER_PENGUINS",
        "fresh_outcome": True,
        "source": {"upstream_commit": "x"},
        "naive_pooled_gain": {"mean_gain": 0.01, "mean_gain_status": "uncertain"},
        "audit_context_gain": {"mean_gain": 0.01, "mean_gain_status": "uncertain"},
        "decision_components": {
            "point_sign_reversal": False,
            "inferential_downgrade": False,
            "strong_attenuation": False
        },
        "decision": "fresh_empirical_no_support"
    }
    path = tmp_path / "penguins.json"
    path.write_text(json.dumps(penguins), encoding="utf-8")

    result = aggregate(path)
    bop = result["systems"]["BOP_RODENT"]

    assert bop["naive_pooled_mean_gain"] > 0
    assert bop["naive_pooled_status"] == "uncertain"
    assert bop["corrected_context_mean_gain"] > 0
    assert bop["corrected_context_status"] == "uncertain"
    assert bop["point_sign_reversal"] is False
    assert bop["inferential_downgrade"] is False
