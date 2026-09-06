from odsp.bias_robust_model_selection_benchmark import run_bias_robust_model_selection_benchmark


def test_frozen_bias_robust_model_selection_benchmark_passes():
    result=run_bias_robust_model_selection_benchmark()
    assert result["passed"] is True
    assert len(result["checks"])==11
    assert all(row["passed"] for row in result["checks"])
    selection=result["selection"]
    assert selection["recommended_by_log_score"]=="robust_balanced"
    assert selection["pareto_front_names"]==["robust_balanced"]
    assert set(selection["bias_robust_trusted_names"])=={"robust_balanced","robust_broad"}
