"""No-outcome publication-metadata source gate for BOP external candidates."""
from dataclasses import replace
import json

import pytest

from odsp.external_source_candidate_gate import (
    freeze_candidate_source, screen_candidate_source,
)


def example(count=30):
    return {
        "candidate_id": "artificial_source",
        "source_url": "https://example.org/dataset/example",
        "source_version": "v1",
        "publisher_evidence_urls": ["https://example.org/dataset/example"],
        "species_animal_count_upper_bounds": {
            "Circus pygargus": count,
            "Buteo buteo": 12,
        },
        "field_evidence": {
            "species": "present",
            "timestamp_utc": "present",
            "longitude": "present",
            "altitude_msl": "present",
            "external_temperature": "absent",
        },
        "longitude_precision": "rounded_0p1_degree",
        "altitude_state_semantics": "compatible_gps_msl",
        "cross_source_identity": "external_crosswalk_attested",
        "source_access": "public_reuse_confirmed",
    }


def screen(raw, route="new_reduced_common_input", aim="positive_population_content",
           stratum="Circus pygargus"):
    return screen_candidate_source(
        freeze_candidate_source(raw), route=route, aim=aim, target_stratum=stratum,
    )


@pytest.mark.parametrize("count,decision", [
    (0, "KNOWN_INCOMPATIBLE"), (8, "KNOWN_INCOMPATIBLE"),
    (9, "KNOWN_INCOMPATIBLE"), (28, "KNOWN_INCOMPATIBLE"),
    (29, "KNOWN_INCOMPATIBLE"), (30, "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"),
    (31, "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"),
])
def test_29_not_enough_because_separate_validation_animal(count, decision):
    result = screen(example(count))
    assert result.status == decision
    assert result.required_animals_upper_bound == 30
    assert result.as_public_dict()["real_biological_source_admitted"] is False


@pytest.mark.parametrize("count,decision", [
    (9, "KNOWN_INCOMPATIBLE"),
    (10, "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"),
])
def test_rank_prediction_count_gate_differs_from_population_content(count, decision):
    result = screen(example(count), aim="new_animal_rank")
    assert result.status == decision
    assert result.required_animals_upper_bound == 10


def test_single_species_counts_cannot_be_rescued_by_pooling_other_species():
    raw = example(count=29)
    raw["species_animal_count_upper_bounds"]["Buteo buteo"] = 100
    result = screen(raw)
    assert result.status == "KNOWN_INCOMPATIBLE"
    assert "PUBLISHER_ANIMAL_COUNT_UPPER_BOUND_BELOW_REQUIRED_ROSTER" in result.known_blockers


def test_missing_target_species_never_treated_as_no_data_to_check():
    result = screen(example(), stratum="Circus aeruginosus")
    assert result.status == "KNOWN_INCOMPATIBLE"
    assert "TARGET_SPECIES_NOT_IN_PUBLISHER_ROSTER" in result.known_blockers


def test_publisher_count_unknown_is_hold_not_passing():
    raw = example()
    raw["species_animal_count_upper_bounds"]["Circus pygargus"] = None
    result = screen(raw)
    assert result.status == "HOLD_METADATA_OR_PERMISSION"


def test_historical_rf_and_reduced_learner_are_different_feature_contracts():
    candidate = example()
    reduced = screen(candidate)
    historic = screen(candidate, route="historic_rf_direct")
    assert reduced.status == "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"
    assert historic.status == "KNOWN_INCOMPATIBLE"
    assert "PUBLISHED_REQUIRED_FIELD_ABSENT:external_temperature" in historic.known_blockers
    assert "HISTORIC_RF_LONGITUDE_PRECISION_NOT_RETAINED" in historic.known_blockers


def test_historic_rf_can_only_be_metadata_possible_with_native_longitude_and_temp():
    raw = example()
    raw["field_evidence"]["external_temperature"] = "present"
    raw["longitude_precision"] = "native"
    result = screen(raw, route="historic_rf_direct")
    assert result.status == "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"
    assert result.as_public_dict()["source_permissions_verified_by_software"] is False


@pytest.mark.parametrize("field", ["species", "timestamp_utc", "longitude", "altitude_msl"])
def test_absent_common_field_is_known_incompatible(field):
    raw = example()
    raw["field_evidence"][field] = "absent"
    result = screen(raw)
    assert result.status == "KNOWN_INCOMPATIBLE"
    assert f"PUBLISHED_REQUIRED_FIELD_ABSENT:{field}" in result.known_blockers


@pytest.mark.parametrize("field", ["species", "timestamp_utc", "longitude", "altitude_msl"])
def test_unknown_common_field_stops_on_unknown(field):
    raw = example()
    raw["field_evidence"][field] = "unknown"
    result = screen(raw)
    assert result.status == "HOLD_METADATA_OR_PERMISSION"


