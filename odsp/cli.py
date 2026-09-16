"""Command-line entry point for executable ODSP contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .endpoint_contract import run_endpoint_contract
from .external_freeze_manifest import create_external_freeze_manifest
from .external_paired_freeze_manifest import create_paired_external_freeze_manifest
from .information_transfer_contract import run_information_transfer_contract
from .refit_information_transfer_contract import run_refit_information_transfer_contract
from .untouched_external_refit_positive_contract_v2 import (
    run_untouched_external_refit_positive_contract_v2,
)
from .untouched_external_refit_shared_block_positive_contract_v3 import (
    run_untouched_external_refit_shared_block_positive_contract_v3,
)


_EXPECTED_USER_ERRORS = (ValueError, TypeError, OSError, ImportError)


def _write_receipt(receipt: dict[str, object], out: str | None) -> None:
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out is None or out == "-":
        print(text, end="")
        return
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _add_common_contract_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--contract", required=True, help="path to contract JSON")
    parser.add_argument(
        "--out",
        help="receipt path; omit or use '-' to write JSON to stdout",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="re-raise expected input/configuration errors with a Python traceback",
    )


def _add_debug_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--debug",
        action="store_true",
        help="re-raise expected input/configuration errors with a Python traceback",
    )


def _add_freeze_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", required=True, help="path to freeze-plan JSON")
    parser.add_argument(
        "--manifest-out",
        required=True,
        help="new freeze-manifest path; existing files are never overwritten",
    )
    parser.add_argument(
        "--out",
        help="freeze receipt path; omit or use '-' to write JSON to stdout",
    )
    _add_debug_argument(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odsp",
        description="Run explicit ecological prediction and information-transfer contracts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser(
        "run",
        help="fit a bundled reference learner and execute a state-prediction contract",
    )
    _add_common_contract_arguments(run)
    transfer = subparsers.add_parser(
        "transfer",
        help=(
            "audit externally generated held-out score columns under a strict "
            "information filtration"
        ),
    )
    _add_common_contract_arguments(transfer)
    transfer_refits = subparsers.add_parser(
        "transfer-refits",
        help=(
            "audit a long-form ensemble of upstream refit score tables under a "
            "strict information filtration"
        ),
    )
    _add_common_contract_arguments(transfer_refits)

    freeze_external = subparsers.add_parser(
        "freeze-refits-external",
        help=(
            "create a non-overwriting pre-outcome semantic freeze manifest for "
            "independent-group external validation"
        ),
    )
    _add_freeze_arguments(freeze_external)
    external_refits = subparsers.add_parser(
        "transfer-refits-external",
        help=(
            "certify one-sided positive transfer across a frozen upstream-refit "
            "ensemble on untouched independent-group external validation rows"
        ),
    )
    _add_common_contract_arguments(external_refits)

    freeze_external_paired = subparsers.add_parser(
        "freeze-refits-external-paired",
        help=(
            "create a non-overwriting pre-outcome semantic freeze manifest for "
            "exact shared-block paired external validation"
        ),
    )
    _add_freeze_arguments(freeze_external_paired)
    external_refits_paired = subparsers.add_parser(
        "transfer-refits-external-paired",
        help=(
            "certify all-refit one-sided positive transfer on untouched external "
            "validation groups paired on exactly the same shared blocks"
        ),
    )
    _add_common_contract_arguments(external_refits_paired)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            receipt = run_endpoint_contract(args.contract)
        elif args.command == "transfer":
            receipt = run_information_transfer_contract(args.contract)
        elif args.command == "transfer-refits":
            receipt = run_refit_information_transfer_contract(args.contract)
        elif args.command == "freeze-refits-external":
            receipt = create_external_freeze_manifest(args.plan, args.manifest_out)
        elif args.command == "transfer-refits-external":
            receipt = run_untouched_external_refit_positive_contract_v2(args.contract)
        elif args.command == "freeze-refits-external-paired":
            receipt = create_paired_external_freeze_manifest(args.plan, args.manifest_out)
        elif args.command == "transfer-refits-external-paired":
            receipt = run_untouched_external_refit_shared_block_positive_contract_v3(
                args.contract
            )
        else:  # pragma: no cover - argparse constrains the command.
            raise AssertionError(f"unhandled command: {args.command}")
        _write_receipt(receipt, args.out)
        return 0
    except _EXPECTED_USER_ERRORS as exc:
        if getattr(args, "debug", False):
            raise
        print(f"odsp: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
