"""Known paper counts only; no events or source-operation rows opened."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from odsp.uljin_published_taxon_rate_sparsity_v1 import (
    published_taxon_rate_sparsity_scenario,
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads(
    (ROOT/"ULJIN_PUBLISHED_SPECIES_SPARSE_MATCH_SENSITIVITY_V1_CONTRACT.json").read_text()
)


def test_paper_species_totals_and_hypothetical_sparse_pairs_only():
    out=published_taxon_rate_sparsity_scenario(PLAN)
    rows=out["published_species_scenarios"]
    assert sum(row["article_total_independent_events"] for row in rows)==4623
    assert len(rows)==4
    result={row["taxon"]:row for row in rows}
    assert result["Naemorhedus caudatus"][
        "expected_station_taxon_date_pairs_with_both_dates_detected"
    ]==pytest.approx(18.753,abs=.001)
    assert result["Hydropotes inermis"][
        "expected_station_taxon_date_pairs_with_both_dates_detected"
    ]==pytest.approx(2.433,abs=.001)
    assert result["Capreolus pygargus"][
        "expected_station_taxon_date_pairs_with_both_dates_detected"
    ]==pytest.approx(2.398,abs=.001)
    assert result["Sus scrofa"][
        "expected_station_taxon_date_pairs_with_both_dates_detected"
    ]==pytest.approx(1.725,abs=.001)
    assert 25<out["sum_hypothetical_matched_station_species_date_pairs"]<26
    assert out["real_station_or_date_eligibility_verified"] is False
    assert out["source_operation_hourly_coverage_verified"] is False
    assert out["uses_published_global_taxon_totals_not_source_event_rows"]
    assert out["new_wildlife_mechanism_claimed"] is False
    assert out["original_41_matched_calendar_dates_changed"] is False
    assert out["independent_spatial_sampling_or_Poisson_process_validated"] is False
    json.dumps(out,allow_nan=False)


def test_do_not_reclassify_v0_equal_rate_scenario_or_select_species_postoutcome():
    changed=json.loads(json.dumps(PLAN))
    changed["predeclared_four_species_total_counts"]["Sus scrofa"]=900
    with pytest.raises(ValueError,match="identity changed"):
        published_taxon_rate_sparsity_scenario(changed)
    changed=json.loads(json.dumps(PLAN))
    del changed["predeclared_four_species_total_counts"]["Hydropotes inermis"]
    with pytest.raises(ValueError,match="identity changed"):
        published_taxon_rate_sparsity_scenario(changed)
    changed=json.loads(json.dumps(PLAN))
    changed["no_original_ecology_or_qualified_ODSP_route_promoted"]=False
    with pytest.raises(ValueError,match="identity changed"):
        published_taxon_rate_sparsity_scenario(changed)
