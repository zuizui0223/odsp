from __future__ import annotations

import json
from pathlib import Path

from odsp.independent_c12_support_calibration import GENERATOR_VERSION


RECEIPT = Path("INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json")


def test_independent_c12_support_envelope_receipt_is_frozen():
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["receipt_type"] == "odsp_independent_c12_one_sided_support_envelope"
    assert payload["generator_version"] == GENERATOR_VERSION
    run = payload["first_1000_simulation_run"]
    assert run["github_actions_run_id"] == 37154714389
    assert run["github_actions_job_id"] == 111295642013
    assert run["head_sha"] == "b4b82c66a4b095fcd45121737872d70bd57abd28"
    assert payload["summary"]["qualification_pass"] is True
    assert payload["summary"]["largest_familywise_false_positive_rate"] == 0.04
    assert payload["summary"]["support_anchor_counts"] == [8, 20, 50]
    assert payload["summary"]["group_count_anchor"] == 6
    assert payload["summary"]["contrast_count"] == 12
    assert payload["summary"]["arbitrary_intermediate_or_larger_block_count_proven"] is False
    assert payload["summary"]["arbitrary_group_count_proven"] is False
    assert [row["one_sided_familywise_false_positive_rate"] for row in payload["scenarios"]] == [
        0.003, 0.025, 0.04, 0.001, 0.01, 0.018,
    ]
    assert all(row["acceptance_pass"] for row in payload["scenarios"])
    assert all(row["terminal_false_generalizing_rate"] == 0.0 for row in payload["scenarios"])
