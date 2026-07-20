#!/usr/bin/env python3
"""Run the frozen ODSP benchmark from complete ACSP fold exports.

Incomplete or missing legacy exports are retained in the audit output and are
never silently removed from the frozen cohort.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from odsp import (
    ACSPExportLayout,
    BenchmarkConfig,
    benchmark_status_table,
    evaluate_benchmark_unit,
    inputs_from_acsp_export,
    load_frozen_manifest,
    summarize_benchmark_cohort,
)


def parse_layout(value: str) -> ACSPExportLayout:
    """Parse COHORT=PATH command-line values."""
    cohort, separator, root = value.partition("=")
    if not separator or not cohort.strip() or not root.strip():
        raise argparse.ArgumentTypeError("layout must be COHORT=PATH")
    return ACSPExportLayout(Path(root).expanduser(), cohort.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).with_name("frozen_taxon_region_manifest.csv")),
        help="Frozen taxon-region manifest CSV",
    )
    parser.add_argument(
        "--layout",
        action="append",
        type=parse_layout,
        required=True,
        help="ACSP export root as COHORT=PATH; repeat once per cohort",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_name("results")),
        help="Output directory",
    )
    parser.add_argument(
        "--support-column",
        default="integrated_support_score",
        help="Preferred support column in ACSP candidate exports",
    )
    return parser.parse_args()


def run_benchmark(
    manifest_path: str | Path,
    layouts: list[ACSPExportLayout],
    output_dir: str | Path,
    *,
    support_column: str = "integrated_support_score",
    config: BenchmarkConfig | None = None,
) -> dict[str, object]:
    """Execute all frozen units and write auditable cohort outputs."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = load_frozen_manifest(manifest_path)
    adapted = inputs_from_acsp_export(
        manifest,
        layouts,
        support_col=support_column,
    )

    metric_frames: list[pd.DataFrame] = []
    adapter_rows: list[dict[str, object]] = []
    for item in adapted:
        audit = {
            "taxon": item.unit.taxon,
            "region": item.unit.region,
            "fold_id": item.unit.fold_id,
            **item.audit,
        }
        adapter_rows.append(audit)
        if item.audit.get("status") != "ready":
            continue
        metrics, _, _ = evaluate_benchmark_unit(
            item.unit,
            item.training_occurrences,
            item.candidate_support,
            item.held_out_occurrences,
            config=config,
        )
        metric_frames.append(metrics)

    metrics = pd.concat(metric_frames, ignore_index=True) if metric_frames else pd.DataFrame()
    adapter_audit = pd.DataFrame(adapter_rows)
    adapter_audit.to_csv(output / "adapter_audit.csv", index=False)

    if metrics.empty:
        status = pd.DataFrame()
        summary = pd.DataFrame()
    else:
        metrics.to_csv(output / "unit_metrics.csv", index=False)
        status = benchmark_status_table(metrics)
        status.to_csv(output / "unit_status.csv", index=False)
        summary = summarize_benchmark_cohort(metrics)
        summary.to_csv(output / "cohort_summary.csv", index=False)

    ready_units = int((adapter_audit.get("status", pd.Series(dtype=str)) == "ready").sum())
    blocked_units = int(len(adapter_audit) - ready_units)
    report = {
        "manifest_rows": int(len(manifest)),
        "adapted_units": int(len(adapted)),
        "ready_units": ready_units,
        "blocked_or_missing_units": blocked_units,
        "evaluated_units": int(
            metrics[["taxon", "region", "fold_id"]].drop_duplicates().shape[0]
        ) if not metrics.empty else 0,
        "metric_rows": int(len(metrics)),
        "status_counts": adapter_audit["status"].value_counts(dropna=False).to_dict()
        if "status" in adapter_audit.columns else {},
        "intention_to_evaluate_complete": blocked_units == 0,
    }
    (output / "run_manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main() -> None:
    args = parse_args()
    report = run_benchmark(
        args.manifest,
        args.layout,
        args.output,
        support_column=args.support_column,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
