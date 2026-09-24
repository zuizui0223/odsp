#!/usr/bin/env python3
"""Build an N2 -> N3 transfer-value payload from a receipt population_result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.transfer_value_handoff import build_population_transfer_value_handoff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--group-semantics", required=True)
    parser.add_argument("--population-cluster-semantics")
    parser.add_argument("--source-contract")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    population = receipt.get("population_result")
    if not isinstance(population, dict):
        raise ValueError("receipt must contain a population_result object")

    payload = build_population_transfer_value_handoff(
        evidence_id=args.evidence_id,
        population_result=population,
        group_semantics=args.group_semantics,
        population_cluster_semantics=args.population_cluster_semantics,
        source_receipt=args.receipt.name,
        source_contract=args.source_contract,
    ).as_dict()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "evidence_id": payload["evidence_id"],
                "fingerprint": payload["fingerprint"],
                "step_count": len(payload["steps"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
