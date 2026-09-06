import json
import math
from pathlib import Path

from odsp.simultaneous_group_certification_benchmark import (
    run_simultaneous_group_certification_benchmark,
)


ROOT=Path(__file__).resolve().parents[1]


def _minimum(rows, field):
    values=[float(row[field]) for row in rows if row[field] is not None]
    return min(values) if values else None


def _maximum(rows, field):
    values=[float(row[field]) for row in rows if row[field] is not None]
    return max(values) if values else None


def test_simultaneous_group_certification_receipt_replays_first_green_result():
    receipt=json.loads((ROOT/"SIMULTANEOUS_GROUP_CERTIFICATION_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result=run_simultaneous_group_certification_benchmark(seed=20260906,bootstrap_draws=4000)
    canonical=receipt["canonical_results"]

    assert result["passed"] is True
    assert len(result["checks"])==canonical["obligation_count"]==15
    assert all(row["passed"] for row in result["checks"])

    strong=result["strong_positive"]
    expected=canonical["strong_positive"]
    for field in (
        "point_transfer_category","marginal_interval_category",
        "bonferroni_transfer_category","max_t_transfer_category",
        "simultaneous_admissible","max_t_robust_positive_group_count",
    ):
        assert strong[field]==expected[field]
    assert math.isclose(_minimum(strong["groups"],"marginal_lower_bound"),expected["minimum_marginal_lower_bound"],abs_tol=1e-12)
    assert math.isclose(_minimum(strong["groups"],"max_t_lower_bound"),expected["minimum_max_t_lower_bound"],abs_tol=1e-12)
    assert math.isclose(_minimum(strong["groups"],"bonferroni_lower_bound"),expected["minimum_bonferroni_lower_bound"],abs_tol=1e-12)
    assert math.isclose(strong["max_t_critical_value"],expected["max_t_critical_value"],abs_tol=1e-12)

    negative=result["strong_negative"]
    expected=canonical["strong_negative"]
    for field in (
        "point_transfer_category","marginal_interval_category",
        "bonferroni_transfer_category","max_t_transfer_category",
        "simultaneous_admissible","max_t_robust_nonpositive_group_count",
    ):
        assert negative[field]==expected[field]
    assert math.isclose(_maximum(negative["groups"],"max_t_upper_bound"),expected["maximum_max_t_upper_bound"],abs_tol=1e-12)
    assert math.isclose(negative["max_t_critical_value"],expected["max_t_critical_value"],abs_tol=1e-12)

    trap=result["multiplicity_trap"]
    expected=canonical["multiplicity_trap"]
    for field in (
        "group_count","point_transfer_category","marginal_interval_category",
        "bonferroni_transfer_category","max_t_transfer_category",
        "simultaneous_admissible","max_t_uncertain_group_count",
    ):
        assert trap[field]==expected[field]
    assert sum(row["marginal_status"]=="robust_positive" for row in trap["groups"])==expected["marginal_positive_group_count"]
    assert math.isclose(result["multiplicity_trap_marginal_minimum_lower_bound"],expected["minimum_marginal_lower_bound"],abs_tol=1e-12)
    assert math.isclose(result["multiplicity_trap_max_t_minimum_lower_bound"],expected["minimum_max_t_lower_bound"],abs_tol=1e-12)
    assert math.isclose(result["multiplicity_trap_bonferroni_minimum_lower_bound"],expected["minimum_bonferroni_lower_bound"],abs_tol=1e-12)
    assert math.isclose(result["max_t_critical_value"],expected["max_t_critical_value"],abs_tol=1e-12)

    mixed=result["one_negative_group"]
    expected=canonical["one_negative_group"]
    for field in (
        "point_transfer_category","marginal_interval_category",
        "bonferroni_transfer_category","max_t_transfer_category",
        "simultaneous_admissible","max_t_robust_positive_group_count",
        "max_t_robust_nonpositive_group_count",
    ):
        assert mixed[field]==expected[field]

    few=result["too_few_blocks"]
    expected=canonical["too_few_blocks"]
    for field in (
        "point_transfer_category","marginal_interval_category",
        "bonferroni_transfer_category","max_t_transfer_category",
        "simultaneous_admissible","unavailable_group_count","max_t_critical_value",
    ):
        assert few[field]==expected[field]

    single=result["single_group"]
    expected=canonical["single_group"]
    assert single["marginal_interval_category"]==expected["marginal_interval_category"]
    assert single["max_t_transfer_category"]==expected["max_t_transfer_category"]
    assert math.isclose(_minimum(single["groups"],"marginal_lower_bound"),expected["minimum_marginal_lower_bound"],abs_tol=1e-12)
    assert math.isclose(_minimum(single["groups"],"max_t_lower_bound"),expected["minimum_max_t_lower_bound"],abs_tol=1e-12)
    assert math.isclose(single["max_t_critical_value"],expected["max_t_critical_value"],abs_tol=1e-12)

    assert result["positive_global_weight_scaling_error"]<=1e-12
    assert result["row_order_error"]<=1e-12
    assert result["group_order_error"]<=1e-12
    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
