from hashlib import sha256

import pytest

from odsp.evaluation_content_provenance import audit_evaluation_content_provenance


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def test_exact_final_content_copy_is_detected():
    final = _digest("final")
    result = audit_evaluation_content_provenance(
        final,
        {
            "candidate_screening": (_digest("dev"), final),
            "model_review": (_digest("model"),),
        },
    )
    assert result.separation_category == "final_evaluation_content_leakage"
    assert result.final_evaluation_content_accessed is True
    assert result.leaking_stage_count == 1
    assert result.final_evaluation_content_match_occurrence_count == 1
    assert result.unique_final_evaluation_content_match_count == 1


def test_clean_digest_ledger_is_content_disjoint_and_duplicates_are_legal():
    duplicate = _digest("dev")
    result = audit_evaluation_content_provenance(
        _digest("final"),
        {"candidate_screening": (duplicate, duplicate)},
    )
    assert result.separation_category == "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
    assert result.final_evaluation_content_accessed is False
    assert result.duplicate_digest_count == 1
    assert result.digests_emitted is False
    assert result.automatic_artifact_hashing is False
    assert result.semantic_equivalence_inferred is False


def test_digest_hex_and_algorithm_tag_case_are_canonicalized():
    final = _digest("final")
    upper = final.upper()
    result = audit_evaluation_content_provenance(
        upper,
        {"review": (final,)},
    )
    assert result.separation_category == "final_evaluation_content_leakage"


def test_invalid_or_wrong_algorithm_digest_is_rejected():
    with pytest.raises(ValueError, match="sha256"):
        audit_evaluation_content_provenance("sha256:bad", {"review": (_digest("x"),)})
    with pytest.raises(ValueError, match="sha256"):
        audit_evaluation_content_provenance("md5:" + "a" * 32, {"review": (_digest("x"),)})


def test_expected_stage_coverage_is_exact():
    with pytest.raises(ValueError, match="missing declared stage"):
        audit_evaluation_content_provenance(
            _digest("final"),
            {"candidate_screening": (_digest("dev"),)},
            expected_stage_names=("candidate_screening", "model_review"),
        )
