from __future__ import annotations

from dataclasses import replace
import json

import pytest

from odsp.common_input_transport import (
    CLASSES, altitude_state, _solar_clock_context,
    calibrate_common_input_transport, freeze_common_input_transport,
    validate_common_input_transport,
)


SPECIES = "Buteo buteo"


def _train():
    rows = []
    for group in ("trA", "trB", "trC"):
        for i in range(16):
            hour = "11" if i % 2 else "23"
            rows.append({
                "row_id":f"train_{group}_{i}", 
                "individual-local-identifier":group,
                "individual-taxon-canonical-name":SPECIES,
                "timestamp":f"2025-06-08T{hour}:20:00Z",
                "location-long":4.35,
                "height-above-msl": [10.0, 120.0, 360.0, 600.0][
                    (i + (group == "trB")) % 4
                ],
            })
    return rows


def _target(role, n):
    rows=[]
    for group in range(n):
        rows.extend({
            "row_id":f"{role}_{group}_{i}",
            "individual.global.identifier":f"{role}_animal_{group}",
            "individual.taxon.canonical.name":SPECIES,
            "timestamp":f"2025-06-08T{'11' if i%2 else '23'}:40:00Z",
            "location.long.rnd":4.3,
        } for i in range(4))
    return rows


def _setup():
    train=_train()
    cal=_target("cal",19)
    val=_target("val",30)
    obj=freeze_common_input_transport(
        training_BOP_rows=train,
        calibration_Dryad_features=cal,
        validation_Dryad_features=val,
    )
    return obj,train,cal,val


def _labels(rows):
    return {
        r["row_id"]:CLASSES[0 if r["timestamp"].split("T")[1].startswith("11") else 3]
        for r in rows
    }


def test_project_and_replay_original_artifact_to_external_forecasts_without_reusing_rf():
    obj,train,cal,val=_setup()
    manifest=obj.public_manifest()
    assert manifest["original_RF_direct_transfer_admissible"] is False
    assert manifest["Dryad_external_candidate_admitted"] is False
    assert manifest["real_cross_source_individual_nonoverlap_verified"] is False
    assert manifest["real_target_group_exchangeability_verified"] is False
    assert manifest["historical_BOP_v2026_same_study_gate_reopened"] is False
    assert manifest["original_BOP_terminal"]=="empirical_state_prediction_mixed"
    assert manifest["model_sha256"]==obj.forecast.plan.model_sha256
    assert manifest["calibration_group_count"]==19
    assert manifest["validation_group_count"]==30
    assert manifest["training_group_count"]==3
    assert "train_trA" not in json.dumps(manifest)
    assert "val_animal_0" not in json.dumps(manifest)
    fitted=calibrate_common_input_transport(obj,_labels(cal))
    scored=validate_common_input_transport(obj,fitted,_labels(val))
    assert scored.validation_group_count==30
    assert scored.strata[0].finite_rank==2
    assert 0<=scored.group_equal_coverage<=1
    assert scored.as_public_dict()["historical_bop_terminal_changed"] is False


@pytest.mark.parametrize("altitude,expected",[
    (-100,CLASSES[0]),(49.9,CLASSES[0]),(50,CLASSES[1]),
    (199.999,CLASSES[1]),(200,CLASSES[2]),(499.999,CLASSES[2]),
    (500,CLASSES[3]),(5000,CLASSES[3]),
])
def test_original_AMSL_bins_are_preserved(altitude,expected):
    assert altitude_state(altitude)==expected


@pytest.mark.parametrize("value",["nan",float("inf"),-101,5001,None])
def test_bad_training_altitude_rejected(value):
    with pytest.raises(ValueError,match="finite|range"):
        altitude_state(value)


def test_rounding_stable_solar_clock_inside_non_boundary_region():
    # Longitude rounded from 4.35 to 4.3 changes mean solar time by only
    # about 12 seconds, not the daytime/nighttime phase away from boundaries.
    for utc in ("2025-06-08T11:59:00Z","2025-06-08T23:59:00Z"):
        bop=_solar_clock_context(utc,4.35,rounded=False)
        dryad=_solar_clock_context(utc,4.3,rounded=True)
        assert bop==dryad
    assert _solar_clock_context("2025-06-08T11:00:00Z",4.35,rounded=False)==1
    assert _solar_clock_context("2025-06-08T23:00:00Z",4.3,rounded=True)==0


