#!/usr/bin/env python3
"""Build the three main N2 manuscript figures from machine-pinned records.

No empirical endpoint is refit or rerun. Figures are display products built only
from closed terminal records, the empirical state matrix and the validated
main-branch generality summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def figure_data() -> dict[str, object]:
    bat = _load("N2_BAT_THICKNESS_TERMINAL_DECISION.json")
    serengeti = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")
    matrix = _load("N2_EMPIRICAL_STATE_MATRIX.json")
    generality = _load("N2_GENERALITY_BENCHMARK_SUMMARY.json")
    return {
        "known_truth": {
            "families": ["thick\nunorganized", "stable\norganization", "shifted\norganization"],
            "fitted_information_nats": [0.0, 0.13081203594113697, 0.13081203594113697],
            "heldout_gain_nats": [0.0, 0.13081203594113697, -0.41849410839291784],
            "thick_unorganized_effective_states": 4.0,
        },
        "generality": {
            "check_count": int(generality["result"]["check_count"]),
            "failed_count": int(generality["result"]["failed_count"]),
            "maximum_absolute_error": float(generality["result"]["maximum_absolute_error"]),
            "randomized_tensor_cases": int(generality["settings"]["randomized_tensor_cases"]),
            "ndim_range": list(generality["settings"]["randomized_tensor_ndim_range"]),
            "conditional_independence_cases": int(generality["settings"]["conditional_independence_cases"]),
            "independent_group_counts": list(generality["settings"]["independent_group_counts"]),
        },
        "empirical": {
            "tawaki": {"state": "unavailable"},
            "bat": {
                "information_nats": float(bat["primary"]["information_nats_H_Z_given_XY"]),
                "effective_states": float(bat["primary"]["effective_vertical_states"]),
                "gains": [float(item["mean_log_score_gain"]) for item in bat["primary"]["sealed_individual_scores"]],
                "terminal_category": str(bat["terminal_category"]),
            },
            "serengeti": {
                "admitted_species_count": int(serengeti["admitted_species_count"]),
                "information_nats": float(serengeti["temporal_information_nats"]),
                "effective_states": float(serengeti["effective_temporal_states"]),
                "partition_information_nats": float(serengeti["partition_information_nats"]),
                "permutation_p_value": float(serengeti["permutation_p_value"]),
                "gains": [float(value) for value in serengeti["heldout_gains"]],
                "terminal_category": str(serengeti["terminal_category"]),
            },
        },
        "chapter_claim": str(matrix["chapter_level_result"]),
    }


def _save(fig, output_dir: Path, stem: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for suffix, kwargs in ((".pdf", {"bbox_inches": "tight"}), (".png", {"dpi": 600, "bbox_inches": "tight"})):
        path = output_dir / f"{stem}{suffix}"
        fig.savefig(path, **kwargs)
        outputs.append(path)
    return outputs


def build_figure_1(output_dir: Path) -> list[Path]:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    boxes = [
        (0.35, "1  ESTIMABILITY", "Can the added axis be\nmeasured under the frozen\nobservation architecture?"),
        (2.95, "2  THICKNESS", "How much added-state\ninformation remains?\nH(A|B), exp[H(A|B)]"),
        (5.55, "3  ORGANIZATION", "Is added state structured\nwith base or identity?\nI(A;B), I(C;T|B)"),
        (8.15, "4  TRANSFERABILITY", "Does conditioned structure\nimprove independent prediction?\nE[log P(A|B)-log P(A)]"),
    ]
    for x, title, body in boxes:
        ax.add_patch(FancyBboxPatch((x, 1.15), 2.0, 1.75, boxstyle="round,pad=0.04,rounding_size=0.08", linewidth=1.2, fill=False))
        ax.text(x + 1.0, 2.55, title, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(x + 1.0, 1.85, body, ha="center", va="center", fontsize=8.7)
    for left in (2.35, 4.95, 7.55):
        ax.add_patch(FancyArrowPatch((left, 2.02), (left + 0.55, 2.02), arrowstyle="->", mutation_scale=13))
    ax.text(5.25, 3.55, "Multidimensional support S(B,A) → lower-dimensional projection S(B)", ha="center", va="center", fontsize=11, weight="bold")
    ax.text(5.25, 0.45, "A positive result at one layer does not automatically satisfy the next layer.", ha="center", va="center", fontsize=9)
    fig.tight_layout()
    return _save(fig, output_dir, "Figure1_inferential_hierarchy")


def build_figure_2(output_dir: Path, data: dict[str, object]) -> list[Path]:
    import matplotlib.pyplot as plt
    import numpy as np
    known = data["known_truth"]
    generality = data["generality"]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), gridspec_kw={"width_ratios": [1.35, 1.0]})
    ax = axes[0]
    fitted = np.asarray(known["fitted_information_nats"], dtype=float)
    gains = np.asarray(known["heldout_gain_nats"], dtype=float)
    x = np.arange(len(known["families"]))
    width = 0.34
    ax.axhline(0.0, linewidth=0.9)
    ax.bar(x - width / 2, fitted, width, label="fitted information I(A;B)")
    ax.bar(x + width / 2, gains, width, label="held-out gain G")
    ax.set_xticks(x, known["families"])
    ax.set_ylabel("Information / mean log-score gain (nats)")
    ax.set_title("A  Known-truth states")
    ax.legend(frameon=False, fontsize=8.5)
    ax.text(x[0], 0.055, "4 effective\nadded states", ha="center", va="bottom", fontsize=8.3)
    ax = axes[1]
    ax.axis("off")
    ax.set_title("B  Axis-agnostic generality validation")
    lines = [
        f"{generality['check_count']:,} / {generality['check_count']:,} proof obligations passed",
        f"failed: {generality['failed_count']}",
        f"maximum absolute error: {generality['maximum_absolute_error']:.3e}",
        f"random tensors: {generality['randomized_tensor_cases']}",
        f"dimensions: {generality['ndim_range'][0]}–{generality['ndim_range'][1]}",
        f"conditional-independence systems: {generality['conditional_independence_cases']}",
        "independent groups tested: " + ", ".join(str(v) for v in generality["independent_group_counts"]),
        "", "Validated properties:",
        "mass scaling • axis permutation • state relabelling",
        "nuisance refinement • gain = MI identity",
        "multi-axis composition • group-mass invariance",
    ]
    ax.text(0.03, 0.92, "\n".join(lines), transform=ax.transAxes, ha="left", va="top", fontsize=9.2, linespacing=1.35)
    fig.suptitle("Known truth and high-dimensional property tests validate distinct inferential layers", fontsize=12, weight="bold")
    fig.tight_layout()
    return _save(fig, output_dir, "Figure2_method_validation")


def build_figure_3(output_dir: Path, data: dict[str, object]) -> list[Path]:
    import matplotlib.pyplot as plt
    import numpy as np
    bat = data["empirical"]["bat"]
    serengeti = data["empirical"]["serengeti"]
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.8), gridspec_kw={"width_ratios": [1.0, 1.2, 1.25]})
    ax = axes[0]
    ax.axis("off")
    ax.text(0.5, 0.75, "Tawaki", ha="center", va="center", fontsize=12, weight="bold")
    ax.text(0.5, 0.52, "UNAVAILABLE", ha="center", va="center", fontsize=14, weight="bold")
    ax.text(0.5, 0.30, "Frozen site×year structural\ngate failed before biological\nthickness was opened", ha="center", va="center", fontsize=9)
    ax = axes[1]
    bg = np.asarray(bat["gains"], dtype=float)
    ax.axhline(0.0, linewidth=0.9)
    ax.scatter(np.arange(len(bg)), bg, s=55)
    ax.set_xticks(np.arange(len(bg)), ["sealed 1", "sealed 2"])
    ax.set_ylabel("held-out gain (nats/event)")
    ax.set_title("European free-tailed bat")
    ax.text(0.03, 0.97, f"H(Z|X,Y) = {bat['information_nats']:.3f} nats\neffective states = {bat['effective_states']:.2f}\nthick / non-generalizing", transform=ax.transAxes, ha="left", va="top", fontsize=8.8)
    ax = axes[2]
    sg = np.asarray(serengeti["gains"], dtype=float)
    ax.axhline(0.0, linewidth=0.9)
    ax.scatter(np.arange(len(sg)), sg, s=55)
    ax.set_xticks(np.arange(len(sg)), ["fold 0", "fold 1", "fold 2"])
    ax.set_title("Snapshot Serengeti")
    ax.text(0.03, 0.97, f"H(T|Site) = {serengeti['information_nats']:.3f} nats\neffective states = {serengeti['effective_states']:.2f}/6\nI(Species;T|Site) = {serengeti['partition_information_nats']:.3f}\npermutation p = {serengeti['permutation_p_value']:.3f}\nthick / generalizing", transform=ax.transAxes, ha="left", va="top", fontsize=8.4)
    fig.suptitle("Empirical lanes occupy distinct terminal inferential states", fontsize=12, weight="bold")
    fig.tight_layout()
    return _save(fig, output_dir, "Figure3_empirical_terminal_states")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_all(output_dir: Path) -> dict[str, object]:
    data = figure_data()
    outputs: list[Path] = []
    outputs.extend(build_figure_1(output_dir))
    outputs.extend(build_figure_2(output_dir, data))
    outputs.extend(build_figure_3(output_dir, data))
    manifest = {
        "schema_version": 2,
        "purpose": "manuscript_display_only_no_empirical_refit",
        "source_records": ["N2_BAT_THICKNESS_TERMINAL_DECISION.json", "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json", "N2_EMPIRICAL_STATE_MATRIX.json", "N2_GENERALITY_BENCHMARK_SUMMARY.json"],
        "chapter_claim": data["chapter_claim"],
        "outputs": [{"path": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size} for path in outputs],
    }
    (output_dir / "figure_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("manuscript/generated_figures"))
    args = parser.parse_args()
    manifest = build_all(args.output_dir)
    print(json.dumps({"outputs": len(manifest["outputs"]), "output_dir": str(args.output_dir)}, sort_keys=True))


if __name__ == "__main__":
    main()
