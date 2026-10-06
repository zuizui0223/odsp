from __future__ import annotations
import json
from pathlib import Path

P=Path("TRAINING_SOURCE_PROCESS_V0_SUPPORT_ENVELOPE_RECEIPT.json")


def test_source_v0_support_receipt_freezes_official_pass():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["support_head_sha"] == "827f84f5205f87a73697b7352d012f78e61b3ee8"
    assert p["official_run"]["github_actions_run_id"] == 37392498151
    assert p["official_run"]["qualification_pass"] is True
    assert p["acceptance"]["largest_observed_component_rate"] == 0.051
    assert p["acceptance"]["all_five_support_scenarios_pass"] is True
    assert max(p["scenarios"].values()) <= p["acceptance"]["maximum_accepted_component_rate"]


def test_source_v0_support_does_not_promote_route_by_itself():
    q=json.loads(P.read_text(encoding="utf-8"))["qualification_boundary"]
    assert q["statistical_qualification_sufficient_for_primary_promotion"] is False
    assert q["outer_source_process_provenance_still_required"] is True
    assert q["managed_nested_generation_still_required"] is True
    assert q["route_registered"] is False