def test_clock_boundary_rejects_ambiguous_precision_even_with_valid_UTC():
    # Zero-degree longitude exactly at 06:00 is ambiguous for original
    # data that may be rounded up/down 0.05 degrees in Dryad.
    for time in ("2025-06-08T06:00:00Z","2025-06-08T18:00:00Z",
                 "2025-06-08T05:59:50Z","2025-06-08T06:00:10Z"):
        with pytest.raises(ValueError,match="ambiguous"):
            _solar_clock_context(time,0.0,rounded=True)
    assert _solar_clock_context("2025-06-08T06:01:00Z",0.0,rounded=True)==1
    assert _solar_clock_context("2025-06-08T05:59:00Z",0.0,rounded=True)==0


@pytest.mark.parametrize("timestamp",[
    "2025-06-08 11:00:00","2025-06-08T11:00:00",
    "2025-06-08T11:00:00+09:00","2025-13-01T11:00:00Z",
    None, "2025-06-08T11:00:00-00:01"
])
def test_explicit_UTC_must_be_declared_before_solar_phase(timestamp):
    with pytest.raises(ValueError,match="timestamp"):
        _solar_clock_context(timestamp,4.3,rounded=True)


def test_Dryad_coarse_longitude_must_be_actual_one_decimal_and_bounded():
    for lon in (4.35,4.34,float("nan"),200,None):
        with pytest.raises(ValueError,match="rounded|longitude"):
            _solar_clock_context("2025-06-08T11:00:00Z",lon,rounded=True)
    assert _solar_clock_context("2025-06-08T11:00:00Z",4.3,rounded=True)==1


@pytest.mark.parametrize("invalid_key",[
    "height.above.msl","height-above-msl","external-temperature","ground.speed",
    "outcome","conditional","reference"
])
def test_holdout_never_contains_label_or_removed_predictor(invalid_key):
    train=_train()
    cal=_target("cal",19)
    val=_target("val",30)
    cal[0][invalid_key]=2
    with pytest.raises(ValueError,match="outcomes/leakage forbidden"):
        freeze_common_input_transport(
            training_BOP_rows=train,calibration_Dryad_features=cal,
            validation_Dryad_features=val
        )


def test_training_model_cannot_retain_unavailable_temperature_predictor():
    train=_train()
    cal=_target("cal",19)
    val=_target("val",30)
    train[0]["external-temperature"]=11.0
    with pytest.raises(ValueError,match="role schema"):
        freeze_common_input_transport(
            training_BOP_rows=train,calibration_Dryad_features=cal,
            validation_Dryad_features=val
        )


def test_training_species_and_group_id_collisions_fail_closed():
    tr=_train();cal=_target("cal",19);val=_target("val",30)
    tr[0]["individual-taxon-canonical-name"]="Milvus milvus"
    with pytest.raises(ValueError,match="species"):
        freeze_common_input_transport(
            training_BOP_rows=tr,calibration_Dryad_features=cal,
            validation_Dryad_features=val
        )
    tr=_train()
    val[0]["row_id"]=cal[0]["row_id"]
    with pytest.raises(ValueError,match="rosters overlap|duplicate row_id"):
        freeze_common_input_transport(
            training_BOP_rows=tr,calibration_Dryad_features=cal,
            validation_Dryad_features=val
        )


def test_external_calibration_validation_outcomes_never_reused():
    obj,tr,cal,val=_setup()
    good=_labels(cal)
    with pytest.raises(ValueError,match="only exact frozen Dryad role outcome IDs"):
        calibrate_common_input_transport(obj,{**good,**_labels(val)})
    fixed=calibrate_common_input_transport(obj,good)
    with pytest.raises(ValueError,match="only exact frozen Dryad role outcome IDs"):
        validate_common_input_transport(obj,fixed,good)
    altered=replace(obj.forecast.plan,validation_rows=(
        replace(obj.forecast.plan.validation_rows[0],conditional=(0.1,0.2,0.3,0.4)),
        *obj.forecast.plan.validation_rows[1:],
    ))
    with pytest.raises(ValueError,match="frozen forecast plan|replay"):
        validate_common_input_transport(
            replace(obj,forecast=replace(obj.forecast,plan=altered)),
            fixed,_labels(val)
        )


def test_namespaced_ids_not_mistaken_for_cross_source_animal_independence():
    obj,tr,cal,val=_setup()
    assert obj.forecast.plan.training_group_ids[0].startswith("BOP:")
    assert obj.forecast.plan.calibration_rows[0].group_id.startswith("DRYAD:")
    assert obj.public_manifest()["real_cross_source_individual_nonoverlap_verified"] is False
