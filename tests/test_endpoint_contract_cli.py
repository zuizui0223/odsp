from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from odsp.cli import main
from odsp.endpoint_contract import run_endpoint_contract, validate_endpoint_contract


def _contract(data_path: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "test-endpoint",
        "data": {"path": data_path, "format": "csv"},
        "columns": {
            "state": "state",
            "features": ["x"],
            "group": "individual",
            "stratum": "species",
            "fold": "fold",
            "weight": None,
        },
        "model": {
            "kind": "multinomial_logit",
            "random_state": 11,
            "parameters": {"C": 100.0, "max_iter": 2000},
        },
        "baseline": "pooled",
        "training_weight_policy": "equal_stratum_equal_group",
        "gain_tolerance": 0.0,
    }


def _write_events(path: Path) -> None:
    definitions = (
        ("A0", "species-a", 0, 8, 2),
        ("A1", "species-a", 1, 8, 2),
        ("B0", "species-b", 0, 2, 8),
        ("B1", "species-b", 1, 2, 8),
    )
    rows: list[dict[str, object]] = []
    for group, species, fold, low_n, high_n in definitions:
        rows.extend(
            {
                "state": "low",
                "x": -1.0,
                "individual": group,
                "species": species,
                "fold": fold,
            }
            for _ in range(low_n)
        )
        rows.extend(
            {
                "state": "high",
                "x": 1.0,
                "individual": group,
                "species": species,
                "fold": fold,
            }
            for _ in range(high_n)
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["state", "x", "individual", "species", "fold"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_contract_rejects_unknown_fields_and_implicit_stratum_requirements():
    contract = _contract("events.csv")
    contract["mystery"] = True
    with pytest.raises(ValueError, match="unknown fields"):
        validate_endpoint_contract(contract)

    contract = _contract("events.csv")
    columns = dict(contract["columns"])
    columns["stratum"] = None
    contract["columns"] = columns
    contract["baseline"] = "stratum"
    with pytest.raises(ValueError, match="requires columns.stratum"):
        validate_endpoint_contract(contract)

    contract = _contract("events.csv")
    columns = dict(contract["columns"])
    columns["stratum"] = None
    contract["columns"] = columns
    with pytest.raises(ValueError, match="requires columns.stratum"):
        validate_endpoint_contract(contract)


def test_contract_normalization_keeps_scientific_choices_explicit():
    normalized = validate_endpoint_contract(_contract("events.csv"))
    assert normalized["baseline"] == "pooled"
    assert normalized["training_weight_policy"] == "equal_stratum_equal_group"
    assert normalized["columns"]["group"] == "individual"
    assert normalized["columns"]["stratum"] == "species"
    assert normalized["columns"]["fold"] == "fold"
    assert normalized["model"]["kind"] == "multinomial_logit"


def test_run_contract_emits_hashed_group_level_receipt(tmp_path: Path):
    pytest.importorskip("sklearn")
    data_path = tmp_path / "events.csv"
    contract_path = tmp_path / "endpoint.json"
    _write_events(data_path)
    contract_path.write_text(
        json.dumps(_contract(data_path.name), indent=2) + "\n",
        encoding="utf-8",
    )

    receipt = run_endpoint_contract(contract_path)
    assert receipt["receipt_type"] == "odsp_state_prediction_endpoint"
    assert receipt["endpoint_id"] == "test-endpoint"
    assert len(receipt["contract_sha256"]) == 64
    assert len(receipt["data_sha256"]) == 64
    assert receipt["input_row_count"] == 40
    assert receipt["scientific_roles"]["independence_unit"] == "individual"
    assert receipt["scientific_roles"]["baseline"] == "pooled"
    groups = receipt["result"]["groups"]
    assert len(groups) == 4
    for row in groups:
        assert row["additivity_error"] == pytest.approx(0.0, abs=1e-12)


def test_cli_writes_same_receipt_to_requested_path(tmp_path: Path):
    pytest.importorskip("sklearn")
    data_path = tmp_path / "events.csv"
    contract_path = tmp_path / "endpoint.json"
    receipt_path = tmp_path / "receipt.json"
    _write_events(data_path)
    contract_path.write_text(
        json.dumps(_contract(data_path.name), indent=2) + "\n",
        encoding="utf-8",
    )

    assert main(["run", "--contract", str(contract_path), "--out", str(receipt_path)]) == 0
    written = json.loads(receipt_path.read_text(encoding="utf-8"))
    direct = run_endpoint_contract(contract_path)
    assert written == direct
