"""Known-source semantics prove why freezing a CSV is not enough."""
from __future__ import annotations

import json

import pytest

from odsp.validation_roster_field_lineage_v0 import (
    ROUTE_VERSION,
    audit_validation_roster_field_lineage_v0,
)


def _field(field,origin="design_recorded",parents=None,correction=False):
    return {
        "field":field,
        "origin":origin,
        "parents":[] if parents is None else list(parents),
        "corrected_using_outcomes":correction,
        "documentation":f"declared lineage for {field}; not independent external attestation",
    }


def _base():
    return {
        "schema_version":1,
        "lineage_method":ROUTE_VERSION,
        "plan_id":"synthetic-outcome-free-validation-sampling",
        "fields":[
            _field("site_id"),
            _field("habitat"),
            _field("camera_array"),
            _field("uniform_weight"),
        ],
        "used_by_roles":{
            "roster_membership":"site_id",
            "validation_group":"habitat",
            "validation_block":"camera_array",
            "sample_weight":"uniform_weight",
        },
    }


def test_declared_independent_inputs_pass_only_semantic_precheck_not_primary():
    out=audit_validation_roster_field_lineage_v0(_base())
    assert out.selection_lineage_status=="DECLARED_INDEPENDENT_LINEAGE_ONLY_NOT_ATTESTED"
    assert out.affected_roles==()
    assert out.declared_source_lineage_independence_supported is True
    assert out.trusted_external_lineage_attestation_verified is False
    assert out.independently_observed_metadata_values_verified is False
    assert out.outcome_bytes_read is False
    assert out.changes_active_odsp_qualified_routes is False
    assert out.retrospectively_reclassifies_old_ecological_results is False
    assert out.declared_node_count==4
    assert out.actually_used_node_count==4
    json.dumps(out.as_dict(),allow_nan=False)


def test_outcome_columns_in_the_same_csv_do_not_alone_taint_unselected_roster():
    plan=_base()
    plan["fields"].append(_field("sequence_time","observation_derived"))
    result=audit_validation_roster_field_lineage_v0(plan)
    assert result.declared_node_count==5
    assert result.actually_used_node_count==4
    assert result.selection_lineage_status=="DECLARED_INDEPENDENT_LINEAGE_ONLY_NOT_ATTESTED"
    assert result.outcome_paths==()


def test_source_corrected_start_and_end_dates_taint_all_calendar_derived_selection():
    p=_base()
    p["fields"].extend([
        _field("first_image_datetime","observation_derived"),
        _field("last_image_datetime","observation_derived"),
        _field("original_placement_date"),
        _field("original_retrieval_date"),
        _field("curated_start_date","derived",["original_placement_date","first_image_datetime"],True),
        _field("curated_end_date","derived",["original_retrieval_date","last_image_datetime"],True),
        _field("calendar_span","derived",["curated_start_date","curated_end_date"]),
        _field("site_inclusion","derived",["site_id","calendar_span"]),
    ])
    p["used_by_roles"]["roster_membership"]="site_inclusion"
    result=audit_validation_roster_field_lineage_v0(p)
    assert result.selection_lineage_status=="HOLD_OUTCOME_DERIVED_SOURCE_METADATA"
    assert result.outcome_dependent_roles==("roster_membership",)
    assert result.undocumented_roles==()
    assert any(path[0]=="roster_membership" and path[-1]=="first_image_datetime"
               for path in result.outcome_paths)
    assert any(path[-1]=="<outcome-based correction>" for path in result.outcome_paths)
    assert not result.declared_source_lineage_independence_supported


def test_direct_human_value_later_corrected_from_observations_is_not_independent():
    p=_base()
    p["fields"]=[
        (_field("site_id",correction=True) if f["field"]=="site_id" else f)
        for f in p["fields"]
    ]
    out=audit_validation_roster_field_lineage_v0(p)
    assert out.selection_lineage_status=="HOLD_OUTCOME_DERIVED_SOURCE_METADATA"
    assert ("roster_membership","site_id","<outcome-based correction>") in out.outcome_paths


def test_outcome_tainted_weights_and_groups_cannot_hide_behind_independent_roster():
    p=_base()
    p["fields"].extend([
        _field("species_count","observation_derived"),
        _field("activity_weight","derived",["uniform_weight","species_count"]),
    ])
    p["used_by_roles"]["sample_weight"]="activity_weight"
    out=audit_validation_roster_field_lineage_v0(p)
    assert out.outcome_dependent_roles==("sample_weight",)
    assert out.selection_lineage_status=="HOLD_OUTCOME_DERIVED_SOURCE_METADATA"


def test_undocumented_upstream_field_is_a_hold_not_a_negative_result():
    p=_base()
    p["fields"].extend([
        _field("mystery_date","unknown"),
        _field("inclusion","derived",["site_id","mystery_date"]),
    ])
    p["used_by_roles"]["roster_membership"]="inclusion"
    out=audit_validation_roster_field_lineage_v0(p)
    assert out.selection_lineage_status=="HOLD_UNDOCUMENTED_SOURCE_METADATA_LINEAGE"
    assert out.undocumented_roles==("roster_membership",)
    assert out.outcome_dependent_roles==()
    assert out.independently_observed_metadata_values_verified is False


@pytest.mark.parametrize("modify,regex",[
    ("missing_group","required roster roles"),
    ("unknown_role","unknown roster role"),
    ("missing_node","missing field"),
    ("cycle","cycle"),
    ("unresolved_parent","unresolved parent"),
    ("unexplained_derivation","must name its upstream"),
    ("root_with_parent","cannot silently"),
    ("duplicated_field","duplicate field"),
    ("wrong_origin","unsupported field origin"),
    ("invalid_correction","explicit boolean"),
])
def test_schema_and_dag_fail_closed(modify,regex):
    p=_base()
    if modify=="missing_group":
        p["used_by_roles"].pop("validation_group")
    elif modify=="unknown_role":
        p["used_by_roles"]["animal_result"]="habitat"
    elif modify=="missing_node":
        p["used_by_roles"]["validation_block"]="not_existing"
    elif modify=="cycle":
        p["fields"].extend([
            _field("a","derived",["b"]),
            _field("b","derived",["a"]),
        ])
    elif modify=="unresolved_parent":
        p["fields"].append(_field("a","derived",["not_existing"]))
    elif modify=="unexplained_derivation":
        p["fields"].append(_field("a","derived"))
    elif modify=="root_with_parent":
        p["fields"].append(_field("a","design_recorded",["site_id"]))
    elif modify=="duplicated_field":
        p["fields"].append(_field("site_id"))
    elif modify=="wrong_origin":
        p["fields"].append(_field("unknown_origin","independence_assured"))
    elif modify=="invalid_correction":
        p["fields"][0]["corrected_using_outcomes"]="false"
    with pytest.raises(ValueError,match=regex):
        audit_validation_roster_field_lineage_v0(p)


def test_paths_and_digest_are_deterministic_for_identical_declarations():
    p=_base()
    left=audit_validation_roster_field_lineage_v0(p)
    right=audit_validation_roster_field_lineage_v0(json.loads(json.dumps(p)))
    assert left.as_dict()==right.as_dict()
    assert len(left.canonical_manifest_sha256)==64
