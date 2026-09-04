from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from odsp.bop_rodent_prediction import (
    BOPEvent,
    build_admissions,
    deterministic_folds,
    feature_matrix,
    hierarchical_training_weights,
    parse_admissible_bop_row,
    terminal_decision,
    thin_hourly_earliest,
)
from odsp.mh_antwerpen_prediction import altitude_state


def _event(individual: str, species: str, hour: int, height: float):
    return BOPEvent(
        timestamp_utc=datetime(2021, 5, 1, tzinfo=timezone.utc) + timedelta(hours=hour),
        longitude=4.5,
        latitude=51.1,
        external_temperature_c=12.0,
        height_m_amsl=height,
        individual_id=individual,
        species=species,
        altitude_state=altitude_state(height),
        source_file="synthetic.csv.gz",
    )


def test_bop_row_parser_requires_species_and_fixed_context():
    row = {
        "timestamp": "2021-05-01 12:00:00",
        "location-long": "4.5",
        "location-lat": "51.1",
        "external-temperature": "12.5",
        "height-above-msl": "220",
        "individual-local-identifier": "raptor-1",
        "individual-taxon-canonical-name": "Buteo buteo",
        "import-marked-outlier": "false",
        "manually-marked-outlier": "false",
    }
    event, reason = parse_admissible_bop_row(row, source_file="x.csv.gz")
    assert reason is None
    assert event is not None
    assert event.species == "Buteo buteo"
    assert event.altitude_state == "upper_mid_200_500"
    assert len(event.continuous_features) == 7

    row["individual-taxon-canonical-name"] = ""
    event, reason = parse_admissible_bop_row(row, source_file="x.csv.gz")
    assert event is None
    assert reason == "missing_species"


def test_hourly_thinning_keeps_earliest_within_individual_hour():
    first = _event("a", "sp1", 0, 20)
    later = BOPEvent(
        **{
            **first.__dict__,
            "timestamp_utc": first.timestamp_utc + timedelta(minutes=40),
            "height_m_amsl": 100.0,
            "altitude_state": altitude_state(100),
        }
    )
    next_hour = _event("a", "sp1", 1, 100)
    other = _event("b", "sp1", 0, 20)
    thinned = thin_hourly_earliest([later, next_hour, other, first])
    assert [(e.individual_id, e.timestamp_utc.hour, e.altitude_state) for e in thinned] == [
        ("a", 0, "low_lt50"),
        ("a", 1, "lower_mid_50_200"),
        ("b", 0, "low_lt50"),
    ]


def test_species_admission_requires_three_eligible_individuals():
    events = []
    for species, ids in {"spA": ["a1", "a2", "a3"], "spB": ["b1", "b2"]}.items():
        for individual in ids:
            for hour in range(300):
                events.append(_event(individual, species, hour, 20 if hour < 150 else 100))
    admissions = {item.individual_id: item for item in build_admissions(events)}
    assert all(admissions[x].final_eligible for x in ("a1", "a2", "a3"))
    assert all(not admissions[x].final_eligible for x in ("b1", "b2"))
    assert all("species_has_too_few_eligible_individuals" in admissions[x].exclusion_reasons for x in ("b1", "b2"))


def test_fold_assignment_is_deterministic_and_spreads_species():
    events = []
    for species in ("spA", "spB", "spC"):
        for j in range(6):
            individual = f"{species}-{j}"
            for hour in range(300):
                events.append(_event(individual, species, hour, 20 if hour < 150 else 100))
    admissions = build_admissions(events)
    a = deterministic_folds(admissions)
    b = deterministic_folds(tuple(reversed(admissions)))
    assert a == b
    for species in ("spA", "spB", "spC"):
        assigned = [a[item.individual_id] for item in admissions if item.species == species]
        assert set(assigned) == {0, 1, 2, 3, 4}


def test_hierarchical_weights_equalize_species_and_individual_mass():
    ids = ["a", "a", "b", "c", "c", "c", "d"]
    species = ["sp1", "sp1", "sp1", "sp2", "sp2", "sp2", "sp2"]
    weights = hierarchical_training_weights(ids, species)
    by_individual = {}
    by_species = {}
    for ind, sp, w in zip(ids, species, weights):
        by_individual[ind] = by_individual.get(ind, 0.0) + float(w)
        by_species[sp] = by_species.get(sp, 0.0) + float(w)
    assert np.isclose(by_species["sp1"], by_species["sp2"])
    assert np.isclose(by_individual["a"], by_individual["b"])
    assert np.isclose(by_individual["c"], by_individual["d"])


def test_feature_matrix_has_seven_context_features_plus_species_one_hot():
    events = [_event("a", "spA", 0, 20), _event("b", "spB", 1, 100)]
    X, y, ids, species = feature_matrix(events, ("spA", "spB"))
    assert X.shape == (2, 9)
    assert np.allclose(X[0, 7:], [1, 0])
    assert np.allclose(X[1, 7:], [0, 1])
    assert y.tolist() == ["low_lt50", "lower_mid_50_200"]
    assert ids == ["a", "b"]
    assert species == ["spA", "spB"]


def test_terminal_fails_closed_when_multispecies_minimum_not_met():
    events = []
    for species in ("spA", "spB"):
        for j in range(6):
            for hour in range(300):
                events.append(_event(f"{species}-{j}", species, hour, 20 if hour < 150 else 100))
    admissions = build_admissions(events)
    decision = terminal_decision(admissions, [])
    assert decision["terminal_category"] == "empirical_state_prediction_unavailable"
    assert decision["reason"] == "frozen_multi_species_admission_minimum_failed"
