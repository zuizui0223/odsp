import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sp=importlib.util.spec_from_file_location("clock_solar",ROOT/"scripts"/"run_uljin_published_clock_solar_pair_extrema_v0.py")
m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
CONTRACT=json.loads((ROOT/"ULJIN_PUBLISHED_CLOCK_SOLAR_PAIR_EXTREMA_V0_CONTRACT.json").read_text())


def dummy():
    solar_values=[.8194876177763057,.7653796423897938,.8122383292714762,.7488301839318245,.7524801451275654,.6334558176270506]
    rows=[]
    for p,delta in zip(CONTRACT["clock_table4_three_decimal"],solar_values):
        rows.append({"species_1":p["a"],"species_2":p["b"],
          "n_1":"2317","n_2":"814","estimator":"Dhat4","delta":str(delta),
          "ci_low":str(delta-.04),"ci_high":str(delta+.04),"n_boot":"1000","time_basis":"solar_time"})
    return {"status":"SOURCE_VERIFIED_PUBLISHED_SOLAR_TIME_AGGREGATE_ONLY",
       "tables":[{"status":"PUB_AGGREGATE_TABLE","columns":list(rows[0]),"row_count":6,"rows":rows}]}


def test_both_public_extrema_stable_but_no_inference():
    x=m.compare(CONTRACT,dummy())
    assert x["lowest_pair_persists"] and x["highest_pair_persists"]
    assert x["lowest_pair"]["species_a"]=="Water deer"
    assert x["lowest_pair"]["species_b"]=="Wild boar"
    assert abs(x["lowest_pair"]["solar_delta"]-.633455818)<1e-8
    assert not x["independent_replication_claimed"]
    assert not x["solar_and_clock_shift_significance_computed"]
    assert not x["original_41_daylength_pair_effect_computed"]


def test_source_roster_or_prevalidated_requirement_cannot_be_removed():
    broken=dummy()
    broken["status"]="NOT_VERIFIED"
    with pytest.raises(ValueError,match="SOURCE_NOT_VERIFIED"):
        m.compare(CONTRACT,broken)
    broken=dummy()
    broken["tables"][0]["rows"].pop()
    broken["tables"][0]["row_count"]=5
    with pytest.raises(ValueError,match="SCHEMA"):
        m.compare(CONTRACT,broken)
