import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_serengeti_terminal_receipt_is_positive_and_internally_consistent():
    receipt = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    assert receipt["schema_id"] == "n2-serengeti-terminal-receipt-v1"
    assert receipt["terminal_category"] == "temporal_partition_generalizing"
    assert receipt["transfer_category"] == "generalizing"
    assert receipt["admitted_species_count"] == 17
    assert math.isclose(
        receipt["effective_temporal_states"],
        math.exp(receipt["temporal_information_nats"]),
        rel_tol=0.0,
        abs_tol=1e-10,
    )
    assert receipt["permutation_p_value"] == 0.005
    assert receipt["heldout_group_ids"] == [
        "site-fold-0",
        "site-fold-1",
        "site-fold-2",
    ]
    assert all(gain > 0.0 for gain in receipt["heldout_gains"])
    assert receipt["axis_resolved_state_allowed_for_empirical_n3"] is False


def test_terminal_decision_exactly_matches_validated_receipt():
    receipt = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")
    decision = _load("N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json")
    primary = decision["primary"]

    assert decision["terminal_category"] == receipt["terminal_category"]
    assert decision["validated_result_fingerprint_sha256"] == receipt[
        "result_fingerprint_sha256"
    ]
    assert primary["admitted_species_count"] == receipt["admitted_species_count"]
    assert primary["temporal_information_nats_H_T_given_Site"] == receipt[
        "temporal_information_nats"
    ]
    assert primary["effective_temporal_states"] == receipt["effective_temporal_states"]
    assert primary["species_time_partition_information_nats_I_C_T_given_Site"] == receipt[
        "partition_information_nats"
    ]
    assert primary["permutation_p_value"] == receipt["permutation_p_value"]
    assert primary["heldout_site_fold_gains"] == receipt["heldout_gains"]
    assert primary["heldout_group_ids"] == receipt["heldout_group_ids"]
    assert primary["transfer_category"] == receipt["transfer_category"]


def test_serengeti_terminal_summary_is_not_silently_promoted_to_n3():
    receipt = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")
    decision = _load("N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json")
    handoff = _load("N2_CURRENT_HANDOFF_DECISIONS.json")

    summary = handoff["validated_terminal_summaries_without_state_artifact"][
        "snapshot_serengeti_temporal_lane"
    ]
    assert receipt["transfer_category"] == "generalizing"
    assert summary["terminal_summary_validated"] is True
    assert summary["integrity_pinned_axis_resolved_state_artifact_exists"] is False
    assert summary["n2_to_n3_payload_issued"] is False
    assert summary["axis_resolved_species_state_allowed_for_empirical_n3"] is False
    assert decision["n3_boundary"]["n2_to_n3_payload_issued"] is False
    assert decision["n3_boundary"]["axis_resolved_state_allowed_for_empirical_n3"] is False


def test_root_contract_closes_temporal_gate_without_reopening_other_endpoints():
    contract = _load("CHAPTER_CONTRACT.json")
    temporal = contract["terminal_temporal_partition_state_2026_09_04"]

    assert temporal["terminal_category"] == "temporal_partition_generalizing"
    assert temporal["scientific_gate_unresolved"] is False
    assert temporal["all_three_frozen_site_fold_gains_positive"] is True
    assert temporal["rerun_or_retune_allowed"] is False
    assert temporal["axis_resolved_state_allowed_for_empirical_n3"] is False
    assert temporal["n2_to_n3_payload_issued"] is False
    assert temporal["bat_or_tawaki_reopened"] is False
    assert temporal["gate_e_authorized"] is False


def test_recovery_and_closeout_provenance_are_pinned():
    decision = _load("N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json")
    provenance = decision["execution_provenance"]

    assert provenance["original_authoritative_run"]["workflow_run_id"] == 33726030526
    assert provenance["original_authoritative_run"]["terminal_artifact_count"] == 0
    assert provenance["successful_recovery"]["workflow_run_id"] == 33774650396
    assert provenance["successful_recovery"]["recovered_artifact_id"] == 9901082589
    assert provenance["validated_closeout"]["workflow_run_id"] == 33775057303
    assert provenance["validated_closeout"]["receipt_artifact_id"] == 9901215081
    assert provenance["validated_closeout"]["validator_succeeded"] is True
