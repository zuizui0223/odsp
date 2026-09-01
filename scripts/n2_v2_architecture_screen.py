#!/usr/bin/env python3
"""Evaluate the frozen Chapter-N2 architecture screen without reading outcomes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.empirical_axis_screen import run_architecture_screen

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "N2_V2_ARCHITECTURE_SCREEN.json"
SELECTION = ROOT / "N2_V2_ARCHITECTURE_SELECTION.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    result = run_architecture_screen(screen, selection)
    payload = result.as_dict()
    payload["forbidden_outcome_metrics_confirmed_absent"] = [
        "z_or_t_distribution",
        "H(Z|X,Y)",
        "H(T|X,Y)",
        "effective_states",
        "axis_thickness_map",
        "projection_loss",
        "held_out_score",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "screen_id": result.screen_id,
                "selected_candidate_id": result.selected_candidate_id,
                "outcome_metrics_computed": result.outcome_metrics_computed,
                "fingerprint": result.fingerprint,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
