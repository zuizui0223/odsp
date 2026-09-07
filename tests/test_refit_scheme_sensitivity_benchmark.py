from odsp.refit_scheme_sensitivity_benchmark import run_refit_scheme_sensitivity_benchmark


def test_frozen_refit_scheme_sensitivity_benchmark_passes():
    result=run_refit_scheme_sensitivity_benchmark(seed=20260907,nested_draws=2500)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    assert result["stable_positive"]["sensitivity_category"]=="scheme_robust_generalizing"
    assert result["stable_negative"]["sensitivity_category"]=="scheme_robust_non_generalizing"
    assert result["scheme_sensitive"]["sensitivity_category"]=="scheme_sensitive"
    assert result["one_unavailable_scheme"]["sensitivity_category"]=="unavailable"
