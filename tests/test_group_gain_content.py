"""Fixed-threshold population content is distinct from marginal rank coverage."""
from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
from itertools import product
import json
import math

import pytest

from odsp.fixed_group_gain_protocol import (
    calibrate_fixed_group_gain, freeze_fixed_group_forecasts,
    validate_fixed_group_gain,
)
from odsp.group_gain_content import (
    assess_group_gain_content, freeze_group_gain_content_plan,
)
from odsp.new_group_gain_envelope import fit_new_group_gain_lower_envelope


MODEL = b"synthetic fixed predictor"
REFERENCE = b"synthetic fixed reference"
IID = "iid_group_gains_within_prespecified_stratum"


def forecast_plan(n, *, other=0, tie_first=False, repeats=1,
                  weight=1.0, reference_probability=0.5):
    calibration, validation, outcomes = [], [], {}
    for stratum, count in (("target", n), ("other", other)):
        if not count:
            continue
        for index in range(count):
            for repeat in range(repeats):
                row_id = f"{stratum}:cal:{index}:{repeat}"
                calibration.append({
                    "row_id": row_id, "group_id": f"{stratum}-cal-{index}",
                    "stratum": stratum,
                    "conditional": [0.5, 0.5] if tie_first and index == 0 else [0.75, 0.25],
                    "reference": [reference_probability, 1 - reference_probability],
                    "weight": weight,
                })
                outcomes[row_id] = "a"
        validation.append({
            "row_id": f"{stratum}:val", "group_id": f"{stratum}-val",
            "stratum": stratum, "conditional": [0.75, 0.25],
            "reference": [0.5, 0.5],
        })
    plan = freeze_fixed_group_forecasts(
        training_group_ids=["training"], classes=["a", "b"],
        calibration_forecasts=calibration, validation_forecasts=validation,
        model_artifact=MODEL, reference_artifact=REFERENCE,
        training_source_sha256="a" * 64,
    )
    return plan, outcomes


def freeze(plan, **kwargs):
    settings = {
        "stratum": "target", "sampling_assumption": IID,
        "model_artifact": MODEL, "reference_artifact": REFERENCE,
    }
    settings.update(kwargs)
    return freeze_group_gain_content_plan(plan, **settings)


def assess(policy, plan, outcomes, **kwargs):
    artifacts = {"model_artifact": MODEL, "reference_artifact": REFERENCE}
    artifacts.update(kwargs)
    return assess_group_gain_content(policy, plan, outcomes, **artifacts)


class UnreadableOutcomes(Mapping):
    def __getitem__(self, key):
        raise AssertionError("outcomes accessed before the count gate")

    def __iter__(self):
        raise AssertionError("outcomes accessed before the count gate")

    def __len__(self):
        raise AssertionError("outcomes accessed before the count gate")


def test_positive_rank_bound_does_not_certify_positive_population_fraction():
    rank = fit_new_group_gain_lower_envelope(
        [1.0] * 9, [f"cal-{j}" for j in range(9)],
        source_design="fixed_predictor_groups",
    )
    assert rank.lower_gain_bound == 1.0
    assert rank.conservative_coverage_if_exchangeable == 0.9
    plan, _ = forecast_plan(9)
    policy = freeze(plan)
    assert policy.count_allows_support is False
    with pytest.raises(ValueError, match="insufficient calibration groups"):
        assess(policy, plan, UnreadableOutcomes())


def test_iid_counterexample_preserves_joint_rank_error_not_selected_positivity():
    selected = joint_error = selected_positive = Fraction(0)
    ids = [f"cal-{j}" for j in range(9)]
    for values in product((-1.0, 1.0), repeat=10):
        positives = values.count(1.0)
        probability = Fraction(4, 5) ** positives * Fraction(1, 5) ** (10 - positives)
        rank = fit_new_group_gain_lower_envelope(values[:9], ids, source_design="fixed_predictor_groups")
        if rank.lower_gain_bound > 0:
            selected += probability
            if values[-1] <= 0:
                joint_error += probability
            else:
                selected_positive += probability
    assert selected == Fraction("0.134217728")
    assert joint_error == Fraction("0.0268435456") < Fraction(1, 10)
    assert selected_positive / selected == Fraction(4, 5) < Fraction(9, 10)


