from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_FREEZE_MANIFEST_CONTRACT.json")


def test_source_v0_provenance_contract_preserves_nested_process_identity():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["source_population_boundary"]["outer_source_draw_is_bootstrap_draw_from_frozen_roster"] is True
    assert p["source_population_boundary"]["outer_source_draw_is_new_independent_ecological_sample"] is False
    assert p["source_population_boundary"]["unknown_ecological_superpopulation_inference_claimed"] is False
    assert p["nested_inner_resampling"]["inner_refit_count_balanced_across_sources"] is True
    assert p["schedule"]["outer_membership_sha256_per_source_frozen"] is True
    assert p["schedule"]["inner_membership_sha256_per_source_refit_frozen"] is True


def test_source_v0_provenance_requires_full_original_frame_separation():
    p=json.loads(P.read_text(encoding="utf-8"))
    s=p["validation_separation"]
    assert s["entire_original_frozen_source_roster_must_be_disjoint_from_validation_rows"] is True
    assert s["checking_only_realized_outer_draws_is_sufficient"] is False
    assert s["checking_only_realized_inner_refits_is_sufficient"] is False
    assert p["routing"]["primary_confirmatory_now"] is False
