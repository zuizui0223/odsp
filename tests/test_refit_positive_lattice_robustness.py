from __future__ import annotations

import itertools

import numpy as np
import pytest

from odsp.information_lattice import InformationBlock
from odsp.refit_information_lattice import RefitInformationLatticeNodeScores
from odsp.refit_positive_lattice_robustness import (
    certify_all_refit_shared_block_positive_information_lattice_v2,
)


def _design(group_count: int = 3, shared_block_count: int = 8):
    groups: list[str] = []
    shared_blocks: list[str] = []
    for group_index in range(group_count):
        for block_index in range(shared_block_count):
            groups.append(f"g{group_index}")
            shared_blocks.append(f"b{block_index}")
    return groups, shared_blocks


def _blocks(names: tuple[str, ...]):
    return tuple(InformationBlock(name=name, variables=(name.lower(),)) for name in names)


def _all_subsets(names: tuple[str, ...]):
    for size in range(len(names) + 1):
        yield from itertools.combinations(names, size)


def _constant_nodes(
    names: tuple[str, ...],
    values_by_refit: list[dict[tuple[str, ...], float]],
    n: int,
):
    nodes: list[RefitInformationLatticeNodeScores] = []
    for subset in _all_subsets(names):
        matrix = np.asarray(
            [[mapping[subset]] * n for mapping in values_by_refit],
            dtype=float,
        )
        nodes.append(RefitInformationLatticeNodeScores(blocks=subset, score=matrix))
    return nodes


def test_two_block_lattice_all_refits_support_all_paths():
    groups, shared = _design()
    names = ("A", "B")
    values = []
    for _ in range(3):
        values.append(
            {
                (): 0.0,
                ("A",): 0.4,
                ("B",): 0.4,
                ("A", "B"): 0.8,
            }
        )
    result = certify_all_refit_shared_block_positive_information_lattice_v2(
        _constant_nodes(names, values, len(groups)),
        _blocks(names),
        groups,
        shared,
        refit_ids=("r2", "r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.refit_ids == ("r0", "r1", "r2")
    assert result.information_block_count == 2
    assert result.edge_count == 4
    assert result.total_admissible_path_count == 2
    assert result.all_refit_robust_full_transfer_path_count == 2
    assert result.all_refit_certified_path_status == "universal_full_transfer"
    assert all(row.category == "robust_across_refits" for row in result.edges)
    assert result.different_refit_paths_can_be_combined is False
    assert result.refit_population_generalization_claimed is False


def test_different_successful_paths_across_refits_do_not_form_global_path():
    groups, shared = _design()
    names = ("A", "B")
    values = [
        {
            (): 0.0,
            ("A",): 0.4,
            ("B",): -0.1,
            ("A", "B"): 0.8,
        },
        {
            (): 0.0,
            ("A",): -0.1,
            ("B",): 0.4,
            ("A", "B"): 0.8,
        },
    ]
    result = certify_all_refit_shared_block_positive_information_lattice_v2(
        _constant_nodes(names, values, len(groups)),
        _blocks(names),
        groups,
        shared,
        refit_ids=("r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert tuple(row.robust_full_transfer_path_count for row in result.per_refit) == (1, 1)
    assert result.all_refit_robust_full_transfer_path_count == 0
    assert result.all_refit_certified_path_status == "no_full_transfer"
    assert result.different_refit_paths_can_be_combined is False
    base_edges = [row for row in result.edges if not row.lower_blocks]
    assert all(row.category == "not_robust_across_refits" for row in base_edges)


def test_three_block_lattice_is_supported_at_calibrated_12_edge_family_size():
    groups, shared = _design()
    names = ("A", "B", "C")
    mapping = {
        subset: 0.3 * len(subset)
        for subset in _all_subsets(names)
    }
    result = certify_all_refit_shared_block_positive_information_lattice_v2(
        _constant_nodes(names, [mapping, mapping], len(groups)),
        _blocks(names),
        groups,
        shared,
        refit_ids=("r1", "r0"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.information_block_count == 3
    assert result.edge_count == 12
    assert result.calibrated_family_size_edge_count == 12
    assert result.total_admissible_path_count == 6
    assert result.all_refit_robust_full_transfer_path_count == 6
    assert result.all_refit_certified_path_status == "universal_full_transfer"


def test_four_block_lattice_hard_stops_outside_calibrated_family_size():
    groups, shared = _design()
    names = ("A", "B", "C", "D")
    mapping = {subset: 0.2 * len(subset) for subset in _all_subsets(names)}
    with pytest.raises(ValueError, match="qualified only for 2 or 3 information blocks"):
        certify_all_refit_shared_block_positive_information_lattice_v2(
            _constant_nodes(names, [mapping, mapping], len(groups)),
            _blocks(names),
            groups,
            shared,
            refit_ids=("r0", "r1"),
            minimum_refits=2,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_insufficient_refits_makes_global_lattice_unavailable():
    groups, shared = _design()
    names = ("A", "B")
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    result = certify_all_refit_shared_block_positive_information_lattice_v2(
        _constant_nodes(names, [mapping, mapping], len(groups)),
        _blocks(names),
        groups,
        shared,
        refit_ids=("r0", "r1"),
        minimum_refits=3,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.robustness_evaluable is False
    assert result.all_refit_robust_full_transfer_path_count == 0
    assert result.all_refit_certified_path_status == "unavailable"
    assert all(row.category == "unavailable" for row in result.edges)


def test_shared_block_support_mismatch_fails_closed_for_all_refit_lattice():
    groups, shared = _design()
    shared[-1] = "mismatch"
    names = ("A", "B")
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_all_refit_shared_block_positive_information_lattice_v2(
            _constant_nodes(names, [mapping, mapping], len(groups)),
            _blocks(names),
            groups,
            shared,
            refit_ids=("r0", "r1"),
            minimum_refits=2,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )
