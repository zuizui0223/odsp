from __future__ import annotations

import numpy as np
import pytest

from odsp.bop_species_baseline import reconstruct_fold_training_marginals
from odsp.covariate_state_prediction import make_state_classifier
from odsp.mh_antwerpen_prediction import STATE_LABELS
from odsp.workflow import (
    EventTableSpec,
    cross_validate_state_events,
    equal_stratum_equal_group_training_weights,
    prepare_event_table,
    training_state_baselines,
)


def _workflow_rows():
    rows = []
    definitions = (
        ("A0", "species-a", 0, 8, 2),
        ("A1", "species-a", 1, 8, 2),
        ("B0", "species-b", 0, 2, 8),
        ("B1", "species-b", 1, 2, 8),
    )
    for group, species, fold, low_n, high_n in definitions:
        rows.extend(
            {
                "state": "low",
                "x": -1.0,
                "individual": group,
                "species": species,
                "fold": fold,
            }
            for _ in range(low_n)
        )
        rows.extend(
            {
                "state": "high",
                "x": 1.0,
                "individual": group,
                "species": species,
                "fold": fold,
            }
            for _ in range(high_n)
        )
    return rows


def test_long_table_workflow_returns_exact_additive_baseline_decomposition():
    pytest.importorskip("sklearn")
    spec = EventTableSpec(
        state="state",
        features=("x",),
        group="individual",
        stratum="species",
        fold="fold",
    )
    estimator = make_state_classifier(
        "multinomial_logit",
        random_state=11,
        C=100.0,
        max_iter=2000,
    )
    pooled = cross_validate_state_events(
        _workflow_rows(),
        spec=spec,
        estimator=estimator,
        baseline="pooled",
        training_weight_policy=equal_stratum_equal_group_training_weights,
    )
    stratum = cross_validate_state_events(
        _workflow_rows(),
        spec=spec,
        estimator=estimator,
        baseline="stratum",
        training_weight_policy=equal_stratum_equal_group_training_weights,
    )

    assert len(pooled.groups) == 4
    assert [row.group for row in pooled.groups] == [row.group for row in stratum.groups]
    for pooled_row, stratum_row in zip(pooled.groups, stratum.groups):
        assert pooled_row.additivity_error == pytest.approx(0.0, abs=1e-12)
        assert stratum_row.additivity_error == pytest.approx(0.0, abs=1e-12)
        assert pooled_row.requested_baseline_gain == pytest.approx(pooled_row.pooled_gain)
        assert stratum_row.requested_baseline_gain == pytest.approx(
            stratum_row.context_within_stratum_component
        )
        assert pooled_row.pooled_gain == pytest.approx(
            pooled_row.stratum_component
            + pooled_row.context_within_stratum_component
        )


def _admission(individual, species, fold, counts):
    return {
        "individual_id": individual,
        "species": species,
        "final_eligible": True,
        "state_counts": dict(zip(STATE_LABELS, counts)),
        "thinned_event_count": sum(counts),
        "fold": fold,
    }


def _bop_synthetic_rows():
    admissions = [
        _admission("A0", "species-a", 0, [8, 2, 0, 0]),
        _admission("A1", "species-a", 1, [6, 4, 0, 0]),
        _admission("B0", "species-b", 0, [0, 0, 7, 3]),
        _admission("B1", "species-b", 1, [0, 0, 5, 5]),
    ]
    rows = []
    for admission in admissions:
        for state_index, state in enumerate(STATE_LABELS):
            for _ in range(admission["state_counts"][state]):
                rows.append(
                    {
                        "state": state,
                        "dummy": float(state_index),
                        "individual": admission["individual_id"],
                        "species": admission["species"],
                        "fold": admission["fold"],
                    }
                )
    return admissions, rows


def test_generic_training_baselines_reproduce_bop_hierarchical_marginals():
    admissions, rows = _bop_synthetic_rows()
    folds = {row["individual_id"]: row["fold"] for row in admissions}
    specific_species, specific_pooled = reconstruct_fold_training_marginals(
        admissions, folds, 0
    )

    spec = EventTableSpec(
        state="state",
        features=("dummy",),
        group="individual",
        stratum="species",
        fold="fold",
    )
    prepared = prepare_event_table(rows, spec)
    train_index = np.flatnonzero(prepared.fold != 0)
    generic = training_state_baselines(
        prepared,
        train_index,
        classes=STATE_LABELS,
        training_weight_policy=equal_stratum_equal_group_training_weights,
    )

    assert np.asarray(generic.pooled) == pytest.approx(specific_pooled)
    for species, expected in specific_species.items():
        assert generic.stratum_probability(species) == pytest.approx(expected)


def test_group_may_not_silently_cross_folds_or_strata():
    rows = _workflow_rows()
    rows[0] = dict(rows[0], fold=99)
    spec = EventTableSpec(
        state="state",
        features=("x",),
        group="individual",
        stratum="species",
        fold="fold",
    )
    with pytest.raises(ValueError, match="multiple fold values"):
        prepare_event_table(rows, spec)


def test_stratum_baseline_requires_declared_stratum():
    spec = EventTableSpec(
        state="state",
        features=("x",),
        group="individual",
        fold="fold",
    )
    with pytest.raises(ValueError, match="requires spec.stratum"):
        cross_validate_state_events(
            _workflow_rows(),
            spec=spec,
            estimator=object(),
            baseline="stratum",
        )
