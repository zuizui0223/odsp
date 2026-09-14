"""Refit-aware certification for complete information-lattice audits.

A fixed information lattice diagnoses whether held-out transfer depends on the
order in which scientifically unordered information blocks are added. This
module adds sensitivity to an explicitly supplied ensemble of upstream refits.

Each Monte Carlo draw selects exactly one refit ID and shares that selected refit
across every independent group and every lattice edge. Within each group the
same resampled validation-block indices are then used for every edge. A single
studentized max-t critical value is formed over the full estimable
group-by-lattice-edge family.

ODSP does not fit models, infer a refit scheme, assume refits are independent, or
average away failed lattice edges. The reference fit and refit-averaged point
summaries are diagnostics only; neither can override the refit-aware familywise
edge audit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .information_lattice import (
    InformationBlock,
    InformationLatticeCertification,
    InformationLatticeNodeScore,
    InformationLatticePointAudit,
    _all_subsets,
    _block_certified_category,
    _canonical_subset,
    _edges,
    _path_count,
    _path_status,
    _validate_blocks,
    audit_information_lattice,
    certify_information_lattice,
)
from .predictive_resolution import _validate_groups, _validate_weights
from .predictive_resolution_certification import _cell_status, _step_category
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class RefitInformationLatticeNodeScores:
    """One lattice node with an aligned [refit, held-out row] score matrix."""

    blocks: tuple[str, ...]
    score: Sequence[Sequence[float]]

    def __post_init__(self) -> None:
        blocks = tuple(str(value).strip() for value in self.blocks)
        if any(not value for value in blocks):
            raise ValueError("lattice-node block labels must be non-empty")
        if len(set(blocks)) != len(blocks):
            raise ValueError("lattice-node block labels must be unique")
        object.__setattr__(self, "blocks", blocks)


@dataclass(frozen=True)
class RefitLatticeCertificationCell:
    group: object
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    row_count: int
    block_count: int
    total_weight: float
    ensemble_mean_gain: float | None
    reference_refit_gain: float | None
    refit_mean_gains: tuple[float, ...]
    positive_refit_count: int
    nonpositive_refit_count: int
    between_refit_standard_deviation: float | None
    nested_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["lower_blocks"] = list(self.lower_blocks)
        payload["upper_blocks"] = list(self.upper_blocks)
        payload["refit_mean_gains"] = list(self.refit_mean_gains)
        return payload


@dataclass(frozen=True)
class RefitLatticeEdgeCertification:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    ensemble_point_category: str
    refit_point_categories: tuple[str, ...]
    refit_category_stability: str
    refit_aware_category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[RefitLatticeCertificationCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "lower_blocks": list(self.lower_blocks),
            "upper_blocks": list(self.upper_blocks),
            "added_block": self.added_block,
            "ensemble_point_category": self.ensemble_point_category,
            "refit_point_categories": list(self.refit_point_categories),
            "refit_category_stability": self.refit_category_stability,
            "refit_aware_category": self.refit_aware_category,
            "robust_positive_group_count": self.robust_positive_group_count,
            "robust_nonpositive_group_count": self.robust_nonpositive_group_count,
            "uncertain_group_count": self.uncertain_group_count,
            "unavailable_group_count": self.unavailable_group_count,
            "groups": [row.as_dict() for row in self.groups],
        }


@dataclass(frozen=True)
class RefitLatticeBlockSummary:
    block: str
    edge_count: int
    ensemble_order_robust_category: str
    refit_aware_order_robust_category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RefitInformationLatticeCertification:
    base_information: tuple[str, ...]
    blocks: tuple[InformationBlock, ...]
    node_count: int
    edge_count: int
    independent_group_count: int
    refit_count: int
    refit_ids: tuple[str, ...]
    reference_refit_id: str
    familywise_confidence_level: float
    nested_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    max_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    total_admissible_path_count: int
    reference_point_full_transfer_path_count: int
    reference_point_path_status: str
    reference_certified_full_transfer_path_count: int
    reference_certified_path_status: str
    refit_point_full_transfer_path_counts: tuple[int, ...]
    refit_point_path_statuses: tuple[str, ...]
    refit_path_stability: str
    ensemble_point_full_transfer_path_count: int
    ensemble_point_path_status: str
    refit_aware_full_transfer_path_count: int
    refit_aware_path_status: str
    selected_refit_draw_counts: tuple[int, ...]
    same_selected_refit_shared_across_all_group_edge_cells: bool
    same_block_draw_shared_across_edges_within_group: bool
    automatic_refit_scheme_inference: bool
    reference_fit_can_override_refit_aware_failure: bool
    best_path_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool
    edges: tuple[RefitLatticeEdgeCertification, ...]
    block_summaries: tuple[RefitLatticeBlockSummary, ...]
    reference_point_audit: InformationLatticePointAudit
    reference_fit_certification: InformationLatticeCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "base_information": list(self.base_information),
            "blocks": [asdict(row) for row in self.blocks],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "independent_group_count": self.independent_group_count,
            "refit_count": self.refit_count,
            "refit_ids": list(self.refit_ids),
            "reference_refit_id": self.reference_refit_id,
            "familywise_confidence_level": self.familywise_confidence_level,
            "nested_draws": self.nested_draws,
            "seed": self.seed,
            "minimum_refits": self.minimum_refits,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "max_t_critical_value": self.max_t_critical_value,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "total_admissible_path_count": self.total_admissible_path_count,
            "reference_point_full_transfer_path_count": self.reference_point_full_transfer_path_count,
            "reference_point_path_status": self.reference_point_path_status,
            "reference_certified_full_transfer_path_count": self.reference_certified_full_transfer_path_count,
            "reference_certified_path_status": self.reference_certified_path_status,
            "refit_point_full_transfer_path_counts": list(self.refit_point_full_transfer_path_counts),
            "refit_point_path_statuses": list(self.refit_point_path_statuses),
            "refit_path_stability": self.refit_path_stability,
            "ensemble_point_full_transfer_path_count": self.ensemble_point_full_transfer_path_count,
            "ensemble_point_path_status": self.ensemble_point_path_status,
            "refit_aware_full_transfer_path_count": self.refit_aware_full_transfer_path_count,
            "refit_aware_path_status": self.refit_aware_path_status,
            "selected_refit_draw_counts": list(self.selected_refit_draw_counts),
            "same_selected_refit_shared_across_all_group_edge_cells": self.same_selected_refit_shared_across_all_group_edge_cells,
            "same_block_draw_shared_across_edges_within_group": self.same_block_draw_shared_across_edges_within_group,
            "automatic_refit_scheme_inference": self.automatic_refit_scheme_inference,
            "reference_fit_can_override_refit_aware_failure": self.reference_fit_can_override_refit_aware_failure,
            "best_path_can_override_failed_edge": self.best_path_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "reference_point_audit": self.reference_point_audit.as_dict(),
            "reference_fit_certification": self.reference_fit_certification.as_dict(),
        }


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    if int(value) < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|refit-information-lattice|blocks|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _shared_refit_draws(seed: int, refit_count: int, draws: int) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|refit-information-lattice|shared-refit".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(0, refit_count, size=draws)


def _refit_ids(
    values: Sequence[object] | None,
    count: int,
) -> tuple[tuple[str, ...], np.ndarray]:
    if values is None:
        ids = tuple(f"refit-{index:09d}" for index in range(count))
    else:
        if len(values) != count:
            raise ValueError("refit_ids must contain one ID per refit")
        ids = tuple(str(value).strip() for value in values)
        if any(not value for value in ids):
            raise ValueError("refit_ids must be non-empty")
    if len(set(ids)) != count:
        raise ValueError("refit_ids must be unique")
    order = np.argsort(np.asarray(ids), kind="stable")
    return tuple(ids[int(index)] for index in order), order


def _validate_refit_nodes(
    nodes: Sequence[RefitInformationLatticeNodeScores],
    block_order: tuple[str, ...],
) -> tuple[dict[tuple[str, ...], np.ndarray], int, int]:
    expected = set(_all_subsets(block_order))
    mapping: dict[tuple[str, ...], np.ndarray] = {}
    shape: tuple[int, int] | None = None
    for node in nodes:
        subset = _canonical_subset(node.blocks, block_order)
        if subset in mapping:
            raise ValueError(f"duplicate lattice score node for blocks {subset!r}")
        matrix = np.asarray(node.score, dtype=float)
        if matrix.ndim != 2 or 0 in matrix.shape:
            raise ValueError(
                f"score matrix for lattice node {subset!r} must be non-empty [refit, row]"
            )
        if shape is None:
            shape = (int(matrix.shape[0]), int(matrix.shape[1]))
        elif matrix.shape != shape:
            raise ValueError(
                "all refit lattice score nodes must share the same refit and held-out row axes"
            )
        if np.isnan(matrix).any() or np.isposinf(matrix).any():
            raise ValueError(
                f"score matrix for lattice node {subset!r} may contain finite values or -inf, "
                "but not NaN or +inf"
            )
        mapping[subset] = matrix
    missing = sorted(expected - set(mapping), key=lambda value: (len(value), value))
    extra = sorted(set(mapping) - expected, key=lambda value: (len(value), value))
    if missing or extra:
        raise ValueError(
            "refit information lattice must supply the complete subset score table; "
            f"missing={missing!r}, extra={extra!r}"
        )
    assert shape is not None
    return mapping, shape[0], shape[1]


def _canonical_group_order(group: np.ndarray) -> tuple[object, ...]:
    return tuple(
        sorted(
            set(group.tolist()),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )


def certify_refit_information_lattice(
    nodes: Sequence[RefitInformationLatticeNodeScores],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    blocks: Sequence[object],
    refit_ids: Sequence[object] | None = None,
    reference_refit_id: object | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    nested_draws: int = 4000,
    seed: int = 20260914,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitInformationLatticeCertification:
    """Jointly audit lattice-order and upstream-refit sensitivity.

    Score matrices must be aligned as ``[refit, held-out row]`` at every node of
    the complete subset lattice. One selected refit is shared across the entire
    group-by-edge family in each Monte Carlo draw. Validation blocks are sampled
    independently between groups, but the same sampled block indices are shared
    across all lattice edges within a group.

    The method treats the supplied refits as a uniformly weighted empirical
    sensitivity ensemble. It does not infer how those refits were generated or
    turn them into independent observations.
    """

    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    nested_draws = _integer(nested_draws, name="nested_draws", minimum=500)
    seed = _integer(seed, name="seed", minimum=0)
    minimum_refits = _integer(
        minimum_refits, name="minimum_refits", minimum=2
    )
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group,
        name="minimum_blocks_per_group",
        minimum=2,
    )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    block_rows = _validate_blocks(information_blocks)
    block_order = tuple(row.name for row in block_rows)
    base = tuple(str(value).strip() for value in base_information)
    if any(not value for value in base) or len(set(base)) != len(base):
        raise ValueError("base_information must contain unique non-empty labels")
    block_variables = {value for row in block_rows for value in row.variables}
    overlap = set(base) & block_variables
    if overlap:
        raise ValueError(
            "base_information must be disjoint from added information blocks; "
            f"overlap={tuple(sorted(overlap))!r}"
        )

    score_by_subset, refit_count, n = _validate_refit_nodes(nodes, block_order)
    group = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)
    block = np.asarray(list(blocks), dtype=object)
    if block.shape != (n,):
        raise ValueError("blocks must contain one value per held-out row")
    for value in block.tolist():
        if value is None:
            raise ValueError("block labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("block labels must be hashable") from exc

    ids, refit_order = _refit_ids(refit_ids, refit_count)
    score_by_subset = {
        subset: matrix[refit_order] for subset, matrix in score_by_subset.items()
    }
    reference_id = ids[0] if reference_refit_id is None else str(reference_refit_id).strip()
    if reference_id not in ids:
        raise ValueError("reference_refit_id must identify one supplied refit")
    reference_index = ids.index(reference_id)

    positive = weight > 0
    full_subset = block_order
    for subset, matrix in score_by_subset.items():
        if subset != full_subset and not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator lattice node {subset!r} must be finite on every "
                "positive-weight row for every refit"
            )

    edge_defs = _edges(block_order)
    edge_count = len(edge_defs)
    gains = np.stack(
        [
            score_by_subset[upper] - score_by_subset[lower]
            for lower, upper, _ in edge_defs
        ],
        axis=1,
    )

    refit_point_audits: list[InformationLatticePointAudit] = []
    edge_refit_categories: list[list[str]] = [[] for _ in range(edge_count)]
    refit_path_counts: list[int] = []
    refit_path_statuses: list[str] = []
    for refit_index in range(refit_count):
        point = audit_information_lattice(
            [
                InformationLatticeNodeScore(
                    blocks=subset,
                    score=matrix[refit_index],
                )
                for subset, matrix in score_by_subset.items()
            ],
            block_rows,
            group,
            base_information=base,
            sample_weight=weight,
            gain_tolerance=gain_tolerance,
        )
        refit_point_audits.append(point)
        refit_path_counts.append(point.full_transfer_path_count)
        refit_path_statuses.append(point.path_status)
        point_categories = {
            (edge.lower_blocks, edge.added_block): edge.gain_category
            for edge in point.edges
        }
        for edge_index, (lower, _, added) in enumerate(edge_defs):
            edge_refit_categories[edge_index].append(
                point_categories[(lower, added)]
            )

    reference_point = refit_point_audits[reference_index]
    reference_nodes = [
        InformationLatticeNodeScore(
            blocks=subset,
            score=matrix[reference_index],
        )
        for subset, matrix in score_by_subset.items()
    ]
    reference_certification = certify_information_lattice(
        reference_nodes,
        block_rows,
        group,
        base_information=base,
        blocks=block,
        sample_weight=weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=nested_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    selected_refits = _shared_refit_draws(seed, refit_count, nested_draws)
    enough_refits = refit_count >= minimum_refits
    group_order = _canonical_group_order(group)

    records: list[list[dict[str, object]]] = [[] for _ in range(edge_count)]
    eligible: list[tuple[int, int]] = []
    sample_columns: list[np.ndarray] = []
    sample_points: list[float] = []
    sample_ses: list[float] = []

    for group_value in group_order:
        mask = group == group_value
        local_weight = weight[mask]
        local_block = block[mask]
        if not float(np.sum(local_weight)) > 0:
            raise ValueError(f"group {group_value!r} has zero total score weight")
        ordered_blocks = tuple(
            sorted(
                set(local_block.tolist()),
                key=lambda value: (type(value).__name__, repr(value)),
            )
        )
        block_weights = np.empty(len(ordered_blocks), dtype=float)
        block_numerators = np.zeros(
            (refit_count, len(ordered_blocks), edge_count), dtype=float
        )
        local_gain = gains[:, :, mask]
        local_positive = local_weight > 0
        finite_edge = np.all(
            np.isfinite(local_gain[:, :, local_positive]), axis=(0, 2)
        )

        for block_index, block_value in enumerate(ordered_blocks):
            block_mask = local_block == block_value
            bw = float(np.sum(local_weight[block_mask]))
            if bw <= 0:
                raise ValueError(
                    "every declared resampling block must have positive total weight"
                )
            block_weights[block_index] = bw
            if np.any(finite_edge):
                weighted = (
                    local_gain[:, finite_edge, :][:, :, block_mask]
                    * local_weight[block_mask][None, None, :]
                )
                block_numerators[:, block_index, finite_edge] = np.sum(
                    weighted, axis=2
                )

        total_weight = float(np.sum(block_weights))
        refit_means = np.full((refit_count, edge_count), np.nan, dtype=float)
        if np.any(finite_edge):
            refit_means[:, finite_edge] = (
                np.sum(block_numerators[:, :, finite_edge], axis=1)
                / total_weight
            )

        rng = np.random.default_rng(_stable_group_seed(seed, group_value))
        sampled_blocks = rng.integers(
            0,
            len(ordered_blocks),
            size=(nested_draws, len(ordered_blocks)),
        )
        sampled_denominator = np.sum(block_weights[sampled_blocks], axis=1)

        for edge_index, (lower, upper, added) in enumerate(edge_defs):
            finite = bool(finite_edge[edge_index])
            means = (
                tuple(float(value) for value in refit_means[:, edge_index])
                if finite
                else ()
            )
            ensemble_mean = (
                float(np.mean(refit_means[:, edge_index])) if finite else None
            )
            reference_gain = (
                float(refit_means[reference_index, edge_index])
                if finite
                else None
            )
            estimable = bool(
                finite
                and enough_refits
                and len(ordered_blocks) >= minimum_blocks_per_group
            )
            record: dict[str, object] = {
                "group": group_value,
                "lower_blocks": lower,
                "upper_blocks": upper,
                "added_block": added,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": len(ordered_blocks),
                "total_weight": total_weight,
                "ensemble_mean_gain": ensemble_mean,
                "reference_refit_gain": reference_gain,
                "refit_mean_gains": means,
                "positive_refit_count": (
                    int(np.count_nonzero(refit_means[:, edge_index] > gain_tolerance))
                    if finite
                    else 0
                ),
                "nonpositive_refit_count": (
                    int(
                        refit_count
                        - np.count_nonzero(
                            refit_means[:, edge_index] > gain_tolerance
                        )
                    )
                    if finite
                    else 0
                ),
                "between_refit_standard_deviation": (
                    float(np.std(refit_means[:, edge_index], ddof=0))
                    if finite
                    else None
                ),
                "nested_standard_error": None,
                "lower_bound": None,
                "upper_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[edge_index])
            records[edge_index].append(record)
            if estimable:
                numerator = np.sum(
                    block_numerators[
                        selected_refits[:, None],
                        sampled_blocks,
                        edge_index,
                    ],
                    axis=1,
                )
                samples = numerator / sampled_denominator
                if not np.isfinite(samples).all():
                    raise ValueError(
                        "nested refit/block resampling produced non-finite lattice gains"
                    )
                se = float(np.std(samples, ddof=1))
                record["nested_standard_error"] = se
                eligible.append((edge_index, record_index))
                sample_columns.append(samples)
                sample_points.append(float(ensemble_mean))
                sample_ses.append(se)

    critical: float | None = None
    if sample_columns:
        sample_matrix = np.column_stack(sample_columns)
        points = np.asarray(sample_points, dtype=float)
        ses = np.asarray(sample_ses, dtype=float)
        standardized = np.zeros_like(sample_matrix)
        nonzero = ses > 1e-15
        standardized[:, nonzero] = (
            np.abs(sample_matrix[:, nonzero] - points[nonzero])
            / ses[nonzero]
        )
        critical = float(
            np.quantile(
                np.max(standardized, axis=1),
                familywise_confidence_level,
            )
        )
        for column, (edge_index, record_index) in enumerate(eligible):
            lower = float(points[column] - critical * ses[column])
            upper = float(points[column] + critical * ses[column])
            records[edge_index][record_index]["lower_bound"] = lower
            records[edge_index][record_index]["upper_bound"] = upper
            records[edge_index][record_index]["status"] = _cell_status(
                lower,
                upper,
                tolerance=gain_tolerance,
            )

    edge_rows: list[RefitLatticeEdgeCertification] = []
    ensemble_edge_categories: dict[tuple[tuple[str, ...], str], str] = {}
    refit_aware_edge_categories: dict[tuple[tuple[str, ...], str], str] = {}
    for edge_index, (lower, upper, added) in enumerate(edge_defs):
        cells = tuple(
            RefitLatticeCertificationCell(**record)
            for record in records[edge_index]
        )
        statuses = [cell.status for cell in cells]
        refit_aware_category = _step_category(statuses)
        finite_ensemble = [
            cell.ensemble_mean_gain
            for cell in cells
            if cell.ensemble_mean_gain is not None
        ]
        if len(finite_ensemble) != len(cells):
            ensemble_category = "unavailable"
        else:
            ensemble_category = classify_independent_gains(
                [float(value) for value in finite_ensemble],
                tolerance=gain_tolerance,
            )
        per_refit = tuple(edge_refit_categories[edge_index])
        stability = (
            "stable" if len(set(per_refit)) == 1 else "refit_sensitive"
        )
        key = (lower, added)
        ensemble_edge_categories[key] = ensemble_category
        refit_aware_edge_categories[key] = refit_aware_category
        edge_rows.append(
            RefitLatticeEdgeCertification(
                lower_blocks=lower,
                upper_blocks=upper,
                added_block=added,
                ensemble_point_category=ensemble_category,
                refit_point_categories=per_refit,
                refit_category_stability=stability,
                refit_aware_category=refit_aware_category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count(
                    "robust_nonpositive"
                ),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    block_summaries = tuple(
        RefitLatticeBlockSummary(
            block=block_name,
            edge_count=sum(
                1 for _, _, added in edge_defs if added == block_name
            ),
            ensemble_order_robust_category=_block_certified_category(
                [
                    (
                        "robust_generalizing"
                        if ensemble_edge_categories[(lower, added)]
                        == "generalizing"
                        else "robust_non_generalizing"
                        if ensemble_edge_categories[(lower, added)]
                        == "non_generalizing"
                        else "unavailable"
                    )
                    for lower, _, added in edge_defs
                    if added == block_name
                ]
            ),
            refit_aware_order_robust_category=_block_certified_category(
                [
                    refit_aware_edge_categories[(lower, added)]
                    for lower, _, added in edge_defs
                    if added == block_name
                ]
            ),
        )
        for block_name in block_order
    )

    ensemble_successful = {
        key
        for key, category in ensemble_edge_categories.items()
        if category == "generalizing"
    }
    refit_aware_successful = {
        key
        for key, category in refit_aware_edge_categories.items()
        if category == "robust_generalizing"
    }
    total_paths = math.factorial(len(block_order))
    ensemble_paths = _path_count(block_order, ensemble_successful)
    robust_paths = _path_count(block_order, refit_aware_successful)
    refit_path_status_tuple = tuple(refit_path_statuses)
    refit_path_stability = (
        "stable"
        if len(set(refit_path_status_tuple)) == 1
        else "refit_sensitive"
    )
    cell_count = len(group_order) * edge_count
    estimable_cell_count = len(eligible)

    return RefitInformationLatticeCertification(
        base_information=base,
        blocks=block_rows,
        node_count=len(score_by_subset),
        edge_count=edge_count,
        independent_group_count=len(group_order),
        refit_count=refit_count,
        refit_ids=ids,
        reference_refit_id=reference_id,
        familywise_confidence_level=float(familywise_confidence_level),
        nested_draws=nested_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        max_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=estimable_cell_count,
        all_cells_estimable=bool(estimable_cell_count == cell_count),
        total_admissible_path_count=total_paths,
        reference_point_full_transfer_path_count=reference_point.full_transfer_path_count,
        reference_point_path_status=reference_point.path_status,
        reference_certified_full_transfer_path_count=reference_certification.robust_full_transfer_path_count,
        reference_certified_path_status=reference_certification.certified_path_status,
        refit_point_full_transfer_path_counts=tuple(refit_path_counts),
        refit_point_path_statuses=refit_path_status_tuple,
        refit_path_stability=refit_path_stability,
        ensemble_point_full_transfer_path_count=ensemble_paths,
        ensemble_point_path_status=_path_status(
            ensemble_paths, total_paths
        ),
        refit_aware_full_transfer_path_count=robust_paths,
        refit_aware_path_status=_path_status(robust_paths, total_paths),
        selected_refit_draw_counts=tuple(
            int(value)
            for value in np.bincount(
                selected_refits, minlength=refit_count
            )
        ),
        same_selected_refit_shared_across_all_group_edge_cells=True,
        same_block_draw_shared_across_edges_within_group=True,
        automatic_refit_scheme_inference=False,
        reference_fit_can_override_refit_aware_failure=False,
        best_path_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
        edges=tuple(edge_rows),
        block_summaries=block_summaries,
        reference_point_audit=reference_point,
        reference_fit_certification=reference_certification,
    )
