#!/usr/bin/env python3
"""Run one deterministic shard of the frozen N2 stage-1 failure-mode experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.n2_failure_mode_stage1 import (
    load_stage1_contract,
    run_anchor_replicates,
    run_factorial_cells,
    scenario_grid,
)


def _factorial_indices(total: int, shard_index: int, shard_count: int) -> list[int]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid factorial shard coordinates")
    return [index for index in range(total) if index % shard_count == shard_index]


def _replicate_indices(total: int, shard_index: int, shard_count: int) -> list[int]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid replicate shard coordinates")
    return [index for index in range(total) if index % shard_count == shard_index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--mode", choices=("factorial", "anchor"), required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--anchor-index", type=int)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = load_stage1_contract(args.contract)
    if args.mode == "factorial":
        if args.anchor_index is not None:
            raise ValueError("--anchor-index is invalid in factorial mode")
        grid = scenario_grid(contract)
        indices = _factorial_indices(
            len(grid), int(args.shard_index), int(args.shard_count)
        )
        payload = run_factorial_cells(contract, cell_indices=indices)
        payload["shard_index"] = int(args.shard_index)
        payload["shard_count"] = int(args.shard_count)
    else:
        if args.anchor_index is None:
            raise ValueError("--anchor-index is required in anchor mode")
        execution = contract["confirmatory_anchor_execution"]
        total = int(execution["replicates_per_anchor"])
        indices = _replicate_indices(
            total, int(args.shard_index), int(args.shard_count)
        )
        payload = run_anchor_replicates(
            contract,
            anchor_index=int(args.anchor_index),
            replicate_indices=indices,
        )
        payload["replicate_shard_index"] = int(args.shard_index)
        payload["replicate_shard_count"] = int(args.shard_count)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "mode": args.mode,
                "output": args.out.as_posix(),
                "records": (
                    payload.get("cell_count")
                    if args.mode == "factorial"
                    else len(payload["replicate_indices"])
                ),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
