from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from odsp.cli import main as cli_main
from odsp.information_transfer_contract import (
    run_information_transfer_contract,
    validate_information_transfer_contract,
)


def _contract(*, block: str | None = "block", mode: str = "confirmatory") -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "external-score-known-truth-v1",
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "group": "group",
            "block": block,
            "weight": "weight",
        },
        "score": {
            "kind": "log",
            "name": "log_predictive_probability",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "evaluation": {
            "analysis_mode": mode,
            "heldout_predictions": True,
            "same_rows_across_levels": True,
            "heldout_outcome_not_used_for_prediction_or_selection": True,
            "filtration_frozen_before_outcome_scoring": mode == "confirmatory",
            "row_independence_if_no_block": block is None,
        },
        "levels": [
            {"name": "pooled", "information": [], "score_column": "pooled"},
            {
                "name": "species",
                "information": ["species"],
                "score_column": "species",
            },
            {
                "name": "species_context",
                "information": ["species", "context"],
                "score_column": "full",
            },
        ],
        "certification": {
            "familywise_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260913,
            "minimum_blocks_per_group": 2,
            "gain_tolerance": 0.0,
        },
    }


def _write_scores(path: Path, *, duplicate_row_id: bool = False) -> None:
    rows: list[dict[str, object]] = []
    index = 0
    for group, full in (("g1", -0.3), ("g2", -0.7)):
        for block in range(4):
            rows.append(
                {
                    "row_id": "row-0" if duplicate_row_id and index == 1 else f"row-{index}",
                    "group": group,
                    "block": f"{group}-b{block}",
                    "weight": 1.0,
                    "pooled": -1.0,
                    "species": -0.5,
                    "full": full,
                }
            )
            index += 1
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_contract(path: Path, contract: dict[str, object]) -> None:
    path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")


