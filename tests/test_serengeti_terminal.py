import copy
import math

import pytest

from odsp.serengeti_terminal import validate_serengeti_terminal_result


def _frozen_base() -> dict[str, object]:
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
        "admitted_species": ["species_a", "species_b"],
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
    }


def _generalizing_result() -> dict[str, object]:
    result = _frozen_base()
    result.update(
        {
            "outcome_opened": True,
            "support_shape_site_species_time": [30, 2, 6],
            "admitted_site_count": 30,
            "admitted_event_count": 4000,
            "temporal_profile": {
                "context_axes": [0],
                "identity_axis": 1,
                "time_axis": 2,
                "temporal_information_given_context_nats": math.log(4.0),
                "effective_temporal_states_given_context": 4.0,
                "identity_information_given_context_nats": 0.6,
                "joint_identity_time_information_given_context_nats": math.log(4.0) + 0.1,
                "identity_time_partition_information_nats": 0.5,
            },
            "permutation_null": {
                "draws": 199,
                "mean_nats": 0.1,
                "q50_nats": 0.1,
                "q95_nats": 0.2,
                "max_nats": 0.3,
            },
            "heldout_site_fold_gains": [0.20, 0.10, 0.05],
            "decision": {
                "observed_partition_information_nats": 0.5,
                "null_draw_count": 199,
                "permutation_p_value": 0.005,
                "alpha": 0.05,
                "heldout_gains": [0.20, 0.10, 0.05],
                "transfer_category": "generalizing",
                "terminal_category": "temporal_partition_generalizing",
            },
            "terminal_category": "temporal_partition_generalizing",
            "claim_boundary": {
                "measured_object": "camera-detected species-time partition under source clock time and declared effort weighting",
                "true_activity_niche_partition_identified": False,
                "interspecific_displacement_causality_identified": False,
                "solar_time_partition_identified": False,
                "bat_endpoint_reinterpreted": False,
            },
        }
    )
    return result


def test_old_runner_generalizing_json_reconstructs_explicit_grouped_receipt():
    receipt = validate_serengeti_terminal_result(_generalizing_result())

    assert receipt.terminal_category == "temporal_partition_generalizing"
    assert receipt.heldout_group_ids == (
        "site-fold-0",
        "site-fold-1",
        "site-fold-2",
    )
    assert receipt.heldout_gains == pytest.approx((0.20, 0.10, 0.05))
    assert receipt.transfer_category == "generalizing"
    assert receipt.axis_resolved_state_allowed_for_empirical_n3 is False
    assert receipt.n3_reason_code == (
        "generalizing_terminal_summary_has_no_integrity_pinned_state_artifact"
    )
    assert len(receipt.result_fingerprint_sha256) == 64


def test_unavailable_result_remains_unopened_and_nonpromoting():
    result = _frozen_base()
    result["admitted_species"] = ["species_a"]
    result.update(
        {
            "outcome_opened": False,
            "terminal_category": "empirical_temporal_partition_unavailable",
            "unavailable_reason": "fewer_than_two_species_passed_frozen_structural_admission",
        }
    )

    receipt = validate_serengeti_terminal_result(result)
    assert receipt.outcome_opened is False
    assert receipt.transfer_category is None
    assert receipt.heldout_gains == ()
    assert receipt.axis_resolved_state_allowed_for_empirical_n3 is False
    assert receipt.n3_reason_code == "temporal_lane_unavailable"


def test_terminal_category_cannot_disagree_with_reconstructed_decision():
    result = _generalizing_result()
    result["terminal_category"] = "temporal_partition_present_not_generalizing"
    with pytest.raises(ValueError, match="terminal_category"):
        validate_serengeti_terminal_result(result)


def test_frozen_pseudocount_drift_fails_closed():
    result = _generalizing_result()
    result["frozen_rules"]["model_species_time_pseudocount"] = 1.0
    with pytest.raises(ValueError, match="pseudocount"):
        validate_serengeti_terminal_result(result)


def test_effective_temporal_state_mismatch_fails_closed():
    result = _generalizing_result()
    result["temporal_profile"]["effective_temporal_states_given_context"] = 5.0
    with pytest.raises(ValueError, match="exp"):
        validate_serengeti_terminal_result(result)


def test_top_level_and_decision_fold_gains_must_match():
    result = _generalizing_result()
    result["decision"]["heldout_gains"][2] = -0.05
    with pytest.raises(ValueError, match="disagree"):
        validate_serengeti_terminal_result(result)


def test_payload_fingerprint_changes_when_result_content_changes():
    first = validate_serengeti_terminal_result(_generalizing_result())
    changed = copy.deepcopy(_generalizing_result())
    changed["admitted_event_count"] = 4001
    second = validate_serengeti_terminal_result(changed)
    assert first.result_fingerprint_sha256 != second.result_fingerprint_sha256
