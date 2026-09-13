from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_information_lattice_method_contract_prevents_order_cherry_picking():
    contract = json.loads(
        (ROOT / "ODSP_INFORMATION_LATTICE_AUDIT_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["schema_version"] == 1
    assert contract["input_requirements"]["subset_score_table"].startswith("one held-out score vector for every one of the 2^m subsets")
    assert contract["path_rule"].startswith("a full path succeeds only when every consecutive edge")
    assert contract["shapley_role"]["can_override_failed_edge"] is False
    assert contract["shapley_role"]["claimed_as_novel"] is False
    assert contract["familywise_certification"]["global_studentized_max_t"] is True
    assert contract["familywise_certification"]["same_block_draw_shared_across_edges_within_group"] is True
    assert contract["scientific_boundaries"]["best_order_selected_from_heldout_outcomes"] is False
    assert contract["scientific_boundaries"]["upstream_refit_uncertainty_included"] is False
