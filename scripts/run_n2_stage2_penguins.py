#!/usr/bin/env python3
"""Run the single fresh Palmer Penguins analysis for frozen N2 stage 2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.n2_stage2_penguins import run_penguins_stage2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-csv", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = run_penguins_stage2(args.raw_csv, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "prepared_row_count": result["source"]["prepared_row_count"],
                "naive_status": result["naive_pooled_gain"]["mean_gain_status"],
                "corrected_status": result["audit_context_gain"]["mean_gain_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
