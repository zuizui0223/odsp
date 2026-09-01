import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "N2_BAT_THICKNESS_CONTRACT.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_bat_thickness_contract_is_post_structural_pre_outcome():
    c = _contract()
    auth = c["structural_authorization"]
    assert c["contract_id"] == "odsp-n2-bat-thickness-v1"
    assert c["chapter_code"] == "N2"
    assert c["core_question"] == "HOW THICK is it?"
    assert auth["boundary_commit"] == "be5a86e850b99457d1e6055289c2990fb8ca358f"
    assert auth["terminal_category"] == "structurally_available"
    assert auth["numeric_height_values_opened_before_this_contract"] is False
    assert auth["predecessor_tawaki_result_retained"] == "empirical_gate_d_unavailable"
    assert c["post_outcome_retuning"] is False


def test_primary_axis_grid_and_bins_are_frozen():
    c = _contract()
    assert c["axis_semantics"]["z_field"] == "height_above_msl"
    assert c["axis_semantics"]["primary_is_height_above_ground"] is False
    assert c["axis_semantics"]["dem_or_terrain_subtraction_primary"] is False
    assert c["primary_horizontal_grid"] == {
        "crs": "EPSG:3035",
        "cell_size_m": 5000,
        "origin_m": [0, 0],
        "cell_rule": "floor(E/5000):floor(N/5000)",
        "minimum_model_events_per_cell": 30,
        "minimum_distinct_model_individuals_per_cell": 3,
        "eligible_cells_are_frozen_from_model_pool_only": True,
        "primary_only_for_decision": True,
    }
    assert c["z_discretization"]["primary_edges_m"] == [
        "-inf", 0, 50, 100, 200, 400, 800, 1600, 3200, "inf"
    ]
    assert c["z_discretization"]["sensitivity_cannot_replace_primary"] is True
    assert c["grid_sensitivity"]["cannot_replace_primary"] is True
    assert c["grid_sensitivity"]["scientific_decision_uses_sensitivity"] is False


def test_model_probabilities_are_individual_equal_weighted_before_sealed_open():
    c = _contract()
    w = c["support_weighting"]
    d = c["model_distribution"]
    assert w["primary_unit"] == "individual"
    assert w["individual_equal_weighting"] is True
    assert w["horizontal_cell_mass"]["event_count_cannot_weight_individuals"] is True
    assert w["within_cell_vertical_distribution"]["event_count_cannot_weight_individuals"] is True
    assert w["within_cell_vertical_distribution"]["minimum_individuals_in_cell"] == 3
    assert "arithmetic mean" in w["within_cell_vertical_distribution"]["definition"]
    assert "Jeffreys pseudocount 0.5" in w["within_cell_vertical_distribution"]["definition"]
    assert "P_model(x,y)*P_model(z|x,y)" in w["joint_support"]
    assert "arithmetic mean" in d["conditional"]
    assert "arithmetic mean" in d["marginal_comparator"]
    assert "0.5" in d["smoothing_stage"]
    assert d["zero_probability_after_smoothing"] is False
    assert d["no_refit_or_bin_change_after_sealed_open"] is True


def test_sealed_answer_check_uses_two_individuals_as_replication_units():
    c = _contract()
    s = c["sealed_answer_check"]
    assert c["whole_individual_split"]["expected_structural_counts"] == {
        "model": 6,
        "sealed": 2,
    }
    assert s["minimum_scored_events_per_sealed_individual"] == 30
    assert s["event_metric"] == "log P_model(z|x,y) - log P_model(z) using the frozen model-only distributions"
    assert s["individual_identity_is_primary_replication_unit"] is True
    assert "unweighted arithmetic mean" in s["aggregate_metric"]
    categories = s["decision_categories"]
    assert "both sealed-individual mean log-score gains are strictly > 0" in categories[
        "estimable_and_generalizing"
    ]
    assert "both sealed-individual gains are <= 0" in categories[
        "estimable_but_non_generalizing"
    ]
    assert "not both >0 and not both <=0" in categories[
        "estimable_but_generalization_mixed"
    ]
    assert "descriptive H(Z|X,Y)>0 alone is not sufficient" in s[
        "primary_scientific_support_rule"
    ]


def test_contract_contains_no_opened_numeric_height_outcome():
    c = _contract()
    serialized = json.dumps(c, sort_keys=True)
    forbidden_result_keys = (
        "height_min_result",
        "height_max_result",
        "height_mean_result",
        "H_Z_given_XY_result",
        "effective_states_result",
        "sealed_gain_result",
        "terminal_result_observed",
    )
    for key in forbidden_result_keys:
        assert key not in serialized
    assert c["primary_estimand"]["magnitude_threshold_for_primary_support"] is None
