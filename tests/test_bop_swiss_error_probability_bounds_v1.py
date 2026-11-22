"""Known predictions qualify aggregate-only deterministic error bounds."""
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import sys

import pytest

from scripts import bop_swiss_error_probability_bounds_v1 as m


def test_sharp_geometric_bound_not_arithmetic_mean_claim():
    result = m.binary_error_bounds(0.5, math.log(4), 2, rounding_radius="1e-12")
    upper = Decimal(result["error_geometric_mean_true_probability_upper_bound"])
    assert Decimal("0.125") <= upper < Decimal("0.12500000001")
    assert result["n_errors"] == 1
    assert result["error_predictions_exist"] is True
    assert result["at_least_one_error_true_probability_upper_bound"] == str(upper)


def test_negative_label_tie_is_error_and_never_forces_below_half():
    # Positive prediction .8 for y=1; positive prediction .5 for y=0.
    loss = (-math.log(0.8) - math.log(0.5)) / 2
    result = m.binary_error_bounds(0.5, loss, 2, rounding_radius="1e-12")
    assert Decimal(result["error_geometric_mean_true_probability_upper_bound"]) == Decimal("0.5")
    assert result["min_predictions_below_threshold"] == 0


def test_all_correct_has_no_conditional_error_claim():
    result = m.binary_error_bounds(1, -math.log(0.9), 8)
    assert result["n_errors"] == 0
    assert result["error_predictions_exist"] is False
    assert result["error_mean_log_loss_lower_bound"] is None
    assert result["error_geometric_mean_true_probability_upper_bound"] is None
    assert result["at_least_one_error_true_probability_upper_bound"] is None
    assert result["min_predictions_below_threshold"] == 0


def test_all_wrong_mean_log_loss_is_identified_up_to_rounding():
    loss = (-math.log(0.1) - math.log(0.2)) / 2
    result = m.binary_error_bounds(0, loss, 2, rounding_radius="1e-12")
    assert result["n_errors"] == 2
    assert loss - 2e-12 <= float(result["error_mean_log_loss_lower_bound"]) <= loss
    assert math.sqrt(0.02) <= float(result["error_geometric_mean_true_probability_upper_bound"]) < math.sqrt(0.02) + 2e-12


def test_tiny_clip_floor_does_not_reject_feasible_all_correct_loss():
    with localcontext() as context:
        context.prec = 350
        epsilon = Decimal("1e-100") + Decimal("7e-141")
        loss = epsilon + Decimal("1e-150")
        assert loss > -(Decimal(1) - epsilon).ln()
    result = m.binary_error_bounds(1, loss, 1, rounding_radius=0, clip_floor=epsilon)
    assert result["n_errors"] == 0
    assert result["error_mean_log_loss_lower_bound"] is None


@pytest.mark.parametrize("last_two,minimum", [
    (("0.01", "0.000001"), 1),
    (("0.000001", "0.000001"), 2),
    (("0.01", "0.01"), 0),
])
def test_strict_threshold_and_integer_boundary(last_two, minimum):
    # Two correct ties and two errors; a probability equal to .01 is not below it.
    with localcontext() as context:
        context.prec = 80
        loss = sum(-Decimal(z).ln() for z in ("0.5", "0.5", *last_two)) / 4
    result = m.binary_error_bounds("0.5", loss, 4, rounding_radius="1e-30", clip_floor="0.000001")
    assert result["min_predictions_below_threshold"] == minimum


@pytest.mark.parametrize("accuracy,loss,n,kwargs", [
    (0.4, 0.5, 3, {}),  # no integer correct count in the rounding interval
    (0.5, 0.5, 100, {"rounding_radius": "0.02"}),  # several possible counts
    (1, 0.8, 8, {}),  # correct classifications cannot average more than ln(2)
    (0, 0.1, 8, {}),  # incorrect classifications cannot average below ln(2)
    (0, 20, 8, {}),  # exceeds the clipping cap
    (-0.1, 1, 10, {}),
    (1.1, 1, 10, {}),
    (0.5, -1, 10, {}),
    (float("nan"), 1, 10, {}),
    (0.5, float("inf"), 10, {}),
    (0.5, 1, 0, {}),
    (0.5, 1, True, {}),
    (0.5, 1, 10, {"rounding_radius": "-0.01"}),
    (0.5, 1, 10, {"clip_floor": "0"}),
    (0.5, 1, 10, {"probability_threshold": "0.0000001"}),
])
def test_invalid_or_unidentifiable_metrics_stop(accuracy, loss, n, kwargs):
    with pytest.raises(ValueError):
        m.binary_error_bounds(accuracy, loss, n, **kwargs)