def test_external_score_contract_recovers_non_skippable_certified_ceiling(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    _write_scores(data)
    _write_contract(contract_path, _contract())

    receipt = run_information_transfer_contract(contract_path)

    assert receipt["receipt_type"] == "odsp_information_transfer_endpoint"
    assert receipt["input_row_count"] == 8
    assert receipt["score_contract"]["kind"] == "log"
    assert receipt["evaluation_declarations"]["analysis_mode"] == "confirmatory"
    assert receipt["scientific_boundary"]["upstream_model_fitted_by_odsp"] is False
    assert receipt["scientific_boundary"]["upstream_model_refit_uncertainty_included"] is False
    assert receipt["scientific_boundary"]["confirmatory_eligible_from_contract_declarations"] is True

    point = receipt["point_result"]["predictive_result"]
    assert point["total_gain_category"] == "generalizing"
    assert point["all_group_point_transfer_ceiling"] == "species"

    certified = receipt["certified_result"]["certification"]
    assert certified["point_transfer_ceiling"] == "species"
    assert certified["certified_transfer_ceiling"] == "species"
    assert certified["steps"][0]["category"] == "robust_generalizing"
    assert certified["steps"][1]["category"] == "mixed"
    assert certified["row_independence_assumed"] is False


def test_transfer_cli_emits_same_deterministic_receipt(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    _write_scores(data)
    _write_contract(contract_path, _contract())

    assert cli_main(["transfer", "--contract", str(contract_path), "--out", str(out_a)]) == 0
    assert cli_main(["transfer", "--contract", str(contract_path), "--out", str(out_b)]) == 0
    assert out_a.read_bytes() == out_b.read_bytes()
    receipt = json.loads(out_a.read_text(encoding="utf-8"))
    assert receipt["certified_result"]["certification"]["certified_transfer_ceiling"] == "species"


def test_contract_rejects_a_model_field_and_lower_is_better_scores():
    contract = _contract()
    contract["model"] = {"kind": "random_forest"}
    with pytest.raises(ValueError, match="unknown fields: model"):
        validate_information_transfer_contract(contract)

    contract = _contract()
    contract["score"]["orientation"] = "lower_is_better"
    with pytest.raises(ValueError, match="higher_is_better"):
        validate_information_transfer_contract(contract)


def test_contract_requires_common_log_reference_measure_and_common_scoring_rule():
    contract = _contract()
    contract["score"]["common_reference_measure"] = False
    with pytest.raises(ValueError, match="common_reference_measure=true"):
        validate_information_transfer_contract(contract)

    contract = _contract()
    contract["score"]["common_scoring_rule"] = False
    with pytest.raises(ValueError, match="common_scoring_rule must be true"):
        validate_information_transfer_contract(contract)


def test_contract_rejects_non_nested_information_and_equal_information_sets():
    contract = _contract()
    contract["levels"][2]["information"] = ["context"]
    with pytest.raises(ValueError, match="not nested"):
        validate_information_transfer_contract(contract)

    contract = _contract()
    contract["levels"][2]["information"] = ["species"]
    with pytest.raises(ValueError, match="adds no information"):
        validate_information_transfer_contract(contract)


def test_confirmatory_contract_requires_frozen_filtration_and_heldout_predictions():
    contract = _contract()
    contract["evaluation"]["filtration_frozen_before_outcome_scoring"] = False
    with pytest.raises(ValueError, match="confirmatory analysis requires"):
        validate_information_transfer_contract(contract)

    contract = _contract()
    contract["evaluation"]["heldout_predictions"] = False
    with pytest.raises(ValueError, match="heldout_predictions must be true"):
        validate_information_transfer_contract(contract)

    contract = _contract()
    contract["evaluation"]["heldout_outcome_not_used_for_prediction_or_selection"] = False
    with pytest.raises(ValueError, match="heldout_outcome_not_used"):
        validate_information_transfer_contract(contract)


def test_blockless_certification_requires_explicit_row_independence_declaration():
    contract = _contract(block=None)
    contract["evaluation"]["row_independence_if_no_block"] = False
    with pytest.raises(ValueError, match="row_independence_if_no_block must be true"):
        validate_information_transfer_contract(contract)

    normalized = validate_information_transfer_contract(_contract(block=None))
    assert normalized["evaluation"]["row_independence_if_no_block"] is True


def test_descriptive_mode_may_record_nonfrozen_filtration_but_is_not_confirmatory(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    _write_scores(data)
    contract = _contract(mode="descriptive")
    _write_contract(contract_path, contract)

    receipt = run_information_transfer_contract(contract_path)
    assert receipt["evaluation_declarations"]["filtration_frozen_before_outcome_scoring"] is False
    assert receipt["scientific_boundary"]["confirmatory_eligible_from_contract_declarations"] is False


def test_duplicate_row_ids_fail_closed(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    _write_scores(data, duplicate_row_id=True)
    _write_contract(contract_path, _contract())

    with pytest.raises(ValueError, match="row_id must be unique"):
        run_information_transfer_contract(contract_path)


def test_other_proper_score_does_not_require_reference_measure():
    contract = _contract()
    contract["score"] = {
        "kind": "other_proper",
        "name": "negative_brier",
        "orientation": "higher_is_better",
        "common_scoring_rule": True,
        "common_reference_measure": None,
    }
    normalized = validate_information_transfer_contract(contract)
    assert normalized["score"]["kind"] == "other_proper"


def test_population_summary_does_not_require_unanimous_positive_groups(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    rows = []
    gains = [0.5, 0.5, 0.5, 0.5, -0.1]
    for index, gain in enumerate(gains):
        rows.append({
            "row_id": f"row-{index}",
            "group": f"g{index}",
            "block": f"b{index}",
            "weight": 1.0,
            "pooled": -1.0,
            "species": -0.5,
            "full": -0.5 + gain,
        })
    with data.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    contract = _contract()
    contract["certification"]["minimum_blocks_per_group"] = 2
    _write_contract(contract_path, contract)

    receipt = run_information_transfer_contract(contract_path)
    population = receipt["population_result"]
    second = population["steps"][1]
    assert second["positive_group_count"] == 4
    assert second["positive_group_fraction"] == pytest.approx(0.8)
    assert second["mean_gain"] == pytest.approx(0.38)
    assert second["mean_gain_status"] == "positive"
    assert population["population_mean_supported_ceiling"] == "species_context"
    assert receipt["point_result"]["predictive_result"]["all_group_point_transfer_ceiling"] == "species"


def test_population_fraction_uses_wilson_without_cluster():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    gains = [0.5] * 27 + [-0.1] * 3
    levels = (
        InformationLevelScore("pooled", (), [0.0] * 30),
        InformationLevelScore("richer", ("x",), gains),
    )
    point = decompose_information_transfer(levels, [f"g{i}" for i in range(30)])
    summary = summarize_population_transfer(point, bootstrap_draws=500, seed=7)
    step = summary.steps[0]
    assert step.positive_group_fraction == pytest.approx(0.9)
    assert step.positive_fraction_lower == pytest.approx(0.743789, abs=1e-6)
    assert step.positive_fraction_lower_method == "wilson_score"


def test_population_cluster_must_be_constant_within_group(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    rows = [
        {"row_id": "r1", "group": "g1", "block": "b1", "weight": 1, "species_id": "s1", "pooled": -1, "species": -.5, "full": -.2},
        {"row_id": "r2", "group": "g1", "block": "b2", "weight": 1, "species_id": "s2", "pooled": -1, "species": -.5, "full": -.2},
    ]
    with data.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    contract = _contract()
    contract["columns"]["population_cluster"] = "species_id"
    _write_contract(contract_path, contract)
    with pytest.raises(ValueError, match="multiple population clusters"):
        run_information_transfer_contract(contract_path)


def test_population_summary_is_invariant_to_within_group_row_duplication():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    levels_a = (
        InformationLevelScore("pooled", (), [0.0, 0.0]),
        InformationLevelScore("richer", ("x",), [0.4, 0.2]),
    )
    point_a = decompose_information_transfer(levels_a, ["g1", "g2"])
    summary_a = summarize_population_transfer(point_a, bootstrap_draws=500, seed=11)

    levels_b = (
        InformationLevelScore("pooled", (), [0.0] * 6),
        InformationLevelScore("richer", ("x",), [0.4] * 5 + [0.2]),
    )
    point_b = decompose_information_transfer(
        levels_b, ["g1"] * 5 + ["g2"]
    )
    summary_b = summarize_population_transfer(point_b, bootstrap_draws=500, seed=11)

    assert summary_a.steps[0].mean_gain == pytest.approx(0.3)
    assert summary_b.steps[0].mean_gain == pytest.approx(0.3)
    assert summary_a.steps[0].positive_group_fraction == pytest.approx(1.0)
    assert summary_b.steps[0].positive_group_fraction == pytest.approx(1.0)


def test_population_status_does_not_acquire_all_group_n_penalty():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    small_gains = [0.5, 0.5, 0.5, 0.5, -0.1]
    large_gains = small_gains * 6

    small = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * len(small_gains)),
            InformationLevelScore("richer", ("x",), small_gains),
        ),
        [f"s{i}" for i in range(len(small_gains))],
    )
    large = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * len(large_gains)),
            InformationLevelScore("richer", ("x",), large_gains),
        ),
        [f"l{i}" for i in range(len(large_gains))],
    )
    small_summary = summarize_population_transfer(small, bootstrap_draws=1000, seed=17)
    large_summary = summarize_population_transfer(large, bootstrap_draws=1000, seed=17)

    assert small_summary.steps[0].mean_gain_status == "positive"
    assert large_summary.steps[0].mean_gain_status == "positive"
    assert small.predictive_result.all_group_point_transfer_ceiling == "pooled"
    assert large.predictive_result.all_group_point_transfer_ceiling == "pooled"


