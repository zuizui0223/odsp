"""Illustrative Chapter-2 contrast with equal x-y footprint.

This example demonstrates the metric only. It is not evidence that real forests
must always have greater niche thickness than real grasslands.
"""
from __future__ import annotations

import json

import numpy as np

from odsp import niche_thickness_profile


def main() -> None:
    # Same 4 × 4 horizontal footprint.
    grassland = np.ones((4, 4, 1), dtype=float)
    forest = np.ones((4, 4, 5), dtype=float)

    grass = niche_thickness_profile(
        grassland,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )
    woods = niche_thickness_profile(
        forest,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )

    print(
        json.dumps(
            {
                "grassland_effective_vertical_states": grass.effective_vertical_states,
                "forest_effective_vertical_states": woods.effective_vertical_states,
                "horizontal_footprint_equal": grassland.shape[:2] == forest.shape[:2],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
