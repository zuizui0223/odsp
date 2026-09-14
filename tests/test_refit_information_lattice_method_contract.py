from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_refit_information_lattice_method_contract_is_fail_closed():
    contract = json.loads(
        (ROOT / "ODSP_REFIT_INFORMATION_LATTICE_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-refit-information-lattice-v1"
    required = contract["required_structure"]
    assert required["complete_boolean_subset_lattice"] is True
    assert required["same_refit_axis_at_every_node"] is True
    assert required["same_heldout_rows_at_every_node"] is True

    resampling = contract["resampling"]
    assert resampling["one_selected_refit_shared_across_all_group_edge_cells_per_draw"] is True
    assert resampling["same_validation_block_draw_shared_across_edges_within_group"] is True
    assert resampling["refit_variability_divided_by_sqrt_refit_count"] is False

    boundary = contract["scientific_boundaries"]
    assert boundary["refits_assumed_independent"] is False
    assert boundary["reference_fit_can_override_refit_aware_failure"] is False
    assert boundary["best_information_order_can_override_failed_edge"] is False
    assert boundary["shapley_average_can_override_failed_edge"] is False
    assert boundary["refit_average_can_override_failed_edge"] is False
    assert boundary["frozen_empirical_endpoint_rerun"] is False
