"""Command-line entry point for executable ODSP contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

from .confirmatory_method_routing import route_confirmatory_method
from .endpoint_contract import run_endpoint_contract
from .external_freeze_manifest import create_external_freeze_manifest
from .external_paired_freeze_manifest import create_paired_external_freeze_manifest
from .external_paired_lattice_freeze_manifest import (
    create_paired_external_lattice_freeze_manifest,
)
from .information_transfer_contract import run_information_transfer_contract
from .refit_information_transfer_contract import run_refit_information_transfer_contract
from .training_process_external_contract import (
    run_training_process_v5_external_contract,
)
from .training_process_external_freeze_v1 import (
    create_training_process_v5_external_freeze,
)
from .training_process_freeze_manifest import (
    create_training_process_freeze_manifest,
)
from .training_process_managed_external_scoring import (
    run_managed_external_scoring_v1,
)
from .training_process_managed_generation import (
    run_managed_training_process_generation,
)
from .untouched_external_refit_positive_contract_v2 import (
    run_untouched_external_refit_positive_contract_v2,
)
from .untouched_external_refit_shared_block_positive_contract_v3 import (
    run_untouched_external_refit_shared_block_positive_contract_v3,
)
from .untouched_external_refit_shared_block_positive_lattice_contract_v4 import (
    run_untouched_external_paired_all_refit_lattice_contract_v4,
)


_EXPECTED_USER_ERRORS = (ValueError, TypeError, OSError, ImportError)
_ROUTE_REQUEST_FIELDS = {
    "alternative",
    "validation_design",
    "information_structure",
    "upstream_refits",
    "external_validation",
    "contrast_count",
    "information_block_count",
}
_ROUTE_REQUIRED_FIELDS = {
    "alternative",
    "validation_design",
    "information_structure",
    "upstream_refits",
    "external_validation",
}
_TRANSFER_VARIANTS = (
    "scores",
    "refits",
    "external-refits",
    "external-paired",
    "external-paired-lattice",
)
_FREEZE_VARIANTS = ("external", "paired", "paired-lattice")


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


def _add_method_route_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--request",
        required=True,
        help="path to a machine-readable method-routing request JSON",
    )
    parser.add_argument(
        "--out",
        help="routing receipt path; omit or use '-' to write JSON to stdout",
    )
    _add_debug_argument(parser)


def _run_transfer_variant(variant: str, contract: str | Path) -> dict[str, object]:
    runners = {
        "scores": run_information_transfer_contract,
        "refits": run_refit_information_transfer_contract,
        "external-refits": run_untouched_external_refit_positive_contract_v2,
        "external-paired": run_untouched_external_refit_shared_block_positive_contract_v3,
        "external-paired-lattice": run_untouched_external_paired_all_refit_lattice_contract_v4,
    }
    try:
        runner = runners[variant]
    except KeyError as exc:  # pragma: no cover - argparse constrains the variant.
        raise ValueError(f"unknown transfer variant: {variant}") from exc
    return runner(contract)


def _run_freeze_variant(
    variant: str,
    plan: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    runners = {
        "external": create_external_freeze_manifest,
        "paired": create_paired_external_freeze_manifest,
        "paired-lattice": create_paired_external_lattice_freeze_manifest,
    }
    try:
        runner = runners[variant]
    except KeyError as exc:  # pragma: no cover - argparse constrains the variant.
        raise ValueError(f"unknown freeze variant: {variant}") from exc
    return runner(plan, manifest_out)


def _run_method_route(path: str | Path) -> dict[str, object]:
    request_path = Path(path)
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("method-route request is not valid JSON") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("method-route request must be a JSON object")
    unknown = sorted(set(raw) - _ROUTE_REQUEST_FIELDS)
    if unknown:
        raise ValueError(
            "method-route request contains unknown fields: " + ", ".join(unknown)
        )
    missing = sorted(_ROUTE_REQUIRED_FIELDS - set(raw))
    if missing:
        raise ValueError(
            "method-route request is missing required fields: " + ", ".join(missing)
        )
    request = {key: raw[key] for key in raw}
    decision = route_confirmatory_method(
        alternative=request["alternative"],
        validation_design=request["validation_design"],
        information_structure=request["information_structure"],
        upstream_refits=request["upstream_refits"],
        external_validation=request["external_validation"],
        contrast_count=request.get("contrast_count"),
        information_block_count=request.get("information_block_count"),
    )
    return {
        "receipt_type": "odsp_confirmatory_method_route_v1",
        "request": request,
        "decision": decision.as_dict(),
        "governance": {
            "routing_is_statistical_inference": False,
            "historical_endpoint_reclassification_allowed": False,
            "unknown_combination_policy": "fail_closed",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odsp",
        description="Run explicit ecological prediction and information-transfer contracts.",
        epilog=(
            "Stable entry points: 'odsp run' and 'odsp transfer'. "
            "Other top-level commands are frozen advanced compatibility surfaces "
            "for existing qualified contracts; the public command set is not open-ended."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="{run,transfer,experimental}",
    )
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
    transfer.add_argument(
        "--variant",
        choices=_TRANSFER_VARIANTS,
        default="scores",
        help=(
            "transfer contract family; 'scores' is the stable default, while "
            "refit/external/paired/lattice families reuse their existing schemas"
        ),
    )

    experimental = subparsers.add_parser(
        "experimental",
        help=(
            "advanced governance and pre-outcome freeze operations; statistical "
            "methods remain unchanged"
        ),
    )
    experimental_subparsers = experimental.add_subparsers(
        dest="experimental_command",
        required=True,
        metavar="{method-route,freeze,training-process}",
    )
    experimental_method_route = experimental_subparsers.add_parser(
        "method-route",
        help="inspect the frozen confirmatory-method routing registry",
    )
    _add_method_route_arguments(experimental_method_route)
    experimental_freeze = experimental_subparsers.add_parser(
        "freeze",
        help="create a pre-outcome freeze manifest for an advanced transfer variant",
    )
    experimental_freeze.add_argument(
        "--variant",
        choices=_FREEZE_VARIANTS,
        required=True,
        help="freeze-manifest family",
    )
    _add_freeze_arguments(experimental_freeze)

    training_process = experimental_subparsers.add_parser(
        "training-process",
        help=(
            "operate the qualified v5 training-process chain without changing "
            "its statistical method"
        ),
    )
    training_process_subparsers = training_process.add_subparsers(
        dest="training_process_command",
        required=True,
        metavar="{freeze,generate,external-freeze,external-score,external-run}",
    )

    training_process_freeze = training_process_subparsers.add_parser(
        "freeze",
        help="freeze one prospective training-resampling process",
    )
    _add_freeze_arguments(training_process_freeze)

    training_process_generate = training_process_subparsers.add_parser(
        "generate",
        help="run ODSP-managed model generation for every frozen refit",
    )
    training_process_generate.add_argument(
        "--plan", required=True, help="managed-generation plan JSON"
    )
    training_process_generate.add_argument(
        "--output-root", required=True, help="new directory for generated refits"
    )
    training_process_generate.add_argument(
        "--receipt-out",
        required=True,
        help="non-overwriting managed-generation receipt path",
    )
    training_process_generate.add_argument(
        "--out", help="command receipt path; omit or use '-' for stdout"
    )
    _add_debug_argument(training_process_generate)

    training_process_external_freeze = training_process_subparsers.add_parser(
        "external-freeze",
        help="freeze untouched-external design and scoring semantics before outcomes",
    )
    training_process_external_freeze.add_argument(
        "--plan", required=True, help="process-v5 external freeze-plan JSON"
    )
    training_process_external_freeze.add_argument(
        "--manifest-out",
        required=True,
        help="new external freeze-manifest path",
    )
    training_process_external_freeze.add_argument(
        "--receipt-out",
        required=True,
        help="new external freeze receipt path",
    )
    training_process_external_freeze.add_argument(
        "--out", help="command receipt path; omit or use '-' for stdout"
    )
    _add_debug_argument(training_process_external_freeze)

    training_process_external_score = training_process_subparsers.add_parser(
        "external-score",
        help="derive external score tensors through frozen managed scoring",
    )
    training_process_external_score.add_argument(
        "--freeze-manifest", required=True
    )
    training_process_external_score.add_argument(
        "--freeze-receipt", required=True
    )
    training_process_external_score.add_argument(
        "--external-roster", required=True
    )
    training_process_external_score.add_argument(
        "--external-roster-format",
        choices=("csv", "json"),
        required=True,
    )
    training_process_external_score.add_argument(
        "--managed-generation-receipt", required=True
    )
    training_process_external_score.add_argument(
        "--generated-model-root", required=True
    )
    training_process_external_score.add_argument(
        "--validation-data", required=True
    )
    training_process_external_score.add_argument(
        "--output-root", required=True
    )
    training_process_external_score.add_argument(
        "--score-bundle-out", required=True
    )
    training_process_external_score.add_argument(
        "--scoring-receipt-out", required=True
    )
    training_process_external_score.add_argument(
        "--out", help="command receipt path; omit or use '-' for stdout"
    )
    _add_debug_argument(training_process_external_score)

    training_process_external_run = training_process_subparsers.add_parser(
        "external-run",
        help="run the qualified untouched-external v5 endpoint from one contract",
    )
    _add_common_contract_arguments(training_process_external_run)

    # Legacy command spellings remain executable for scripts and frozen receipts,
    # but are intentionally hidden from the public help surface.
    transfer_refits = subparsers.add_parser("transfer-refits")
    _add_common_contract_arguments(transfer_refits)

    method_route = subparsers.add_parser("method-route")
    _add_method_route_arguments(method_route)

    freeze_external = subparsers.add_parser("freeze-refits-external")
    _add_freeze_arguments(freeze_external)
    external_refits = subparsers.add_parser("transfer-refits-external")
    _add_common_contract_arguments(external_refits)

    freeze_external_paired = subparsers.add_parser("freeze-refits-external-paired")
    _add_freeze_arguments(freeze_external_paired)
    external_refits_paired = subparsers.add_parser("transfer-refits-external-paired")
    _add_common_contract_arguments(external_refits_paired)

    freeze_external_paired_lattice = subparsers.add_parser(
        "freeze-refits-external-paired-lattice"
    )
    _add_freeze_arguments(freeze_external_paired_lattice)
    external_refits_paired_lattice = subparsers.add_parser(
        "transfer-refits-external-paired-lattice"
    )
    _add_common_contract_arguments(external_refits_paired_lattice)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            receipt = run_endpoint_contract(args.contract)
        elif args.command == "transfer":
            receipt = _run_transfer_variant(args.variant, args.contract)
        elif args.command == "experimental":
            if args.experimental_command == "method-route":
                receipt = _run_method_route(args.request)
            elif args.experimental_command == "freeze":
                receipt = _run_freeze_variant(
                    args.variant,
                    args.plan,
                    args.manifest_out,
                )
            elif args.experimental_command == "training-process":
                if args.training_process_command == "freeze":
                    receipt = create_training_process_freeze_manifest(
                        args.plan,
                        args.manifest_out,
                    )
                elif args.training_process_command == "generate":
                    receipt = run_managed_training_process_generation(
                        args.plan,
                        args.output_root,
                        args.receipt_out,
                    )
                elif args.training_process_command == "external-freeze":
                    receipt = create_training_process_v5_external_freeze(
                        args.plan,
                        args.manifest_out,
                        args.receipt_out,
                    )
                elif args.training_process_command == "external-score":
                    receipt = run_managed_external_scoring_v1(
                        args.freeze_manifest,
                        args.freeze_receipt,
                        args.external_roster,
                        external_roster_format=args.external_roster_format,
                        managed_generation_receipt_path=args.managed_generation_receipt,
                        generated_model_root=args.generated_model_root,
                        validation_data_path=args.validation_data,
                        output_root=args.output_root,
                        score_bundle_out=args.score_bundle_out,
                        scoring_receipt_out=args.scoring_receipt_out,
                    )
                elif args.training_process_command == "external-run":
                    receipt = run_training_process_v5_external_contract(
                        args.contract
                    )
                else:  # pragma: no cover - argparse constrains the command.
                    raise AssertionError(
                        "unhandled training-process command: "
                        f"{args.training_process_command}"
                    )
            else:  # pragma: no cover - argparse constrains the command.
                raise AssertionError(
                    f"unhandled experimental command: {args.experimental_command}"
                )
        elif args.command == "transfer-refits":
            receipt = run_refit_information_transfer_contract(args.contract)
        elif args.command == "method-route":
            receipt = _run_method_route(args.request)
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
        elif args.command == "freeze-refits-external-paired-lattice":
            receipt = create_paired_external_lattice_freeze_manifest(
                args.plan, args.manifest_out
            )
        elif args.command == "transfer-refits-external-paired-lattice":
            receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(
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
