from odsp.evaluation_content_provenance_benchmark import run_evaluation_content_provenance_benchmark


def test_evaluation_content_provenance_frozen_known_truth_benchmark_passes():
    result = run_evaluation_content_provenance_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["clean"]["separation_category"] == "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
    assert result["single_exact_copy"]["separation_category"] == "final_evaluation_content_leakage"
    assert result["single_exact_copy"]["final_evaluation_content_match_occurrence_count"] == 1
    assert result["repeated_exact_copy"]["final_evaluation_content_match_occurrence_count"] == 2
    assert result["multi_stage_exact_copy"]["leaking_stage_count"] == 3
