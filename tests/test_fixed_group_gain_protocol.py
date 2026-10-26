from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from odsp.fixed_group_gain_protocol import (
    calibrate_fixed_group_gain,
    freeze_fixed_group_forecasts,
    validate_fixed_group_gain,
)


MODEL = b"frozen test model built only on training groups"
REFERENCE = b"frozen test training-only reference"
TRAINING_SHA = hashlib.sha256(b"training source roster and outcomes").hexdigest()


def _row(role, group, name, stratum="raptor_A", model=(0.8, 0.2),
         ref=(0.5, 0.5)):
    return {
        "row_id": f"{role}-{name}",
        "group_id": group,
        "stratum": stratum,
        "conditional": model,
        "reference": ref,
    }


def _setup(n_cal=19):
    cal = [_row("cal", f"animal_c{i}", str(i)) for i in range(n_cal)]
    val = [_row("val", f"animal_v{i}", str(i)) for i in range(30)]
    plan = freeze_fixed_group_forecasts(
        training_group_ids=["train1", "train2"],
        calibration_forecasts=cal,
        validation_forecasts=val,
        classes=["alt_low", "alt_high"],
        model_artifact=MODEL,
        reference_artifact=REFERENCE,
        training_source_sha256=TRAINING_SHA,
        miscoverage=0.1,
    )
    return plan, cal, val


def _calibration(plan, cal, label="alt_low"):
    return calibrate_fixed_group_gain(
        plan,
        {row["row_id"]: label for row in cal},
        model_artifact=MODEL,
        reference_artifact=REFERENCE,
    )


def _validate(plan, result, val, label="alt_low"):
    return validate_fixed_group_gain(
        plan, result, {row["row_id"]: label for row in val},
        model_artifact=MODEL, reference_artifact=REFERENCE,
    )


def test_frozen_model_stratum_rank_pipeline_success_and_digest():
    plan, cal, val = _setup()
    assert len(plan.digest) == 64
    manifest = plan.public_manifest()
    assert manifest["training_group_count"] == 2
    assert manifest["calibration_group_count"] == 19
    assert manifest["validation_group_count"] == 30
    assert manifest["outcomes_accessed_by_freeze"] is False
    assert "alt_low" not in str(manifest["strata"])
    assert "animal_c0" not in str(manifest)
    result = _calibration(plan, cal)
    assert len(result.gains) == 19
    checked = _validate(plan, result, val)
    assert checked.group_equal_coverage == 1.0
    assert checked.covered_validation_group_count == 30
    assert checked.validation_group_count == 30
    assert checked.strata[0].finite_rank == 2
    assert checked.strata[0].vacuous is False
    assert checked.as_public_dict()["exchangeability_verified_by_software"] is False
    assert checked.as_public_dict()["historical_bop_terminal_changed"] is False


def test_fails_if_validation_outcomes_are_supplied_during_calibration():
    plan, cal, val = _setup()
    wrong = {row["row_id"]: "alt_low" for row in cal + val}
    with pytest.raises(ValueError, match="outcome row IDs"):
        _cal = calibrate_fixed_group_gain(
            plan, wrong, model_artifact=MODEL, reference_artifact=REFERENCE
        )


def test_fails_if_calibration_rows_are_rescored_as_validation():
    plan, cal, val = _setup()
    c = _calibration(plan, cal)
    with pytest.raises(ValueError, match="outcome row IDs"):
        _validate(plan, c, cal)


def test_probability_and_model_artifact_mutation_fail_closed():
    plan, cal, val = _setup()
    with pytest.raises(ValueError, match="model artifact hash"):
        calibrate_fixed_group_gain(
            plan, {row["row_id"]: "alt_low" for row in cal},
            model_artifact=b"RETRAINED after observing calibration",
            reference_artifact=REFERENCE,
        )
    changed = replace(
        plan,
        calibration_rows=(
            replace(plan.calibration_rows[0], conditional=(0.1, 0.9)),
            *plan.calibration_rows[1:],
        ),
    )
    with pytest.raises(ValueError, match="frozen forecast plan"):
        _calibration(changed, cal)
    with pytest.raises(ValueError, match="reference artifact hash"):
        calibrate_fixed_group_gain(
            plan, {row["row_id"]: "alt_low" for row in cal},
            model_artifact=MODEL,
            reference_artifact=b"new pooled baseline",
        )


