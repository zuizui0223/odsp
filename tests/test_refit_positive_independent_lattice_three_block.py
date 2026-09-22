from __future__ import annotations

import itertools

import numpy as np
import pytest

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.information_lattice import InformationBlock
from odsp.refit_information_lattice import RefitInformationLatticeNodeScores
from odsp.refit_positive_independent_lattice_robustness import (
    certify_all_refit_independent_positive_information_lattice_v2,
)


def _design(group_count: int = 3, blocks_per_group: int = 8):
    groups: list[str] = []
    blocks: list[str] = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index:02d}")
    return groups, blocks


def _blocks(names: tuple[str, ...]):
    return tuple(InformationBlock(name=name, variables=(name.lower(),)) for name in names)


def _subsets(names: tuple[str, ...]):
    for size in range(len(names) + 1):
        yield from itertools.combinations(names, size)


def _nodes(
    names: tuple[str, ...],
    mappings: list[dict[tuple[str, ...], float]],
    n: int,
):
    return tuple(
        RefitInformationLatticeNodeScores(
            blocks=subset,
            score=np.asarray([[mapping[subset]] * n for mapping in mappings], dtype=float),
        )
        for subset in _subsets(names)
    )


def test_all_refit_three_block_independent_lattice_supports_universal_paths():
    groups, resampling_blocks = _design()
    names = ("A", "B", "C")
    mapping = {subset: 0.3 * len(subset) for subset in _subsets(names)}
    result = certify_all_refit_independent_positive_information_lattice_v2(
        _nodes(names, [mapping, mapping, mapping], len(groups)),
        _blocks(names),
        groups,
        blocks=resampling_blocks,
        refit_ids=("r2", "r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=101,
    )

    assert result.refit_ids == ("r0", "r1", "r2")
    assert result.information_block_count == 3
    assert result.edge_count == 12
    assert result.calibrated_family_size_edge_count == 12
    assert result.total_admissible_path_count == 6
    assert result.all_refit_robust_full_transfer_path_count == 6
    assert result.all_refit_certified_path_status == "universal_full_transfer"
    assert all(row.category == "robust_across_refits" for row in result.edges)


def test_different_three_block_paths_across_refits_cannot_form_global_path():
    groups, resampling_blocks = _design()
    names = ("A", "B", "C")
    r0 = {
        (): 0.0,
        ("A",): 0.4,
        ("B",): -0.2,
        ("C",): -0.2,
        ("A", "B"): 0.8,
        ("A", "C"): -0.3,
        ("B", "C"): -0.3,
        ("A", "B", "C"): 1.2,
    }
    r1 = {
        (): 0.0,
        ("A",): -0.2,
        ("B",): -0.2,
        ("C",): 0.4,
        ("A", "B"): -0.3,
        ("A", "C"): -0.3,
        ("B", "C"): 0.8,
        ("A", "B", "C"): 1.2,
    }
    result = certify_all_refit_independent_positive_information_lattice_v2(
        _nodes(names, [r0, r1], len(groups)),
        _blocks(names),
        groups,
        blocks=resampling_blocks,
        refit_ids=("r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=103,
    )

    assert all(row.robust_full_transfer_path_count >= 1 for row in result.per_refit)
    assert result.all_refit_robust_full_transfer_path_count == 0
    assert result.all_refit_certified_path_status == "no_full_transfer"
    assert result.different_refit_paths_can_be_combined is False


def test_four_block_all_refit_independent_lattice_remains_unqualified():
    groups, resampling_blocks = _design()
    names = ("A", "B", "C", "D")
    mapping = {subset: 0.3 * len(subset) for subset in _subsets(names)}
    with pytest.raises(ValueError, match="2 or 3 information blocks"):
        certify_all_refit_independent_positive_information_lattice_v2(
            _nodes(names, [mapping, mapping], len(groups)),
            _blocks(names),
            groups,
            blocks=resampling_blocks,
            refit_ids=("r0", "r1"),
            minimum_refits=2,
            bootstrap_draws=500,
            minimum_blocks_per_group=8,
        )


def test_router_promotes_fixed_set_three_block_independent_lattice():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=3,
    )
    assert route.role == "primary_confirmatory"
    assert route.edge_count == 12
    assert route.canonical_surface == (
        "odsp.refit_positive_independent_lattice_robustness."
        "certify_all_refit_independent_positive_information_lattice_v2"
    )

    external = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert external.role == "unqualified"
