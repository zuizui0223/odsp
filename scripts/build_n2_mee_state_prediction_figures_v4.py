#!/usr/bin/env python3
"""Build receipt-backed figures for the ODSP state-prediction manuscript v4.

Receipt extraction is intentionally lightweight and does not require matplotlib.
Plotting dependencies are imported only when figures are actually rendered.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PREDICTION_RECEIPT = ROOT / "STATE_RESOLVED_PREDICTION_VALIDATION_RECEIPT.json"
BOP_RECEIPT = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"
MATRIX = ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plotting():
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    except ImportError as exc:
        raise ImportError(
            "rendering manuscript figures requires matplotlib; receipt-backed "
            "figure_data() itself has no matplotlib dependency"
        ) from exc
    return plt, FancyArrowPatch, FancyBboxPatch


def figure_data() -> dict[str, Any]:
    pred = _load(PREDICTION_RECEIPT)
    bop = _load(BOP_RECEIPT)
    matrix = _load(MATRIX)

    cells = pred["finite_sample_benchmark"]["cells"]
    families = ("stable_generalizing", "unorganized", "shifted_non_generalizing")
    sample_sizes = pred["finite_sample_benchmark"]["sample_sizes_per_base"]
    benchmark = {
        family: [
            next(
                cell for cell in cells
                if cell["family"] == family and cell["sample_size_per_base"] == n
            )["mean_log_score_gain"]
            for n in sample_sizes
        ]
        for family in families
    }

    species_order = ["Buteo buteo", "Circus aeruginosus", "Circus cyaneus", "Circus pygargus"]
    species = bop["primary_random_forest"]["species_categories"]
    bop_payload = {
        name: {
            "gains": species[name]["gains"],
            "positive_count": species[name]["positive_count"],
            "individual_count": species[name]["individual_count"],
            "category": species[name]["category"],
        }
        for name in species_order
    }

    return {
        "benchmark": {
            "sample_sizes": sample_sizes,
            "families": benchmark,
            "replicates_per_cell": pred["finite_sample_benchmark"]["replicates_per_cell"],
        },
        "bop": {
            "species_order": species_order,
            "species": bop_payload,
            "terminal_category": bop["primary_random_forest"]["terminal_category"],
            "positive_count": bop["primary_random_forest"]["positive_individual_count"],
            "total_count": bop["primary_random_forest"]["eligible_individual_count"],
            "positive_brier_count": bop["primary_random_forest"]["positive_brier_improvement_count"],
            "mean_gain": bop["primary_random_forest"]["mean_gain_descriptive"],
            "mean_brier_improvement": bop["primary_random_forest"]["mean_brier_improvement_descriptive"],
        },
        "matrix_claim": matrix["chapter_level_claim"],
    }


def _save(fig: Any, outdir: Path, stem: str) -> list[Path]:
    plt, _, _ = _plotting()
    outdir.mkdir(parents=True, exist_ok=True)
    pdf = outdir / f"{stem}.pdf"
    png = outdir / f"{stem}.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=600, bbox_inches="tight")
    plt.close(fig)
    return [pdf, png]


def build_figure1(outdir: Path) -> list[Path]:
    plt, FancyArrowPatch, FancyBboxPatch = _plotting()
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (0.03, 0.60, 0.20, 0.24, "Context / environment\nX"),
        (0.29, 0.60, 0.22, 0.24, "Probabilistic learner\nRF / logit / other"),
        (0.57, 0.60, 0.20, 0.24, "State distribution\nP(A | X)"),
        (0.81, 0.60, 0.16, 0.24, "State-rich output\nwhich state?\nwith what probability?"),
        (0.30, 0.16, 0.25, 0.22, "Lower-information comparator\nP(A) from training"),
        (0.63, 0.16, 0.28, 0.22, "Independent-group audit\nΔ log score, Brier, top-1\n→ generalizing / mixed / non-generalizing"),
    ]
    for x, y, w, h, label in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fill=False, linewidth=1.3)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)

    arrows = [
        ((0.23, 0.72), (0.29, 0.72)),
        ((0.51, 0.72), (0.57, 0.72)),
        ((0.77, 0.72), (0.81, 0.72)),
        ((0.67, 0.60), (0.69, 0.38)),
        ((0.55, 0.27), (0.63, 0.27)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=13, linewidth=1.2))

    ax.text(
        0.50,
        0.48,
        "A scalar map collapses ecological state; ODSP predicts the state distribution and audits its independent transfer.",
        fontsize=9,
        ha="center",
        va="center",
    )
    ax.set_title("Figure 1. State-resolved ecological prediction and independent transfer audit", fontsize=12)
    return _save(fig, outdir, "Figure1_state_resolved_prediction_workflow")


def build_figure2(outdir: Path, data: dict[str, Any]) -> list[Path]:
    plt, _, _ = _plotting()
    benchmark = data["benchmark"]
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    x = np.asarray(benchmark["sample_sizes"], dtype=float)
    labels = {
        "stable_generalizing": "stable organization",
        "unorganized": "unorganized",
        "shifted_non_generalizing": "shifted organization",
    }
    markers = {"stable_generalizing": "o", "unorganized": "s", "shifted_non_generalizing": "^"}
    for family, values in benchmark["families"].items():
        ax.plot(x, values, marker=markers[family], linewidth=1.5, label=labels[family])
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(v)) for v in x])
    ax.set_xlabel("Observations per base state")
    ax.set_ylabel("Mean held-out Δ log score (nats/event)")
    ax.set_title(f"Figure 2. Known-truth state-prediction benchmark ({benchmark['replicates_per_cell']} replicates/cell)")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, outdir, "Figure2_known_truth_state_prediction")


def build_figure3(outdir: Path, data: dict[str, Any]) -> list[Path]:
    plt, _, _ = _plotting()
    bop = data["bop"]
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    x_positions: list[float] = []
    gains: list[float] = []
    tick_positions: list[float] = []
    tick_labels: list[str] = []
    boundaries: list[float] = []
    cursor = 0.0
    for species_name in bop["species_order"]:
        group = bop["species"][species_name]
        group_gains = group["gains"]
        positions = [cursor + i for i in range(len(group_gains))]
        x_positions.extend(positions)
        gains.extend(group_gains)
        tick_positions.append(float(np.mean(positions)))
        short = species_name.replace("Circus ", "C. ").replace("Buteo ", "B. ")
        tick_labels.append(f"{short}\n{group['positive_count']}/{group['individual_count']} positive")
        cursor += len(group_gains) + 1.5
        boundaries.append(cursor - 0.75)

    ax.scatter(x_positions, gains, s=32)
    ax.axhline(0.0, linewidth=1.0)
    for boundary in boundaries[:-1]:
        ax.axvline(boundary, linewidth=0.6, alpha=0.35)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.set_ylabel("Held-out RF Δ log score (nats/event)")
    ax.set_title(
        "Figure 3. BOP_RODENT cross-individual state prediction\n"
        f"{bop['positive_count']}/{bop['total_count']} positive log-score gains; "
        f"{bop['positive_brier_count']}/{bop['total_count']} positive Brier improvements"
    )
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.01,
        0.98,
        f"Terminal: mixed\nMean gain: {bop['mean_gain']:+.3f}\nMean Brier improvement: {bop['mean_brier_improvement']:+.3f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )
    return _save(fig, outdir, "Figure3_bop_individual_transfer")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(outdir: Path) -> dict[str, Any]:
    data = figure_data()
    files: list[Path] = []
    files.extend(build_figure1(outdir))
    files.extend(build_figure2(outdir, data))
    files.extend(build_figure3(outdir, data))
    manifest = {
        "schema_version": 1,
        "role": "n2_mee_state_prediction_figures_v4",
        "source_receipts": [
            PREDICTION_RECEIPT.name,
            BOP_RECEIPT.name,
            MATRIX.name,
        ],
        "files": [
            {"name": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in files
        ],
        "empirical_endpoint_rerun": False,
    }
    manifest_path = outdir / "figure_manifest_v4.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("build/figures_v4"))
    args = parser.parse_args()
    print(json.dumps(build(args.outdir), sort_keys=True))


if __name__ == "__main__":
    main()
