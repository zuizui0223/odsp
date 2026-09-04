from odsp.state_prediction_benchmark import run_state_prediction_benchmark


def _cell(result, family, sample_size):
    return next(
        cell
        for cell in result.cells
        if cell.family == family and cell.sample_size_per_base == sample_size
    )


def test_finite_sample_prediction_benchmark_recovers_expected_transfer_states():
    result = run_state_prediction_benchmark()
    assert result.seed == 20260904
    assert result.sample_sizes == (50, 250, 1000)
    assert result.replicates == 128
    assert len(result.cells) == 9

    for n in result.sample_sizes:
        stable = _cell(result, "stable_generalizing", n)
        shifted = _cell(result, "shifted_non_generalizing", n)
        unorganized = _cell(result, "unorganized", n)

        assert stable.mean_log_score_gain > 0.15
        assert stable.positive_gain_fraction >= 0.95
        assert stable.mean_brier_improvement > 0

        assert shifted.mean_log_score_gain < -0.30
        assert shifted.negative_gain_fraction >= 0.95
        assert shifted.mean_brier_improvement < 0

        assert abs(unorganized.mean_log_score_gain) < 0.03


def test_probability_recovery_improves_with_sample_size():
    result = run_state_prediction_benchmark()
    for family in (
        "stable_generalizing",
        "unorganized",
        "shifted_non_generalizing",
    ):
        low = _cell(result, family, 50)
        high = _cell(result, family, 1000)
        assert high.mean_probability_rmse < low.mean_probability_rmse
        assert high.mean_probability_rmse < 0.03