def test_calibration_drift_rejected_before_validation():
    plan, cal, val = _setup()
    c = _calibration(plan, cal)
    tampered = replace(
        c,
        gains=(
            replace(c.gains[0], weighted_mean_gain=999.0),
            *c.gains[1:],
        ),
    )
    with pytest.raises(ValueError, match="frozen calibration group scores"):
        _validate(plan, tampered, val)
    other, _, _ = _setup(n_cal=18)
    with pytest.raises(ValueError, match="different frozen plan"):
        _validate(other, c, val)


def test_validation_shift_is_detected_as_loss_of_coverage_not_recalibrated():
    plan, cal, val = _setup()
    c = _calibration(plan, cal, "alt_low")
    test = _validate(plan, c, val, "alt_high")
    assert test.group_equal_coverage == 0.0
    assert test.strata[0].observed_group_coverage == 0.0


def test_underpowered_stratum_has_vacuous_lower_bound():
    plan, cal, val = _setup(n_cal=5)
    c = _calibration(plan, cal)
    result = _validate(plan, c, val)
    assert result.strata[0].vacuous is True
    assert result.strata[0].finite_rank == 0
    assert result.as_public_dict()["strata"][0]["bound"] is None


@pytest.mark.parametrize(
    "modify,match",
    [
        ("train_overlap", "training group overlaps"),
        ("role_overlap", "one group cannot cross"),
        ("duplicate_row", "duplicate row_id"),
        ("no_cal_for_validation_stratum", "validation stratum"),
        ("label_in_forecast", "outcomes must not be frozen"),
        ("zero_probability", "strictly positive"),
        ("bad_sum", "sum to one"),
        ("missing_state", "strictly positive"),
        ("negative_weight", "weight must be"),
        ("bad_source_hash", "SHA256"),
    ],
)
def test_freeze_rejects_invalid_row_roles_or_support(modify, match):
    _, cal, val = _setup(n_cal=5)
    cal = [dict(x) for x in cal]
    val = [dict(x) for x in val]
    kwargs = dict(
        training_group_ids=["train1", "train2"],
        calibration_forecasts=cal, validation_forecasts=val,
        classes=["alt_low", "alt_high"], model_artifact=MODEL,
        reference_artifact=REFERENCE, training_source_sha256=TRAINING_SHA,
    )
    if modify == "train_overlap":
        cal[0]["group_id"] = "train1"
    elif modify == "role_overlap":
        val[0]["group_id"] = "animal_c0"
    elif modify == "duplicate_row":
        val[0]["row_id"] = cal[0]["row_id"]
    elif modify == "no_cal_for_validation_stratum":
        val[0]["stratum"] = "raptor_B"
    elif modify == "label_in_forecast":
        cal[0]["observed_state"] = "alt_high"
    elif modify == "zero_probability":
        cal[0]["conditional"] = [1.0, 0.0]
    elif modify == "bad_sum":
        cal[0]["reference"] = [0.6, 0.6]
    elif modify == "missing_state":
        cal[0]["conditional"] = [0.5]
    elif modify == "negative_weight":
        cal[0]["weight"] = -1
    elif modify == "bad_source_hash":
        kwargs["training_source_sha256"] = "x"
    with pytest.raises(ValueError, match=match):
        freeze_fixed_group_forecasts(**kwargs)


def test_group_mean_gives_equal_group_rank_regardless_of_event_count():
    cal = [_row("cal", "single", "small", model=(0.8, 0.2))]
    cal += [_row("cal", "many", str(i), model=(0.6, 0.4)) for i in range(200)]
    val = [_row("val", "unseen", "one")]
    plan = freeze_fixed_group_forecasts(
        training_group_ids=["train"],
        calibration_forecasts=cal, validation_forecasts=val,
        classes=["alt_low", "alt_high"], model_artifact=MODEL,
        reference_artifact=REFERENCE, training_source_sha256=TRAINING_SHA,
    )
    c = _calibration(plan, cal)
    assert len(c.gains) == 2
    assert sorted(row.row_count for row in c.gains) == [1, 200]
    output = _validate(plan, c, val)
    assert output.strata[0].vacuous is True


def test_row_forecasts_are_bound_to_calibration_plan_not_inferred_from_labels():
    plan, cal, val = _setup()
    # No way to "calibrate" with a different probability field or changed
    # outcome label vocabulary: both must fail rather than be fitted implicitly.
    with pytest.raises(ValueError, match="observed state"):
        _calibration(plan, cal, "hidden_new_label")
