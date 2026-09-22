from __future__ import annotations

import json
from pathlib import Path

from odsp.independent_positive_lattice_family_calibration import GENERATOR_VERSION


RECEIPT = Path("INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json")


def test_independent_directional_lattice_family_receipt_is_frozen():
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["receipt_type"] == "odsp_independent_directional_lattice_family_null_calibration"
    assert payload["generator_version"] == GENERATOR_VERSION
    assert payload["first_1000_simulation_run"]["head_sha"] == "68cc06ba9f65e32ddf1f76864836615c9d1f87ca"
    assert payload["summary"]["qualification_pass"] is True
    assert payload["summary"]["largest_familywise_false_positive_rate"] == 0.046
    assert payload["summary"]["three_information_block_complete_lattice_qualified"] is True
    assert payload["summary"]["four_or_more_information_block_complete_lattice_qualified"] is False
    assert [row["contrast_count"] for row in payload["scenarios"]] == [12, 12, 12]
    assert [row["one_sided_familywise_false_positive_rate"] for row in payload["scenarios"]] == [
        0.017,
        0.046,
        0.006,
    ]
    assert all(row["acceptance_pass"] for row in payload["scenarios"])
    assert all(row["terminal_false_generalizing_rate"] == 0.0 for row in payload["scenarios"])
