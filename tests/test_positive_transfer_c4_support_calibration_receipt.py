from __future__ import annotations

import json
from pathlib import Path

from odsp.positive_transfer_c4_support_calibration import GENERATOR_VERSION


RECEIPT = Path("INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json")


def test_independent_c4_support_envelope_receipt_is_frozen():
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["receipt_type"] == "odsp_independent_c4_one_sided_support_envelope"
    assert payload["generator_version"] == GENERATOR_VERSION
    run = payload["first_1000_simulation_run"]
    assert run["github_actions_run_id"] == 35553098486
    assert run["github_actions_job_id"] == 106191409010
    assert run["head_sha"] == "78bc7c884c271b4d33b2370a1a49af7ba83f9e1c"
    assert payload["summary"]["qualification_pass"] is True
    assert payload["summary"]["largest_familywise_false_positive_rate"] == 0.048
    assert payload["summary"]["support_anchor_counts"] == [8, 20, 50]
    assert payload["summary"]["arbitrary_intermediate_or_larger_block_count_proven"] is False
    assert [row["one_sided_familywise_false_positive_rate"] for row in payload["scenarios"]] == [
        0.015, 0.036, 0.048, 0.003, 0.017, 0.026,
    ]
    assert all(row["acceptance_pass"] for row in payload["scenarios"])
    assert all(row["terminal_false_generalizing_rate"] == 0.0 for row in payload["scenarios"])