@pytest.mark.parametrize("n,feasible", [(9, False), (28, False), (29, True)])
def test_all_positive_count_gate_before_labels(n, feasible):
    plan, outcomes = forecast_plan(n)
    policy = freeze(plan)
    assert policy.count_allows_support is feasible
    public = policy.as_public_dict()
    assert public["calibration_group_count"] == n
    assert public["outcomes_accessed_by_freeze"] is False
    if feasible:
        result = assess(policy, plan, outcomes)
        assert result.supported is True
        assert result.exact_p_value == Fraction(9, 10) ** 29
    else:
        with pytest.raises(ValueError, match="insufficient calibration groups"):
            assess(policy, plan, UnreadableOutcomes())


@pytest.mark.parametrize("n,supported", [(45, False), (46, True)])
def test_one_nonpositive_group_exact_boundary(n, supported):
    plan, outcomes = forecast_plan(n)
    outcomes["target:cal:0:0"] = "b"
    result = assess(freeze(plan), plan, outcomes)
    expected = Fraction(9, 10) ** n + n * Fraction(1, 10) * Fraction(9, 10) ** (n - 1)
    assert result.nonpositive_group_count == 1
    assert result.positive_group_count == n - 1
    assert result.exact_p_value == expected
    assert result.supported is supported
    assert Fraction.from_float(result.as_public_dict()["p_value_upper_bound"]) >= expected


def test_threshold_ties_count_as_nonpositive():
    plan, outcomes = forecast_plan(29, tie_first=True)
    result = assess(freeze(plan), plan, outcomes)
    assert result.nonpositive_group_count == 1
    assert result.supported is False


def test_threshold_is_frozen_and_changes_the_actual_scored_event():
    plan, outcomes = forecast_plan(29)
    threshold = math.log(0.75) - math.log(0.5)
    result = assess(freeze(plan, gain_threshold=threshold), plan, outcomes)
    assert result.nonpositive_group_count == 29
    assert result.exact_p_value == 1
    assert result.supported is False


@pytest.mark.parametrize("repeats", [1, 4])
@pytest.mark.parametrize("weight,reference_probability,threshold", [
    (0.01, 0.5, math.log(0.75) - math.log(0.5)),
    (5e-324, 0.375, 0.8),
])
def test_finite_weight_roundoff_cannot_turn_threshold_failure_into_support(
    repeats, weight, reference_probability, threshold,
):
    plan, outcomes = forecast_plan(
        29, repeats=repeats, weight=weight,
        reference_probability=reference_probability,
    )
    # Identical within-animal deltas have the same mean at every positive
    # weight. The inherited float products nevertheless move above t.
    row_gain = math.log(0.75) - math.log(reference_probability)
    assert row_gain <= threshold
    calibration = calibrate_fixed_group_gain(
        plan, outcomes, model_artifact=MODEL, reference_artifact=REFERENCE,
    )
    assert all(g.weighted_mean_gain > threshold for g in calibration.gains)
    with pytest.raises(ValueError, match="weighted gain threshold classification"):
        assess(freeze(plan, gain_threshold=threshold), plan, outcomes)


@pytest.mark.parametrize("weight,reference_probability", [(0.01, 0.5), (5e-324, 0.375)])
def test_weight_scale_is_admitted_when_the_threshold_decision_is_unambiguous(
    weight, reference_probability,
):
    plan, outcomes = forecast_plan(29, weight=weight, reference_probability=reference_probability)
    result = assess(freeze(plan), plan, outcomes)
    assert result.nonpositive_group_count == 0
    assert result.supported is True
    assert result.calibration == calibrate_fixed_group_gain(
        plan, outcomes, model_artifact=MODEL, reference_artifact=REFERENCE,
    )


def test_calibration_outcomes_are_consumed_once_for_scoring_and_threshold_guard():
    plan, outcomes = forecast_plan(29)
    seen = set()

    class SingleReadOutcomes(Mapping):
        def __iter__(self):
            return iter(outcomes)

        def __len__(self):
            return len(outcomes)

        def __getitem__(self, key):
            assert key not in seen, "calibration label was reread"
            seen.add(key)
            return outcomes[key]

    result = assess(freeze(plan), plan, SingleReadOutcomes())
    assert result.supported is True
    assert seen == set(outcomes)


