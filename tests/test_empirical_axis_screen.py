import json
from pathlib import Path

import pytest

from odsp.empirical_axis_screen import run_architecture_screen

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "N2_V2_ARCHITECTURE_SCREEN.json"
SELECTION = ROOT / "N2_V2_ARCHITECTURE_SELECTION.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_architecture_screen_selects_bat_without_outcomes():
    result = run_architecture_screen(_load(SCREEN), _load(SELECTION))
    assert result.selected_candidate_id == "european_free_tailed_bat_movebank_52nn82r9"
    assert result.outcome_metrics_computed is False
    by_id = {candidate.candidate_id: candidate for candidate in result.candidates}
    assert by_id["european_free_tailed_bat_movebank_52nn82r9"].admitted
    assert by_id["antarctic_petrel_movebank_q206rm6b"].admitted
    assert not by_id["two_banded_plover_zenodo_20748797"].admitted
    assert "effort_semantics_unavailable_without_abstention_rule" in by_id[
        "two_banded_plover_zenodo_20748797"
    ].reasons
    assert "source_axis_or_time_precision_not_preserved" in by_id[
        "two_banded_plover_zenodo_20748797"
    ].reasons


def test_screen_result_contains_no_odsp_biological_outcomes():
    payload = run_architecture_screen(_load(SCREEN), _load(SELECTION)).as_dict()
    serialized = json.dumps(payload, sort_keys=True)
    forbidden = (
        "H(Z|X,Y)",
        "axis_thickness_map",
        "projection_loss",
        "held_out_score",
        "altitude_distribution",
        "effective_states",
    )
    for name in forbidden:
        assert name not in serialized


def test_candidate_universe_cannot_be_changed_silently():
    screen = _load(SCREEN)
    screen["candidates"] = screen["candidates"][:-1]
    with pytest.raises(ValueError, match="universes differ|missing from selection manifest"):
        run_architecture_screen(screen, _load(SELECTION))


def test_declared_selected_candidate_must_follow_frozen_ranking():
    selection = _load(SELECTION)
    selection["selected_candidate_id"] = "antarctic_petrel_movebank_q206rm6b"
    with pytest.raises(ValueError, match="does not match deterministic"):
        run_architecture_screen(_load(SCREEN), selection)
