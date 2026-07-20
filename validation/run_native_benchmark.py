#!/usr/bin/env python3
"""Run ODSP from producer-agnostic native benchmark units."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from odsp.benchmark import benchmark_status_table, evaluate_benchmark_unit, summarize_benchmark_cohort
from odsp.benchmark_input import discover_native_benchmark_units, load_native_benchmark_unit


def run_benchmark(units_root: str | Path, output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics = []
    audit = []
    unit_paths = discover_native_benchmark_units(units_root)
    for unit_path in unit_paths:
        try:
            item = load_native_benchmark_unit(unit_path)
            result, _, _ = evaluate_benchmark_unit(
                item.unit,
                item.training_occurrences,
                item.candidate_support,
                item.held_out_occurrences,
            )
            result["support_method"] = str(item.provenance["support_method"])
            metrics.append(result)
            audit.append({"unit_path": str(unit_path), "status": "evaluated", "support_method": item.provenance["support_method"]})
        except Exception as exc:
            audit.append({"unit_path": str(unit_path), "status": "failed_input_contract", "error_type": type(exc).__name__, "error_message": str(exc)})
    audit_frame = pd.DataFrame(audit)
    audit_frame.to_csv(output / "input_audit.csv", index=False)
    metric_frame = pd.concat(metrics, ignore_index=True) if metrics else pd.DataFrame()
    if not metric_frame.empty:
        metric_frame.to_csv(output / "unit_metrics.csv", index=False)
        benchmark_status_table(metric_frame).to_csv(output / "unit_status.csv", index=False)
        summarize_benchmark_cohort(metric_frame).to_csv(output / "cohort_summary.csv", index=False)
    report = {
        "discovered_units": len(unit_paths),
        "evaluated_units": len(metrics),
        "failed_input_units": int((audit_frame.status == "failed_input_contract").sum()) if not audit_frame.empty else 0,
        "support_methods": sorted(audit_frame.get("support_method", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()),
        "producer_specific_dependency": False,
    }
    (output / "run_manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units-root", required=True)
    parser.add_argument("--output", default="validation/results")
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.units_root, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
