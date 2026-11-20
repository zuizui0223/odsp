"""Source-free qualification for 2022 Swiss proper-score sign disagreement."""
from __future__ import annotations

from copy import deepcopy
import json
import math
import pytest

from scripts import bop_swiss_proper_score_discordance_v1 as m


def original():
    return m.load_locked()


def test_original_pre_frozen_diagnostic_all_twelve():
    c, s, r = original()
    out = m.analyze(c, s, r)
    assert out["n_source_models"] == 96
    assert out["n_frozen_cells"] == 12
    assert out["n_opposite_sign_cells"] == 2
    assert {(x["cutoff"], x["target"], x["mode"]) for x in out["opposite_sign_cells"]} == {
        (2022, "HR", "full_forward"),
        (2022, "HR", "bird_purged_forward"),
    }
    cells = {(x["cutoff"], x["target"], x["mode"]): x for x in out["all_frozen_cells"]}
    full = cells[2022, "HR", "full_forward"]
    purged = cells[2022, "HR", "bird_purged_forward"]
    assert full["brier_gain_vs_training_reference"] == pytest.approx(0.121707, abs=0.000002)
    assert purged["brier_gain_vs_training_reference"] == pytest.approx(0.166552, abs=0.000002)
    assert full["source_log_score_gain_vs_training_reference"] == pytest.approx(-0.584100)
    assert purged["source_log_score_gain_vs_training_reference"] == pytest.approx(-0.609657)
    assert purged["train_only_reference_positive_fraction"] == pytest.approx(0.445045)
    assert purged["test_positive_fraction"] == pytest.approx(0.875)
    assert purged["training_prevalence_reference_brier"] == pytest.approx(0.294236, abs=0.000002)
    nest_2022 = cells[2022, "nest", "bird_purged_forward"]
    assert nest_2022["brier_gain_vs_training_reference"] > 0
    assert nest_2022["source_log_score_gain_vs_training_reference"] == pytest.approx(0.184597)
    assert all(x["brier_gain_vs_training_reference"] > 0 for x in out["all_frozen_cells"])
    assert all(x["source_log_score_gain_vs_training_reference"] > 0
               for x in out["all_frozen_cells"] if x["cutoff"] in (2020, 2021))
    assert max(abs(x["recomputed_log_gain_rounding_difference"])
               for x in out["all_frozen_cells"]) < 0.00001
    assert out["original_BOP"] == "empirical_state_prediction_mixed"
    assert out["redkite_external"] == "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"


def test_algebra_simple_known_truth():
    # 2 positives / 3 test records, training q=1/4; no raw source needed.
    p, q = 2 / 3, 1 / 4
    brier_ref = p * (1 - q) ** 2 + (1 - p) * q**2
    assert brier_ref == pytest.approx(0.3958333333333333)
    log_ref = -(p * math.log(q) + (1 - p) * math.log1p(-q))
    assert log_ref > -math.log(0.5)


def test_source_receipt_drift_fails_closed(monkeypatch, tmp_path):
    c, s, r = original()
    copied = tmp_path / "tampered.json"
    copied.write_text(json.dumps(s), encoding="utf-8")
    monkeypatch.setattr(m, "SOURCE", copied)
    with pytest.raises(ValueError, match="PINNED_AGGREGATE_OR_CONTRACT_BLOB_DRIFT"):
        m.load_locked()


def test_changed_class_prior_does_not_silently_reclassify():
    c, s, r = original()
    s = deepcopy(s)
    # Directly alter a rounded train-only reference without refitting models.
    s["first_models"]["all_twelve_cell_means"][9][11] = 0.90
    with pytest.raises(ValueError, match="LOG_SCORE_GAIN_IDENTITY_FAILED"):
        m.analyze(c, s, r)


def test_duplicate_or_missing_cell_fails():
    c, s, r = original()
    s = deepcopy(s)
    s["first_models"]["all_twelve_cell_means"][0] = deepcopy(
        s["first_models"]["all_twelve_cell_means"][1])
    with pytest.raises(ValueError, match="DUPLICATE_OR_UNEXPECTED_CELL"):
        m.analyze(c, s, r)
    s["first_models"]["all_twelve_cell_means"].pop()
    with pytest.raises(ValueError, match="EXPECTED_ALL_TWELVE_CELLS"):
        m.analyze(c, s, r)


def test_claim_promotions_or_test_prevalence_drift_stop():
    c, s, r = original()
    altered_contract = deepcopy(c)
    altered_contract["claims"]["no_future_animal_exchangeability_or_coverage_certificate"] = False
    with pytest.raises(ValueError, match="CLAIM_SCOPE_OR_INPUT_DESIGN_DRIFT"):
        m.analyze(altered_contract, s, r)
    bad = deepcopy(s)
    bad["first_models"]["all_twelve_cell_means"][1][10] += 0.01
    with pytest.raises(ValueError, match="TEST_MAJORITY_ORACLE_INCONSISTENT"):
        m.analyze(c, bad, r)
