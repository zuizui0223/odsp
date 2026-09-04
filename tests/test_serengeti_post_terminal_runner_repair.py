import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_n2_serengeti_temporal_partition.py"
RECORD = ROOT / "N2_SERENGETI_POST_TERMINAL_RUNNER_REPAIR.json"


def test_repaired_runner_is_valid_python():
    source = RUNNER.read_text(encoding="utf-8")
    ast.parse(source)
    assert '"outcome_opened": true' not in source
    assert '"outcome_opened": false' not in source
    assert '"true_activity_niche_partition_identified": false' not in source
    assert '"interspecific_displacement_causality_identified": false' not in source
    assert '"solar_time_partition_identified": false' not in source
    assert '"bat_endpoint_reinterpreted": false' not in source


def test_frozen_serengeti_constants_are_unchanged():
    source = RUNNER.read_text(encoding="utf-8")
    required = (
        'EXPECTED_CONSENSUS_MD5 = "5ed2d32fd09127c178cf9dca8ccfd623"',
        'EXPECTED_EFFORT_MD5 = "27cb42f3feaa0642b17cbde24ba15fbd"',
        "CERTAINTY_MIN = 0.8",
        "INDEPENDENCE_MINUTES = 30",
        "MIN_EVENTS = 500",
        "MIN_SITES = 20",
        "MIN_EVENTS_EACH_FOLD = 50",
        "N_FOLDS = 3",
        "N_PERMUTATIONS = 199",
        "PERMUTATION_SEED = 20260903",
        "ALPHA = 0.05",
        "PSEUDOCOUNT = 0.5",
    )
    for token in required:
        assert token in source


def test_repair_record_forbids_post_terminal_rerun_or_reinterpretation():
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["terminal_category"] == "temporal_partition_generalizing"
    assert record["scientific_endpoint_closed_before_this_repair"] is True
    assert record["scientific_quantities_changed"] is False
    assert record["terminal_result_recomputed"] is False
    assert record["rerun_authorized"] is False
    assert len(record["repair"]["replacements"]) == 6
