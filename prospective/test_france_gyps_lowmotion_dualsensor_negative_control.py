"""Frozen 2019-2021 French low-motion Gyps negative-control source guards."""
from collections import Counter
import csv
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from prospective import france_gyps_lowmotion_source_gate as source
from prospective import france_gyps_lowmotion_dualsensor_negative_control as negative


def made_birds():
    return [f"Bird-{i:02d}" for i in range(28)]


def source_mock(birds,low_eligible=None):
    if low_eligible is None:low_eligible=birds[:11]
    allsha=hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest()
    lowsha=hashlib.sha256("\n".join(sorted(low_eligible)).encode()).hexdigest()
    origin={
       "phase":"FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT",
       "numeric_native_GPS_height_values_read":False,
       "source_zip_md5":source.ORIGINAL_MD5,
       "quarantined_nonbiological_animal_IDs":["Test géodésie ornitela"],
       "horizontal_day_eligibility_by_cell_m":{"5000":{
           "admitted_bird_ids":birds,"source_bird_ID_sha256":allsha
       }}
    }
    low={
       "analysis":negative.LOWMOTION_STAGE,
       "independent_native_height_values_opened":False,
       "source_MD5":source.ORIGINAL_MD5,
       "original_previous_flight_eligible_bird_roster_sha256":allsha,
       "original_eligible_lowmotion_bird_IDs":sorted(low_eligible),
       "lowmotion_eligible_bird_ID_sha256":lowsha,
       "original_eligible_lowmotion_birds":len(low_eligible),
       "admitted_for_separately_frozen_negative_control":len(low_eligible)>=10,
       "all_source_lowmotion_five_minute_events":300,
       "lowmotion_eligible_bird_days":22,
       "lowmotion_eligible_scored_five_minute_events":300
    }
    flight={
       "analysis":"FRENCH_GYPS_2019_2021_GPS_VS_BARO_5KM_INDIVIDUAL_HEIGHT_SHAPE_V1",
       "terminal":"paired_sensor_robust_individual_height_shape",
       "source_archive_md5":source.ORIGINAL_MD5,
       "preheight_bird_roster_sha256":allsha,
       "sensor_results":{"GPS":{"observed":{"per_bird":{}}},"BAROMETRIC":{"observed":{"per_bird":{}}}}
    }
    return origin,low,flight,allsha


def test_no_height_before_lowmotion_prehorizon_candidate_gate(monkeypatch,tmp_path):
    birds=made_birds()
    origin,low,flight,sha=source_mock(birds,low_eligible=birds[:9])
    monkeypatch.setattr(source,"PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA",sha)
    # Fake source file is deliberately absent. The negative control *must*
    # return unavailable without opening even one source height.
    report=negative.test_results(tmp_path/"NO_SOURCE_ZIP.zip",low,origin,flight,tmp_path/"out")
    assert report["status"]=="unavailable"
    assert report["reason"]=="frozen_nonheight_low_motion_5km_source_below_10_birds"
    assert "native_low_motion_quality" not in report
    assert (tmp_path/"out/FRANCE_GYPS_LOWMOTION_DUAL_HEIGHT_NEGATIVE_CONTROL_RESULT_V1.json").exists()


def test_preheight_eligibility_only_frozen_flight_names(monkeypatch):
    birds=made_birds()
    origin,low,flight,sha=source_mock(birds)
    monkeypatch.setattr(source,"PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA",sha)
    assert negative.verify_source_gates(low,origin,flight)==set(birds[:11])
    low["original_eligible_lowmotion_bird_IDs"].append("NotAnOriginalBird")
    low["original_eligible_lowmotion_birds"]+=1
    with pytest.raises(ValueError,match="28-bird"):
        negative.verify_source_gates(low,origin,flight)


def test_corrupted_original_flight_positive_cannot_be_reclassified(monkeypatch):
    birds=made_birds()
    origin,low,flight,sha=source_mock(birds)
    monkeypatch.setattr(source,"PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA",sha)
    flight["terminal"]="not_supported_own_bird_altitude_shape"
    with pytest.raises(ValueError,match="archived positive flight result"):
        negative.verify_source_gates(low,origin,flight)


def test_lowmotion_native_first_fix_selected_without_height_aware_replacement(monkeypatch,tmp_path):
    monkeypatch.setattr(source,"check_immutable_source",lambda path:None)
    headers=[
      "timestamp","individual-local-identifier","individual-taxon-canonical-name",
      "location-long","location-lat","ground-speed",
      "visible","import-marked-outlier","gps:hdop","gps:satellite-count",
      "tag-local-identifier",
      "height-above-msl","bar:barometric-height"
    ]
    first=["2019-08-01 08:00:00.000","Bird1","Gyps fulvus",
           "2.8","43.7","0.25","true","false","1.1","10","tag1",
           "NATIVE_HEIGHT_MISSING","NATIVE_BARO_MISSING"]
    later=list(first)
    later[0]="2019-08-01 08:01:00.000"
    later[-2]="1100"
    later[-1]="1000"
    zipfile_path=tmp_path/"fake.zip"
    with zipfile.ZipFile(zipfile_path,"w") as archive:
        for year in (2019,2020,2021):
            for season in ("Jan_to_May","Jun_to_Aug","Sep_to_Dec"):
                filename=f"Vulturestracks_{season}{year}.csv"
                file_lines=[",".join(headers)]
                if year==2019 and season=="Jun_to_Aug":
                    file_lines.extend([",".join(first),",".join(later)])
                archive.writestr(filename,"\n".join(file_lines)+"\n")
    chosen,audit=negative.native_lowmotion_first_heights(zipfile_path,{"Bird1"})
    assert len(chosen)==1
    v=next(iter(chosen.values()))
    assert v[0]=="2019-08-01 08:00:00.000"
    assert v[3]=="NATIVE_HEIGHT_MISSING"
    assert v[4]=="NATIVE_BARO_MISSING"


def test_speed_band_no_overlap_flight_speed():
    assert negative.LOWSPEED==(0.,1.)
    assert negative.LOWSPEED[1]<5.0
