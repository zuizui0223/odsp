#!/usr/bin/env python3
"""Build deterministic double-anonymous review bundle for state-prediction manuscript v4.

The v4 archive starts from the policy-compliant v3 review surface, replaces the
manuscript/table/captions, and adds only scientific state-prediction code,
prospective contracts, selected QA and a sanitized evidence summary. Raw terminal
receipts carrying internal workflow/PR provenance are intentionally not included.

The review environment is historically frozen at ODSP 0.10.0. Later package
releases may add functionality, but rebuilding the v4 review artifact must not
silently rewrite the package version recorded inside that frozen bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile

from scripts.build_n2_mee_manuscript_v4 import build_manuscript_text as build_v4_text
from scripts.build_n2_mee_review_bundle import FORBIDDEN_IDENTITY_TOKENS
from scripts.build_n2_mee_review_bundle_v3 import AI_DISCLOSURE, _annotate_python, build_bundle as build_v3_bundle


ROOT = Path(__file__).resolve().parents[1]
FROZEN_REVIEW_PACKAGE_VERSION = "0.10.0"

PREDICTION_MODULES = (
    "state_prediction.py",
    "state_prediction_benchmark.py",
    "covariate_state_prediction.py",
    "mh_antwerpen_prediction.py",
    "bop_rodent_prediction.py",
)

PREDICTION_TESTS = (
    "test_state_prediction.py",
    "test_state_prediction_benchmark.py",
    "test_covariate_state_prediction.py",
    "test_mh_antwerpen_state_prediction.py",
    "test_mh_antwerpen_state_prediction_contract.py",
    "test_bop_rodent_state_prediction.py",
    "test_bop_rodent_state_prediction_contract.py",
)

PREDICTION_RUNNERS = (
    "run_state_prediction_benchmark.py",
    "run_mh_antwerpen_state_prediction.py",
    "run_bop_rodent_state_prediction.py",
)

PREDICTION_CONTRACTS = (
    "STATE_RESOLVED_PREDICTION_CONTRACT.json",
    "MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json",
    "BOP_RODENT_STATE_PREDICTION_CONTRACT.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def _scan_identity(stage: Path) -> None:
    violations: list[str] = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_IDENTITY_TOKENS:
            if token in text:
                violations.append(f"{path.relative_to(stage)}: {token}")
    if violations:
        raise ValueError("anonymous bundle contains identity tokens: " + "; ".join(violations))


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def _freeze_review_pyproject(stage: Path) -> None:
    path = stage / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(?m)^version = "[^"]+"$',
        f'version = "{FROZEN_REVIEW_PACKAGE_VERSION}"',
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("expected exactly one project version in review pyproject")
    path.write_text(updated, encoding="utf-8")


def _state_summary() -> dict[str, object]:
    matrix = json.loads((ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json").read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "purpose": "anonymous_peer_review_state_prediction_scientific_summary",
        "method_position": matrix["method_position"],
        "synthetic_prediction_validation": matrix["synthetic_prediction_validation"],
        "prospective_state_prediction_endpoints": matrix["prospective_state_prediction_endpoints"],
        "supporting_projection_and_transfer_diagnostics": matrix["supporting_projection_and_transfer_diagnostics"],
        "chapter_level_claim": matrix["chapter_level_claim"],
        "claim_ceiling": matrix["claim_ceiling"],
        "n3_state_artifact_included": False,
    }


def _review_readme() -> str:
    return """# Anonymous peer-review code and evidence bundle

This archive accompanies the double-anonymous review draft **State-resolved
ecological prediction: from flat suitability to transferable ecological-state
distributions**.

## Central method

ODSP predicts a probability distribution over declared ecological states,
`P(A|X)` or `P(A|B)`, and evaluates whether that added state resolution improves
prediction in prospectively independent groups relative to the training marginal
state distribution `P(A)`. It is a model-agnostic prediction/evaluation framework,
not a competing occurrence-SDM learner.

## Included

- generic information, transferability and state-prediction method code;
- finite-sample and high-dimensional known-truth validation;
- selected prediction and empirical-contract QA;
- public-source runners for inspection (not executed by bundle tests);
- prospective MH_ANTWERPEN and BOP_RODENT contracts;
- sanitized state-prediction evidence summary with no internal PR/workflow provenance;
- v4 anonymous manuscript, Table 1 and figure captions;
- generative-AI disclosure and whole-file conservative annotations on submitted Python files.

Git history, repository identifiers, author metadata, non-anonymous submission files,
PR numbers, workflow IDs and internal closeout provenance are intentionally excluded.
The bundle does not rerun any public empirical endpoint during installation or tests.

## Install and test

