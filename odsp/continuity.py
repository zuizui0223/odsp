"""Occurrence-conditioned environmental continuity analysis.

ODSP does not interpret support values as occurrence probabilities.  It treats
an externally supplied support field as a weighted geographical graph and asks
how strongly each supported location remains connected to known occurrences.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math

import numpy as np
import pandas as pd

from .patches import haversine_distance_m


@dataclass(frozen=True)
class EnvironmentalContinuityConfig:
    """Frozen graph and interpretation settings."""

    link_distance_m: float = 1_000.0
    occurrence_anchor_distance_m: float = 1_000.0
    strong_continuity_threshold: float = 0.65
    weak_continuity_threshold: float = 0.35

    def validate(self) -> None:
        if self.link_distance_m <= 0:
            raise ValueError("link_distance_m must be positive")
        if self.occurrence_anchor_distance_m < 0:
            raise ValueError("occurrence_anchor_distance_m must be non-negative")
        if not 0 <= self.weak_continuity_threshold <= self.strong_continuity_threshold <= 1:
            raise ValueError("continuity thresholds must satisfy 0 <= weak <= strong <= 1")


def _validated_support(frame: pd.DataFrame, support_col: str) -> pd.DataFrame:
    required = {"latitude", "longitude", support_col}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"support field is missing columns: {', '.join(sorted(missing))}")
    work = frame.copy().reset_index(drop=True)
    for column in ("latitude", "longitude", support_col):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["latitude", "longitude", support_col]).reset_index(drop=True)
    work[support_col] = work[support_col].clip(0.0, 1.0)
    return work


def _adjacency(work: pd.DataFrame, link_distance_m: float) -> list[list[int]]:
    adjacency: list[list[int]] = [[] for _ in range(len(work))]
    lats = work.latitude.to_numpy(float)
    lons = work.longitude.to_numpy(float)
    for i in range(len(work)):
        distances = haversine_distance_m(lats[i], lons[i], lats[i + 1 :], lons[i + 1 :])
        for j in (np.flatnonzero(distances <= link_distance_m) + i + 1).tolist():
            adjacency[i].append(j)
            adjacency[j].append(i)
    return adjacency


def _anchor_nodes(work: pd.DataFrame, occurrences: pd.DataFrame, max_distance_m: float) -> set[int]:
    required = {"latitude", "longitude"}
    missing = required - set(occurrences.columns)
    if missing:
        raise ValueError(f"occurrences is missing columns: {', '.join(sorted(missing))}")
    known = occurrences.copy()
    known["latitude"] = pd.to_numeric(known["latitude"], errors="coerce")
    known["longitude"] = pd.to_numeric(known["longitude"], errors="coerce")
    known = known.dropna(subset=["latitude", "longitude"])
    anchors: set[int] = set()
    if work.empty or known.empty:
        return anchors
    lats = work.latitude.to_numpy(float)
    lons = work.longitude.to_numpy(float)
    for row in known[["latitude", "longitude"]].itertuples(index=False):
        distances = haversine_distance_m(row.latitude, row.longitude, lats, lons)
        position = int(np.argmin(distances))
        if float(distances[position]) <= max_distance_m:
            anchors.add(position)
    return anchors


def environmental_continuity(
    support_field: pd.DataFrame,
    occurrences: pd.DataFrame,
    *,
    support_col: str = "candidate_support",
    config: EnvironmentalContinuityConfig | None = None,
) -> pd.DataFrame:
    """Calculate maximum bottleneck support from known-occurrence anchors.

    For node ``v``, the continuity value is

    ``max_path min_node_support(path)``

    over all geographical graph paths from any anchored occurrence node to
    ``v``.  A high value means that a path can reach the node without crossing
    a low-support bottleneck.  This is a structural property of the support
    field, not an estimate of presence probability.
    """

    cfg = config or EnvironmentalContinuityConfig()
    cfg.validate()
    work = _validated_support(support_field, support_col)
    if work.empty:
        return work.assign(
            occurrence_continuity=pd.Series(dtype=float),
            environmental_continuity_class=pd.Series(dtype=str),
            is_occurrence_anchor=pd.Series(dtype=bool),
        )

    adjacency = _adjacency(work, cfg.link_distance_m)
    anchors = _anchor_nodes(work, occurrences, cfg.occurrence_anchor_distance_m)
    support = work[support_col].to_numpy(float)
    capacity = np.zeros(len(work), dtype=float)
    queue: list[tuple[float, int]] = []
    for node in anchors:
        capacity[node] = support[node]
        heapq.heappush(queue, (-capacity[node], node))

    while queue:
        negative_value, node = heapq.heappop(queue)
        value = -negative_value
        if value < capacity[node]:
            continue
        for neighbour in adjacency[node]:
            proposal = min(value, support[neighbour])
            if proposal > capacity[neighbour]:
                capacity[neighbour] = proposal
                heapq.heappush(queue, (-proposal, neighbour))

    labels: list[str] = []
    for node_support, continuity in zip(support, capacity):
        if continuity >= cfg.strong_continuity_threshold:
            labels.append("continuous_environmental_extension")
        elif continuity >= cfg.weak_continuity_threshold:
            labels.append("weak_neck_extension")
        elif node_support >= cfg.strong_continuity_threshold:
            labels.append("detached_environmental_analogue")
        else:
            labels.append("unsupported_or_low_support")

    work["occurrence_continuity"] = capacity
    work["environmental_bottleneck_depth"] = np.maximum(0.0, support - capacity)
    work["environmental_continuity_class"] = labels
    work["is_occurrence_anchor"] = work.index.to_series().isin(anchors).to_numpy()
    return work


def summarize_continuity(annotated: pd.DataFrame) -> pd.DataFrame:
    """Summarize the structural classes and bottleneck values."""
    required = {
        "environmental_continuity_class",
        "occurrence_continuity",
        "environmental_bottleneck_depth",
    }
    missing = required - set(annotated.columns)
    if missing:
        raise ValueError(f"annotated field is missing columns: {', '.join(sorted(missing))}")
    if annotated.empty:
        return pd.DataFrame()
    return (
        annotated.groupby("environmental_continuity_class", as_index=False)
        .agg(
            node_count=("environmental_continuity_class", "size"),
            continuity_mean=("occurrence_continuity", "mean"),
            continuity_min=("occurrence_continuity", "min"),
            bottleneck_depth_mean=("environmental_bottleneck_depth", "mean"),
        )
        .sort_values("environmental_continuity_class")
        .reset_index(drop=True)
    )
