#!/usr/bin/env python3
"""Build an anonymized Methods in Ecology and Evolution review bundle.

The bundle is deliberately narrower than the development repository. It contains
only the scientific implementation, tests, frozen public-data evidence and
submission-facing manuscript needed for double-anonymous review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]

# NOTE: Keep this script identity-neutral. It is copied conceptually into the
# anonymous review surface and its output is scanned for identifying tokens.
FORBIDDEN_IDENTITY_TOKENS = (
    "zuizui0223",
    "zhang ruiqi",
    "張瑞琪",
    "rachelzhang",
)

REVIEW_IMPLEMENTATION_FILES = (
    "odsp/__init__.py",
    "odsp/niche_geometry.py",
    "odsp/projection_loss.py",
    "odsp/added_axis_evidence.py",
    "odsp/vertical_information.py",
    "odsp/temporal_information.py",
    "odsp/temporal_partition.py",
    "odsp/temporal_crossfit.py",
    "odsp/grouped_transferability.py",
    "odsp/crossfitted_transferability.py",
    "odsp/transferability.py",
    "odsp/synthetic_benchmark.py",
    "odsp/generality_benchmark.py",
    "odsp/generalization_profile.py",
    "odsp/grouped_benchmark.py",
)

REVIEW_TEST_FILES = (
    "tests/test_niche_geometry.py",
    "tests/test_projection_loss.py",
    "tests/test_added_axis_evidence.py",
    "tests/test_vertical_information.py",
    "tests/test_temporal_information.py",
    "tests/test_temporal_partition.py",
    "tests/test_temporal_crossfit.py",
    "tests/test_grouped_temporal_partition.py",
    "tests/test_grouped_transferability.py",
    "tests/test_transferability.py",
    "tests/test_synthetic_benchmark.py",
    "tests/test_n2_generality_benchmark.py",
    "tests/test_generalization_profile.py",
)

REVIEW_EVIDENCE_FILES = (
    "N2_GENERALITY_CONTRACT.json",
    "N2_GENERALITY_BENCHMARK_SUMMARY.json",
    "N2_BAT_THICKNESS_TERMINAL_DECISION.json",
    "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json",
)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)


def _review_readme() -> str:
    return """# ODSP review package

This anonymous package contains the scientific implementation, tests and frozen
public-data evidence required to review the accompanying Methods in Ecology and
Evolution manuscript.

The repository-development history, author metadata, operational governance and
post-freeze exploratory infrastructure are intentionally excluded from this
review surface.

## Install and test

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

