import csv,io,hashlib
import pytest
from prospective.france_scacco_gyps_source_crosswalk import (
 source_studies,crosswalk,norm,EXCLUDED_CALIBRATION,FRANCE_5KM_HASH
)

def old():
    data=[
      {"studyName":"Vultures in Sardinia","studyID":"122120597",
       "individualID":"otherA","species":"Gyps fulvus","dataSource":"Movebank","segm_timeStart":"2018-06-01"},
      {"studyName":"Vultures in Israel","studyID":"44080734",
       "individualID":"otherB","species":"Gyps fulvus","dataSource":"Movebank","segm_timeStart":"2018-06-01"},
    ]
    buf=io.StringIO();f=csv.DictWriter(buf,fieldnames=list(data[0]));f.writeheader();f.writerows(data);buf.seek(0)
    return source_studies(csv.DictReader(buf))[0]

def french():
    ids={"b"+str(i) for i in range(28)}
    assert hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()!=FRANCE_5KM_HASH
    # The real roster is required to match SHA; substitute for tiny synthetic set
    x={
      "phase":"FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT",
      "numeric_native_GPS_height_values_read":False,
      "source_zip_md5":"b18cc8004d311d19ff24060f655178bf",
      "selected_animal_IDs":sorted(ids|{EXCLUDED_CALIBRATION,"notincluded"}),
      "horizontal_day_eligibility_by_cell_m":{
        "5000":{"admitted_bird_ids":sorted(ids),
                 "source_bird_ID_sha256":hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()},
        "50000":{"admitted_bird_ids":sorted(ids|{EXCLUDED_CALIBRATION})}
      }
    }
    return x,ids

def test_normalized_study_name_is_deterministic():
    assert norm("  Eurasian  GRIFFON  vulture  ")=="eurasian griffon vulture"

def test_preheight_roster_rejects_drift_even_when_ids_look_reasonable():
    f,ids=french()
    with pytest.raises(ValueError,match="5km"):
        crosswalk(old(),f)

def test_geodesy_test_cannot_be_reclassified_as_bird_after_gate(monkeypatch):
    from prospective import france_scacco_gyps_source_crosswalk as code
    f,ids=french()
    monkeypatch.setattr(code,"FRANCE_5KM_HASH", f["horizontal_day_eligibility_by_cell_m"]["5000"]["source_bird_ID_sha256"])
    c=crosswalk(old(),f)
    assert c["France_original_5km_biological_birds"]==28
    assert c["France_corrected_50km_biological_birds"]==28
    assert not c["fully_independent_device_or_parent_confirmed"]
    assert c["independence_class"]=="NO_LITERAL_STUDY_NAME_OR_BIRD_ID_OVERLAP_PARENT_ID_UNCONFIRMED"
    assert c["native_GPS_altitude_value_read"] is False

def test_exact_previous_parent_study_name_identified(monkeypatch):
    from prospective import france_scacco_gyps_source_crosswalk as code
    f,ids=french()
    monkeypatch.setattr(code,"FRANCE_5KM_HASH", f["horizontal_day_eligibility_by_cell_m"]["5000"]["source_bird_ID_sha256"])
    oldv=old()
    oldv["122120597"]["study_names"]={"Eurasian griffon vulture in France (Grands Causses 2018) ID_PROG 961":1}
    c=crosswalk(oldv,f)
    assert c["independence_class"]=="POTENTIAL_SAME_STUDY_PARENT_OR_BIRDS"
    assert c["exact_study_name_matches"]==["122120597"]

def test_prior_height_screened_receipt_fails(monkeypatch):
    from prospective import france_scacco_gyps_source_crosswalk as code
    f,ids=french();f["numeric_native_GPS_height_values_read"]=True
    with pytest.raises(ValueError,match="height"):
        crosswalk(old(),f)
