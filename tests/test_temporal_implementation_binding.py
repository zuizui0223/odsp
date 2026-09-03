import json
from pathlib import Path


def _read_json(name: str) -> dict[str, object]:
    return json.loads(Path(name).read_text(encoding="utf-8"))


def test_temporal_binding_preserves_frozen_scientific_estimand():
    binding = _read_json("N2_TEMPORAL_PARTITION_IMPLEMENTATION_BINDING.json")
    assert binding["lane_id"] == "n2_serengeti_temporal_partition_v1"
    assert binding["frozen_scientific_contract"] == "N2_TEMPORAL_PARTITION_CONTRACT.json"
    assert binding["scientific_estimand_changed"] is False
    assert binding["frozen_thresholds_changed"] is False
    assert binding["frozen_time_bins_changed"] is False
    assert binding["frozen_species_admission_changed"] is False
    assert binding["frozen_pseudocount_changed"] is False


def test_temporal_binding_requires_fold_specific_cross_fitting():
    binding = _read_json("N2_TEMPORAL_PARTITION_IMPLEMENTATION_BINDING.json")
    design = binding["cross_fitted_design"]
    assert design["group_ids"] == ["site-fold-0", "site-fold-1", "site-fold-2"]
    assert design["model_species_time_pseudocount"] == 0.5
    assert design["gain_tolerance"] == 0.0
    assert design["pooled_event_mass_can_override_group_failure"] is False

    api = binding["implementation_api"]
    assert api["generic_cross_fitted_scorer"].endswith(
        "score_crossfitted_independent_groups"
    )
    assert api["temporal_cross_fitted_scorer"].endswith(
        "score_identity_temporal_crossfitted_groups"
    )
    assert api["decision_serializes_group_ids"] is True
    assert api["decision_serializes_gain_tolerance"] is True


def test_binding_does_not_authorize_second_outcome_run_or_rescue():
    binding = _read_json("N2_TEMPORAL_PARTITION_IMPLEMENTATION_BINDING.json")
    workflow = binding["authoritative_terminal_workflow"]
    assert workflow["run_id"] == 33726030526
    assert workflow["rerun_authorized_by_this_binding"] is False

    boundaries = binding["hard_boundaries"]
    assert boundaries["queued_authoritative_run_may_be_replaced_post_outcome"] is False
    assert boundaries["bat_endpoint_reopened"] is False
    assert boundaries["tawaki_endpoint_reopened"] is False
    assert boundaries["gate_e_reopened"] is False
