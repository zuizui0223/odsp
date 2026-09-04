#!/usr/bin/env python3
"""Build a deterministic double-anonymous peer-review bundle for the N2 paper.

The bundle is whitelist-based. It contains the method implementation, selected
method/empirical tests, reviewer-facing manuscript files, public source DOIs and
a sanitized empirical summary. It intentionally omits git history, PR/workflow
provenance, repository URLs and author-identifying metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_IDENTITY_TOKENS = (
    "zuizui0223",
    "zhang ruiqi",
    "rachelzhang",
    "rachel zhang",
)

CORE_MODULES = (
    "niche_geometry.py",
    "projection_loss.py",
    "transferability.py",
    "grouped_transferability.py",
    "crossfitted_transferability.py",
    "temporal_partition.py",
    "temporal_crossfit.py",
    "temporal_information.py",
    "vertical_information.py",
    "synthetic_benchmark.py",
    "grouped_benchmark.py",
    "concealed_recovery.py",
    "n2_bat_preflight.py",
    "n2_bat_thickness.py",
)

SELECTED_TESTS = (
    "test_niche_geometry.py",
    "test_projection_loss.py",
    "test_transferability.py",
    "test_grouped_transferability.py",
    "test_temporal_partition.py",
    "test_grouped_temporal_partition.py",
    "test_temporal_crossfit.py",
    "test_synthetic_benchmark.py",
    "test_concealed_recovery.py",
    "test_n2_bat_thickness.py",
    "test_serengeti_temporal_partition_script.py",
)

MANUSCRIPT_FILES = (
    "N2_MEE_MANUSCRIPT_DRAFT_v1.md",
    "N2_MEE_TABLE1_DRAFT_v1.md",
    "N2_MEE_FIGURE_CAPTIONS_DRAFT_v1.md",
    "N2_MEE_REFERENCE_CORE_v1.md",
)

EMPIRICAL_SCRIPTS = (
    "n2_bat_thickness_execute.py",
    "run_n2_serengeti_temporal_partition.py",
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _review_init() -> str:
    return '''"""Anonymous review surface for the N2 multidimensional-support method."""\n\nfrom .concealed_recovery import *\nfrom .crossfitted_transferability import *\nfrom .grouped_transferability import *\nfrom .niche_geometry import *\nfrom .projection_loss import *\nfrom .temporal_crossfit import *\nfrom .temporal_information import *\nfrom .temporal_partition import *\nfrom .transferability import *\nfrom .vertical_information import *\n'''


def _review_readme() -> str:
    return """# Anonymous peer-review code and evidence bundle

This archive accompanies the double-anonymous review draft **Beyond flat niche
maps: separating added-axis thickness from transferable ecological organization**.

## What is included

- the general information-theoretic N2 method implementation;
- analytic/finite-observation benchmark code and selected tests;
- frozen empirical runner code for the European free-tailed bat and Snapshot
  Serengeti demonstrations;
- an anonymous machine-readable summary of the completed empirical terminal
  states;
- the manuscript draft, Table 1, figure captions and verified reference core.

Git history, repository identifiers, author metadata, pull-request/workflow logs
and internal recovery provenance are deliberately excluded from this anonymous
review archive. The terminal values in `review_evidence/EMPIRICAL_SUMMARY.json`
are copied from independently frozen/validated terminal records in the source
project; this bundle does not rerun or reinterpret those endpoints.

## Install and test

```bash
python -m pip install -e '.[dev]'
pytest -q
```

## Public empirical sources

- Tawaki: Otis et al. 2025, PeerJ, DOI 10.7717/peerj.19650; processed archive
  DOI 10.5281/zenodo.14849008.
- European free-tailed bat: O'Mara et al. 2021, Current Biology, DOI
  10.1016/j.cub.2020.12.042; Movebank archive DOI 10.5441/001/1.52nn82r9.
- Snapshot Serengeti: Swanson et al. 2015, Scientific Data, DOI
  10.1038/sdata.2015.26; Dryad DOI 10.5061/dryad.5pt92.

## Interpretation boundary

The archive supports the manuscript's estimability → thickness → organization →
independent-transferability hierarchy. It does not promote a terminal summary to
a downstream axis-resolved state artifact, and it does not claim causal temporal
displacement or compare bat and Serengeti information values as controlled
cross-system effect sizes.
"""


def _sanitized_pyproject() -> str:
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    source = source.replace('readme = "README.md"', 'readme = "README_REVIEW.md"')
    return source


def _empirical_summary() -> dict[str, object]:
    bat = _read_json(ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json")
    serengeti = _read_json(ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    return {
        "schema_version": 1,
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
            "heldout_individual_gains": [
                item["mean_log_score_gain"]
                for item in bat["primary"]["sealed_individual_scores"]
            ],
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


def _copy_required(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    _write(target, source.read_bytes())


def _stage_bundle(stage: Path) -> None:
    _write(stage / "LICENSE", (ROOT / "LICENSE").read_bytes())
    _write(stage / "README_REVIEW.md", _review_readme())
    _write(stage / "pyproject.toml", _sanitized_pyproject())
    _write(stage / "odsp" / "__init__.py", _review_init())

    for name in CORE_MODULES:
        _copy_required(ROOT / "odsp" / name, stage / "odsp" / name)

    included_tests = 0
    for name in SELECTED_TESTS:
        source = ROOT / "tests" / name
        if source.is_file():
            _copy_required(source, stage / "tests" / name)
            included_tests += 1
    if included_tests < 8:
        raise ValueError(f"too few selected review tests were found: {included_tests}")

    for name in EMPIRICAL_SCRIPTS:
        _copy_required(ROOT / "scripts" / name, stage / "scripts" / name)

    for name in MANUSCRIPT_FILES:
        _copy_required(ROOT / "manuscript" / name, stage / "manuscript" / name)

    summary = _empirical_summary()
    _write(
        stage / "review_evidence" / "EMPIRICAL_SUMMARY.json",
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
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


def _manifest(stage: Path) -> dict[str, object]:
    files = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        if path.name == "REVIEW_BUNDLE_MANIFEST.json":
            continue
        files.append({
            "path": path.relative_to(stage).as_posix(),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return {
        "schema_version": 1,
        "bundle_role": "double_anonymous_peer_review",
        "manuscript_title": "Beyond flat niche maps: separating added-axis thickness from transferable ecological organization",
        "contains_git_history": False,
        "contains_author_identity": False,
        "contains_internal_workflow_or_pr_provenance": False,
        "contains_public_data_dois": True,
        "files": files,
    }


def _zip_deterministic(stage: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            relative = path.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(relative)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def build_bundle(output: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="n2-review-") as temp:
        stage = Path(temp) / "n2_review_bundle"
        stage.mkdir(parents=True)
        _stage_bundle(stage)
        _scan_identity(stage)
        manifest = _manifest(stage)
        _write(
            stage / "REVIEW_BUNDLE_MANIFEST.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
        _scan_identity(stage)
        _zip_deterministic(stage, output)
    return {
        "output": str(output),
        "sha256": _sha256_file(output),
        "bytes": output.stat().st_size,
        "file_count": len(manifest["files"]) + 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dist/N2_MEE_ANONYMOUS_REVIEW_BUNDLE.zip"))
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
