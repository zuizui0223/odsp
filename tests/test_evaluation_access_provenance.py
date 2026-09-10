import pytest

from odsp.evaluation_access_provenance import audit_evaluation_access_provenance


def test_clean_and_leaked_access():
    clean = audit_evaluation_access_provenance(
        "final",
        {"ranking": ("dev-a",), "tuning": ("cv-a", "cv-a")},
        expected_stage_names=("tuning", "ranking"),
    )
    assert clean.separation_category == "final_evaluation_not_accessed_in_declared_pre_final_stages"
    assert clean.final_evaluation_accessed is False
    assert clean.duplicate_access_count == 1

    leaked = audit_evaluation_access_provenance(
        "final",
        {"ranking": ("dev-a", "final"), "tuning": ("final", "final")},
    )
    assert leaked.separation_category == "final_evaluation_access_leakage"
    assert leaked.leaking_stage_count == 2
    assert leaked.final_evaluation_access_occurrence_count == 3
    assert leaked.maximum_stage_final_access_count == 2
    assert leaked.accessed_artifact_ids_emitted is False
    assert leaked.ledger_completeness_assumed is False


def test_invalid_ids_and_stage_coverage_fail_closed():
    with pytest.raises(ValueError, match="missing"):
        audit_evaluation_access_provenance(None, {"ranking": ("dev",)})
    with pytest.raises(ValueError, match="at least one artifact"):
        audit_evaluation_access_provenance("final", {"ranking": ()})
    with pytest.raises(ValueError, match="missing declared stage"):
        audit_evaluation_access_provenance("final", {"ranking": ("dev",)}, expected_stage_names=("ranking", "tuning"))
    with pytest.raises(ValueError, match="unexpected extra stage"):
        audit_evaluation_access_provenance("final", {"ranking": ("dev",), "tuning": ("cv",)}, expected_stage_names=("ranking",))


def test_serialized_audit_never_emits_artifact_ids():
    result = audit_evaluation_access_provenance("final", {"ranking": ("final", "dev")}).as_dict()
    forbidden = {"accessed_artifact_ids", "artifact_ids", "final_evaluation_artifact_id"}
    assert forbidden.isdisjoint(result)
    assert all(forbidden.isdisjoint(row) for row in result["stages"])
