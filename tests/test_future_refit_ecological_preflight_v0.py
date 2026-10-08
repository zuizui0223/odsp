from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from odsp.future_refit_ecological_preflight_v0 import (
    preflight_shared_validation_ecological_roster,
)
from scripts.audit_future_refit_ecological_admission_v0 import (
    ROOT,
    audit_closed_ecological_lanes,
)


def _roster(B: int = 8):
    rows = tuple(f"val-{i:03d}" for i in range(2*B))
    groups = tuple("group0" if i < B else "group1" for i in range(2*B))
    blocks = tuple(f"g{i//B}-site-{i%B:03d}" for i in range(2*B))
    source = tuple(f"source-{i:03d}" for i in range(15))
    refit_ids = tuple(f"refit-{i:03d}" for i in range(20))
    return rows, groups, blocks, source, refit_ids


def _check(rows, groups, blocks, source, ids, **kwargs):
    source_units = kwargs.pop(
        "training_source_unit_ids",
        tuple(f"train-unit-{i:03d}" for i in range(len(source))),
    )
    validation_units = kwargs.pop(
        "validation_unit_ids",
        tuple(f"validation-unit-{b}" for b in blocks),
    )
    return preflight_shared_validation_ecological_roster(
        rows,groups,blocks,source,refit_ids=ids,
        identity_namespace="stable_record_namespace",
        training_source_unit_ids=source_units,
        validation_unit_ids=validation_units,
        physical_unit_kind="camera_site",
        **kwargs,
    )


def test_structural_roster_admission_never_proves_ecological_sampling():
    a = _check(*_roster())
    assert a.structural_status == "STRUCTURALLY_ADMISSIBLE_UNVERIFIED_SAMPLING"
    assert a.refit_count == 20
    assert a.physical_unit_kind == "camera_site"
    assert a.training_validation_physical_unit_overlap_checked
    assert a.within_group_physical_unit_fragmentation_checked
    assert not a.physical_unit_sampling_independence_verified
    assert a.validation_row_count == 16
    assert a.group_count == 2
    assert a.contrast_count == 2
    assert a.validation_block_count_by_group == (("group0",8),("group1",8))
    assert a.training_source_frame_disjoint_checked
    assert not a.validation_sampling_iid_verified
    assert not a.score_bounds_process_wide_verified
    assert not a.model_to_score_provenance_verified
    assert not a.training_process_iid_verified
    assert not a.pre_outcome_freeze_verified
    assert not a.route_primary_qualified
    assert not a.historical_ecological_results_reclassified
    json.dumps(a.as_dict(),allow_nan=False)


def test_entire_source_frame_overlap_even_unselected_source_row_is_forbidden():
    rows,groups,blocks,source,ids=_roster()
    source = source + (rows[0],)
    with pytest.raises(ValueError, match="entire frozen training source"):
        _check(rows,groups,blocks,source,ids)


@pytest.mark.parametrize("variant,match", [
    ("duplicate_validation_id","unique"),
    ("repeat_refit","unique"),
    ("one_group","two validation groups"),
    ("seven_blocks","too few"),
    ("zero_weight_support","too few"),
    ("negative_weight","finite nonnegative"),
    ("few_refits","unique"),
    ("only_two_levels","exactly three"),
])
def test_invalid_ecological_rosters_fail_closed(variant,match):
    rows,groups,blocks,source,ids=_roster()
    kwargs={}
    if variant=="duplicate_validation_id":
        rows=(rows[0],)+rows[0:15]
    elif variant=="repeat_refit":
        ids=(ids[0],)+ids[:-1]
    elif variant=="one_group":
        groups=("group0",)*16
    elif variant=="seven_blocks":
        blocks=(blocks[0],)+blocks[:-1]
    elif variant=="zero_weight_support":
        weights=[1.]*16
        weights[0]=0.
        kwargs["sample_weight"]=weights
    elif variant=="negative_weight":
        weights=[1.]*16
        weights[0]=-1.
        kwargs["sample_weight"]=weights
    elif variant=="few_refits":
        ids=ids[:7]
    elif variant=="only_two_levels":
        kwargs["ordered_level_names"]=("marginal","identity")
    with pytest.raises(ValueError,match=match):
        _check(rows,groups,blocks,source,ids,**kwargs)



def test_distinct_row_ids_cannot_hide_same_train_and_validation_camera():
    rows,groups,blocks,source,ids=_roster()
    source_units=tuple(f"train-unit-{i:03d}" for i in range(len(source)))
    validation_units=list(f"validation-unit-{b}" for b in blocks)
    validation_units[0]=source_units[-1]
    assert not (set(source) & set(rows))
    with pytest.raises(ValueError,match="share a physical sampling unit"):
        _check(rows,groups,blocks,source,ids,
               training_source_unit_ids=source_units,
               validation_unit_ids=validation_units)


