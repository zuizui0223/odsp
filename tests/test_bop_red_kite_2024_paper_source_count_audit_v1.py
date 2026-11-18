"""No-GPS, no-reproductive-label, first-receipt and historical code citation audit."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.audit_bop_red_kite_paper_source_count_path_v1 import (
    MATRIX,IDENTITY,GPS,STAGES,evaluate,run,
)

def objs():
    return tuple(json.loads(f.read_text(encoding="utf-8"))
                 for f in (MATRIX,IDENTITY,GPS,STAGES))

def test_actual_historical_frozen_receipts_contradict_paper_bird_count():
    result=run()
    assert result["status"]=="CODE_COUNT_PATH_DISCREPANCY_IDENTIFIED_AUTHOR_CAUSE_UNCONFIRMED"
    assert result["published_original"]=={"seasons":163,"birds":65}
    assert result["frozen_source_original"]=={"seasons":159,"bird_id_strings":63}
    assert result["published_eligible"]=={"seasons":99,"birds":63}
    assert result["frozen_source_eligibility"]=={"seasons":99,"bird_id_strings":49}
    assert result["source_birds_lost_at_GPS_threshold"]==14
    assert result["source_seasons_lost_at_GPS_threshold"]==60
    assert result["raw_unfiltered_bird_ID_count_equals_published_eligible_count"] is True
    assert result["archived_script_explicit_unfiltered_count"] is True
    assert result["proves_author_error"] is False
    assert result["recomputed_outcomes_or_predictions"] is False
    assert result["verified_biological_individuals"] is False
    assert result["historical_BOP_terminal"]=="empirical_state_prediction_mixed"

@pytest.mark.parametrize("path,value",[
    (("references","paper","reported_eligible_GER_birds"),49),
    (("references","paper","reported_original_GER_birds"),63),
    (("references","contemporary_code","blob_sha"),"0"*40),
    (("references","contemporary_code","exact_counting_operator"),"number_of_fixes >= minlocs"),
    (("references","archive_script_evidence","unfiltered_global_GER_bird_count_line"),487),
    (("references","archive_script_evidence","unfiltered_R_expression"),"length(unique(GER_data_input$summary$bird_id))"),
    (("references","contemporary_code","direct_2024_GitHub_to_Zenodo_binary_package_SHA_parity_verified"),True),
    (("source_to_paper_discrepancies","paper_63_may_be_unfiltered_count"),"CONFIRMED"),
    (("source_to_paper_discrepancies","paper_eligible_63_birds_reproduced"),True),
    (("additional_unresolved","exact_original_upstream_GPS_60_min_resampling_recipe_unknown"),False),
    (("statistical_claim_ceiling","red_kite_real_group_rank"),"SUCCESS"),
])
def test_documentary_overclaim_or_rewritten_code_fails(path,value):
    data=list(objs())
    m=deepcopy(data[0])
    item=m
    for k in path[:-1]:
        item=item[k]
    item[path[-1]]=value
    with pytest.raises(ValueError):
        evaluate(m,*data[1:])

@pytest.mark.parametrize("which,path,value",[
    (1,("original_source_output","sources",0,"distinct_bird_ID_strings"),65),
    (2,("observed_source","all_12_fixed_arms",0,2),63),
    (3,("observed_first","stages",4,2),63),
    (3,("observed_first","full_provider_MD5s_verified"),False),
])
def test_tampered_source_receipts_rejected(which,path,value):
    data=list(objs())
    bad=deepcopy(data[which])
    item=bad
    for k in path[:-1]:
        item=item[k]
    item[path[-1]]=value
    data[which]=bad
    with pytest.raises(ValueError):
        evaluate(*data)

def test_no_access_to_original_csv_or_sensitive_identifiers():
    m,*_=objs()
    assert m["role"]=="POSTPUBLICATION_CODE_PROVENANCE_AND_SOURCE_COUNT_RECONCILIATION_NO_NEW_DATA_ACCESS"
    assert m["frozen_internal_evidence"]["label_column_values_not_read"] is True
    assert m["frozen_internal_evidence"]["no_exact_GPS_or_bird_ID_exported"] is True
    assert m["additional_unresolved"]["appendix_s1_sex_age_sample_count_independently_checked"] is False
    assert m["source_to_paper_discrepancies"]["paper_63_may_be_unfiltered_count"]=="PLAUSIBLE_NOT_PROVEN"
