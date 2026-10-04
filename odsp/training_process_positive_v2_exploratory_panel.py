"""Exploratory post-failure comparison for the PSD-clipped v2 candidate."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .training_process_positive_calibration import (
    SCENARIOS,
    _crossed_null_world,
    _flatten_world,
)
from .training_process_positive_power_calibration import _oracle_cell_standard_error
from .training_process_positive_v2_exploration import evaluate_psd_candidate


@dataclass(frozen=True)
class CandidateScenarioDiagnostic:
    scenario_id: str
    simulations: int
    null_familywise_false_positive_rate: float
    strong_terminal_power: float
    infinite_critical_value_rate: float
    mean_point_negative_raw_variance_fraction: float
    mean_bootstrap_nonpositive_raw_variance_fraction: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_psd_candidate_exploration(
    *,
    seed: int = 20261007,
    simulations_per_scenario: int = 250,
    bootstrap_draws: int = 500,
) -> dict[str, object]:
    if simulations_per_scenario < 50:
        raise ValueError("simulations_per_scenario must be >= 50")
    rng = np.random.default_rng(seed)
    rows: list[CandidateScenarioDiagnostic] = []

    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in enumerate(SCENARIOS):
        false_positive = 0
        strong_success = 0
        infinite = 0
        point_negative = 0.0
        bootstrap_nonpositive = 0.0
        oracle_se = _oracle_cell_standard_error(
            distribution=distribution,
            refit_count=refit_count,
            blocks_per_group=block_count,
            training_sd=training_sd,
            validation_sd=validation_sd,
            interaction_sd=interaction_sd,
        )
        strong_shift = 5.0 * oracle_se

        for simulation_index in range(simulations_per_scenario):
            world = _crossed_null_world(
                rng,
                refit_count=refit_count,
                blocks_per_group=block_count,
                group_count=6,
                contrast_count=2,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
                training_cross_cell_correlation=0.35,
                contrast_correlation=0.5,
                distribution=distribution,
            )
            gains, groups, blocks = _flatten_world(world)
            local_seed = seed + 1000003 * (scenario_index + 1) + 10007 * (simulation_index + 1)
            result = evaluate_psd_candidate(
                gains,
                groups,
                blocks=blocks,
                refit_ids=tuple(f"refit-{i:03d}" for i in range(refit_count)),
                confidence_level=0.95,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
            )
            lower = np.asarray(result.lower_bounds)
            false_positive += int(np.any(lower > 0.0))
            strong_success += int(np.all(lower + strong_shift > 0.0))
            infinite += int(result.infinite_critical_value)
            point_negative += result.point_negative_raw_variance_fraction
            bootstrap_nonpositive += result.bootstrap_nonpositive_raw_variance_fraction

        rows.append(
            CandidateScenarioDiagnostic(
                scenario_id=scenario_id,
                simulations=simulations_per_scenario,
                null_familywise_false_positive_rate=float(
                    false_positive / simulations_per_scenario
                ),
                strong_terminal_power=float(
                    strong_success / simulations_per_scenario
                ),
                infinite_critical_value_rate=float(
                    infinite / simulations_per_scenario
                ),
                mean_point_negative_raw_variance_fraction=float(
                    point_negative / simulations_per_scenario
                ),
                mean_bootstrap_nonpositive_raw_variance_fraction=float(
                    bootstrap_nonpositive / simulations_per_scenario
                ),
            )
        )

    return {
        "status": "exploratory_post_v1_power_failure_not_qualification_evidence",
        "seed": seed,
        "simulations_per_scenario": simulations_per_scenario,
        "bootstrap_draws": bootstrap_draws,
        "candidate": "raw_two_way_variance_positive_semidefinite_scalar_clip",
        "scenarios": [row.as_dict() for row in rows],
    }