@pytest.mark.parametrize("confidence,supported", [
    (Fraction(1, 2), True),
    (Fraction(1, 2) + Fraction(1, 10**20), False),
])
def test_exact_probability_boundary_does_not_use_float_tolerance(confidence, supported):
    plan, outcomes = forecast_plan(3)
    outcomes["target:cal:0:0"] = "b"
    policy = freeze(plan, minimum_positive_fraction=Fraction(1, 2), confidence_level=confidence)
    result = assess(policy, plan, outcomes)
    assert result.exact_p_value == Fraction(1, 2)
    assert result.supported is supported


@pytest.mark.parametrize("failures,tail_numerator", list(enumerate([1, 7, 22, 42, 57, 63, 64])))
def test_every_failure_count_matches_known_six_trial_binomial(failures, tail_numerator):
    plan, outcomes = forecast_plan(6)
    for index in range(failures):
        outcomes[f"target:cal:{index}:0"] = "b"
    result = assess(freeze(plan, minimum_positive_fraction="1/2", confidence_level="3/4"), plan, outcomes)
    assert result.exact_p_value == Fraction(tail_numerator, 64)
    assert result.supported is (failures <= 1)


def test_selected_stratum_requires_its_own_reserved_validation_group():
    original, _ = forecast_plan(29, other=29)
    calibration = [{k: v for k, v in row.canonical().items() if k != "role"}
                   for row in original.calibration_rows]
    validation = [{k: v for k, v in row.canonical().items() if k != "role"}
                  for row in original.validation_rows if row.stratum == "other"]
    plan = freeze_fixed_group_forecasts(
        training_group_ids=["training"], classes=["a", "b"],
        calibration_forecasts=calibration, validation_forecasts=validation,
        model_artifact=MODEL, reference_artifact=REFERENCE,
        training_source_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="reserved validation groups"):
        freeze(plan)


def test_successful_other_stratum_does_not_rescue_selected_stratum():
    plan, outcomes = forecast_plan(29, other=100)
    outcomes["target:cal:0:0"] = "b"
    result = assess(freeze(plan), plan, outcomes)
    assert result.calibration_group_count == 29
    assert result.nonpositive_group_count == 1
    assert result.supported is False


def test_event_replication_does_not_increase_animal_count():
    plan, outcomes = forecast_plan(29, repeats=4)
    result = assess(freeze(plan), plan, outcomes)
    assert result.calibration_group_count == 29
    assert result.exact_p_value == Fraction(9, 10) ** 29
    assert all(row.row_count == 4 for row in result.calibration.gains)


def test_calibration_can_be_reused_for_unchanged_reserved_validation():
    plan, outcomes = forecast_plan(29)
    result = assess(freeze(plan), plan, outcomes)
    original = calibrate_fixed_group_gain(plan, outcomes, model_artifact=MODEL, reference_artifact=REFERENCE)
    assert result.calibration == original
    validation = validate_fixed_group_gain(
        plan, result.calibration, {"target:val": "b"},
        model_artifact=MODEL, reference_artifact=REFERENCE,
    )
    assert validation.validation_group_count == 1
    assert validation.strata[0].positive_validation_group_count == 0
    assert result.supported is True  # the separate validation cannot retune it


def test_public_result_has_counts_and_limits_without_group_ids_or_predictions():
    plan, outcomes = forecast_plan(29)
    result = assess(freeze(plan), plan, outcomes)
    public = result.as_public_dict()
    encoded = json.dumps(public, allow_nan=False)
    assert public["supported_under_declared_iid_sampling"] is True
    assert public["sampling_independence_verified_by_software"] is False
    assert public["simultaneous_strata_claim"] is False
    assert public["validation_outcomes_accessed"] is False
    assert "target-cal-" not in encoded
    assert "conditional" not in public
    assert "outcomes" not in public


@pytest.mark.parametrize("kwargs", [
    {"minimum_positive_fraction": 0}, {"minimum_positive_fraction": 1},
    {"minimum_positive_fraction": True}, {"minimum_positive_fraction": float("nan")},
    {"minimum_positive_fraction": float("inf")}, {"confidence_level": 0},
    {"confidence_level": 1}, {"confidence_level": False},
    {"confidence_level": "invalid"}, {"gain_threshold": True},
    {"gain_threshold": float("nan")}, {"gain_threshold": float("inf")},
    {"sampling_assumption": "exchangeable_groups"},
    {"sampling_assumption": ""}, {"stratum": "missing"}, {"stratum": " target "},
])
def test_invalid_or_unjustified_policy_inputs_stop(kwargs):
    plan, _ = forecast_plan(29)
    with pytest.raises(ValueError):
        freeze(plan, **kwargs)


