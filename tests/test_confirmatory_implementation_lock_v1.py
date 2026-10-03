from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from odsp.confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from odsp.frozen_confirmatory_route import (
    build_frozen_confirmatory_route,
    verify_frozen_confirmatory_route,
)


def _paths(snapshot: object) -> list[str]:
    assert isinstance(snapshot, list)
    return [str(row["path"]) for row in snapshot]


def test_independent_external_route_snapshot_reaches_statistical_core():
    route = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )
    assert route["implementation_lock_id"] == IMPLEMENTATION_LOCK_ID
    paths = _paths(route["implementation_source_snapshot"])
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))
    for required in (
        "odsp/untouched_external_refit_positive_contract_v2.py",
        "odsp/frozen_confirmatory_route.py",
        "odsp/refit_positive_information_transfer.py",
        "odsp/information_transfer_positive_v2.py",
        "odsp/positive_transfer_bootstrap_t.py",
        "odsp/bootstrap_t.py",
    ):
        assert required in paths


def test_paired_external_lattice_snapshot_reaches_shared_block_core():
    route = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=3,
    )
    paths = _paths(route["implementation_source_snapshot"])
    for required in (
        "odsp/untouched_external_refit_shared_block_positive_lattice_contract_v4.py",
        "odsp/refit_positive_lattice_robustness.py",
        "odsp/shared_block_positive_information.py",
        "odsp/shared_block_positive_certification.py",
        "odsp/bootstrap_t.py",
    ):
        assert required in paths


def test_implementation_snapshot_hashes_exact_source_bytes():
    surface = (
        "odsp.untouched_external_refit_positive_contract_v2."
        "run_untouched_external_refit_positive_contract_v2"
    )
    snapshot = implementation_source_snapshot_for_surface(surface)
    assert snapshot
    for row in snapshot:
        path = Path(str(row["path"]))
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_runtime_rejects_tampered_implementation_digest():
    frozen = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )
    tampered = json.loads(json.dumps(frozen))
    tampered["implementation_source_snapshot"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="confirmatory_route"):
        verify_frozen_confirmatory_route(
            tampered,
            validation_design="independent_groups",
            information_structure="filtration",
            contrast_count=2,
        )


def test_surface_snapshot_fails_closed_outside_odsp_package():
    with pytest.raises(ValueError, match="odsp"):
        implementation_source_snapshot_for_surface("thirdparty.module.run")
