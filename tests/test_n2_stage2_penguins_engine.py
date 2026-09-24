from __future__ import annotations

import csv
from pathlib import Path

import pytest

from odsp.n2_stage2_penguins import (
    FROZEN_STAGE2_CONTRACT_MERGE_SHA,
    prepare_penguins,
    run_penguins_stage2,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_POOLED_REFERENCE_FAILURE_MODE_STAGE2_REAL_DATA_CONTRACT.json"


def _write_fixture(path: Path) -> None:
    rows = []
    species_values = ("Adelie", "Chinstrap", "Gentoo")
    island_values = ("Biscoe", "Dream", "Torgersen")
    for year_index, year in enumerate(("2007", "2008", "2009")):
        for species_index, species in enumerate(species_values):
            for replicate in range(18):
                island = island_values[species_index]
                base = 35.0 + 8.0 * species_index
                rows.append(
                    {
                        "species": species,
                        "island": island,
                        "year": year,
                        "bill_length_mm": base + 0.03 * replicate + 0.01 * year_index,
                        "bill_depth_mm": 15.0 + 2.0 * species_index + 0.01 * replicate,
                        "flipper_length_mm": 180.0 + 20.0 * species_index + 0.1 * replicate,
                        "body_mass_g": 3200.0 + 900.0 * species_index + 2.0 * replicate,
                    }
                )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_stage2_penguins_engine_is_bound_to_merged_contract():
    assert (
        FROZEN_STAGE2_CONTRACT_MERGE_SHA
        == "8a83079f395b7e22bf82d87a430d8169247bf996"
    )


def test_prepare_penguins_uses_source_row_id_before_filtering(tmp_path: Path):
    path = tmp_path / "penguins.csv"
    _write_fixture(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("Adelie,Torgersen,2007,NA,18,190,3500\n")

    prepared = prepare_penguins(path)
    assert len(prepared) == 162
    assert prepared[0].row_id == "penguin-000"
    assert prepared[-1].row_id == "penguin-161"


def test_stage2_penguins_synthetic_fixture_uses_small_cluster_correction(tmp_path: Path):
    pytest.importorskip("sklearn")
    path = tmp_path / "penguins.csv"
    _write_fixture(path)

    result = run_penguins_stage2(path, CONTRACT)

    assert result["source"]["prepared_row_count"] == 162
    assert result["source"]["years"] == ["2007", "2008", "2009"]
    assert result["source"]["species"] == ["Adelie", "Chinstrap", "Gentoo"]
    assert result["audit_additivity_max_abs_error"] <= 1e-12

    for key in (
        "naive_pooled_gain",
        "audit_layer_component",
        "audit_context_gain",
        "audit_total_gain",
    ):
        summary = result[key]
        assert summary["cluster_count"] == 3
        assert summary["mean_gain_interval_method"] == "cluster_robust_t_cr1"
        assert summary["mean_gain_interval_df"] == 2
        assert (
            summary["positive_fraction_lower_method"]
            == "wilson_score_group_level_small_cluster_fallback"
        )

    assert result["decision"] in {
        "fresh_empirical_reversal",
        "fresh_empirical_attenuation",
        "fresh_empirical_no_support",
    }


def test_stage2_penguins_result_does_not_claim_causality_or_prevalence(tmp_path: Path):
    pytest.importorskip("sklearn")
    path = tmp_path / "penguins.csv"
    _write_fixture(path)

    result = run_penguins_stage2(path, CONTRACT)
    boundary = result["scientific_boundary"]
    assert boundary["species_layer_is_causal"] is False
    assert boundary["morphology_determines_island_causally"] is False
    assert boundary["result_estimates_literature_prevalence"] is False
    assert boundary["stage1_claim_reclassified"] is False
