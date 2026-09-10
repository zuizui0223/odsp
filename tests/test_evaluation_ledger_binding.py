import pytest

from odsp.evaluation_ledger_binding import audit_evaluation_ledger_binding


def _digest(char: str) -> str:
    return "sha256:" + char * 64


def _fixture():
    manifest = {
        "final": _digest("a"),
        "x": _digest("b"),
        "y": _digest("c"),
    }
    ids = {"screening": ("x", "x", "y")}
    digests = {"screening": (_digest("b"), _digest("b"), _digest("c"))}
    return manifest, ids, digests


def test_clean_ledgers_are_consistently_bound():
    manifest, ids, digests = _fixture()
    result = audit_evaluation_ledger_binding(
        "final", _digest("a"), manifest, ids, digests
    )
    assert result.ledger_binding_consistent is True
    assert result.separation_category == "evaluation_ledgers_consistently_bound"
    assert result.mismatched_stage_count == 0
    assert result.binding_discrepancy_occurrence_count == 0
    assert result.duplicate_artifact_id_access_count == 1
    assert result.duplicate_digest_access_count == 1


def test_final_binding_mismatch_is_fail_closed():
    manifest, ids, digests = _fixture()
    result = audit_evaluation_ledger_binding(
        "final", _digest("d"), manifest, ids, digests
    )
    assert result.final_evaluation_binding_match is False
    assert result.ledger_binding_consistent is False
    assert result.separation_category == "evaluation_ledger_binding_mismatch"


def test_stage_digest_substitution_is_detected():
    manifest, ids, digests = _fixture()
    bad = {"screening": (_digest("b"), _digest("b"), _digest("b"))}
    result = audit_evaluation_ledger_binding(
        "final", _digest("a"), manifest, ids, bad
    )
    assert result.final_evaluation_binding_match is True
    assert result.ledger_binding_consistent is False
    assert result.mismatched_stage_count == 1
    assert result.binding_discrepancy_occurrence_count == 1
    assert result.stages[0].status == "stage_binding_mismatch"


def test_unknown_accessed_id_is_rejected():
    manifest, _ids, digests = _fixture()
    with pytest.raises(ValueError, match="missing from artifact_digest_by_id"):
        audit_evaluation_ledger_binding(
            "final",
            _digest("a"),
            manifest,
            {"screening": ("unknown",)},
            {"screening": (_digest("b"),)},
        )


def test_stage_coverage_mismatch_is_rejected():
    manifest, ids, _digests = _fixture()
    with pytest.raises(ValueError, match="stage coverage must exactly match"):
        audit_evaluation_ledger_binding(
            "final",
            _digest("a"),
            manifest,
            ids,
            {"other": (_digest("b"),)},
        )
