from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_GENERALITY_CONTRACT.json"
PROOF = ROOT / "docs" / "n2_generality_proof_2026-09-04.md"


def test_generality_contract_separates_algorithmic_from_biological_generality():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    layers = contract["generality_layers"]

    assert layers["mathematical_genericity_over_finite_discrete_support"] is True
    assert layers["implementation_property_stress_tested"] is True
    assert layers["heterogeneous_empirical_portability_demonstrated"] is True
    assert layers["universal_biological_outcome_claimed"] is False
    assert layers["causal_generality_claimed"] is False


def test_generality_contract_freezes_required_analytic_properties():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    obligations = {item["id"] for item in contract["analytic_proof_obligations"]}

    assert {
        "positive_mass_scaling",
        "axis_permutation_equivariance",
        "state_label_permutation",
        "omitted_nuisance_refinement",
        "same_distribution_information_identity",
        "conditional_independence_composition",
        "independent_group_mass_invariance",
        "effective_state_cardinality_bound",
    } == obligations


def test_generality_benchmark_contract_is_substantive_not_token_smoke_test():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    bench = contract["executable_benchmark"]

    assert bench["seed"] == 20260904
    assert bench["randomized_tensor_cases"] >= 128
    assert bench["randomized_tensor_ndim_min"] == 2
    assert bench["randomized_tensor_ndim_max"] >= 6
    assert bench["conditional_independence_cases"] >= 32
    assert bench["independent_group_counts_tested"] == [1, 3, 7]
    assert bench["minimum_required_proof_checks"] >= 1800
    assert bench["maximum_allowed_numerical_error"] <= 2e-9


def test_empirical_portability_uses_distinct_architectures_axes_and_units():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    lanes = list(contract["empirical_portability"]["lanes"].values())

    assert len(lanes) == 3
    assert len({lane["observation_architecture"] for lane in lanes}) == 3
    assert len({lane["added_axis_semantics"] for lane in lanes}) == 3
    assert len({lane["replication_or_gate"] for lane in lanes}) == 3
    assert {lane["terminal_state"] for lane in lanes} == {
        "unavailable",
        "thick_non_generalizing",
        "thick_partitioned_generalizing",
    }


def test_generality_proof_states_the_claim_ceiling_explicitly():
    text = PROOF.read_text(encoding="utf-8")

    assert "Axis-agnostic mathematical form" in text
    assert "Same-distribution identity" in text
    assert "Independent-group mass invariance" in text
    assert "not claimed to be a universal biological law" in text
    assert "success on three empirical architectures proves universal biological frequency or mechanism" in text
    assert "generality of the inferential machinery plus heterogeneous empirical portability" in text
    assert "not universality of the biological outcomes" in text
