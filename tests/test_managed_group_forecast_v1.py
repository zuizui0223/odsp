from __future__ import annotations

from dataclasses import replace
import json

import pytest

from odsp.managed_group_forecast_v1 import (
    ManagedFeatureRow,
    calibrate_managed_group_gain,
    freeze_managed_group_forecasts,
    validate_managed_group_gain,
)


CLASSES = ("low", "middle_low", "middle_high", "high")


def _train():
    rows = []
    for group in ("train_A", "train_B", "train_C"):
        for i in range(8):
            rows.append({
                "row_id": f"{group}_{i}", "group_id": group,
                "stratum": "test_raptor", "context": i % 2,
                "outcome": CLASSES[(i + (group == "train_B")) % 4],
            })
    return rows


def _features(role, n=19):
    return [
        {"row_id": f"{role}_{i}", "group_id": f"{role}_animal_{i}",
         "stratum": "test_raptor", "context": i % 2}
        for i in range(n)
    ]


def _frozen():
    training = _train()
    cal = _features("cal")
    val = _features("val", 30)
    frozen = freeze_managed_group_forecasts(
        training_rows=training,
        calibration_features=cal,
        validation_features=val,
        classes=CLASSES,
        pseudocount=0.1,
    )
    return frozen, training, cal, val


def _cal(frozen, cal):
    return calibrate_managed_group_gain(
        frozen, {r["row_id"]: CLASSES[int(r["context"])] for r in cal}
    )


def _test(frozen, fit, val):
    return validate_managed_group_gain(
        frozen, fit, {r["row_id"]: CLASSES[int(r["context"])] for r in val}
    )


def test_managed_complete_training_to_forecast_to_untouched_validation():
    frozen, training, cal, val = _frozen()
    obj = frozen.public_manifest()
    assert obj["artifact_to_forecast_replay_verified"] is True
    assert obj["training_source_to_model_replay_verified"] is True
    assert obj["external_chronology_attested"] is False
    assert obj["independent_external_evidence_collected"] is False
    assert "train_A" not in json.dumps(obj)
    assert "cal_animal_0" not in json.dumps(obj)
    assert len(frozen.plan.calibration_rows) == 19
    assert len(frozen.plan.validation_rows) == 30
    assert frozen.plan.calibration_rows[0].conditional != (
        frozen.plan.calibration_rows[0].reference
    )
    cal_result = _cal(frozen, cal)
    scored = _test(frozen, cal_result, val)
    assert scored.validation_group_count == 30
    assert 0 <= scored.group_equal_coverage <= 1
    assert scored.as_public_dict()["historical_bop_terminal_changed"] is False


def test_forecasts_are_exactly_generated_from_training_only_model_artifacts():
    frozen, training, cal, val = _frozen()
    model = json.loads(frozen.model_artifact)
    ref = json.loads(frozen.reference_artifact)
    assert model["kind"] == "odsp-managed-stratum-context-categorical-v1"
    assert ref["kind"] == "odsp-managed-stratum-categorical-reference-v1"
    assert model["training_source_sha256"] == frozen.plan.training_source_sha256
    assert ref["training_source_sha256"] == frozen.plan.training_source_sha256
    for row in frozen.plan.calibration_rows + frozen.plan.validation_rows:
        source = (
            frozen.calibration_features if row.role == "calibration"
            else frozen.validation_features
        )
        feature = next(x for x in source if x.row_id == row.row_id)
        expected = model["probabilities"][feature.stratum][feature.context]
        assert list(row.conditional) == pytest.approx(expected, abs=0)
        assert list(row.reference) == pytest.approx(
            ref["probabilities"][feature.stratum], abs=0
        )


def test_outcome_or_probability_in_holdout_features_fails():
    _, train, cal, val = _frozen()
    cal[0]["outcome"] = "high"
    with pytest.raises(ValueError, match="role schema"):
        freeze_managed_group_forecasts(
            training_rows=train, calibration_features=cal,
            validation_features=val, classes=CLASSES,
        )
    del cal[0]["outcome"]
    val[0]["conditional"] = [0.95, 0.02, 0.02, 0.01]
    with pytest.raises(ValueError, match="role schema"):
        freeze_managed_group_forecasts(
            training_rows=train, calibration_features=cal,
            validation_features=val, classes=CLASSES,
        )


def test_tampered_training_outcome_model_and_features_rejected():
    frozen, train, cal, val = _frozen()
    changed_train = replace(
        frozen,
        training_rows=(
            replace(frozen.training_rows[0], outcome="high"),
            *frozen.training_rows[1:],
        ),
    )
    with pytest.raises(ValueError, match="retraining replay"):
        changed_train.assert_replayed()
    changed_model = replace(frozen, model_artifact=frozen.model_artifact+b" ")
    with pytest.raises(ValueError, match="retraining replay"):
        changed_model.assert_replayed()
    changed_reference = replace(frozen, reference_artifact=b"another model")
    with pytest.raises(ValueError, match="retraining replay"):
        changed_reference.assert_replayed()
    changed_features = replace(
        frozen,
        validation_features=(
            replace(frozen.validation_features[0], context=1-frozen.validation_features[0].context),
            *frozen.validation_features[1:],
        ),
    )
    with pytest.raises(ValueError, match="feature roster modified"):
        changed_features.assert_replayed()
    changed_forecast = replace(
        frozen.plan,
        calibration_rows=(
            replace(frozen.plan.calibration_rows[0], conditional=(0.5,0.2,0.2,0.1)),
            *frozen.plan.calibration_rows[1:],
        ),
    )
    with pytest.raises(ValueError, match="frozen forecast plan"):
        replace(frozen, plan=changed_forecast).assert_replayed()


