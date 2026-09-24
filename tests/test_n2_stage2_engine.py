from __future__ import annotations

import copy
import csv
from pathlib import Path

import pytest

from odsp.n2_failure_mode_stage2 import (
    FROZEN_CONTRACT_MERGE_SHA,
    load_stage2_contract,
    prepare_penguins_rows,
    run_penguins_stage2,
    stage2_synthesis,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_POOLED_REFERENCE_FAILURE_MODE_STAGE2_REAL_DATA_CONTRACT.json"


def _contract() -> dict[str, object]:
    return load_stage2_contract(CONTRACT)


def _toy_penguins(path: Path) -> None:
    rows = []
    species = ("Adelie", "Chinstrap", "Gentoo")
    islands = ("Biscoe", "Dream", "Torgersen")
    years = ("2007", "2008", "2009")
    index = 0
    for year_index, year in enumerate(years):
        for species_index, name in enumerate(species):
            for replicate in range(36):
                island = islands[(species_index + (replicate % 2 if species_index == 0 else 0)) % 3]
                rows.append(
                    {
                        "species": name,
                        "island": island,
                        "year": year,
                        "bill_length_mm": 35 + 6 * species_index + 0.05 * replicate + 0.1 * year_index,
                        "bill_depth_mm": 15 + 1.5 * species_index + 0.03 * replicate,
                        "flipper_length_mm": 180 + 18 * species_index + replicate % 5,
                        "body_mass_g": 3200 + 700 * species_index + 5 * replicate,
                    }
                )
                index += 1
    assert len(rows) == 324
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_stage2_engine_is_bound_to_merged_frozen_contract():
    contract = _contract()
    assert contract["status"] == "pre_fresh_result_frozen"
    assert FROZEN_CONTRACT_MERGE_SHA == "8a83079f395b7e22bf82d87a430d8169247bf996"


def test_penguins_preparation_retains_species_and_source_row_identity(tmp_path: Path):
    source = tmp_path / "penguins.csv"
    _toy_penguins(source)
    rows = prepare_penguins_rows(source)

    assert len(rows) == 324
    assert {row.species for row in rows} == {"Adelie", "Chinstrap", "Gentoo"}
    assert {row.year for row in rows} == {"2007", "2008", "2009"}
    assert rows[0].row_id == "penguin-000"
    assert rows[-1].row_id == "penguin-323"


def test_toy_penguins_runs_with_three_year_small_cluster_policy(tmp_path: Path):
    pytest.importorskip("sklearn")
    source = tmp_path / "penguins.csv"
    _toy_penguins(source)
    contract = copy.deepcopy(_contract())
    penguins = next(
        row for row in contract["systems"] if row["system_id"] == "PALMER_PENGUINS"
    )
    penguins["learner"]["parameters"]["n_estimators"] = 10

    result = run_penguins_stage2(source, contract=contract)
    naive = result["naive_population_result"]
    audit = result["audit_population_result"]

    assert result["prepared_row_count"] == 324
    assert result["years"] == ["2007", "2008", "2009"]
    assert naive["cluster_count"] == 3
    assert audit["cluster_count"] == 3
    assert naive["total_gain"]["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert naive["total_gain"]["mean_gain_interval_df"] == 2
    assert audit["steps"][1]["mean_gain_interval_method"] == "cluster_robust_t_cr1"
    assert audit["steps"][1]["mean_gain_interval_df"] == 2
    assert result["scientific_boundary"]["naive_and_audit_models_are_not_an_additive_identity"] is True
    assert result["scientific_boundary"]["causal_morphology_claim_supported"] is False


def test_stage2_synthesis_keeps_serengeti_out_of_failure_denominator():
    penguins = {
        "comparison": {
            "point_sign_reversal": True,
            "inferential_downgrade": True,
            "strong_attenuation": True,
            "fresh_penguins_decision": "fresh_empirical_reversal",
        },
        "naive_population_result": {"cluster_count": 3},
    }
    bop = {
        "population_result": {
            "cluster_count": 4,
            "total_gain": {
                "mean_gain": 0.57,
                "mean_gain_status": "uncertain",
            },
            "steps": [
                {"mean_gain": 0.07, "mean_gain_status": "uncertain"},
                {"mean_gain": 0.50, "mean_gain_status": "uncertain"},
            ],
        }
    }
    serengeti = {
        "terminal_category": "temporal_partition_generalizing",
        "transfer_category": "generalizing",
        "heldout_gains": [0.057, 0.045, 0.045],
    }

    result = stage2_synthesis(
        penguins,
        bop_v2_receipt=bop,
        serengeti_receipt=serengeti,
    )
    assert result["descriptive_counts"]["failure_eligible_system_count"] == 2
    assert result["systems"]["SNAPSHOT_SERENGETI"]["failure_mode_eligible"] is False
    assert "species identity is itself" in result["systems"]["SNAPSHOT_SERENGETI"]["semantic_control"]
    assert result["descriptive_counts"]["prevalence_or_meta_analytic_rate_claimed"] is False
    assert result["stage1_full_claim_reclassified"] is False