@pytest.mark.parametrize("shift", range(6))
def test_bounds_enclose_real_errors_after_two_stage_rounding(shift):
    # Deterministic synthetic seed-record arrays, including both labels and ties.
    probabilities = [1e-6, 0.0001, 0.01, 0.1, 0.5, 0.8, 0.99, 1 - 1e-6]
    all_errors = []
    seed_accuracy, seed_loss = [], []
    for seed in range(8):
        correct, losses = [], []
        for index in range(8):
            y = index % 2
            p = probabilities[(index + seed + shift) % len(probabilities)]
            z = p if y else 1 - p
            is_correct = (p >= 0.5) == bool(y)
            correct.append(is_correct)
            losses.append(-math.log(z))
            if not is_correct:
                all_errors.append(z)
        seed_accuracy.append(round(sum(correct) / 8, 6))
        seed_loss.append(round(sum(losses) / 8, 6))
    accuracy = round(sum(seed_accuracy) / 8, 6)
    loss = round(sum(seed_loss) / 8, 6)
    result = m.binary_error_bounds(accuracy, loss, 64)
    actual_error_loss = sum(-math.log(z) for z in all_errors) / len(all_errors)
    assert result["n_errors"] == len(all_errors)
    assert float(result["error_mean_log_loss_lower_bound"]) <= actual_error_loss
    assert math.exp(-actual_error_loss) <= float(result["error_geometric_mean_true_probability_upper_bound"])
    assert min(all_errors) <= float(result["at_least_one_error_true_probability_upper_bound"])
    assert result["min_predictions_below_threshold"] <= sum(z < 0.01 for z in all_errors)


def test_pinned_twelve_cell_replay_reports_prediction_not_bird_counts():
    report = m.replay()
    assert report["n_cells"] == 12
    cells = report["all_cells"]
    assert [x["n_errors"] for x in cells] == [123, 99, 271, 283, 56, 55, 144, 156, 32, 32, 54, 64]
    assert {x["n_predictions"] for x in cells} == {2336, 936, 256}
    indexed = {(x["cutoff"], x["target"], x["mode"]): x for x in cells}
    full = indexed[2022, "HR", "full_forward"]
    purged = indexed[2022, "HR", "bird_purged_forward"]
    assert full["n_predictions"] == purged["n_predictions"] == 256
    assert full["source_bird_ID_strings"] == purged["source_bird_ID_strings"] == 32
    assert Decimal("0.004631") < Decimal(full["error_geometric_mean_true_probability_upper_bound"]) < Decimal("0.004632")
    assert Decimal("0.001871") < Decimal(purged["error_geometric_mean_true_probability_upper_bound"]) < Decimal("0.001872")
    assert full["min_predictions_below_threshold"] == 3
    assert purged["min_predictions_below_threshold"] == 6
    assert sum(x["min_predictions_below_threshold"] > 0 for x in cells) == 2
    assert report["original_BOP"] == "empirical_state_prediction_mixed"
    assert report["redkite_external"] == "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    assert report["original_Dryad"] == "NOT_ADMITTED"
    assert report["errors_are_not_independent_animals"] is True


# Every protected file gets the same actual filesystem-alias exercise. Copies
# are used so an intentionally failing regression cannot damage repository data.
PROTECTED_NAMES = [
    "BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json",
    "BOP_SWISS_2022_RANK_RESOLUTION_V1_FIRST_RECEIPT.json",
    "research/BOP_SWISS_PROPER_SCORE_DISCORDANCE_V1_CONTRACT.json",
    "scripts/bop_swiss_proper_score_discordance_v1.py",
    "research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json",
    "scripts/bop_swiss_ranger_focal_prior_year_v1.R",
    "scripts/bop_swiss_temporal_bird_purge_ranger_v1.R",
    "research/BOP_SWISS_ERROR_PROBABILITY_BOUNDS_V1_CONTRACT.json",
    "scripts/bop_swiss_error_probability_bounds_v1.py",
]


def copied_inputs(monkeypatch, tmp_path):
    for relative in PROTECTED_NAMES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((m.ROOT / relative).read_bytes())
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "__file__", str(tmp_path / PROTECTED_NAMES[-1]))
    return {relative: (tmp_path / relative).read_bytes() for relative in PROTECTED_NAMES}


@pytest.mark.parametrize("relative", PROTECTED_NAMES)
@pytest.mark.parametrize("alias", ["direct", "relative", "symlink", "hardlink"])
def test_output_cannot_overwrite_any_pinned_input(monkeypatch, tmp_path, relative, alias):
    before = copied_inputs(monkeypatch, tmp_path)
    target = tmp_path / relative
    output = target
    if alias == "relative":
        monkeypatch.chdir(tmp_path)
        output = Path(relative)
    elif alias == "symlink":
        output = tmp_path / "output-symlink.json"
        output.symlink_to(target)
    elif alias == "hardlink":
        output = tmp_path / "output-hardlink.json"
        output.hardlink_to(target)
    monkeypatch.setattr(sys, "argv", ["bounds", "--out", str(output)])
    with pytest.raises(ValueError, match="cannot overwrite immutable"):
        m.main()
    assert {name: (tmp_path / name).read_bytes() for name in PROTECTED_NAMES} == before


@pytest.mark.parametrize("relative", PROTECTED_NAMES[:-1])
def test_input_byte_drift_stops_replay(monkeypatch, tmp_path, relative):
    copied_inputs(monkeypatch, tmp_path)
    target = tmp_path / relative
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="PINNED_INPUT_DRIFT"):
        m.replay()


@pytest.mark.parametrize("destination", ["file", "stdout"])
def test_normal_cli_output_preserves_inputs(monkeypatch, tmp_path, capsys, destination):
    paths = m.protected_paths()
    before = [p.read_bytes() for p in paths]
    output = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", ["bounds", "--out", str(output)] if destination == "file" else ["bounds"])
    m.main()
    content = output.read_text(encoding="utf-8") if destination == "file" else capsys.readouterr().out
    assert json.loads(content)["n_cells"] == 12
    assert [p.read_bytes() for p in paths] == before
