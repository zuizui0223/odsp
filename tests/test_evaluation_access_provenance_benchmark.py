from odsp.evaluation_access_provenance_benchmark import run_evaluation_access_provenance_benchmark


def test_evaluation_access_provenance_known_truth_benchmark():
    result = run_evaluation_access_provenance_benchmark()
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["pre_final_stage_count"] == 3
    assert result["clean"]["separation_category"] == "final_evaluation_not_accessed_in_declared_pre_final_stages"
    assert result["single_leak"]["leaking_stage_count"] == 1
    assert result["repeated_leak"]["final_evaluation_access_occurrence_count"] == 2
    assert result["multi_stage_leak"]["leaking_stage_count"] == 3
    assert result["multi_stage_leak"]["final_evaluation_access_occurrence_count"] == 4
    assert result["stage_order_invariant"] is True
