#!/usr/bin/env python3
"""Run the ODSP Campanula case from frozen candidate and occurrence CSVs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from odsp import (
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    annotate_occurrence_connectivity,
    build_candidate_patches,
    cluster_detections,
    connectivity_sensitivity,
    incremental_recovery_summary,
    patch_recovery_table,
    summarize_candidate_patches,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, help="CSV with latitude, longitude, candidate_support")
    parser.add_argument("--occurrences", required=True, help="Historical occurrence CSV")
    parser.add_argument("--detections", default=str(Path(__file__).with_name("locations_2026.csv")))
    parser.add_argument("--output", default=str(Path(__file__).with_name("results")))
    return parser.parse_args()


def main():
    args = parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    candidates = pd.read_csv(args.candidates)
    occurrences = pd.read_csv(args.occurrences)
    detections = pd.read_csv(args.detections)

    patches = build_candidate_patches(candidates, config=CandidatePatchConfig())
    annotated = annotate_occurrence_connectivity(patches, occurrences, OccurrenceConnectivityConfig())
    clusters = cluster_detections(detections, radius_m=500, group_col="island")
    recovery = patch_recovery_table(annotated, clusters)
    incremental = incremental_recovery_summary(annotated, clusters)
    labels, stability = connectivity_sensitivity(
        patches,
        occurrences,
        occurrence_link_distances_m=(250, 500, 750, 1000),
        candidate_link_distances_m=(500, 750, 1000),
        near_max_distances_m=(3000, 5000, 8000, 12000),
    )

    annotated.to_csv(output / "candidate_patch_members.csv", index=False)
    summarize_candidate_patches(annotated).to_csv(output / "candidate_patch_summary.csv", index=False)
    clusters.to_csv(output / "detection_clusters.csv", index=False)
    recovery.to_csv(output / "cluster_recovery.csv", index=False)
    incremental.to_csv(output / "incremental_recovery.csv", index=False)
    labels.to_csv(output / "connectivity_labels_by_setting.csv", index=False)
    stability.to_csv(output / "connectivity_stability.csv", index=False)
    manifest = {
        "status": "development_case_not_untouched_confirmation",
        "candidate_rows": int(len(candidates)),
        "historical_occurrence_rows": int(len(occurrences)),
        "positive_detection_rows": int(len(detections)),
        "detection_clusters": int(len(clusters)),
        "candidate_patches": int(annotated.candidate_patch_id.nunique()) if not annotated.empty else 0,
        "field_data_used_for_patch_construction": False,
        "field_data_used_for_evaluation": True,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
