"""Occurrence-defined survey patch construction in geographical space."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

EARTH_RADIUS_M = 6_371_008.8


def haversine_distance_m(lat, lon, other_lats, other_lons):
    lat1, lon1 = math.radians(float(lat)), math.radians(float(lon))
    lat2 = np.radians(np.asarray(other_lats, dtype=float))
    lon2 = np.radians(np.asarray(other_lons, dtype=float))
    a = np.sin((lat2-lat1)/2)**2 + math.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _locations(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    missing = {"latitude", "longitude"} - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(sorted(missing))}")
    out = frame.copy().reset_index(drop=True)
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    return out.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)


def connected_components(latitudes, longitudes, radius_m: float):
    if radius_m <= 0:
        raise ValueError("radius_m must be positive")
    n = len(latitudes)
    adjacency = [[] for _ in range(n)]
    for i in range(n):
        distances = haversine_distance_m(latitudes[i], longitudes[i], latitudes[i+1:], longitudes[i+1:])
        for j in (np.flatnonzero(distances <= radius_m) + i + 1).tolist():
            adjacency[i].append(j); adjacency[j].append(i)
    seen, result = set(), []
    for start in range(n):
        if start in seen: continue
        stack, component = [start], []
        seen.add(start)
        while stack:
            node = stack.pop(); component.append(node)
            for neighbour in adjacency[node]:
                if neighbour not in seen:
                    seen.add(neighbour); stack.append(neighbour)
        result.append(sorted(component))
    return result


@dataclass(frozen=True)
class CandidatePatchConfig:
    support_thresholds: tuple[float, ...] = (0.45, 0.55, 0.65)
    link_distance_m: float = 1_000.0
    min_patch_members: int = 2
    min_overlap_fraction: float = 0.5


@dataclass(frozen=True)
class OccurrenceConnectivityConfig:
    occurrence_link_distance_m: float = 500.0
    candidate_occurrence_link_distance_m: float = 750.0
    near_disconnected_max_distance_m: float = 5_000.0


def build_occurrence_patches(occurrences: pd.DataFrame, link_distance_m: float = 500.0) -> pd.DataFrame:
    known = _locations(occurrences, "occurrences")
    components = connected_components(known.latitude.to_numpy(), known.longitude.to_numpy(), link_distance_m)
    ids = {}
    for ordinal, component in enumerate(components, 1):
        for position in component:
            ids[position] = f"occurrence-patch-{ordinal:03d}"
    known["occurrence_patch_id"] = known.index.map(ids)
    return known


def build_candidate_patches(candidates: pd.DataFrame, support_col: str = "candidate_support", config: CandidatePatchConfig | None = None) -> pd.DataFrame:
    cfg = config or CandidatePatchConfig()
    work = _locations(candidates, "candidates")
    if support_col not in work:
        raise ValueError(f"candidates is missing support column: {support_col}")
    work[support_col] = pd.to_numeric(work[support_col], errors="coerce")
    work = work.dropna(subset=[support_col]).reset_index(drop=True)
    thresholds = tuple(sorted(set(cfg.support_thresholds)))
    by_threshold = {}
    for threshold in thresholds:
        eligible = work.index[work[support_col] >= threshold].to_numpy()
        subset = work.loc[eligible]
        by_threshold[threshold] = [set(eligible[c]) for c in connected_components(subset.latitude.to_numpy(), subset.longitude.to_numpy(), cfg.link_distance_m)]
    rows = []
    for ordinal, members in enumerate(by_threshold[thresholds[0]], 1):
        if len(members) < cfg.min_patch_members: continue
        represented = 0
        for components in by_threshold.values():
            overlap = max((len(members & c)/len(members) for c in components), default=0)
            represented += overlap >= cfg.min_overlap_fraction
        patch = work.loc[sorted(members)].copy()
        patch["candidate_patch_id"] = f"candidate-patch-{ordinal:03d}"
        patch["candidate_patch_persistence"] = represented / len(thresholds)
        patch["candidate_patch_support_mean"] = float(patch[support_col].mean())
        patch["candidate_patch_member_count"] = len(patch)
        rows.append(patch)
    return pd.concat(rows, ignore_index=True) if rows else work.iloc[0:0].assign(candidate_patch_id=pd.Series(dtype=str))


def annotate_occurrence_connectivity(candidate_members: pd.DataFrame, occurrences: pd.DataFrame, config: OccurrenceConnectivityConfig | None = None) -> pd.DataFrame:
    cfg = config or OccurrenceConnectivityConfig()
    if cfg.near_disconnected_max_distance_m < cfg.candidate_occurrence_link_distance_m:
        raise ValueError("near_disconnected_max_distance_m must be at least the connection distance")
    candidates = _locations(candidate_members, "candidate_members")
    if "candidate_patch_id" not in candidates:
        raise ValueError("candidate_members is missing candidate_patch_id")
    known = build_occurrence_patches(occurrences, cfg.occurrence_link_distance_m)
    output = []
    for patch_id, patch in candidates.groupby("candidate_patch_id", sort=True):
        best_distance, best_occurrence_patch = math.inf, None
        for row in patch[["latitude", "longitude"]].itertuples(index=False):
            distances = haversine_distance_m(row.latitude, row.longitude, known.latitude.to_numpy(), known.longitude.to_numpy())
            if len(distances) and float(distances.min()) < best_distance:
                pos = int(np.argmin(distances)); best_distance = float(distances[pos])
                best_occurrence_patch = known.iloc[pos]["occurrence_patch_id"]
        if best_distance <= cfg.candidate_occurrence_link_distance_m:
            label = "occurrence_patch_extension"
        elif best_distance <= cfg.near_disconnected_max_distance_m:
            label = "near_disconnected_occurrence_patch"
        else:
            label = "remote_candidate_patch"
        annotated = patch.copy()
        annotated["nearest_occurrence_patch_id"] = best_occurrence_patch
        annotated["candidate_occurrence_edge_distance_m"] = best_distance
        annotated["occurrence_patch_connectivity_class"] = label
        output.append(annotated)
    return pd.concat(output, ignore_index=True) if output else pd.DataFrame()
