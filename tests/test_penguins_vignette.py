from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.endpoint_contract import validate_endpoint_contract

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "penguins"


def test_penguins_contract_is_explicit_and_independent_of_manuscript_endpoints():
    contract = json.loads((EXAMPLE / "endpoint.json").read_text(encoding="utf-8"))
    normalized = validate_endpoint_contract(contract)
    assert normalized["columns"]["state"] == "island"
    assert normalized["columns"]["group"] == "row_id"
    assert normalized["columns"]["stratum"] == "sex"
    assert normalized["columns"]["fold"] == "year"
    assert normalized["baseline"] == "pooled"
    assert normalized["training_weight_policy"] == "equal_stratum_equal_group"
    assert not any(token in normalized["endpoint_id"].lower() for token in ("bop", "mh", "raptor", "bat"))


def test_penguins_vignette_stays_short_and_pins_upstream_source():
    readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
    script = (EXAMPLE / "prepare_penguins.py").read_text(encoding="utf-8")
    assert len(script.splitlines()) <= 50
    assert "8957207b78d6ccd1b4654a9dd9c9041b657478ab" in script
    assert "CC0 1.0" in readme
    assert "causally" in readme


def test_prepared_penguins_endpoint_runs_when_fixture_has_been_built():
    pytest.importorskip("sklearn")
    data = EXAMPLE / "penguins_complete.csv"
    if not data.exists():
        pytest.skip("prepared public-data fixture is built in the vignette CI lane")
    from odsp.endpoint_contract import run_endpoint_contract

    receipt = run_endpoint_contract(EXAMPLE / "endpoint.json")
    assert receipt["input_row_count"] > 300
    assert receipt["scientific_roles"]["state"] == "island"
    assert len(receipt["result"]["groups"]) == receipt["input_row_count"]
