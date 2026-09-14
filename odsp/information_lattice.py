"""Order-sensitivity audit for held-out information transfer on a subset lattice.

A single strict filtration imposes an order on information additions.  When two
or more information blocks are scientifically unordered, adjacent transfer gains
can depend on that choice.  This module keeps every admissible subset comparison
explicit instead of selecting one convenient path.

Callers provide one held-out score vector for every node of the Boolean lattice
formed by declared information blocks above a fixed base information set.  ODSP
then scores every directed edge S -> S U {z} on independent groups, summarizes
path dependence, and optionally certifies the full group x edge family with one
studentized max-t interval family.

Shapley contributions are returned only as order-averaged descriptive summaries.
They never override a failed edge or an order-sensitive full-transfer result.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import math
from typing import Mapping, Sequence

import numpy as np

from .predictive_resolution import _validate_groups, _validate_weights
from .predictive_resolution_certification import _block_labels, _cell_status, _step_category
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class InformationBlock:
    """One scientifically atomic information addition in the lattice."""

    name: str
    variables: tuple[str, ...]

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("information-block name must be non-empty")
        variables = tuple(str(value).strip() for value in self.variables)
        if not variables or any(not value for value in variables):
            raise ValueError(f"information block {name!r} must contain non-empty variables")
        if len(set(variables)) != len(variables):
            raise ValueError(f"information block {name!r} contains duplicate variables")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "variables", variables)


@dataclass(frozen=True)
class InformationLatticeNodeScore:
    """Held-out row scores for one subset of declared information blocks."""

    blocks: tuple[str, ...]
    score: Sequence[float]

    def __post_init__(self) -> None:
        blocks = tuple(str(value).strip() for value in self.blocks)
        if any(not value for value in blocks):
            raise ValueError("lattice-node block labels must be non-empty")
        if len(set(blocks)) != len(blocks):
            raise ValueError("lattice-node block labels must be unique")
        object.__setattr__(self, "blocks", blocks)


@dataclass(frozen=True)
class LatticeGroupEdgeScore:
    group: object
    mean_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LatticeEdgePointResult:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    gain_category: str
    groups: tuple[LatticeGroupEdgeScore, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "lower_blocks": list(self.lower_blocks),
            "upper_blocks": list(self.upper_blocks),
            "added_block": self.added_block,
            "gain_category": self.gain_category,
            "groups": [row.as_dict() for row in self.groups],
        }


@dataclass(frozen=True)
class LatticeBlockPointSummary:
    block: str
    edge_count: int
    order_robust_category: str
    shapley_group_gains: tuple[LatticeGroupEdgeScore, ...]
    shapley_gain_category: str

    def as_dict(self) -> dict[str, object]:
        return {
            "block": self.block,
            "edge_count": self.edge_count,
            "order_robust_category": self.order_robust_category,
            "shapley_group_gains": [row.as_dict() for row in self.shapley_group_gains],
            "shapley_gain_category": self.shapley_gain_category,
        }


@dataclass(frozen=True)
class InformationLatticePointAudit:
    base_information: tuple[str, ...]
    blocks: tuple[InformationBlock, ...]
    node_count: int
    edge_count: int
    independent_group_count: int
    full_vs_base_gain_category: str
    full_vs_base_group_gains: tuple[LatticeGroupEdgeScore, ...]
    edges: tuple[LatticeEdgePointResult, ...]
    block_summaries: tuple[LatticeBlockPointSummary, ...]
    total_admissible_path_count: int
    full_transfer_path_count: int
    full_transfer_path_fraction: float
    path_status: str
    all_edges_generalizing: bool
    shapley_additivity_error_max_abs: float | None
    shapley_can_override_edge_failure: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "base_information": list(self.base_information),
            "blocks": [asdict(row) for row in self.blocks],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "independent_group_count": self.independent_group_count,
            "full_vs_base_gain_category": self.full_vs_base_gain_category,
            "full_vs_base_group_gains": [row.as_dict() for row in self.full_vs_base_group_gains],
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "total_admissible_path_count": self.total_admissible_path_count,
            "full_transfer_path_count": self.full_transfer_path_count,
            "full_transfer_path_fraction": self.full_transfer_path_fraction,
            "path_status": self.path_status,
            "all_edges_generalizing": self.all_edges_generalizing,
            "shapley_additivity_error_max_abs": self.shapley_additivity_error_max_abs,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
        }


@dataclass(frozen=True)
class LatticeCertificationCell:
    group: object
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LatticeEdgeCertification:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[LatticeCertificationCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "lower_blocks": list(self.lower_blocks),
            "upper_blocks": list(self.upper_blocks),
            "added_block": self.added_block,
            "category": self.category,
            "robust_positive_group_count": self.robust_positive_group_count,
            "robust_nonpositive_group_count": self.robust_nonpositive_group_count,
            "uncertain_group_count": self.uncertain_group_count,
            "unavailable_group_count": self.unavailable_group_count,
            "groups": [row.as_dict() for row in self.groups],
        }


@dataclass(frozen=True)
class LatticeBlockCertificationSummary:
    block: str
    edge_count: int
    order_robust_category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class InformationLatticeCertification:
    point_audit: InformationLatticePointAudit
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    row_independence_assumed: bool
    max_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    edges: tuple[LatticeEdgeCertification, ...]
    block_summaries: tuple[LatticeBlockCertificationSummary, ...]
    total_admissible_path_count: int
    robust_full_transfer_path_count: int
    robust_full_transfer_path_fraction: float
    certified_path_status: str
    all_edges_robust_generalizing: bool
    total_gain_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "point_audit": self.point_audit.as_dict(),
            "familywise_confidence_level": self.familywise_confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "row_independence_assumed": self.row_independence_assumed,
            "max_t_critical_value": self.max_t_critical_value,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "total_admissible_path_count": self.total_admissible_path_count,
            "robust_full_transfer_path_count": self.robust_full_transfer_path_count,
            "robust_full_transfer_path_fraction": self.robust_full_transfer_path_fraction,
            "certified_path_status": self.certified_path_status,
            "all_edges_robust_generalizing": self.all_edges_robust_generalizing,
            "total_gain_can_override_failed_edge": self.total_gain_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
        }


def _validate_blocks(blocks: Sequence[InformationBlock]) -> tuple[InformationBlock, ...]:
    rows = tuple(blocks)
    if not rows:
        raise ValueError("information lattice requires at least one information block")
    names = [row.name for row in rows]
    if len(set(names)) != len(names):
        raise ValueError("information-block names must be unique")
    variables: set[str] = set()
    for row in rows:
        overlap = variables & set(row.variables)
        if overlap:
            raise ValueError(
                f"information blocks must be variable-disjoint; repeated={tuple(sorted(overlap))!r}"
            )
        variables.update(row.variables)
    return rows


def _canonical_subset(values: Sequence[str], order: tuple[str, ...]) -> tuple[str, ...]:
    local = tuple(str(value).strip() for value in values)
    if any(not value for value in local) or len(set(local)) != len(local):
        raise ValueError("lattice-node block labels must be non-empty and unique")
    unknown = sorted(set(local) - set(order))
    if unknown:
        raise ValueError(f"lattice node contains unknown information blocks: {unknown!r}")
    chosen = set(local)
    return tuple(name for name in order if name in chosen)


def _all_subsets(order: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    result: list[tuple[str, ...]] = []
    for size in range(len(order) + 1):
        result.extend(tuple(combo) for combo in itertools.combinations(order, size))
    return tuple(result)


def _validate_nodes(
    nodes: Sequence[InformationLatticeNodeScore],
    block_order: tuple[str, ...],
) -> tuple[dict[tuple[str, ...], np.ndarray], int]:
    expected = set(_all_subsets(block_order))
    mapping: dict[tuple[str, ...], np.ndarray] = {}
    n: int | None = None
    for node in nodes:
        subset = _canonical_subset(node.blocks, block_order)
        if subset in mapping:
            raise ValueError(f"duplicate lattice score node for blocks {subset!r}")
        score = np.asarray(node.score, dtype=float)
        if score.ndim != 1 or score.size == 0:
            raise ValueError(f"score for lattice node {subset!r} must be a non-empty vector")
        if n is None:
            n = int(score.size)
        elif score.size != n:
            raise ValueError("all lattice score nodes must contain the same held-out rows")
        if np.isnan(score).any() or np.isposinf(score).any():
            raise ValueError(
                f"score for lattice node {subset!r} may contain finite values or -inf, but not NaN or +inf"
            )
        mapping[subset] = score
    missing = sorted(expected - set(mapping), key=lambda value: (len(value), value))
    extra = sorted(set(mapping) - expected, key=lambda value: (len(value), value))
    if missing or extra:
        raise ValueError(
            f"information lattice must supply the complete subset score table; missing={missing!r}, extra={extra!r}"
        )
    assert n is not None
    return mapping, n


def _edges(block_order: tuple[str, ...]) -> tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...]:
    result: list[tuple[tuple[str, ...], tuple[str, ...], str]] = []
    for subset in _all_subsets(block_order):
        chosen = set(subset)
        for block in block_order:
            if block in chosen:
                continue
            upper_set = chosen | {block}
            upper = tuple(name for name in block_order if name in upper_set)
            result.append((subset, upper, block))
    return tuple(result)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    positive = weights > 0
    if not np.any(positive):
        raise ValueError("every independent group must have positive total weight")
    selected = values[positive]
    selected_weights = weights[positive]
    if np.isneginf(selected).any():
        return float("-inf")
    return float(np.sum(selected * selected_weights) / np.sum(selected_weights))


def _path_count(
    block_order: tuple[str, ...],
    successful_edges: set[tuple[tuple[str, ...], str]],
) -> int:
    counts: dict[tuple[str, ...], int] = {(): 1}
    for size in range(len(block_order)):
        for subset in itertools.combinations(block_order, size):
            current = tuple(subset)
            count = counts.get(current, 0)
            if count == 0:
                continue
            chosen = set(current)
            for block in block_order:
                if block in chosen or (current, block) not in successful_edges:
                    continue
                upper_set = chosen | {block}
                upper = tuple(name for name in block_order if name in upper_set)
                counts[upper] = counts.get(upper, 0) + count
    return counts.get(block_order, 0)


def _path_status(successful: int, total: int) -> str:
    if successful == total:
        return "universal_full_transfer"
    if successful == 0:
        return "no_full_transfer"
    return "order_sensitive_full_transfer"


def _block_point_category(categories: Sequence[str]) -> str:
    values = tuple(categories)
    if values and all(value == "generalizing" for value in values):
        return "order_robust_generalizing"
    if values and all(value == "non_generalizing" for value in values):
        return "order_robust_non_generalizing"
    return "order_sensitive"


def _block_certified_category(categories: Sequence[str]) -> str:
    values = tuple(categories)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_generalizing" for value in values):
        return "order_robust_generalizing"
    if values and all(value == "robust_non_generalizing" for value in values):
        return "order_robust_non_generalizing"
    if any(value == "uncertain" for value in values):
        return "uncertain_or_order_sensitive"
    return "order_sensitive"


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|information-lattice|max-t|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _shapley_weights(block_count: int) -> dict[int, float]:
    denominator = math.factorial(block_count)
    return {
        size: (
            math.factorial(size)
            * math.factorial(block_count - size - 1)
            / denominator
        )
        for size in range(block_count)
    }


def audit_information_lattice(
    nodes: Sequence[InformationLatticeNodeScore],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    sample_weight: Sequence[float] | None = None,
    gain_tolerance: float = 0.0,
) -> InformationLatticePointAudit:
    """Audit point transfer over every edge and every admissible information order."""

    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")
    blocks = _validate_blocks(information_blocks)
    block_order = tuple(row.name for row in blocks)
    base = tuple(str(value).strip() for value in base_information)
    if any(not value for value in base) or len(set(base)) != len(base):
        raise ValueError("base_information must contain unique non-empty labels")
    block_variables = {value for row in blocks for value in row.variables}
    overlap = set(base) & block_variables
    if overlap:
        raise ValueError(
            f"base_information must be disjoint from added information blocks; overlap={tuple(sorted(overlap))!r}"
        )
    score_by_subset, n = _validate_nodes(nodes, block_order)
    group_array = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)
    positive = weight > 0
    full_subset = block_order

    # Every non-full node is a comparator for at least one outgoing edge.
    for subset, score in score_by_subset.items():
        if subset != full_subset and not np.isfinite(score[positive]).all():
            raise ValueError(
                f"comparator lattice node {subset!r} must be finite on every positive-weight row"
            )

    edge_defs = _edges(block_order)
    ordered_groups = tuple(dict.fromkeys(group_array.tolist()))
    edge_rows: list[LatticeEdgePointResult] = []
    edge_group_mean: dict[tuple[tuple[str, ...], str], dict[object, float]] = {}
    edge_category: dict[tuple[tuple[str, ...], str], str] = {}

    for lower, upper, added in edge_defs:
        row_gain = score_by_subset[upper] - score_by_subset[lower]
        group_scores: list[LatticeGroupEdgeScore] = []
        means: dict[object, float] = {}
        for group in ordered_groups:
            mask = group_array == group
            mean = _weighted_mean(row_gain[mask], weight[mask])
            means[group] = mean
            group_scores.append(LatticeGroupEdgeScore(group=group, mean_gain=mean))
        category = classify_independent_gains(
            list(means.values()), tolerance=gain_tolerance
        )
        key = (lower, added)
        edge_group_mean[key] = means
        edge_category[key] = category
        edge_rows.append(
            LatticeEdgePointResult(
                lower_blocks=lower,
                upper_blocks=upper,
                added_block=added,
                gain_category=category,
                groups=tuple(group_scores),
            )
        )

    base_score = score_by_subset[()]
    full_score = score_by_subset[full_subset]
    full_group_scores: list[LatticeGroupEdgeScore] = []
    full_gains: list[float] = []
    for group in ordered_groups:
        mask = group_array == group
        gain = _weighted_mean(full_score[mask] - base_score[mask], weight[mask])
        full_group_scores.append(LatticeGroupEdgeScore(group=group, mean_gain=gain))
        full_gains.append(gain)
    full_category = classify_independent_gains(full_gains, tolerance=gain_tolerance)

    shapley_by_group: dict[object, dict[str, float]] = {
        group: {block: 0.0 for block in block_order} for group in ordered_groups
    }
    shapley_available = True
    weights_by_size = _shapley_weights(len(block_order))
    for lower, _, added in edge_defs:
        coefficient = weights_by_size[len(lower)]
        for group in ordered_groups:
            gain = edge_group_mean[(lower, added)][group]
            if not math.isfinite(gain):
                shapley_available = False
            else:
                shapley_by_group[group][added] += coefficient * gain

    block_summaries: list[LatticeBlockPointSummary] = []
    if shapley_available:
        for block in block_order:
            local_edges = [
                edge_category[(lower, added)]
                for lower, _, added in edge_defs
                if added == block
            ]
            shapley_rows = tuple(
                LatticeGroupEdgeScore(
                    group=group,
                    mean_gain=float(shapley_by_group[group][block]),
                )
                for group in ordered_groups
            )
            block_summaries.append(
                LatticeBlockPointSummary(
                    block=block,
                    edge_count=len(local_edges),
                    order_robust_category=_block_point_category(local_edges),
                    shapley_group_gains=shapley_rows,
                    shapley_gain_category=classify_independent_gains(
                        [row.mean_gain for row in shapley_rows],
                        tolerance=gain_tolerance,
                    ),
                )
            )
        additivity_error = max(
            abs(
                sum(shapley_by_group[group].values())
                - next(row.mean_gain for row in full_group_scores if row.group == group)
            )
            for group in ordered_groups
        )
    else:
        for block in block_order:
            local_edges = [
                edge_category[(lower, added)]
                for lower, _, added in edge_defs
                if added == block
            ]
            block_summaries.append(
                LatticeBlockPointSummary(
                    block=block,
                    edge_count=len(local_edges),
                    order_robust_category=_block_point_category(local_edges),
                    shapley_group_gains=(),
                    shapley_gain_category="unavailable",
                )
            )
        additivity_error = None

    successful = {
        key for key, category in edge_category.items() if category == "generalizing"
    }
    total_paths = math.factorial(len(block_order))
    full_paths = _path_count(block_order, successful)

    return InformationLatticePointAudit(
        base_information=base,
        blocks=blocks,
        node_count=len(score_by_subset),
        edge_count=len(edge_defs),
        independent_group_count=len(ordered_groups),
        full_vs_base_gain_category=full_category,
        full_vs_base_group_gains=tuple(full_group_scores),
        edges=tuple(edge_rows),
        block_summaries=tuple(block_summaries),
        total_admissible_path_count=total_paths,
        full_transfer_path_count=full_paths,
        full_transfer_path_fraction=float(full_paths / total_paths),
        path_status=_path_status(full_paths, total_paths),
        all_edges_generalizing=bool(full_paths == total_paths),
        shapley_additivity_error_max_abs=(
            None if additivity_error is None else float(additivity_error)
        ),
        shapley_can_override_edge_failure=False,
    )


def certify_information_lattice(
    nodes: Sequence[InformationLatticeNodeScore],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260913,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> InformationLatticeCertification:
    """Familywise-certify every group x edge cell of a complete information lattice."""

    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    if isinstance(bootstrap_draws, bool) or not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(minimum_blocks_per_group, bool)
        or not isinstance(minimum_blocks_per_group, int)
        or minimum_blocks_per_group < 2
    ):
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    point = audit_information_lattice(
        nodes,
        information_blocks,
        groups,
        base_information=base_information,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    block_rows = point.blocks
    block_order = tuple(row.name for row in block_rows)
    score_by_subset, n = _validate_nodes(nodes, block_order)
    group_array = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)
    block_array, row_independence = _block_labels(blocks, n)
    edge_defs = _edges(block_order)
    edge_count = len(edge_defs)
    row_gain_matrix = np.column_stack(
        [score_by_subset[upper] - score_by_subset[lower] for lower, upper, _ in edge_defs]
    )
    ordered_groups = tuple(dict.fromkeys(group_array.tolist()))

    records: list[list[dict[str, object]]] = [[] for _ in range(edge_count)]
    eligible: list[tuple[int, int]] = []
    sample_columns: list[np.ndarray] = []
    sample_points: list[float] = []
    sample_ses: list[float] = []

    for group in ordered_groups:
        mask = group_array == group
        local_gain = row_gain_matrix[mask]
        local_weight = weight[mask]
        local_block = block_array[mask]
        positive = local_weight > 0
        ordered_blocks = tuple(sorted(set(local_block[positive].tolist()), key=str))
        if not ordered_blocks:
            raise ValueError(f"group {group!r} has no positive-mass resampling blocks")
        finite_edge = np.all(np.isfinite(local_gain[positive]), axis=0)

        block_weight = np.empty(len(ordered_blocks), dtype=float)
        block_numerator = np.zeros((len(ordered_blocks), edge_count), dtype=float)
        for block_index, block_id in enumerate(ordered_blocks):
            block_mask = local_block == block_id
            bw = float(np.sum(local_weight[block_mask]))
            if bw <= 0:
                raise ValueError("every declared resampling block must have positive total weight")
            block_weight[block_index] = bw
            if np.any(finite_edge):
                weighted = (
                    local_gain[block_mask][:, finite_edge]
                    * local_weight[block_mask][:, None]
                )
                block_numerator[block_index, finite_edge] = np.sum(weighted, axis=0)
        total_weight = float(np.sum(block_weight))
        point_mean = np.full(edge_count, np.nan)
        point_mean[finite_edge] = np.sum(
            block_numerator[:, finite_edge], axis=0
        ) / total_weight

        rng = np.random.default_rng(_stable_group_seed(seed, group))
        sampled = rng.integers(
            0,
            len(ordered_blocks),
            size=(bootstrap_draws, len(ordered_blocks)),
        )
        denominator = np.sum(block_weight[sampled], axis=1)

        for edge_index, (lower, upper, added) in enumerate(edge_defs):
            estimable = bool(
                finite_edge[edge_index]
                and len(ordered_blocks) >= minimum_blocks_per_group
            )
            record: dict[str, object] = {
                "group": group,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": len(ordered_blocks),
                "total_weight": total_weight,
                "mean_gain": (
                    float(point_mean[edge_index])
                    if finite_edge[edge_index]
                    else float("-inf")
                ),
                "bootstrap_standard_error": None,
                "lower_bound": None,
                "upper_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[edge_index])
            records[edge_index].append(record)
            if estimable:
                numerator = np.sum(block_numerator[sampled, edge_index], axis=1)
                samples = numerator / denominator
                se = float(np.std(samples, ddof=1))
                record["bootstrap_standard_error"] = se
                eligible.append((edge_index, record_index))
                sample_columns.append(samples)
                sample_points.append(float(point_mean[edge_index]))
                sample_ses.append(se)

    critical: float | None = None
    if sample_columns:
        sample_matrix = np.column_stack(sample_columns)
        points = np.asarray(sample_points)
        ses = np.asarray(sample_ses)
        standardized = np.zeros_like(sample_matrix)
        nonzero = ses > 1e-15
        standardized[:, nonzero] = (
            np.abs(sample_matrix[:, nonzero] - points[nonzero]) / ses[nonzero]
        )
        critical = float(
            np.quantile(np.max(standardized, axis=1), familywise_confidence_level)
        )
        for column, (edge_index, record_index) in enumerate(eligible):
            lower = float(points[column] - critical * ses[column])
            upper = float(points[column] + critical * ses[column])
            records[edge_index][record_index]["lower_bound"] = lower
            records[edge_index][record_index]["upper_bound"] = upper
            records[edge_index][record_index]["status"] = _cell_status(
                lower, upper, tolerance=gain_tolerance
            )

    edge_rows: list[LatticeEdgeCertification] = []
    edge_categories: dict[tuple[tuple[str, ...], str], str] = {}
    for edge_index, (lower, upper, added) in enumerate(edge_defs):
        cells = tuple(
            LatticeCertificationCell(**record) for record in records[edge_index]
        )
        statuses = [row.status for row in cells]
        category = _step_category(statuses)
        edge_categories[(lower, added)] = category
        edge_rows.append(
            LatticeEdgeCertification(
                lower_blocks=lower,
                upper_blocks=upper,
                added_block=added,
                category=category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count("robust_nonpositive"),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    block_summaries = tuple(
        LatticeBlockCertificationSummary(
            block=block,
            edge_count=sum(1 for _, _, added in edge_defs if added == block),
            order_robust_category=_block_certified_category(
                [
                    edge_categories[(lower, added)]
                    for lower, _, added in edge_defs
                    if added == block
                ]
            ),
        )
        for block in block_order
    )
    successful = {
        key
        for key, category in edge_categories.items()
        if category == "robust_generalizing"
    }
    total_paths = math.factorial(len(block_order))
    robust_paths = _path_count(block_order, successful)
    cell_count = len(ordered_groups) * edge_count
    estimable_count = len(eligible)

    return InformationLatticeCertification(
        point_audit=point,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        row_independence_assumed=row_independence,
        max_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=estimable_count,
        all_cells_estimable=bool(estimable_count == cell_count),
        edges=tuple(edge_rows),
        block_summaries=block_summaries,
        total_admissible_path_count=total_paths,
        robust_full_transfer_path_count=robust_paths,
        robust_full_transfer_path_fraction=float(robust_paths / total_paths),
        certified_path_status=_path_status(robust_paths, total_paths),
        all_edges_robust_generalizing=bool(robust_paths == total_paths),
        total_gain_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
    )