def test_validation_result_does_not_feed_back_into_calibration():
    frozen, train, cal, val = _frozen()
    with pytest.raises(ValueError, match="outcome row IDs"):
        calibrate_managed_group_gain(
            frozen,
            {**{r["row_id"]: "low" for r in cal},
             **{r["row_id"]: "high" for r in val}},
        )
    calibrator = _cal(frozen, cal)
    with pytest.raises(ValueError, match="outcome row IDs"):
        validate_managed_group_gain(
            frozen, calibrator,
            {r["row_id"]: "low" for r in cal},
        )


def test_training_order_irrelevant_but_group_outcome_is_not():
    frozen, train, cal, val = _frozen()
    reordered = freeze_managed_group_forecasts(
        training_rows=list(reversed(train)),
        calibration_features=list(reversed(cal)),
        validation_features=list(reversed(val)),
        classes=CLASSES,
    )
    assert reordered.model_artifact == frozen.model_artifact
    assert reordered.reference_artifact == frozen.reference_artifact
    assert reordered.plan.digest == frozen.plan.digest
    altered = [dict(x) for x in train]
    altered[0]["outcome"] = "high"
    new = freeze_managed_group_forecasts(
        training_rows=altered,
        calibration_features=cal,
        validation_features=val,
        classes=CLASSES,
    )
    assert new.model_artifact != frozen.model_artifact
    assert new.plan.digest != frozen.plan.digest


def test_gps_pseudoreplication_does_not_change_equal_group_training_mass():
    # 100 exact duplicates from a single animal do not have 100x weight.
    group_a = [
        {"row_id":f"a{i}", "group_id":"a", "stratum":"s",
         "context":0,"outcome":"low"}
        for i in range(100)
    ]
    group_a.append(
        {"row_id":"a_context1", "group_id":"a", "stratum":"s",
         "context":1,"outcome":"middle_low"}
    )
    group_b = [
        {"row_id":"b0","group_id":"b","stratum":"s",
         "context":0,"outcome":"middle_low"},
        {"row_id":"b1","group_id":"b","stratum":"s",
         "context":1,"outcome":"low"},
    ]
    plan = freeze_managed_group_forecasts(
        training_rows=group_a+group_b,
        calibration_features=[{"row_id":"c", "group_id":"c", "stratum":"s", "context":0}],
        validation_features=[{"row_id":"v", "group_id":"v", "stratum":"s", "context":1}],
        classes=CLASSES
    )
    probs = json.loads(plan.reference_artifact)["probabilities"]["s"]
    # Both whole animals contribute unit total training weight:
    assert probs[0] < 0.65
    assert probs[1] > 0.35


@pytest.mark.parametrize("mode,pattern", [
    ("duplicate_training_row","duplicate row_id"),
    ("cross_role_row","row_id rosters overlap"),
    ("cross_role_group","training group overlaps"),
    ("cross_train_stratum","training group crosses strata"),
    ("unsupported_stratum","stratum absent"),
    ("unknown_label","training outcome"),
    ("no_context","both context"),
    ("bool_context","context must be"),
    ("float_context","context must be"),
    ("zero_weight","weight must be"),
    ("infinite_weight","weight must be"),
    ("bad_pseudocount","pseudocount"),
])
def test_managed_fit_fail_closed_for_semantic_violations(mode, pattern):
    train = _train()
    cal = _features("cal")
    val = _features("val", 30)
    kwargs = {"training_rows":train, "calibration_features":cal,
              "validation_features":val, "classes":CLASSES}
    if mode == "duplicate_training_row":
        train.append(dict(train[0]))
    elif mode == "cross_role_row":
        cal[0]["row_id"] = train[0]["row_id"]
    elif mode == "cross_role_group":
        val[0]["group_id"] = train[0]["group_id"]
    elif mode == "cross_train_stratum":
        train[0]["stratum"] = "other"
    elif mode == "unsupported_stratum":
        val[0]["stratum"] = "untrained"
    elif mode == "unknown_label":
        train[0]["outcome"] = "absent"
    elif mode == "no_context":
        for row in train:
            row["context"] = 0
    elif mode == "bool_context":
        cal[0]["context"] = True
    elif mode == "float_context":
        cal[0]["context"] = 0.0
    elif mode == "zero_weight":
        train[0]["weight"] = 0
    elif mode == "infinite_weight":
        train[0]["weight"] = float("inf")
    elif mode == "bad_pseudocount":
        kwargs["pseudocount"] = -1
    with pytest.raises(ValueError, match=pattern):
        freeze_managed_group_forecasts(**kwargs)
