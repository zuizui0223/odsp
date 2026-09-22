from __future__ import annotations

import pytest

from odsp._confirmatory_execution_guard import verify_confirmatory_execution_route


def test_independent_external_route_is_verified_with_frozen_evidence_chain():
    receipt = verify_confirmatory_execution_route(
        validation_design="independent_groups",
        information_structure="filtration",
        canonical_surface=(
            "odsp.untouched_external_refit_positive_contract_v2."
            "run_untouched_external_refit_positive_contract_v2"
        ),
        contrast_count=2,
    )
    assert receipt["verified"] is True
    assert receipt["role"] == "primary_confirmatory"
    assert receipt["qualification_key"]
    assert receipt["qualification_evidence"]
    assert receipt["requires_preoutcome_freeze"] is True


def test_unqualified_external_family_fails_closed():
    with pytest.raises(ValueError, match="not a qualified primary confirmatory route|unqualified"):
        verify_confirmatory_execution_route(
            validation_design="independent_groups",
            information_structure="filtration",
            canonical_surface=(
                "odsp.untouched_external_refit_positive_contract_v2."
                "run_untouched_external_refit_positive_contract_v2"
            ),
            contrast_count=3,
        )


def test_runner_surface_must_match_routed_canonical_surface():
    with pytest.raises(ValueError, match="canonical surface mismatch"):
        verify_confirmatory_execution_route(
            validation_design="paired_shared_blocks",
            information_structure="filtration",
            canonical_surface="odsp.some_other_external_runner",
            contrast_count=2,
        )
