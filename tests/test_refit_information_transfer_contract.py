from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from odsp.cli import main as cli_main
from odsp.refit_information_transfer_contract import (
    run_refit_information_transfer_contract,
    validate_refit_information_transfer_contract,
)


def _contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "known-refit-transfer-v1",
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
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
            "analysis_mode": "confirmatory",
            "heldout_predictions": True,
            "same_rows_across_levels": True,
            "same_rows_across_refits": True,
            "heldout_outcome_not_used_for_prediction_or_selection": True,
            "filtration_frozen_before_outcome_scoring": True,
            "refit_scheme_frozen_before_outcome_scoring": True,
            "refit_independence_assumed": False,
            "refit_mixture_weighting": "uniform",
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
            "nested_draws": 700,
            "seed": 20260913,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 2,
            "gain_tolerance": 0.0,
            "reference_refit_id": "r0",
        },
    }


def _rows() -> list[dict[str, object]]:
    increments = [0.30, 0.20, 0.10, -0.30, -0.40, -0.20, -0.10, 0.00]
    rows: list[dict[str, object]] = []
    for refit, increment in enumerate(increments):
        for group in ("g1", "g2"):
            for block in range(4):
                row_index = (0 if group == "g1" else 4) + block
                rows.append(
                    {
                        "row_id": f"row-{row_index}",
                        "refit_id": f"r{refit}",
                        "group": group,
                        "block": f"{group}-b{block}",
                        "weight": 1.0,
                        "pooled": -1.0,
                        "species": -0.5,
                        "full": -0.5 + increment,
                    }
                )
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_contract(path: Path, contract: dict[str, object]) -> None:
    path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")


def test_long_refit_contract_recovers_reference_vs_refit_aware_ceiling(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    _write_csv(data, _rows())
    _write_contract(contract_path, _contract())

    receipt = run_refit_information_transfer_contract(contract_path)

    assert receipt["receipt_type"] == "odsp_refit_information_transfer_endpoint"
    assert receipt["input_long_row_count"] == 64
    assert receipt["refit_count"] == 8
    assert receipt["heldout_row_count_per_refit"] == 8
    assert receipt["scientific_boundary"]["same_heldout_row_set_across_refits_validated"] is True
    assert receipt["scientific_boundary"]["same_group_block_weight_metadata_across_refits_validated"] is True
    assert receipt["scientific_boundary"]["refit_independence_assumed"] is False
    assert receipt["scientific_boundary"]["confirmatory_eligible_from_contract_declarations"] is True

    result = receipt["result"]
    assert result["reference_fit_certified_transfer_ceiling"] == "species_context"
    assert result["refit_aware_certified_transfer_ceiling"] == "species"
    assert result["refit_ceiling_stability"] == "refit_sensitive"
    assert result["same_selected_refit_shared_across_all_group_step_cells"] is True


def test_refit_transfer_cli_writes_deterministic_receipt(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    _write_csv(data, _rows())
    _write_contract(contract_path, _contract())

    assert cli_main(["transfer-refits", "--contract", str(contract_path), "--out", str(a)]) == 0
    assert cli_main(["transfer-refits", "--contract", str(contract_path), "--out", str(b)]) == 0
    assert a.read_bytes() == b.read_bytes()


def test_row_and_refit_order_do_not_change_scientific_result(tmp_path: Path):
    contract_path = tmp_path / "endpoint.json"
    first_path = tmp_path / "scores.csv"
    _write_contract(contract_path, _contract())
    rows = _rows()
    _write_csv(first_path, rows)
    first = run_refit_information_transfer_contract(contract_path)

    _write_csv(first_path, list(reversed(rows)))
    second = run_refit_information_transfer_contract(contract_path)

    assert second["result"]["refit_ids"] == first["result"]["refit_ids"]
    assert second["result"]["refit_aware_certified_transfer_ceiling"] == first["result"]["refit_aware_certified_transfer_ceiling"]
    assert second["result"]["max_t_critical_value"] == pytest.approx(first["result"]["max_t_critical_value"])


def test_missing_row_in_one_refit_fails_closed(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    rows = _rows()
    rows = [row for row in rows if not (row["refit_id"] == "r7" and row["row_id"] == "row-7")]
    _write_csv(data, rows)
    _write_contract(contract_path, _contract())

    with pytest.raises(ValueError, match="does not contain the canonical held-out row set"):
        run_refit_information_transfer_contract(contract_path)


def test_metadata_mismatch_for_same_row_fails_closed(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    rows = _rows()
    for row in rows:
        if row["refit_id"] == "r3" and row["row_id"] == "row-2":
            row["group"] = "wrong-group"
            break
    _write_csv(data, rows)
    _write_contract(contract_path, _contract())

    with pytest.raises(ValueError, match="metadata differs across refits"):
        run_refit_information_transfer_contract(contract_path)


def test_duplicate_refit_row_pair_fails_closed(tmp_path: Path):
    data = tmp_path / "scores.csv"
    contract_path = tmp_path / "endpoint.json"
    rows = _rows()
    rows.append(dict(rows[0]))
    _write_csv(data, rows)
    _write_contract(contract_path, _contract())

    with pytest.raises(ValueError, match="duplicate refit_id,row_id pair"):
        run_refit_information_transfer_contract(contract_path)


def test_confirmatory_refit_contract_requires_frozen_scheme_and_reference_refit():
    contract = _contract()
    contract["evaluation"]["refit_scheme_frozen_before_outcome_scoring"] = False
    with pytest.raises(ValueError, match="both the information filtration and refit scheme"):
        validate_refit_information_transfer_contract(contract)

    contract = _contract()
    contract["certification"]["reference_refit_id"] = None
    with pytest.raises(ValueError, match="requires certification.reference_refit_id"):
        validate_refit_information_transfer_contract(contract)


def test_refit_contract_does_not_assume_refit_independence_or_nonuniform_mixture():
    contract = _contract()
    contract["evaluation"]["refit_independence_assumed"] = True
    with pytest.raises(ValueError, match="must be false"):
        validate_refit_information_transfer_contract(contract)

    contract = _contract()
    contract["evaluation"]["refit_mixture_weighting"] = "performance_weighted"
    with pytest.raises(ValueError, match="must be 'uniform'"):
        validate_refit_information_transfer_contract(contract)