def test_same_physical_site_split_across_two_blocks_fails_closed():
    rows,groups,blocks,source,ids=_roster()
    validation_units=list(f"validation-unit-{b}" for b in blocks)
    validation_units[1]=validation_units[0]
    with pytest.raises(ValueError,match="split across distinct validation blocks"):
        _check(rows,groups,blocks,source,ids,
               validation_unit_ids=validation_units)


def test_missing_physical_unit_roster_fails_closed():
    rows,groups,blocks,source,ids=_roster()
    with pytest.raises(ValueError,match="physical unit metadata"):
        _check(rows,groups,blocks,source,ids,
               training_source_unit_ids=("one-site-only",))



def test_existing_ecological_endpoints_are_not_falsely_registered():
    out=audit_closed_ecological_lanes(ROOT)
    assert out["audit_kind"]=="outcome_free_contract_structure_only"
    assert out["outcomes_read"] is False
    assert out["terminal_receipt_content_read"] is False
    assert out["raw_public_data_downloaded"] is False
    assert out["qualified_future_refit_ecological_endpoints"] == 0
    assert out["existing_lanes_audited"] == 4
    assert out["prior_empirical_terminal_categories_reclassified"] is False
    assert len(out["records"])==4
    assert all(row["original_comparison_count"]==1 for row in out["records"])
    assert all(row["already_outcome_opened"] for row in out["records"])
    assert all(row["eligible_iid_blocks_per_group"] is None for row in out["records"])
    assert all(len(row["contract_sha256"])==64 for row in out["records"])
    assert out["records"][0]["heldout_fold_count"]==3
    assert out["records"][1]["heldout_fold_count"]==5
    assert out["records"][2]["sealed_individual_count"]==2
    json.dumps(out,allow_nan=False)


def test_auditor_rejects_frozen_source_contract_semantic_drift(tmp_path: Path):
    contracts=[
        "N2_TEMPORAL_PARTITION_CONTRACT.json",
        "BOP_RODENT_STATE_PREDICTION_CONTRACT.json",
        "N2_BAT_THICKNESS_CONTRACT.json",
        "GATE_D_TAWAKI_CONTRACT.json",
    ]
    terminal_markers=[
        "N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json",
        "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json",
        "N2_BAT_THICKNESS_TERMINAL_DECISION.json",
        "GATE_D_TAWAKI_TERMINAL_RECEIPT.json",
    ]
    for path in contracts:
        shutil.copy2(ROOT/path,tmp_path/path)
    for path in terminal_markers:
        (tmp_path/path).write_text("existing; deliberately not read",encoding="utf-8")
    assert audit_closed_ecological_lanes(tmp_path)["existing_lanes_audited"]==4
    filename=tmp_path/contracts[0]
    obj=json.loads(filename.read_text())
    obj["frozen_preprocessing"]["site_fold_rule"]="newly altered after endpoint"
    filename.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match="Serengeti frozen"):
        audit_closed_ecological_lanes(tmp_path)



def test_snapshot_safari_public_source_screen_cannot_claim_admission():
    # Public site-count discovery is not evidence of iid site selection,
    # outcome-free individual timestamp coverage or per-group power.
    path=ROOT/"ODSP_FUTURE_REFIT_SNAPSHOT_SAFARI_SOURCE_SCREEN_V0.json"
    s=json.loads(path.read_text(encoding="utf-8"))
    assert s["record_type"]=="public_ecological_source_discovery_not_validation_freeze"
    assert s["status"]=="DISCOVERY_ONLY_NOT_ADMITTED"
    assert s["provider_stated"]["location_id_count"]==1824
    assert s["source_overlap"]["has_SER_Snapshot_Serengeti_component"]
    assert s["source_overlap"]["require_exclude_all_SER_locations_if_training_source_contains_prior_Serengeti"]
    assert s["outcome_knowledge_before_specific_freeze"]["provider_page_aggregate_label_counts_visible"]
    assert s["outcome_knowledge_before_specific_freeze"]["individual_image_timestamps_opened_by_this_screen"] is False
    assert s["outcome_knowledge_before_specific_freeze"]["all_historical_nonaccess_proved"] is False
    assert s["remaining_source_eligibility_unknown"]["camera_site_iid_sampling_law_proven"] is False
    assert s["remaining_source_eligibility_unknown"]["valid_per_sequence_or_per_image_datetime_coverage"] is None
    assert s["remaining_source_eligibility_unknown"]["outcomes_untouched_frozen"] is False
    assert s["primary_confirmatory"] is False
    assert s["route_registry_updated"] is False
