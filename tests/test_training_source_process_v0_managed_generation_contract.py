from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_GENERATION_CONTRACT.json")


def test_managed_source_v0_contract_requires_both_membership_levels():
    p=json.loads(P.read_text(encoding="utf-8"))
    m=p["membership_materialization"]
    assert m["outer_membership_reconstructed_from_frozen_outer_seed"] is True
    assert m["inner_membership_reconstructed_from_outer_membership_and_frozen_inner_seed"] is True
    assert m["outer_membership_digest_must_match_manifest"] is True
    assert m["inner_membership_digest_must_match_manifest"] is True
    assert m["both_memberships_canonicalized_on_original_source_roster"] is True


def test_managed_source_v0_execution_is_balanced_and_outcome_blind():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["execution"]["shell_used"] is False
    assert p["execution"]["one_fit_process_per_source_refit_pair"] is True
    assert p["balanced_design"]["source_draws_equal_outer_weight"] is True
    assert p["balanced_design"]["same_inner_refit_count_under_every_source_draw"] is True
    assert p["inputs"]["validation_outcomes_allowed"] is False
    assert p["boundary"]["route_registered"] is False
