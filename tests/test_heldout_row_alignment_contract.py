import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_heldout_row_alignment_contract_is_frozen():
    contract = json.loads((ROOT / "HELDOUT_ROW_ALIGNMENT_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"] == "odsp-heldout-row-alignment-v1"
    definition = contract["definition"]
    assert definition["base_row_ids_are_canonical"] is True
    assert definition["exact_same_unique_order_category"] == "exact_alignment"
    assert definition["same_unique_row_set_different_order_category"] == "reorderable_alignment"
    assert definition["missing_extra_or_duplicate_source_ids_category"] == "row_mismatch"
    assert definition["permutation_maps_source_rows_to_base_order"] is True
    assert definition["row_contents_are_never_used_to_guess_identity"] is True
    assert definition["rows_are_never_silently_dropped_or_imputed"] is True
    assert definition["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 13
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_boundary"].values())