def test_few_declared_population_clusters_use_cluster_robust_t_and_wilson_fallback():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    gains = [0.05, 0.06, 0.10, 0.11]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 4),
            InformationLevelScore("richer", ("x",), gains),
        ),
        ["g1", "g2", "g3", "g4"],
    )
    summary = summarize_population_transfer(
        point,
        group_clusters={"g1": "sp1", "g2": "sp1", "g3": "sp2", "g4": "sp2"},
        bootstrap_draws=500,
        seed=23,
    )
    receipt = summary.as_dict()
    step = summary.steps[0]
    assert summary.cluster_count == 2
    assert receipt["uncertainty"]["mean_interval_method"] == "cluster_robust_t_cr1"
    assert receipt["uncertainty"]["resampling_unit"] == "declared_population_cluster"
    assert receipt["uncertainty"]["small_cluster_policy"] is not None
    assert step.mean_gain == pytest.approx(0.08)
    assert step.mean_gain_interval_method == "cluster_robust_t_cr1"
    assert step.mean_gain_interval_df == 1
    assert step.mean_gain_lower < 0.0 < step.mean_gain_upper
    assert step.positive_group_fraction == 1.0
    assert step.positive_fraction_lower < 1.0
    assert (
        step.positive_fraction_lower_method
        == "wilson_score_group_level_small_cluster_fallback"
    )
    assert receipt["familywise_confirmatory_claim"] is False


def test_ten_declared_population_clusters_use_cluster_bootstrap():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    gains = [0.1 + 0.01 * i for i in range(10)]
    groups = [f"g{i}" for i in range(10)]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 10),
            InformationLevelScore("richer", ("x",), gains),
        ),
        groups,
    )
    summary = summarize_population_transfer(
        point,
        group_clusters={group: f"sp{i}" for i, group in enumerate(groups)},
        bootstrap_draws=500,
        seed=29,
    )
    assert summary.cluster_count == 10
    assert summary.steps[0].mean_gain_interval_method == "cluster_percentile_bootstrap"
    assert summary.steps[0].mean_gain_interval_df is None
    assert summary.steps[0].positive_fraction_lower_method == "cluster_percentile_bootstrap"


def test_one_declared_population_cluster_fails_closed_for_mean_uncertainty():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    groups = ["g1", "g2", "g3"]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 3),
            InformationLevelScore("richer", ("x",), [0.1, 0.2, 0.3]),
        ),
        groups,
    )
    with pytest.raises(ValueError, match="at least two declared population clusters"):
        summarize_population_transfer(
            point,
            group_clusters={group: "sp1" for group in groups},
            bootstrap_draws=500,
            seed=31,
        )


def test_population_total_gain_is_reported_separately_from_stepwise_ceiling():
    from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
    from odsp.population_transfer import summarize_population_transfer

    species_step = [-0.2, -0.2, 0.3, 0.3, 0.3, 0.3]
    context_step = [0.6] * 6
    full = [a + b for a, b in zip(species_step, context_step)]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 6),
            InformationLevelScore("species", ("species",), species_step),
            InformationLevelScore(
                "species_context", ("species", "context"), full
            ),
        ),
        [f"g{i}" for i in range(6)],
    )
    summary = summarize_population_transfer(point, bootstrap_draws=1000, seed=31)

    assert summary.total_gain.mean_gain_status == "positive"
    assert summary.total_gain.mean_gain == pytest.approx(sum(full) / len(full))
    assert summary.steps[0].mean_gain_status == "uncertain"
    assert summary.population_mean_supported_ceiling == "pooled"
