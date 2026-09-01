import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json"


def test_terminal_decision_is_frozen_non_generalizing_result():
    d = json.loads(DECISION.read_text(encoding="utf-8"))
    assert d["terminal_category"] == "empirical_n2_thickness_not_generalizing"
    assert d["scientific_terminal_decision"] is True
    assert d["workflow"]["run_id"] == 33481773409
    assert d["workflow"]["head_sha"] == "fe7d66c49902f7bca7a3d0229b15cd1e884ace85"
    assert d["workflow"]["artifact_id"] == 9790203720
    assert d["workflow"]["artifact_digest"] == (
        "sha256:4e28817908650ea3dbcf91341c0a27c00982102f0c8a690c1ce8ba5ed5f19d8b"
    )
    assert d["frozen_boundaries"]["post_outcome_retuning"] is False


def test_primary_thickness_and_sealed_result_cannot_be_reinterpreted():
    d = json.loads(DECISION.read_text(encoding="utf-8"))
    p = d["primary"]
    assert p["eligible_cell_count"] == 18
    assert p["information_nats_H_Z_given_XY"] == 1.3918623004770097
    assert p["effective_vertical_states"] == 4.022333876564191
    assert p["answer_check_category"] == "estimable_but_non_generalizing"
    gains = [item["mean_log_score_gain"] for item in p["sealed_individual_scores"]]
    assert gains == [-0.43541033813280833, -0.021938657402345435]
    assert all(value <= 0 for value in gains)
    assert p["sealed_equal_individual_mean_log_score_gain"] == -0.22867449776757687
    assert len(p["local_cells"]) == 18


def test_sensitivities_do_not_rescue_primary():
    d = json.loads(DECISION.read_text(encoding="utf-8"))
    s = d["sensitivities"]
    assert s["primary_decision_not_overridden"] is True
    for key in ("grid_2500_m", "grid_10000_m", "fine_z_bins", "coarse_z_bins"):
        assert s[key]["status"] == "evaluable"
        assert s[key]["answer_check_category"] == "estimable_but_non_generalizing"
        assert all(value <= 0 for value in s[key]["sealed_gains"])
    assert s["exclude_source_marked_outliers"]["status"] == "not_evaluable"


def test_gate_e_remains_blocked_and_no_rescue_is_authorized():
    d = json.loads(DECISION.read_text(encoding="utf-8"))
    assert d["next_action"] == (
        "close this empirical lane without rescue, retuning, rerun, dataset substitution, or Gate-E promotion"
    )
    do_not = set(d["interpretation"]["do_not_conclude"])
    assert "the vertical axis is absent" in do_not
    assert "there is no vertical niche thickness" in do_not
    assert "forest-versus-grassland Gate-E is supported" in do_not
