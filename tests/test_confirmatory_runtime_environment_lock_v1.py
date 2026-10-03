from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from odsp.confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from odsp.frozen_confirmatory_route import (
    build_frozen_confirmatory_route,
    verify_frozen_confirmatory_route,
)


def _distribution_names(snapshot: dict[str, object]) -> set[str]:
    rows = snapshot["distributions"]
    assert isinstance(rows, list)
    return {str(row["name"]).lower() for row in rows}


def test_environment_snapshot_captures_python_and_external_distributions():
    surface = (
        "odsp.untouched_external_refit_positive_contract_v2."
        "run_untouched_external_refit_positive_contract_v2"
    )
    snapshot = runtime_environment_snapshot_for_surface(surface)
    assert snapshot["python"]["implementation"]
    assert isinstance(snapshot["python"]["major"], int)
    assert isinstance(snapshot["python"]["minor"], int)
    assert "numpy" in snapshot["external_modules"]
    assert "numpy" in _distribution_names(snapshot)


def test_new_frozen_confirmatory_route_includes_runtime_environment_lock():
    route = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )
    assert route["environment_lock_id"] == ENVIRONMENT_LOCK_ID
    snapshot = route["runtime_environment_snapshot"]
    assert snapshot["external_modules"]
    assert snapshot["distributions"]


def test_runtime_rejects_tampered_external_distribution_version():
    frozen = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=2,
    )
    tampered = copy.deepcopy(frozen)
    distributions = tampered["runtime_environment_snapshot"]["distributions"]
    assert distributions
    distributions[0]["version"] = "0.0.0-tampered"
    with pytest.raises(ValueError, match="confirmatory_route"):
        verify_frozen_confirmatory_route(
            tampered,
            validation_design="paired_shared_blocks",
            information_structure="complete_lattice",
            information_block_count=2,
        )


def test_environment_lock_contract_freezes_runtime_dependency_identity():
    payload = json.loads(
        Path("ODSP_CONFIRMATORY_RUNTIME_ENVIRONMENT_LOCK_V1.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == ENVIRONMENT_LOCK_ID
    assert payload["freeze"]["python_implementation_frozen"] is True
    assert payload["freeze"]["python_major_minor_frozen"] is True
    assert payload["freeze"]["external_import_module_names_frozen"] is True
    assert payload["freeze"]["external_distribution_versions_frozen"] is True
    assert payload["runtime"]["exact_snapshot_match_required"] is True
    assert payload["scope"]["platform_and_blas_identity_frozen"] is False
    assert payload["scope"]["bitwise_reproducibility_claimed"] is False
    assert payload["historical_governance"]["post_outcome_retroactive_upgrade_allowed"] is False


def test_routing_contract_requires_environment_identity_for_new_external_freezes():
    payload = json.loads(
        Path("ODSP_CONFIRMATORY_METHOD_ROUTING_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    lock = payload["runtime_environment_identity"]
    assert lock["contract"] == "ODSP_CONFIRMATORY_RUNTIME_ENVIRONMENT_LOCK_V1.json"
    assert lock["environment_lock_id"] == ENVIRONMENT_LOCK_ID
    assert lock["pre_outcome_freeze_required"] is True
    assert lock["runtime_exact_snapshot_match_required"] is True
