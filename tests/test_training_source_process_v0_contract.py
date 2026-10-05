from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_CONTRACT.json")


def _payload():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_source_process_v0_is_new_unqualified_route():
    p=_payload()
    assert p["status"] == "experimental_prequalification"
    assert p["routing"]["new_route_required"] is True
    assert p["routing"]["reuse_predeclared_training_process_route_key"] is False
    assert p["routing"]["register_before_qualification"] is False
    assert p["routing"]["primary_confirmatory_now"] is False
    assert p["relationship_to_v5"]["v5_results_reclassified"] is False


def test_source_process_v0_preserves_nested_not_pooled_refits():
    p=_payload()
    d=p["dependence_structure"]
    assert d["inner_refits"] == "nested within outer source draw"
    assert d["inner_refits_pooled_as_independent_outer_draws"] is False
    assert d["validation_sample_size_multiplied_by_inner_refit_count"] is False
    c=p["candidate_reduction"]
    assert c["effective_training_side_cluster_count"] == (
        "number of outer source draws S, not S times R"
    )
    assert c["outer_source_draw_weighting"].startswith("equal weight")


def test_source_process_v0_does_not_claim_source_superpopulation():
    p=_payload()
    b=p["scientific_boundary"]
    assert b["outer_source_process_is_process_defined"] is True
    assert b["original_ecological_source_superpopulation_generalization_claimed"] is False
    assert b["individual_future_source_sample_success_probability_claimed"] is False


def test_source_process_v0_requires_new_prospective_qualification():
    p=_payload()
    q=p["qualification_plan"]
    assert q["must_be_prospective"] is True
    assert q["maximum_accepted_component_rate"] == 0.06378404875209022
    assert q["strong_power_shift_oracle_standard_errors"] == 5.0
    assert q["minimum_strong_terminal_power"] == 0.8
    assert q["failure_may_not_be_rescued_by_posthoc_threshold_change"] is True
