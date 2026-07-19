"""Occurrence-defined survey patch construction and validation.

ODSP operates in geographical space.  Graph labels are operational survey
classes under declared distance rules; they do not establish biological
isolation, barriers, fragmentation, or occupancy probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

EARTH_RADIUS_M = 6_371_008.8
DEFAULT_RECOVERY_RADII_KM = (1.0, 2.0, 5.0, 10.0)


def haversine_distance_m(lat, lon, other_lats, other_lons):
    """Vectorized great-circle distance in metres."""
    lat1, lon1 = math.radians(float(lat)), math.radians(float(lon))
    lat2 = np.radians(np.asarray(other_lats, dtype=float))
    lon2 = np.radians(np.asarray(other_lons, dtype=float))
    a = np.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _locations(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if frame is None:
        raise ValueError(f"{name} must be a DataFrame")
    missing = {"latitude", "longitude"} - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(sorted(missing))}")
    out = frame.copy().reset_index(drop=True)
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    return out.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)


def connected_components(latitudes, longitudes, radius_m: float) -> list[list[int]]:
    """Connected components of a geographic radius graph."""
    if radius_m <= 0:
        raise ValueError("radius_m must be positive")
    lats = np.asarray(latitudes, dtype=float)
    lons = np.asarray(longitudes, dtype=float)
    if len(lats) != len(lons):
        raise ValueError("latitudes and longitudes must have equal length")
    n = len(lats)
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        distances = haversine_distance_m(lats[i], lons[i], lats[i + 1 :], lons[i + 1 :])
        for j in (np.flatnonzero(distances <= radius_m) + i + 1).tolist():
            adjacency[i].append(j)
            adjacency[j].append(i)
    seen: set[int] = set()
    result: list[list[int]] = []
    for start in range(n):
        if start in seen:
            continue
        stack, component = [start], []
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in adjacency[node]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        result.append(sorted(component))
    return result


@dataclass(frozen=True)
class CandidatePatchConfig:
    support_thresholds: tuple[float, ...] = (0.45, 0.55, 0.65)
    link_distance_m: float = 1_000.0
    min_patch_members: int = 2
    min_overlap_fraction: float = 0.5

    def validate(self) -> tuple[float, ...]:
        thresholds = tuple(sorted({float(value) for value in self.support_thresholds}))
        if not thresholds:
            raise ValueError("support_thresholds must not be empty")
        if thresholds[0] < 0 or thresholds[-1] > 1:
            raise ValueError("support_thresholds must lie in [0, 1]")
        if self.link_distance_m <= 0:
            raise ValueError("link_distance_m must be positive")
        if self.min_patch_members < 1:
            raise ValueError("min_patch_members must be at least one")
        if not 0 < self.min_overlap_fraction <= 1:
            raise ValueError("min_overlap_fraction must lie in (0, 1]")
        return thresholds


@dataclass(frozen=True)
class OccurrenceConnectivityConfig:
    occurrence_link_distance_m: float = 500.0
    candidate_occurrence_link_distance_m: float = 750.0
    near_disconnected_max_distance_m: float = 5_000.0

    def validate(self) -> None:
        if self.occurrence_link_distance_m <= 0:
            raise ValueError("occurrence_link_distance_m must be positive")
        if self.candidate_occurrence_link_distance_m < 0:
            raise ValueError("candidate_occurrence_link_distance_m must be non-negative")
        if self.near_disconnected_max_distance_m < self.candidate_occurrence_link_distance_m:
            raise ValueError("near_disconnected_max_distance_m must be at least the connection distance")


def build_occurrence_patches(occurrences: pd.DataFrame, link_distance_m: float = 500.0) -> pd.DataFrame:
    """Assign known occurrences to geographic radius-graph patches."""
    if link_distance_m <= 0:
        raise ValueError("link_distance_m must be positive")
    known = _locations(occurrences, "occurrences")
    if known.empty:
        return known.assign(occurrence_patch_id=pd.Series(dtype=str))
    components = connected_components(known.latitude.to_numpy(), known.longitude.to_numpy(), link_distance_m)
    ids: dict[int, str] = {}
    for ordinal, component in enumerate(components, 1):
        for position in component:
            ids[position] = f"occurrence-patch-{ordinal:03d}"
    known["occurrence_patch_id"] = known.index.map(ids)
    return known


def build_candidate_patches(
    candidates: pd.DataFrame,
    support_col: str = "candidate_support",
    config: CandidatePatchConfig | None = None,
) -> pd.DataFrame:
    """Construct threshold-persistent candidate patches and retain members."""
    cfg = config or CandidatePatchConfig()
    thresholds = cfg.validate()
    work = _locations(candidates, "candidates")
    if support_col not in work.columns:
        raise ValueError(f"candidates is missing support column: {support_col}")
    work[support_col] = pd.to_numeric(work[support_col], errors="coerce")
    work = work.dropna(subset=[support_col]).reset_index(drop=True)
    work[support_col] = work[support_col].clip(0, 1)
    if work.empty:
        return work.assign(candidate_patch_id=pd.Series(dtype=str))

    by_threshold: dict[float, list[set[int]]] = {}
    for threshold in thresholds:
        eligible = work.index[work[support_col] >= threshold].to_numpy(dtype=int)
        subset = work.loc[eligible]
        components = connected_components(subset.latitude.to_numpy(), subset.longitude.to_numpy(), cfg.link_distance_m)
        by_threshold[threshold] = [{int(eligible[position]) for position in component} for component in components]

    rows: list[pd.DataFrame] = []
    for ordinal, members in enumerate(by_threshold[thresholds[0]], 1):
        if len(members) < cfg.min_patch_members:
            continue
        represented = 0
        for components in by_threshold.values():
            overlap = max((len(members & component) / len(members) for component in components), default=0.0)
            represented += int(overlap >= cfg.min_overlap_fraction)
        patch = work.loc[sorted(members)].copy()
        patch_id = f"candidate-patch-{ordinal:03d}"
        patch["candidate_patch_id"] = patch_id
        patch["candidate_patch_persistence"] = represented / len(thresholds)
        patch["candidate_patch_support_mean"] = float(patch[support_col].mean())
        patch["candidate_patch_member_count"] = len(patch)
        patch["candidate_patch_centroid_latitude"] = float(patch.latitude.mean())
        patch["candidate_patch_centroid_longitude"] = float(patch.longitude.mean())
        rows.append(patch)
    return pd.concat(rows, ignore_index=True) if rows else work.iloc[0:0].assign(candidate_patch_id=pd.Series(dtype=str))


def summarize_candidate_patches(candidate_members: pd.DataFrame) -> pd.DataFrame:
    """Return one auditable row per candidate patch."""
    if candidate_members is None or candidate_members.empty:
        return pd.DataFrame()
    required = {"candidate_patch_id", "candidate_patch_persistence", "candidate_patch_support_mean", "candidate_patch_member_count"}
    missing = required - set(candidate_members.columns)
    if missing:
        raise ValueError(f"candidate_members is missing columns: {', '.join(sorted(missing))}")
    return candidate_members.drop_duplicates("candidate_patch_id").sort_values("candidate_patch_id").reset_index(drop=True)


def annotate_occurrence_connectivity(
    candidate_members: pd.DataFrame,
    occurrences: pd.DataFrame,
    config: OccurrenceConnectivityConfig | None = None,
) -> pd.DataFrame:
    """Classify candidate patches relative to known occurrence patches."""
    cfg = config or OccurrenceConnectivityConfig()
    cfg.validate()
    candidates = _locations(candidate_members, "candidate_members")
    if "candidate_patch_id" not in candidates.columns:
        raise ValueError("candidate_members is missing candidate_patch_id")
    if candidates.empty:
        return candidates
    known = build_occurrence_patches(occurrences, cfg.occurrence_link_distance_m)
    output: list[pd.DataFrame] = []
    for _, patch in candidates.groupby("candidate_patch_id", sort=True):
        best_distance, best_occurrence_patch = math.inf, None
        if not known.empty:
            known_lats = known.latitude.to_numpy(float)
            known_lons = known.longitude.to_numpy(float)
            for row in patch[["latitude", "longitude"]].itertuples(index=False):
                distances = haversine_distance_m(row.latitude, row.longitude, known_lats, known_lons)
                position = int(np.argmin(distances))
                if float(distances[position]) < best_distance:
                    best_distance = float(distances[position])
                    best_occurrence_patch = str(known.iloc[position]["occurrence_patch_id"])
        if best_distance <= cfg.candidate_occurrence_link_distance_m:
            label = "occurrence_patch_extension"
        elif best_distance <= cfg.near_disconnected_max_distance_m:
            label = "near_disconnected_occurrence_patch"
        else:
            label = "remote_candidate_patch"
        annotated = patch.copy()
        annotated["nearest_occurrence_patch_id"] = best_occurrence_patch
        annotated["candidate_occurrence_edge_distance_m"] = best_distance
        annotated["candidate_occurrence_gap_width_m"] = max(0.0, best_distance - cfg.candidate_occurrence_link_distance_m)
        annotated["occurrence_patch_connectivity_class"] = label
        output.append(annotated)
    return pd.concat(output, ignore_index=True)


def cluster_detections(detections: pd.DataFrame, radius_m: float = 500.0, group_col: str | None = None) -> pd.DataFrame:
    """Cluster field detections and return observed medoids."""
    work = _locations(detections, "detections")
    if work.empty:
        return work.assign(cluster_id=pd.Series(dtype=str))
    groups = [("all", work)] if group_col is None else list(work.groupby(group_col, sort=True, dropna=False))
    rows: list[pd.Series] = []
    ordinal = 0
    for group_value, group in groups:
        group = group.reset_index(drop=True)
        for component in connected_components(group.latitude.to_numpy(), group.longitude.to_numpy(), radius_m):
            ordinal += 1
            subset = group.iloc[component]
            totals = []
            for row in subset[["latitude", "longitude"]].itertuples(index=False):
                totals.append(float(haversine_distance_m(row.latitude, row.longitude, subset.latitude.to_numpy(), subset.longitude.to_numpy()).sum()))
            medoid = subset.iloc[int(np.argmin(totals))].copy()
            medoid["cluster_id"] = f"detection-cluster-{ordinal:03d}"
            medoid["cluster_member_count"] = len(subset)
            if group_col is not None:
                medoid[group_col] = group_value
            rows.append(medoid)
    return pd.DataFrame(rows).reset_index(drop=True)


def patch_recovery_table(
    candidate_members: pd.DataFrame,
    detection_clusters: pd.DataFrame,
    radii_km: Iterable[float] = DEFAULT_RECOVERY_RADII_KM,
) -> pd.DataFrame:
    """Evaluate clusters against nearest patch member, never only a centroid."""
    clusters = _locations(detection_clusters, "detection_clusters")
    candidates = _locations(candidate_members, "candidate_members")
    radii = tuple(sorted({float(value) for value in radii_km if float(value) >= 0}))
    rows: list[dict[str, object]] = []
    for index, cluster in clusters.iterrows():
        row: dict[str, object] = {"cluster_id": cluster.get("cluster_id", f"cluster-{index + 1}")}
        if candidates.empty:
            nearest_distance, nearest_patch, nearest_class = math.inf, None, None
        else:
            distances = haversine_distance_m(cluster.latitude, cluster.longitude, candidates.latitude.to_numpy(), candidates.longitude.to_numpy())
            position = int(np.argmin(distances))
            nearest = candidates.iloc[position]
            nearest_distance = float(distances[position])
            nearest_patch = nearest.get("candidate_patch_id")
            nearest_class = nearest.get("occurrence_patch_connectivity_class")
        row.update({"nearest_patch_id": nearest_patch, "nearest_patch_class": nearest_class, "nearest_patch_distance_m": nearest_distance})
        for radius in radii:
            row[f"recovered_within_{radius:g}km"] = nearest_distance <= radius * 1000
        rows.append(row)
    return pd.DataFrame(rows)


def incremental_recovery_summary(
    annotated_members: pd.DataFrame,
    detection_clusters: pd.DataFrame,
    radii_km: Iterable[float] = DEFAULT_RECOVERY_RADII_KM,
) -> pd.DataFrame:
    """Compare extension-only with extension plus near-disconnected patches."""
    classes = annotated_members.get("occurrence_patch_connectivity_class", pd.Series(dtype=str))
    extension = annotated_members[classes.eq("occurrence_patch_extension")]
    expanded = annotated_members[classes.isin(["occurrence_patch_extension", "near_disconnected_occurrence_patch"])]
    ext = patch_recovery_table(extension, detection_clusters, radii_km)
    full = patch_recovery_table(expanded, detection_clusters, radii_km)
    rows = []
    for radius in sorted({float(value) for value in radii_km if float(value) >= 0}):
        column = f"recovered_within_{radius:g}km"
        ext_recall = float(ext[column].mean()) if not ext.empty else 0.0
        full_recall = float(full[column].mean()) if not full.empty else 0.0
        rows.append({"radius_km": radius, "extension_only_recall": ext_recall, "extension_plus_near_disconnected_recall": full_recall, "incremental_recall": full_recall - ext_recall})
    return pd.DataFrame(rows)


def connectivity_sensitivity(
    candidate_members: pd.DataFrame,
    occurrences: pd.DataFrame,
    occurrence_link_distances_m: Sequence[float],
    candidate_link_distances_m: Sequence[float],
    near_max_distances_m: Sequence[float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return labels by setting and per-patch class frequencies."""
    label_rows: list[dict[str, object]] = []
    setting_id = 0
    for occurrence_link, candidate_link, near_max in product(occurrence_link_distances_m, candidate_link_distances_m, near_max_distances_m):
        if near_max < candidate_link:
            continue
        setting_id += 1
        cfg = OccurrenceConnectivityConfig(float(occurrence_link), float(candidate_link), float(near_max))
        annotated = annotate_occurrence_connectivity(candidate_members, occurrences, cfg)
        for patch_id, patch in annotated.groupby("candidate_patch_id", sort=True):
            label_rows.append({"setting_id": setting_id, "occurrence_link_distance_m": occurrence_link, "candidate_occurrence_link_distance_m": candidate_link, "near_disconnected_max_distance_m": near_max, "candidate_patch_id": patch_id, "connectivity_class": patch.iloc[0]["occurrence_patch_connectivity_class"]})
    labels = pd.DataFrame(label_rows)
    if labels.empty:
        return labels, pd.DataFrame()
    counts = labels.groupby(["candidate_patch_id", "connectivity_class"]).size().rename("count").reset_index()
    totals = labels.groupby("candidate_patch_id").setting_id.nunique().rename("setting_count").reset_index()
    stability = counts.merge(totals, on="candidate_patch_id")
    stability["class_frequency"] = stability["count"] / stability["setting_count"]
    return labels, stability.sort_values(["candidate_patch_id", "connectivity_class"]).reset_index(drop=True)
