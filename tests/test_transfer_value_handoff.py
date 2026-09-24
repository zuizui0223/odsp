from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from odsp.transfer_value_handoff import (
    build_population_transfer_value_handoff,
    population_result_fingerprint,
    validate_population_transfer_value_handoff,
)


ROOT = Path(__file__).resolve().parents[1]
BOP = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"
SCHEMA = ROOT / "N2_TO_N3_TRANSFER_VALUE_PAYLOAD_SCHEMA.json"
CONTRACT = ROOT / "N2_TO_N3_TRANSFER_VALUE_HANDOFF_CONTRACT.json"


def _bop_population() -> dict[str, object]:
    receipt = json.loads(BOP.read_text(encoding="utf-8"))
    return receipt["population_result"]


def test_bop_population_result_builds_bounded_n3_transfer_value_payload():
    population = _bop_population()
    payload = build_population_transfer_value_handoff(
        evidence_id="bop-rodent-population-transfer-v2",
        population_result=population,
        group_semantics="heldout individual",
        population_cluster_semantics="species",
        score_kind="log",
        score_name="mean_log_predictive_probability",
        score_unit="nats_per_event",
        source_receipt=BOP.name,
        source_contract="BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_CONTRACT_V2.json",
    ).as_dict()

    assert payload["schema_id"] == "n2-to-n3-transfer-value-payload-v1"
    assert payload["target"] == {
        "chapter": "N3",
        "system": "EOG",
        "role": "information_transfer_value_for_downstream_reachability",
    }
    assert payload["semantics"]["group"] == "heldout individual"
    assert payload["semantics"]["population_cluster"] == "species"
    assert payload["semantics"]["gain_tolerance"] == 0.0
    assert payload["semantics"]["score"] == {
        "kind": "log",
        "name": "mean_log_predictive_probability",
        "unit": "nats_per_event",
        "orientation": "higher_is_better",
    }
    assert payload["provenance"]["source_population_fingerprint"] == population_result_fingerprint(
        population
    )
    assert validate_population_transfer_value_handoff(payload) == payload["fingerprint"]


def test_uncertain_bop_steps_carry_zero_conservative_value_not_fake_priority():
    payload = build_population_transfer_value_handoff(
        evidence_id="bop-rodent-population-transfer-v2",
        population_result=_bop_population(),
        group_semantics="heldout individual",
        population_cluster_semantics="species",
        score_kind="log",
        score_name="mean_log_predictive_probability",
        score_unit="nats_per_event",
    )

    assert payload.total_value.mean_status == "uncertain"
    assert payload.total_value.expected_gain > 0
    assert payload.total_value.conservative_mean_value == 0.0

    assert len(payload.steps) == 2
    assert all(step.mean_status == "uncertain" for step in payload.steps)
    assert all(step.conservative_mean_value == 0.0 for step in payload.steps)
    assert all(
        step.positive_fraction_lower_method
        == "wilson_score_group_level_small_cluster_fallback"
        for step in (payload.total_value, *payload.steps)
    )


def test_positive_step_exposes_expected_and_conservative_value_without_ranking_places():
    population = copy.deepcopy(_bop_population())
    step = population["steps"][1]
    step["mean_gain_lower"] = 0.12
    step["mean_gain_upper"] = 0.80
    step["mean_gain_status"] = "positive"

    total = population["total_gain"]
    total["mean_gain_lower"] = 0.10
    total["mean_gain_upper"] = 0.90
    total["mean_gain_status"] = "positive"

    payload = build_population_transfer_value_handoff(
        evidence_id="synthetic-positive-transfer-value",
        population_result=population,
        group_semantics="site",
        population_cluster_semantics="region",
        score_kind="log",
        score_name="mean_log_predictive_probability",
        score_unit="nats_per_site",
    ).as_dict()

    assert payload["total_value"]["expected_gain"] == pytest.approx(
        population["total_gain"]["mean_gain"]
    )
    assert payload["total_value"]["conservative_mean_value"] == pytest.approx(0.10)
    assert payload["steps"][1]["conservative_mean_value"] == pytest.approx(0.12)

    boundary = payload["boundary"]
    assert boundary["authorizes_spatial_patch_ranking"] is False
    assert boundary["authorizes_survey_site_selection"] is False
    assert boundary["authorizes_n4_action"] is False
    assert boundary["n4_survey_action_owner"] == "ACSP"


def test_payload_tampering_cannot_promote_state_or_survey_action():
    payload = build_population_transfer_value_handoff(
        evidence_id="bop-rodent-population-transfer-v2",
        population_result=_bop_population(),
        group_semantics="heldout individual",
        population_cluster_semantics="species",
        score_kind="log",
        score_name="mean_log_predictive_probability",
        score_unit="nats_per_event",
    ).as_dict()

    forged = copy.deepcopy(payload)
    forged["boundary"]["authorizes_spatial_patch_ranking"] = True
    with pytest.raises(ValueError, match="authorizes_spatial_patch_ranking"):
        validate_population_transfer_value_handoff(forged)

    forged = copy.deepcopy(payload)
    forged["boundary"]["authorizes_state_promotion"] = True
    with pytest.raises(ValueError, match="authorizes_state_promotion"):
        validate_population_transfer_value_handoff(forged)


def test_payload_rejects_noncontiguous_information_chain():
    population = copy.deepcopy(_bop_population())
    population["steps"][1]["lower_level"] = "wrong-level"

    with pytest.raises(ValueError, match="contiguous information chain"):
        build_population_transfer_value_handoff(
            evidence_id="broken-chain",
            population_result=population,
            group_semantics="heldout individual",
            score_kind="log",
            score_name="mean_log_predictive_probability",
            score_unit="nats_per_event",
        )


def test_transfer_value_schema_and_contract_preserve_chapter_ownership():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert schema["properties"]["schema_id"]["const"] == (
        "n2-to-n3-transfer-value-payload-v1"
    )
    assert schema["properties"]["target"]["properties"]["chapter"]["const"] == "N3"
    assert schema["properties"]["target"]["properties"]["system"]["const"] == "EOG"
    boundary = schema["properties"]["boundary"]["properties"]
    assert boundary["authorizes_spatial_patch_ranking"]["const"] is False
    assert boundary["authorizes_survey_site_selection"]["const"] is False
    assert boundary["n4_survey_action_owner"]["const"] == "ACSP"

    assert contract["compatibility"]["new_top_level_cli_command_added"] is False
    assert contract["downstream_boundary"]["n4_owner"] == "ACSP"
    assert contract["accepted_source"]["requires_contiguous_adjacent_steps"] is True


def test_score_currency_tampering_breaks_payload_fingerprint():
    payload = build_population_transfer_value_handoff(
        evidence_id="bop-rodent-population-transfer-v2",
        population_result=_bop_population(),
        group_semantics="heldout individual",
        population_cluster_semantics="species",
        score_kind="log",
        score_name="mean_log_predictive_probability",
        score_unit="nats_per_event",
    ).as_dict()

    forged = copy.deepcopy(payload)
    forged["semantics"]["score"]["unit"] = "nats_per_site"
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        validate_population_transfer_value_handoff(forged)
