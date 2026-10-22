from collections import Counter
import io,csv
import pytest
from prospective.gyps_source_nonoverlap_crosswalk import (
   source_segments,hash_ids,normalize_name,FRENCH_SOURCE
)

def french():
    birds=[f"bird{i}" for i in range(30)]
    return {
      "selected_animal_IDs":birds,
      "horizontal_day_eligibility_by_cell_m":{"5000":{"admitted_bird_ids":birds[:28]}}
    }

def synthetic_csv():
    header=["studyID","studyName","species","individualID","segmentID",
            "dataSource","segm_timeStart"]
    rows=[
      ["122120597","Middle East Gyps source","Gyps fulvus","A1","s1","Movebank","2019-02-01"],
      ["44080734","Different Gyps source","Gyps fulvus","B1","s2","Movebank","2019-02-01"],
      ["122120597","Middle East Gyps source","Gyps africanus","AF1","s3","Movebank","2019-02-01"]
    ]
    out=io.StringIO()
    w=csv.writer(out);w.writerow(header);w.writerows(rows);out.seek(0)
    return csv.DictReader(out)

def test_metadata_id_compared_only_with_original_species_studies(monkeypatch):
    import prospective.gyps_source_nonoverlap_crosswalk as module
    monkeypatch.setattr(module,"FRENCH_HASH",hash_ids(french()["horizontal_day_eligibility_by_cell_m"]["5000"]["admitted_bird_ids"]))
    a=source_segments(synthetic_csv(),french())
    assert a["source_independence_category"]=="DIFFERENT_STUDY_NAMES_AND_ZERO_EXACT_SOURCE_ANIMAL_IDS"
    assert a["exact_bird_id_overlap_across_both_2026_Gyps_parents"]==0
    assert not a["native_height_values_read"]

def test_source_name_alias_case_whitespace_compare():
    assert normalize_name(FRENCH_SOURCE)==normalize_name("  EURASIAN griffon vulture in France (Grands Causses 2018) ID_PROG 961 ")

def test_reuse_same_bird_stops_independence(monkeypatch):
    import prospective.gyps_source_nonoverlap_crosswalk as module
    monkeypatch.setattr(module,"FRENCH_HASH",hash_ids(french()["horizontal_day_eligibility_by_cell_m"]["5000"]["admitted_bird_ids"]))
    x=synthetic_csv()
    rows=list(x)
    rows[0]["individualID"]="bird0"
    z=io.StringIO()
    w=csv.DictWriter(z,fieldnames=x.fieldnames);w.writeheader();w.writerows(rows);z.seek(0)
    a=source_segments(csv.DictReader(z),french())
    assert a["source_independence_category"]=="SOURCE_OR_ANIMAL_OVERLAP_REQUIRES_REVIEW"
    assert a["exact_bird_id_overlap_across_both_2026_Gyps_parents"]==1
