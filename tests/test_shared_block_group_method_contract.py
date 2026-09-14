from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shared_block_group_method_contract_keeps_paired_design_explicit():
    contract = json.loads(
        (ROOT / "ODSP_SHARED_BLOCK_GROUP_CERTIFICATION_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-shared-block-group-certification-v1"
    eligibility = contract["eligibility"]
    assert eligibility["same_positive_mass_block_set_in_every_group"] is True
    assert eligibility["unbalanced_block_support_allowed"] is False
    assert eligibility["missing_shared_blocks_imputed"] is False
    assert eligibility["silent_fallback_to_independent_group_bootstrap"] is False

    resampling = contract["resampling"]
    assert resampling["same_block_draw_shared_across_all_groups_and_contrasts"] is True
    assert resampling["validation_group_independence_assumed"] is False
    assert resampling["shared_block_exchangeability_assumed"] is True

    boundary = contract["scientific_boundaries"]
    assert boundary["general_arbitrary_cross_group_dependence_solved"] is False
    assert boundary["unbalanced_cluster_bootstrap_supported"] is False
    assert boundary["paired_block_identity_inferred_from_outcomes"] is False
    assert boundary["frozen_empirical_endpoint_rerun"] is False
