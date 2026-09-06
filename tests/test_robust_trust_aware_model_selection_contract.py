from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_robust_selection_contract_freezes_uncertainty_gate():
    contract=json.loads((ROOT/"ROBUST_TRUST_AWARE_MODEL_SELECTION_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-robust-trust-aware-model-selection-v3"
    settings=contract["frozen_settings"]
    assert settings["minimum_blocks_per_group"]==8
    assert settings["bootstrap_draws"]==2000
    obligations=contract["frozen_obligations"]
    assert obligations["fragile_legacy_v2_trusted"] is True
    assert obligations["fragile_v3_robust_rejected"] is True
    assert obligations["too_few_blocks_category"]=="unavailable"
    assert obligations["recommended_candidate"]=="robust_balanced"
    assert obligations["aggregate_confidence_score_emitted"] is False
    ceiling=contract["claim_boundary"]
    assert ceiling["bootstrap_interval_is_exact_finite_sample_guarantee"] is False
    assert ceiling["groupwise_coverage_is_conditional_coverage_theorem"] is False
    assert ceiling["block_bootstrap_repairs_bad_block_definition"] is False
