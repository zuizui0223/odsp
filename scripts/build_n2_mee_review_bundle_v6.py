#!/usr/bin/env python3
"""Build deterministic anonymous MEE review bundle v6.

Version 6 reuses the validated v5 review archive, replaces the manuscript surface,
and adds only the sanitized code/evidence required for the post-outcome BOP
population-transfer summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from scripts.build_n2_mee_manuscript_v6 import build_manuscript_text as build_v6_text
from scripts.build_n2_mee_review_bundle import FORBIDDEN_IDENTITY_TOKENS
from scripts.build_n2_mee_review_bundle_v3 import AI_DISCLOSURE, _annotate_python
from scripts.build_n2_mee_review_bundle_v5 import build_bundle as build_v5_bundle


ROOT = Path(__file__).resolve().parents[1]
POPULATION_RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def _remove(path: Path) -> None:
    if path.exists():
        path.unlink()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sanitized_population_summary() -> dict[str, object]:
    receipt = _read_json(POPULATION_RECEIPT)
    primary = receipt["frozen_primary_endpoint"]
    population = receipt["population_result"]
    return {
        "schema_version": 1,
        "role": "anonymous_peer_review_post_outcome_bop_population_transfer",
        "post_outcome_amendment": True,
        "analysis_type": receipt["analysis_type"],
        "primary_endpoint_preserved": {
            "terminal_category": primary["terminal_category"],
            "positive_individual_count": primary["positive_individual_count"],
            "eligible_individual_count": primary["eligible_individual_count"],
            "terminal_decision_recomputed": primary["terminal_decision_recomputed"],
            "terminal_decision_changed": primary["terminal_decision_changed"],
        },
        "population_result": population,
        "interpretation": receipt["interpretation"],
        "model_refit_performed": receipt["model_refit_performed"],
        "raw_source_data_reaccessed": receipt["raw_source_data_reaccessed"],
        "retuning_performed": receipt["retuning_performed"],
        "internal_workflow_or_artifact_provenance_included": False,
    }


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


def _review_readme(existing: str) -> str:
    text = existing.replace("state-prediction version 5", "state-prediction version 6")
    text += """

## BOP population-transfer summary

The prospective BOP_RODENT endpoint remains
`empirical_state_prediction_mixed`. A post-outcome descriptive summary treats
held-out individuals as equal-weight groups and species as the resampling cluster.
It reports total first-to-final transfer separately from the non-skippable
adjacent-step ceiling, together with prevalence and heterogeneity summaries.
This analysis does not refit the model, re-access raw tracking data, retune any
rule, or reclassify the prospective endpoint. Only four species clusters are
represented, so cluster-level uncertainty is explicitly treated as descriptive.
See `review_evidence/BOP_POPULATION_TRANSFER.json` and
`odsp/population_transfer.py`.
"""
    return text


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
        "schema_version": 6,
        "bundle_role": "double_anonymous_state_prediction_peer_review",
        "manuscript_title": "State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions",
        "contains_git_history": False,
        "contains_author_identity": False,
        "contains_internal_workflow_or_pr_provenance": False,
        "contains_raw_bop_population_receipt": False,
        "contains_state_prediction_manuscript_v6": True,
        "contains_post_outcome_bop_decomposition": True,
        "contains_post_outcome_bop_population_summary": True,
        "bop_primary_terminal_reclassified": False,
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
    with tempfile.TemporaryDirectory(prefix="n2-review-v6-") as temp:
        root = Path(temp)
        base_zip = root / "base-v5.zip"
        build_v5_bundle(base_zip)
        stage = root / "stage"
        stage.mkdir()
        with zipfile.ZipFile(base_zip) as archive:
            archive.extractall(stage)

        _remove(stage / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v5.md")
        _remove(stage / "manuscript" / "N2_MEE_TABLE1_DRAFT_v5.md")
        _remove(stage / "manuscript" / "N2_MEE_FIGURE_CAPTIONS_DRAFT_v5.md")
        _remove(stage / "N2_MEE_STATE_PREDICTION_V5_CONTRACT.json")
        _remove(stage / "REVIEW_BUNDLE_MANIFEST.json")

        (stage / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v6.md").write_text(
            build_v6_text(), encoding="utf-8"
        )
        _copy(
            ROOT / "manuscript" / "N2_MEE_TABLE1_DRAFT_v4.md",
            stage / "manuscript" / "N2_MEE_TABLE1_DRAFT_v6.md",
        )
        _copy(
            ROOT / "manuscript" / "N2_MEE_FIGURE_CAPTIONS_DRAFT_v4.md",
            stage / "manuscript" / "N2_MEE_FIGURE_CAPTIONS_DRAFT_v6.md",
        )

        for name in (
            "transferability.py",
            "predictive_resolution.py",
            "predictive_resolution_certification.py",
            "information_transfer.py",
            "population_transfer.py",
        ):
            _copy(ROOT / "odsp" / name, stage / "odsp" / name)

        (stage / "tests" / "test_population_transfer_review.py").write_text(
            """from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
from odsp.population_transfer import summarize_population_transfer


def test_population_transfer_review_example():
    gains = [0.5, 0.5, 0.5, 0.5, -0.1]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 5),
            InformationLevelScore("richer", ("context",), gains),
        ),
        [f"g{i}" for i in range(5)],
    )
    summary = summarize_population_transfer(point, bootstrap_draws=500, seed=17)
    assert summary.total_gain.mean_gain > 0
    assert summary.total_gain.positive_group_count == 4
    assert summary.total_gain.positive_group_fraction == 0.8
    assert summary.population_mean_supported_ceiling == "richer"
""",
            encoding="utf-8",
        )
        _copy(
            ROOT / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json",
            stage / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json",
        )

        init_path = stage / "odsp" / "__init__.py"
        init_text = init_path.read_text(encoding="utf-8")
        for line in (
            "from .information_transfer import *\n",
            "from .population_transfer import *\n",
        ):
            if line not in init_text:
                init_text += line
        init_path.write_text(init_text, encoding="utf-8")

        evidence_path = stage / "review_evidence" / "BOP_POPULATION_TRANSFER.json"
        evidence_path.write_text(
            json.dumps(
                _sanitized_population_summary(),
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        readme_path = stage / "README_REVIEW.md"
        readme_path.write_text(
            _review_readme(readme_path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        (stage / "AI_ASSISTANCE_DISCLOSURE.md").write_text(
            AI_DISCLOSURE, encoding="utf-8"
        )

        for path in sorted(stage.rglob("*.py")):
            path.write_text(
                _annotate_python(path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )

        _scan_identity(stage)
        manifest = _manifest(stage)
        (stage / "REVIEW_BUNDLE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
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
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/N2_MEE_ANONYMOUS_REVIEW_BUNDLE_v6.zip"),
    )
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
