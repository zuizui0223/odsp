"""Command-line entry point for executable ODSP endpoint contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .endpoint_contract import run_endpoint_contract


def _write_receipt(receipt: dict[str, object], out: str | None) -> None:
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out is None or out == "-":
        print(text, end="")
        return
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odsp",
        description="Run explicit state-resolved ecological prediction contracts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser(
        "run",
        help="execute an endpoint contract and emit a deterministic receipt",
    )
    run.add_argument("--contract", required=True, help="path to endpoint contract JSON")
    run.add_argument(
        "--out",
        help="receipt path; omit or use '-' to write JSON to stdout",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        receipt = run_endpoint_contract(args.contract)
        _write_receipt(receipt, args.out)
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