@pytest.mark.parametrize("change", [
    {"gain_threshold": 1.0}, {"stratum": "other"},
    {"minimum_positive_fraction": Fraction(1, 2)},
    {"confidence_level": Fraction(1, 2)}, {"calibration_group_count": 1000},
    {"sampling_assumption": "exchangeable_groups"},
])
def test_policy_mutation_stops_before_outcomes(change):
    plan, _ = forecast_plan(29)
    altered = replace(freeze(plan), **change)
    with pytest.raises(ValueError, match="policy.*changed"):
        assess(altered, plan, UnreadableOutcomes())


def test_policy_from_another_forecast_plan_is_rejected_before_outcomes():
    original, _ = forecast_plan(29)
    different, _ = forecast_plan(30)
    with pytest.raises(ValueError, match="different frozen forecast plan"):
        assess(freeze(original), different, UnreadableOutcomes())


@pytest.mark.parametrize("artifact", ["model_artifact", "reference_artifact"])
def test_changed_artifact_is_rejected_before_outcomes(artifact):
    plan, _ = forecast_plan(29)
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        assess(freeze(plan), plan, UnreadableOutcomes(), **{artifact: b"changed"})


def test_changed_forecast_plan_is_rejected_before_outcomes():
    plan, _ = forecast_plan(29)
    row = replace(plan.calibration_rows[0], conditional=(0.9, 0.1))
    changed = replace(plan, calibration_rows=(row, *plan.calibration_rows[1:]))
    with pytest.raises(ValueError, match="forecast plan contents changed"):
        assess(freeze(plan), changed, UnreadableOutcomes())


@pytest.mark.parametrize("role_change", ["extra_validation", "validation_only", "missing"])
def test_only_complete_calibration_outcomes_are_accepted(role_change):
    plan, outcomes = forecast_plan(29)
    if role_change == "extra_validation":
        outcomes["target:val"] = "a"
    elif role_change == "validation_only":
        outcomes = {"target:val": "a"}
    else:
        outcomes.pop("target:cal:0:0")
    with pytest.raises(ValueError, match="outcome row IDs must match exactly"):
        assess(freeze(plan), plan, outcomes)


@pytest.mark.parametrize("role_change", ["extra_validation", "validation_only", "missing"])
def test_role_mismatch_is_rejected_before_any_label_value_is_opened(role_change):
    plan, outcomes = forecast_plan(29)
    keys = set(outcomes)
    if role_change == "extra_validation":
        keys.add("target:val")
    elif role_change == "validation_only":
        keys = {"target:val"}
    else:
        keys.remove("target:cal:0:0")

    class UnopenedWrongRole(Mapping):
        def __iter__(self):
            return iter(keys)

        def __len__(self):
            return len(keys)

        def __getitem__(self, key):
            raise AssertionError("a role-mismatched label value was opened")

    with pytest.raises(ValueError, match="outcome row IDs must match exactly"):
        assess(freeze(plan), plan, UnopenedWrongRole())


def test_nonfinite_scoring_arithmetic_cannot_be_counted_as_positive():
    original, outcomes = forecast_plan(29)
    rows = []
    for row in original.calibration_rows:
        values = row.canonical()
        values.pop("role")
        values.update(conditional=[0.5, 0.5], reference=[1e-300, 1.0], weight=1e308)
        rows.append(values)
    validation = original.validation_rows[0].canonical()
    validation.pop("role")
    plan = freeze_fixed_group_forecasts(
        training_group_ids=["training"], classes=["a", "b"],
        calibration_forecasts=rows, validation_forecasts=[validation],
        model_artifact=MODEL, reference_artifact=REFERENCE,
        training_source_sha256="a" * 64,
    )
    # The true finite gain is about 690, below 1000; overflow is not a success.
    with pytest.raises(ValueError):
        assess(freeze(plan, gain_threshold=1000), plan, outcomes)
