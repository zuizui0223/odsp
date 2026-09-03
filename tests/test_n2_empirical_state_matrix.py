import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_bat_matrix_row_matches_terminal_decision():
    matrix = _load("N2_EMPIRICAL_STATE_MATRIX.json")["lanes"][
        "european_free_tailed_bat"
    ]
    terminal = _load("N2_BAT_THICKNESS_TERMINAL_DECISION.json")
    primary = terminal["primary"]

    assert matrix["terminal_category"] == terminal["terminal_category"]
    assert matrix["added_axis_thickness"]["information_nats"] == primary[
        "information_nats_H_Z_given_XY"
    ]
    assert matrix["added_axis_thickness"]["effective_states"] == primary[
        "effective_vertical_states"
    ]
    expected_gains = [
        score["mean_log_score_gain"]
        for score in primary["sealed_individual_scores"]
    ]
    assert matrix["independent_transferability"]["gains"] == expected_gains
    assert matrix["independent_transferability"]["classification"] == "non_generalizing"


def test_serengeti_matrix_row_matches_validated_receipt():
    matrix = _load("N2_EMPIRICAL_STATE_MATRIX.json")["lanes"]["snapshot_serengeti"]
    receipt = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    assert matrix["terminal_category"] == receipt["terminal_category"]
    assert matrix["admitted_species_count"] == receipt["admitted_species_count"]
    assert matrix["added_axis_thickness"]["information_nats"] == receipt[
        "temporal_information_nats"
    ]
    assert matrix["added_axis_thickness"]["effective_states"] == receipt[
        "effective_temporal_states"
    ]
    assert matrix["conditioned_organization"]["information_nats"] == receipt[
        "partition_information_nats"
    ]
    assert matrix["conditioned_organization"]["permutation_p_value"] == receipt[
        "permutation_p_value"
    ]
    assert matrix["independent_transferability"]["gains"] == receipt["heldout_gains"]
    assert matrix["independent_transferability"]["classification"] == receipt[
        "transfer_category"
    ]


def test_three_lanes_are_kept_as_distinct_terminal_states():
    lanes = _load("N2_EMPIRICAL_STATE_MATRIX.json")["lanes"]

    assert lanes["tawaki"]["structural_estimability"] is False
    assert lanes["tawaki"]["added_axis_thickness"]["status"] == "unavailable"
    assert lanes["european_free_tailed_bat"]["added_axis_thickness"]["status"] == "present"
    assert lanes["european_free_tailed_bat"]["independent_transferability"]["classification"] == "non_generalizing"
    assert lanes["snapshot_serengeti"]["added_axis_thickness"]["status"] == "present"
    assert lanes["snapshot_serengeti"]["independent_transferability"]["classification"] == "generalizing"


def test_synthesis_does_not_turn_cross_system_contrast_into_axis_causality():
    inference = _load("N2_EMPIRICAL_STATE_MATRIX.json")["cross_lane_inference"]
    unsupported = " ".join(inference["not_supported"])

    assert "Vertical axes are intrinsically less generalizable than temporal axes." in unsupported
    assert "directly comparable" in unsupported
    assert "rescues or changes" in unsupported


def test_no_matrix_lane_is_an_empirical_n3_state_artifact():
    lanes = _load("N2_EMPIRICAL_STATE_MATRIX.json")["lanes"]
    assert all(
        lane["axis_resolved_species_state_allowed_for_empirical_n3"] is False
        for lane in lanes.values()
    )
