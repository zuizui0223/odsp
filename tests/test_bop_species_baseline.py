from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.bop_species_baseline import (
    decompose_frozen_bop_gains,
    reconstruct_fold_training_marginals,
)
from odsp.mh_antwerpen_prediction import STATE_LABELS


def _admission(individual, species, fold, counts):
    return {
        "individual_id": individual,
        "species": species,
        "final_eligible": True,
        "state_counts": dict(zip(STATE_LABELS, counts)),
        "thinned_event_count": sum(counts),
        "fold": fold,
    }


def _mean_log(counts, probability):
    counts = np.asarray(counts, dtype=float)
    q = counts / counts.sum()
    positive = q > 0
    return float(np.dot(q[positive], np.log(np.asarray(probability)[positive])))


def _synthetic_result():
    admissions = [
        _admission("A0", "species-a", 0, [8, 2, 0, 0]),
        _admission("A1", "species-a", 1, [6, 4, 0, 0]),
        _admission("B0", "species-b", 0, [0, 0, 7, 3]),
        _admission("B1", "species-b", 1, [0, 0, 5, 5]),
    ]
    folds = {row["individual_id"]: row["fold"] for row in admissions}
    heldout = []
    for row in admissions:
        fold = row["fold"]
        species_marginals, pooled = reconstruct_fold_training_marginals(
            admissions, folds, fold
        )
        counts = [row["state_counts"][state] for state in STATE_LABELS]
        mean_pool = _mean_log(counts, pooled)
        mean_model = mean_pool + 0.2
        heldout.append(
            {
                "fold": fold,
                "heldout_individual": row["individual_id"],
                "heldout_event_count": sum(counts),
                "heldout_state_counts": row["state_counts"],
                "primary_status": "scored",
                "primary_score": {
                    "mean_log_score": mean_model,
                    "mean_marginal_log_score": mean_pool,
                    "mean_log_score_gain": 0.2,
                },
                "species": row["species"],
            }
        )
    return {
        "admissions": admissions,
        "fold_assignment": folds,
        "heldout_results": heldout,
    }


def test_reconstruct_fold_marginals_match_hierarchical_weighting():
    result = _synthetic_result()
    species, pooled = reconstruct_fold_training_marginals(
        result["admissions"], result["fold_assignment"], 0
    )
    assert species["species-a"] == pytest.approx([0.6, 0.4, 0.0, 0.0])
    assert species["species-b"] == pytest.approx([0.0, 0.0, 0.5, 0.5])
    assert pooled == pytest.approx([0.3, 0.2, 0.25, 0.25])


def test_decomposition_is_exact_and_does_not_reclassify_primary():
    output = decompose_frozen_bop_gains(_synthetic_result())
    assert output["primary_terminal_decision_recomputed"] is False
    assert output["primary_terminal_decision_changed"] is False
    assert len(output["individual_rows"]) == 4
    for row in output["individual_rows"]:
        assert row["total_gain_frozen"] == pytest.approx(0.2)
        assert row["total_gain_frozen"] == pytest.approx(
            row["species_component"] + row["context_within_species_component"]
        )
        assert abs(row["pooled_baseline_reconstruction_error"]) <= 1e-12
        assert abs(row["additivity_error"]) <= 1e-12
    assert output["overall_summary"]["mean_total_gain"] == pytest.approx(0.2)


def test_reconstruction_guard_rejects_drifted_frozen_marginal_score():
    result = _synthetic_result()
    result["heldout_results"][0]["primary_score"]["mean_marginal_log_score"] += 0.01
    with pytest.raises(AssertionError, match="pooled baseline reconstruction failed"):
        decompose_frozen_bop_gains(result)


def test_additivity_guard_rejects_drifted_frozen_gain():
    result = _synthetic_result()
    result["heldout_results"][0]["primary_score"]["mean_log_score_gain"] += 0.01
    with pytest.raises(AssertionError, match="gain decomposition failed"):
        decompose_frozen_bop_gains(result)


def test_species_baseline_requires_training_support_for_observed_states():
    result = _synthetic_result()
    # Put observed mass into a state absent from the same-species training individual.
    row = result["heldout_results"][0]
    row["heldout_state_counts"] = dict(zip(STATE_LABELS, [8, 0, 2, 0]))
    # Keep the old frozen comparator fields: the reconstruction guard must fail closed.
    with pytest.raises((AssertionError, ValueError)):
        decompose_frozen_bop_gains(result)
