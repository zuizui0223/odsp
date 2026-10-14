"""Regression tests grounded in exact 12-row source structure, not pseudo animal data."""
import hashlib
import io
import importlib.util
import json
import sys
import zipfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import inspect_uljin_published_supp3_aggregate_v0 as reader
sp=importlib.util.spec_from_file_location("published_zones",ROOT/"scripts"/"run_uljin_published_supp3_daypart_signatures_v0.py")
analyzer=importlib.util.module_from_spec(sp)
sp.loader.exec_module(analyzer)
CONTRACT=json.loads((ROOT/"ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json").read_text())


def fixture_zip():
    rows=["Species\tdiel_period\tn\tn_total\tprop_pct\thours_total\tdetections_per_hour\tdetections_per_100h"]
    count_by_species={
      "Long-tailed goral":[1325,139,853],
      "Siberian roe deer":[463,73,272],
      "Water deer":[264,51,499],
      "Wild boar":[475,37,172],
    }
    for sp,counts in count_by_species.items():
        total=sum(counts)
        for p,n in zip(analyzer.PERIODS,counts):
            h=CONTRACT["published_period_hours"][p]
            rows.append(f"{sp}\t{p}\t{n}\t{total}\t{n/total*100:.1f}\t{h}\t{n/h}\t{100*n/h}")
    data=("\n".join(rows)+"\n").encode()
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr(CONTRACT["source"]["member"],data)
    return b.getvalue()


def analyze_fixture(monkeypatch):
    raw=fixture_zip()
    monkeypatch.setattr(reader,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    return analyzer.evaluate(CONTRACT,raw)


def test_report_does_not_promote_original_source_or_station_inference(monkeypatch):
    r=analyze_fixture(monkeypatch)
    assert r["status"]=="REPRODUCED_PUBLISHED_DAYPART_POOLED_DESCRIPTIVE_SIGNATURE_ONLY"
    assert r["calendar_24h_day_equivalent"]==387
    assert r["reproduced_total_events"]==4623
    assert len(r["six_pairwise_night_to_day_rate_ratio_comparisons"])==6
    assert r["posthoc_largest_descriptive_night_day_divergence"]["species_a"]=="Water deer"
    assert r["posthoc_largest_descriptive_night_day_divergence"]["species_b"]=="Wild boar"
    assert abs(r["posthoc_largest_descriptive_night_day_divergence"]["ratio_of_night_day_rate_ratios"]-5.21989517)<1e-7
    assert not r["frozen_original_41_day_pairs_tested"]
    assert not r["original_hourly_camera_operation_verified"]
    assert r["civil_twilight_is_NOT_daylight_edge_of_original_H1"]
    assert not r["inferential_p_value_computed"]


def test_published_source_rate_fields_not_trusted_if_inconsistent(monkeypatch):
    raw=fixture_zip()
    monkeypatch.setattr(reader,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    c=dict(CONTRACT)
    c["published_period_hours"]=dict(CONTRACT["published_period_hours"])
    c["published_period_hours"]["nighttime"]=1.
    with pytest.raises(ValueError,match="SOURCE_RATE"):
        analyzer.evaluate(c,raw)


def test_relabel_original_41_pair_result_not_permitted(monkeypatch):
    raw=fixture_zip()
    monkeypatch.setattr(reader,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    c=dict(CONTRACT)
    c["original_2022_fixed_41_matched_pairs_analyzed"]=True
    with pytest.raises(ValueError,match="POST_OUTCOME"):
        analyzer.evaluate(c,raw)