The package is a scientific representation and validation layer rather than a
replacement occurrence-SDM learner. See the manuscript for the exact inferential
claims and frozen empirical boundaries.
"""


def _review_init() -> str:
    source = (ROOT / "odsp" / "__init__.py").read_text(encoding="utf-8")
    # The review package is restricted to the declared implementation surface.
    allowed_modules = {
        Path(path).stem for path in REVIEW_IMPLEMENTATION_FILES if path != "odsp/__init__.py"
    }
    lines: list[str] = []
    skip = False
    for line in source.splitlines():
        if line.startswith("from ."):
            module = line.split("from .", 1)[1].split(" import", 1)[0]
            skip = module not in allowed_modules
        if not skip:
            lines.append(line)
        if skip and line.rstrip().endswith(")"):
            skip = False
    return "\n".join(lines).rstrip() + "\n"


def _sanitized_pyproject() -> str:
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # The live distribution may use a PyPI-specific landing page, whereas the
    # frozen anonymous review bundle must always bind metadata to its anonymous
    # README. Support both the historical and current live-package filenames.
    source = source.replace('readme = "README.md"', 'readme = "README_REVIEW.md"')
    source = source.replace('readme = "PYPI_README.md"', 'readme = "README_REVIEW.md"')
    return source


def _empirical_summary() -> dict[str, object]:
    bat = _read_json(ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json")
    serengeti = _read_json(ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")
    return {
        "schema_version": 2,
        "purpose": "anonymous_peer_review_terminal_scientific_summary",
        "tawaki": {
            "public_source_article_doi": "10.7717/peerj.19650",
            "public_processed_data_doi": "10.5281/zenodo.14849008",
            "terminal_category": "empirical_gate_d_unavailable",
            "thickness_opened": False,
            "interpretation": "frozen structural architecture was unavailable before biological thickness was opened",
        },
        "european_free_tailed_bat": {
            "public_source_article_doi": "10.1016/j.cub.2020.12.042",
            "public_data_doi": "10.5441/001/1.52nn82r9",
            "terminal_category": bat["terminal_category"],
            "information_nats_H_Z_given_XY": bat["primary"]["information_nats_H_Z_given_XY"],
            "effective_vertical_states": bat["primary"]["effective_vertical_states"],
            "heldout_individual_gains": [item["mean_log_score_gain"] for item in bat["primary"]["sealed_individual_scores"]],
            "interpretation": "descriptively vertically thick but independently non-generalizing",
        },
        "snapshot_serengeti": {
            "public_source_article_doi": "10.1038/sdata.2015.26",
            "public_data_doi": "10.5061/dryad.5pt92",
            "terminal_category": serengeti["terminal_category"],
            "admitted_species_count": serengeti["admitted_species_count"],
            "information_nats_H_T_given_Site": serengeti["temporal_information_nats"],
            "effective_temporal_states": serengeti["effective_temporal_states"],
            "partition_information_nats_I_Species_T_given_Site": serengeti["partition_information_nats"],
            "permutation_p_value": serengeti["permutation_p_value"],
            "heldout_site_fold_gains": serengeti["heldout_gains"],
            "interpretation": "temporally thick, species-partitioned and independently generalizing across all frozen site folds",
        },
        "chapter_claim": "Projection loss has empirically separable components: added-axis thickness magnitude and independent transferability of added-state organization.",
        "n3_state_artifact_included": False,
    }


def _generality_summary() -> dict[str, object]:
    source = _read_json(ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json")
    return {
        "schema_version": 1,
        "purpose": "anonymous_peer_review_generality_summary",
        "settings": source["settings"],
        "result": source["result"],
        "properties_validated": source["properties_validated"],
        "claim_boundary": {
            "finite_discrete_support_genericity_supported": True,
            "multiple_base_axes_supported": True,
            "multiple_added_axes_supported": True,
            "universal_biological_outcomes_supported": False,
            "causal_interpretation_supported": False,
            "observation_bias_removed": False,
        },
    }


def _copy_required(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    _write(target, source.read_bytes())


def _stage_bundle(stage: Path) -> None:
    _write(stage / "LICENSE", (ROOT / "LICENSE").read_bytes())
    _write(stage / "README_REVIEW.md", _review_readme())
    _write(stage / "pyproject.toml", _sanitized_pyproject())
    _write(stage / "odsp" / "__init__.py", _review_init())

    for relative in REVIEW_IMPLEMENTATION_FILES:
        if relative == "odsp/__init__.py":
            continue
        _copy_required(ROOT / relative, stage / relative)
    for relative in REVIEW_TEST_FILES:
        _copy_required(ROOT / relative, stage / relative)
    for relative in REVIEW_EVIDENCE_FILES:
        _copy_required(ROOT / relative, stage / relative)

    _write(
        stage / "EMPIRICAL_TERMINAL_SUMMARY.json",
        json.dumps(_empirical_summary(), indent=2, sort_keys=True) + "\n",
    )
    _write(
        stage / "GENERALITY_VALIDATION_SUMMARY.json",
        json.dumps(_generality_summary(), indent=2, sort_keys=True) + "\n",
    )


def _scan_identity(stage: Path) -> None:
    violations: list[str] = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        for token in FORBIDDEN_IDENTITY_TOKENS:
            if token in lowered:
                violations.append(f"{path.relative_to(stage)}: {token}")
    if violations:
        raise ValueError("anonymous review bundle contains identity tokens: " + "; ".join(violations))


def _zip_tree(stage: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = sorted(p for p in stage.rglob("*") if p.is_file())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            info = zipfile.ZipInfo(path.relative_to(stage).as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "output": output.name,
        "file_count": len(entries),
        "bytes": output.stat().st_size,
        "sha256": digest,
    }


def build_bundle(output: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="n2-review-") as temp:
        stage = Path(temp) / "n2_review_bundle"
        stage.mkdir(parents=True, exist_ok=True)
        _stage_bundle(stage)
        _scan_identity(stage)
        return _zip_tree(stage, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "N2_MEE_ANONYMOUS_REVIEW_BUNDLE.zip",
    )
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
