from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.information_lattice import InformationBlock, InformationLatticeNodeScore
from odsp.information_lattice_positive_v2 import certify_positive_information_lattice_v2


def _rows(group_count: int = 3, blocks_per_group: int = 20):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index:02d}")
    return tuple(groups), tuple(blocks)


def _blocks(names: tuple[str, ...]):
    return tuple(InformationBlock(name, (name.lower(),)) for name in names)


def _nodes(names: tuple[str, ...], n: int):
    return tuple(
        InformationLatticeNodeScore(subset, [0.25 * len(subset)] * n)
        for size in range(len(names) + 1)
        for subset in itertools.combinations(names, size)
    )


def test_three_block_independent_positive_lattice_uses_twelve_edge_family():
    groups, resampling_blocks = _rows()
    names = ("A", "B", "C")
    result = certify_positive_information_lattice_v2(
        _nodes(names, len(groups)),
        _blocks(names),
        groups,
        blocks=resampling_blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=91,
    )
    assert result.edge_count == 12
    assert result.one_sided_bootstrap_t_audit.contrast_count == 12
    assert result.total_admissible_path_count == 6
    assert result.robust_full_transfer_path_count == 6
    assert result.certified_path_status == "universal_full_transfer"
    assert result.calibrated_family_size_edge_count == 12
    assert result.qualification_inherited_from_four_contrast_panel is False
    assert result.qualification_inherited_from_twelve_contrast_panel is True


def test_four_block_independent_positive_lattice_remains_unqualified():
    groups, resampling_blocks = _rows()
    names = ("A", "B", "C", "D")
    with pytest.raises(ValueError, match="2 or 3 information blocks"):
        certify_positive_information_lattice_v2(
            _nodes(names, len(groups)),
            _blocks(names),
            groups,
            blocks=resampling_blocks,
            bootstrap_draws=500,
            minimum_blocks_per_group=8,
        )


def test_router_promotes_fixed_score_three_block_independent_lattice_only_after_calibration():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=3,
    )
    assert route.role == "primary_confirmatory"
    assert route.edge_count == 12
    assert route.canonical_surface == (
        "odsp.information_lattice_positive_v2.certify_positive_information_lattice_v2"
    )

    refit = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=3,
    )
    assert refit.role == "unqualified"

    larger = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=4,
    )
    assert larger.role == "unqualified"
    assert larger.edge_count == 32


def test_machine_contract_freezes_independent_four_and_twelve_edge_scope():
    payload = json.loads(
        Path("ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["qualified_information_block_counts"] == [2, 3]
    assert payload["qualified_edge_counts"] == [4, 12]
    assert payload["unqualified_next_edge_count"] == 32
    assert payload["qualification_sources"]["twelve_edge"]["receipt"] == (
        "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json"
    )
    assert payload["boundaries"]["upstream_refit_uncertainty_included"] is False
    assert payload["boundaries"]["untouched_external_validation_included"] is False
