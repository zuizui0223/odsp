from odsp.simultaneous_group_certification_benchmark import (
    run_simultaneous_group_certification_benchmark,
)


def test_frozen_simultaneous_group_certification_benchmark_passes():
    result=run_simultaneous_group_certification_benchmark(
        seed=20260906,bootstrap_draws=4000
    )
    assert result["passed"] is True
    assert len(result["checks"])==15
    assert all(row["passed"] for row in result["checks"])
    trap=result["multiplicity_trap"]
    assert trap["marginal_interval_category"]=="robust_generalizing"
    assert trap["max_t_transfer_category"]=="uncertain"
    assert trap["bonferroni_transfer_category"]=="uncertain"
    assert result["multiplicity_trap_marginal_minimum_lower_bound"]>0.0
    assert result["multiplicity_trap_max_t_minimum_lower_bound"]<=0.0
    assert result["multiplicity_trap_bonferroni_minimum_lower_bound"]<=0.0
    assert result["max_t_critical_value"]>1.96
