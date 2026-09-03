import json
from pathlib import Path

import pytest

from odsp.handoff_payload import validate_n2_to_n3_payload


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_bat_n3_payload_validates_and_remains_descriptive_only():
    payload = json.loads((ROOT / "N2_BAT_N3_HANDOFF_PAYLOAD.json").read_text())

    assert validate_n2_to_n3_payload(payload) == payload["fingerprint"]
    assert payload["handoff"]["handoff_category"] == "descriptive_projection_only"
    assert payload["handoff"]["axis_resolved_species_state_allowed_for_empirical_n3"] is False
    assert payload["state_artifact"] is None


def test_frozen_bat_payload_matches_terminal_numerics():
    payload = json.loads((ROOT / "N2_BAT_N3_HANDOFF_PAYLOAD.json").read_text())
    terminal = json.loads((ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json").read_text())

    assert payload["projection_summary"]["H_Z_given_XY_nats"] == pytest.approx(
        terminal["primary"]["information_nats_H_Z_given_XY"]
    )
    assert payload["projection_summary"]["effective_vertical_states"] == pytest.approx(
        terminal["primary"]["effective_vertical_states"]
    )
    assert payload["transferability"]["independent_gains"] == pytest.approx(
        [
            score["mean_log_score_gain"]
            for score in terminal["primary"]["sealed_individual_scores"]
        ]
    )
