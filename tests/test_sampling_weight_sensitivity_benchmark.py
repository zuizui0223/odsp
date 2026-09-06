from odsp.sampling_weight_sensitivity_benchmark import run_sampling_weight_sensitivity_benchmark


def test_frozen_sampling_weight_sensitivity_benchmark_passes():
    result=run_sampling_weight_sensitivity_benchmark(seed=20260906,bootstrap_draws=2000)
    assert result["passed"] is True
    assert len(result["checks"])==11
    assert all(row["passed"] for row in result["checks"])
    assert result["stable"]["sensitivity_category"]=="weight_robust_generalizing"
    assert result["sensitive"]["sensitivity_category"]=="weight_sensitive"
    by={row["name"]:row for row in result["sensitive"]["scenarios"]}
    assert by["uniform"]["robust_transfer_category"]=="robust_generalizing"
    assert by["upweight_negative"]["robust_transfer_category"]=="robust_non_generalizing"
    assert result["too_few_blocks"]["sensitivity_category"]=="stable_unavailable"