@pytest.mark.parametrize("field,value,code", [
    ("longitude_precision", "absent", "PUBLISHED_LONGITUDE_COORDINATES_ABSENT"),
    ("altitude_state_semantics", "different_outcome", "ALTITUDE_STATE_DEFINITION_INCOMPATIBLE"),
    ("cross_source_identity", "known_overlap", "TRAINING_TARGET_ANIMAL_IDENTITY_OVERLAP"),
])
def test_explicit_incompatibility_remains_a_hard_block(field, value, code):
    raw = example()
    raw[field] = value
    result = screen(raw)
    assert result.status == "KNOWN_INCOMPATIBLE"
    assert code in result.known_blockers


@pytest.mark.parametrize("field,value", [
    ("longitude_precision", "unknown"),
    ("altitude_state_semantics", "unknown"),
    ("cross_source_identity", "unknown"),
    ("source_access", "permission_required"),
    ("source_access", "unknown"),
])
def test_unknown_or_permission_requirement_is_hold(field, value):
    raw = example()
    raw[field] = value
    assert screen(raw).status == "HOLD_METADATA_OR_PERMISSION"


def test_known_blockers_and_unresolved_holds_are_both_preserved():
    raw = example(29)
    raw["field_evidence"]["altitude_msl"] = "absent"
    raw["cross_source_identity"] = "unknown"
    result = screen(raw)
    assert result.status == "KNOWN_INCOMPATIBLE"
    assert len(result.known_blockers) == 2
    assert result.unresolved_holds == ("INDEPENDENT_CANONICAL_CROSSWALK_UNVERIFIED",)


def test_metadata_freeze_has_no_biological_data_or_id_values_in_public_output():
    raw = example()
    frozen = freeze_candidate_source(raw)
    output = screen_candidate_source(
        frozen, route="new_reduced_common_input",
        aim="positive_population_content", target_stratum="Circus pygargus",
    ).as_public_dict()
    assert output["only_publisher_metadata_were_considered"]
    assert not output["source_animal_counts_verified_by_software"]
    assert not output["canonical_animal_nonoverlap_verified_by_software"]
    assert not output["real_biological_source_admitted"]
    assert "animal_id" not in json.dumps(output)


@pytest.mark.parametrize("mutation", [
    "unexpected", "hidden_outcomes", "missing_fields", "boolean_count",
    "negative_count", "floating_count", "insecure_url", "credential_url",
    "invalid_permission", "invalid_height", "wrong_field", "empty_evidence",
])
def test_schema_or_unverified_metadata_is_never_silently_accepted(mutation):
    raw = example()
    if mutation == "unexpected":
        raw["other"] = True
    elif mutation == "hidden_outcomes":
        raw["gps_positions"] = []
    elif mutation == "missing_fields":
        raw.pop("field_evidence")
    elif mutation == "boolean_count":
        raw["species_animal_count_upper_bounds"]["Circus pygargus"] = True
    elif mutation == "negative_count":
        raw["species_animal_count_upper_bounds"]["Circus pygargus"] = -1
    elif mutation == "floating_count":
        raw["species_animal_count_upper_bounds"]["Circus pygargus"] = 29.9
    elif mutation == "insecure_url":
        raw["source_url"] = "http://example.org"
    elif mutation == "credential_url":
        raw["source_url"] = "https://token:secret@example.org/data"
    elif mutation == "invalid_permission":
        raw["source_access"] = "always_granted"
    elif mutation == "invalid_height":
        raw["altitude_state_semantics"] = "earth_centered"
    elif mutation == "wrong_field":
        raw["field_evidence"]["outcome"] = "present"
    elif mutation == "empty_evidence":
        raw["publisher_evidence_urls"] = []
    with pytest.raises(ValueError):
        freeze_candidate_source(raw)


@pytest.mark.parametrize("change", [
    {"candidate_id": "changed"}, {"source_access": "unknown"},
    {"source_version": "v2"}, {"longitude_precision": "native"},
])
def test_frozen_metadata_cannot_be_modified_without_new_digest(change):
    frozen = freeze_candidate_source(example())
    altered = replace(frozen, **change)
    with pytest.raises(ValueError, match="changed since freeze"):
        screen_candidate_source(altered, route="new_reduced_common_input",
                                aim="positive_population_content", target_stratum="Circus pygargus")


@pytest.mark.parametrize("route,aim,stratum", [
    ("other", "new_animal_rank", "Circus pygargus"),
    ("historic_rf_direct", "other", "Circus pygargus"),
    ("historic_rf_direct", "new_animal_rank", "Milvus milvus"),
])
def test_unknown_routes_aims_and_bop_species_rejected(route, aim, stratum):
    with pytest.raises(ValueError):
        screen_candidate_source(freeze_candidate_source(example()),
                                route=route, aim=aim, target_stratum=stratum)
