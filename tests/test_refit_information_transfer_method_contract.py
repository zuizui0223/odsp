from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_refit_information_transfer_method_contract_keeps_alignment_and_nonoverride_rules():
    contract = json.loads(
        (ROOT / "ODSP_REFIT_INFORMATION_TRANSFER_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["schema_version"] == 1
    assert contract["command"] == "odsp transfer-refits --contract ENDPOINT.json"
    assert "every refit contains exactly the same held-out row_id set" in contract["alignment_requirements"]
    assert contract["refit_mixture"]["weighting"] == "uniform"
    assert contract["refit_mixture"]["refit_independence_assumed"] is False
    assert contract["refit_mixture"]["variance_divided_by_sqrt_refit_count"] is False
    assert contract["confirmatory_rules"]["refit_scheme_frozen_before_outcome_scoring"] is True
    assert contract["confirmatory_rules"]["reference_refit_id_required"] is True
    assert contract["non_override_rules"]["reference_fit_can_override_refit_aware_failure"] is False
    assert contract["non_override_rules"]["total_gain_can_override_failed_information_step"] is False
    assert contract["scientific_boundaries"]["upstream_refits_generated_by_odsp"] is False
    assert contract["scientific_boundaries"]["refit_aware_interval_is_exact_population_guarantee"] is False
