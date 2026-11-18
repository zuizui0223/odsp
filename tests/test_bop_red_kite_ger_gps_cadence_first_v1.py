"""First official source-GPS time-gap receipt: immutability and scientific ceiling."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest

from scripts.verify_bop_red_kite_ger_gps_cadence_first_v1 import (
    CONTRACT,RECEIPT,verify_first,
)

def sources():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_original_99_49_cadence_and_official_artifact_are_locked():
    receipt,c=sources()
    r=verify_first(receipt,c)
    assert r["first_official_archive_hash_verified"] is True
    assert r["original_cadence_source_run"]==44290699238
    assert r["original_eligible_seasons"]==99
    assert r["original_eligible_bird_strings"]==49
    assert r["eligible_fraction_under_55min"]==0.487398
    assert r["eligible_fraction_under_60min"]==0.64955
    assert r["original_downsampling_algorithm_known"] is False
    assert receipt["first_actions"]["artifact_id"]==14421093958
    assert receipt["cohorts"][1]["bins"]["30to45m"]==96527
    assert receipt["cohorts"][1]["bins"]["55to65m"]==82563

@pytest.mark.parametrize("path,value",[
    (("first_actions","artifact_zip_sha256"),"0"*64),
    (("first_actions","official_JSON_sha256"),"0"*64),
    (("first_actions","contract_sha256"),"0"*64),
    (("source_funnel","original_GPS_physical_lines"),500777),
    (("cohorts",1,"birds"),63),
    (("cohorts",1,"seasons"),100),
    (("cohorts",1,"p_under55"),0.0),
    (("cohorts",1,"bins","30to45m"),0),
    (("cohorts",1,"quantiles_minutes","q50"),60),
    (("interpretation","publication_input_GPS_downsampling_algorithm_identified"),True),
    (("interpretation","no_nesting_or_success_labels_accessed"),False),
    (("interpretation","original_BOP_terminal"),"generalizing"),
])
def test_mutated_source_metrics_or_claims_are_rejected(path,value):
    r,c=sources()
    altered=deepcopy(r)
    node=altered
    for k in path[:-1]:
        node=node[k]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(altered,c)

def test_modified_source_output_never_counts_as_first_official_gps_receipt():
    r,c=sources()
    with pytest.raises(ValueError,match="differs"):
        verify_first(r,c,raw=b'{"status":"SOURCE_GPS_CADENCE_OBSERVED_ONLY"}\n')

def test_first_code_artifact_contains_only_aggregate_histograms():
    r,_=sources()
    assert {c["cohort"] for c in r["cohorts"]}=={
        "all_linked_geo_season_years","source_primary_gt800_eligible_years"
    }
    assert all(isinstance(v,int) for a in r["cohorts"] for v in a["bins"].values())
    assert r["interpretation"]["no_real_GPS_coordinate_or_timestamp_or_birdID_exported"] is True
