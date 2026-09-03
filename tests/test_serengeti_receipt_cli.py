import json
from pathlib import Path

import pytest

from scripts.validate_n2_serengeti_terminal_result import validate_file


def _unavailable_result(species: str = "species_a") -> dict[str, object]:
    return {
        "lane_id": "n2_serengeti_temporal_partition_v1",
        "source": {
            "consensus_md5": "5ed2d32fd09127c178cf9dca8ccfd623",
            "effort_md5": "27cb42f3feaa0642b17cbde24ba15fbd",
            "timezone": "UTC+03:00_source_local_clock_no_dst",
        },
        "effort_audit": {},
        "event_audit": {},
        "species_admission_audit": {},
        "admitted_species": [species],
        "frozen_rules": {
            "certainty_min": 0.8,
            "independence_minutes": 30,
            "time_bins_hours": [[0, 4], [4, 8], [8, 12], [12, 16], [16, 20], [20, 24]],
            "site_fold": "sha256_siteid_mod_3",
            "min_events": 500,
            "min_sites": 20,
            "min_events_each_fold": 50,
            "permutations": 199,
            "permutation_seed": 20260903,
            "alpha": 0.05,
            "model_species_time_pseudocount": 0.5,
        },
        "outcome_opened": False,
        "terminal_category": "empirical_temporal_partition_unavailable",
        "unavailable_reason": "fewer_than_two_species_passed_frozen_structural_admission",
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_cli_creates_canonical_receipt_then_is_idempotent(tmp_path):
    terminal = tmp_path / "terminal.json"
    receipt = tmp_path / "receipt.json"
    _write_json(terminal, _unavailable_result())

    first = validate_file(terminal, receipt)
    second = validate_file(terminal, receipt)

    assert first["status"] == "created"
    assert second["status"] == "unchanged"
    assert first["terminal_category"] == "empirical_temporal_partition_unavailable"
    assert first["axis_resolved_state_allowed_for_empirical_n3"] is False
    assert len(first["result_fingerprint_sha256"]) == 64

    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert stored["schema_id"] == "n2-serengeti-terminal-receipt-v1"
    assert stored["workflow_run_id"] == 33726030526


def test_existing_different_receipt_cannot_be_overwritten(tmp_path):
    first_terminal = tmp_path / "terminal-a.json"
    second_terminal = tmp_path / "terminal-b.json"
    receipt = tmp_path / "receipt.json"
    _write_json(first_terminal, _unavailable_result("species_a"))
    _write_json(second_terminal, _unavailable_result("species_b"))

    validate_file(first_terminal, receipt)
    with pytest.raises(ValueError, match="already exists with different content"):
        validate_file(second_terminal, receipt)


def test_cli_rejects_non_object_terminal_json(tmp_path):
    terminal = tmp_path / "terminal.json"
    receipt = tmp_path / "receipt.json"
    _write_json(terminal, ["not", "an", "object"])

    with pytest.raises(ValueError, match="root must be an object"):
        validate_file(terminal, receipt)
    assert not receipt.exists()