```bash
python -m pip install -e '.[dev,predict]'
pytest -q
```

## Claim boundary

The evidence supports finite-discrete state prediction, model-agnostic probability
scoring and independent-group transfer assessment. It does not establish universal
positive transfer, causal effects, fundamental niches, automatic correction of
observation bias, height above ground from absolute altitude, or automatic N2-to-N3
state promotion.
"""


def _manifest(stage: Path) -> dict[str, object]:
    files = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        if path.name == "REVIEW_BUNDLE_MANIFEST.json":
            continue
        files.append({
            "path": path.relative_to(stage).as_posix(),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        })
    python_files = [item["path"] for item in files if str(item["path"]).endswith(".py")]
    return {
        "schema_version": 4,
        "bundle_role": "double_anonymous_state_prediction_peer_review",
        "manuscript_title": "State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions",
        "contains_git_history": False,
        "contains_author_identity": False,
        "contains_internal_workflow_or_pr_provenance": False,
        "contains_public_data_dois": True,
        "contains_state_prediction_manuscript_v4": True,
        "contains_state_prediction_validation": True,
        "contains_prospective_prediction_contracts": True,
        "contains_raw_terminal_receipts_with_internal_provenance": False,
        "contains_generative_ai_disclosure": True,
        "python_file_ai_annotation_mode": "whole_file_conservative",
        "python_file_ai_annotation_count": len(python_files),
        "files": files,
    }


def _zip_deterministic(stage: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(stage).as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def build_bundle(output: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="n2-review-v4-") as temp:
        root = Path(temp)
        base_zip = root / "base-v3.zip"
        build_v3_bundle(base_zip)
        stage = root / "stage"
        stage.mkdir()
        with zipfile.ZipFile(base_zip) as archive:
            archive.extractall(stage)

        # Preserve the exact review-environment package version used when v4 was
        # frozen, even when the live package advances to 0.11+.
        _freeze_review_pyproject(stage)

        for name in (
            "N2_MEE_MANUSCRIPT_DRAFT_v3.md",
            "N2_MEE_TABLE1_DRAFT_v2.md",
            "N2_MEE_FIGURE_CAPTIONS_DRAFT_v2.md",
        ):
            _remove_if_exists(stage / "manuscript" / name)
        _remove_if_exists(stage / "REVIEW_BUNDLE_MANIFEST.json")

        (stage / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v4.md").write_text(build_v4_text(), encoding="utf-8")
        _copy(ROOT / "manuscript" / "N2_MEE_TABLE1_DRAFT_v4.md", stage / "manuscript" / "N2_MEE_TABLE1_DRAFT_v4.md")
        _copy(ROOT / "manuscript" / "N2_MEE_FIGURE_CAPTIONS_DRAFT_v4.md", stage / "manuscript" / "N2_MEE_FIGURE_CAPTIONS_DRAFT_v4.md")

        for name in PREDICTION_MODULES:
            _copy(ROOT / "odsp" / name, stage / "odsp" / name)
        for name in PREDICTION_TESTS:
            _copy(ROOT / "tests" / name, stage / "tests" / name)
        for name in PREDICTION_RUNNERS:
            _copy(ROOT / "scripts" / name, stage / "scripts" / name)
        for name in PREDICTION_CONTRACTS:
            _copy(ROOT / name, stage / name)

        init_path = stage / "odsp" / "__init__.py"
        init_text = init_path.read_text(encoding="utf-8")
        for module in ("state_prediction", "state_prediction_benchmark", "covariate_state_prediction"):
            line = f"from .{module} import *\n"
            if line not in init_text:
                init_text += line
        init_path.write_text(init_text, encoding="utf-8")

        (stage / "review_evidence" / "STATE_PREDICTION_SUMMARY.json").write_text(
            json.dumps(_state_summary(), indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (stage / "README_REVIEW.md").write_text(_review_readme(), encoding="utf-8")
        (stage / "AI_ASSISTANCE_DISCLOSURE.md").write_text(AI_DISCLOSURE, encoding="utf-8")

        for path in sorted(stage.rglob("*.py")):
            path.write_text(_annotate_python(path.read_text(encoding="utf-8")), encoding="utf-8")

        _scan_identity(stage)
        manifest = _manifest(stage)
        (stage / "REVIEW_BUNDLE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _scan_identity(stage)
        _zip_deterministic(stage, output)

    return {
        "output": str(output),
        "sha256": _sha256(output),
        "bytes": output.stat().st_size,
        "file_count": len(manifest["files"]) + 1,
        "python_file_ai_annotation_count": manifest["python_file_ai_annotation_count"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dist/N2_MEE_ANONYMOUS_REVIEW_BUNDLE_v4.zip"))
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
