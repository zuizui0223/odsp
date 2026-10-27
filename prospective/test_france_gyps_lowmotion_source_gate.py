"""Low-motion ALTITUDE-BLIND matched-source Gyps negative-control tests."""
from collections import Counter
import csv
import hashlib
import io

import pytest

from prospective import france_gyps_lowmotion_source_gate as lm


FIELDS=[
 "timestamp","individual-local-identifier","tag-local-identifier",
 "individual-taxon-canonical-name","location-long","location-lat",
 "ground-speed","visible","import-marked-outlier","gps:hdop",
 "gps:satellite-count","height-above-msl","bar:barometric-height"
]

def make_row(bird,day,k=0,speed="0.3",height="NO_NUMERIC_HEIGHT",tag="T1"):
    hour=8+k//12
    minute=5*(k%12)
    return dict(timestamp=f"{day} {hour:02d}:{minute:02d}:00.000",
                **{
                 "individual-local-identifier":bird,
                 "tag-local-identifier":tag,
                 "individual-taxon-canonical-name":"Gyps fulvus",
                 "location-long":"2.83",
                 "location-lat":"43.91",
                 "ground-speed":speed,
                 "visible":"true",
                 "import-marked-outlier":"false",
                 "gps:hdop":"1.1",
                 "gps:satellite-count":"10",
                 "height-above-msl":height,
                 "bar:barometric-height":"UNKNOWN_BARO"
                })

def read(rows):
    f=io.StringIO()
    w=csv.DictWriter(f,fieldnames=FIELDS)
    w.writeheader()
    for row in rows:w.writerow(row)
    f.seek(0)
    return csv.reader(f)


def run(rows,birds,year="2019"):
    first={}
    counts=Counter()
    lm.screen_member(read(rows),set(birds),first,counts,year)
    return first,counts


def test_ten_birds_repeated_lowmotion_other_dates_same_cell():
    cohort=[f"Bird{i}" for i in range(10)]
    rows=[make_row(bird,day,k)
          for bird in cohort for day in ("2019-05-01","2019-05-02")
          for k in range(60)]
    first,c=run(rows,cohort)
    assert len(first)==1200
    s=lm.make_support(first,set(cohort))
    assert s["original_eligible_lowmotion_birds"]==10
    assert s["admitted_for_separately_frozen_negative_control"]
    assert s["lowmotion_eligible_bird_days"]==20
    assert s["lowmotion_eligible_scored_five_minute_events"]==1200
    assert s["independent_native_height_values_opened"] is False


def test_exact_source_5minute_earliest_even_when_later_height_exists():
    cohort={"Bird1"}
    a=make_row("Bird1","2019-05-01",0,height="GPS_IS_NOT_NUMERIC")
    b=make_row("Bird1","2019-05-01",0,height="100")
    b["timestamp"]="2019-05-01 08:01:00.000"
    first,c=run([a,b],cohort)
    assert len(first)==1
    assert next(iter(first.values()))[0]=="2019-05-01 08:00:00.000"
    assert "height" not in str(first)


def test_faster_flight_and_negative_motion_speed_never_enter():
    birds={"Bird1"}
    rows=[make_row("Bird1","2019-05-01",0,speed="0.0"),
          make_row("Bird1","2019-05-01",1,speed="0.99"),
          make_row("Bird1","2019-05-01",2,speed="1.01"),
          make_row("Bird1","2019-05-01",3,speed="5.0"),
          make_row("Bird1","2019-05-01",4,speed="-1"),
          make_row("Bird1","2019-05-01",5,speed="NA")]
    first,c=run(rows,birds)
    assert len(first)==2
    assert c["outside_frozen_low_motion_speed"]==3
    assert c["nonheight_GPS_bad_xy_or_speed"]==1


def test_no_other_birds_makes_control_unavailable():
    rows=[make_row("Bird1",day,k)
          for day in ("2019-05-01","2019-05-02") for k in range(60)]
    first,c=run(rows,{"Bird1"})
    x=lm.make_support(first,{"Bird1"})
    assert x["original_eligible_lowmotion_birds"]==0


def test_nonbird_dummy_cannot_be_admitted_even_if_present_at_low_speed():
    dummy="Test géodésie ornitela"
    birds={"Bird1"}
    rows=[make_row(dummy,"2019-05-01",0),
          make_row("Bird1","2019-05-01",0)]
    first,c=run(rows,birds)
    assert len(first)==1 and next(iter(first))[0]=="Bird1"
    assert c["outside_28_frozen_birds_or_geodesy_test"]==1


def test_stale_preheight_roster_rejected():
    cohort=[f"bird{i}" for i in range(28)]
    source={"phase":"FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT",
       "numeric_native_GPS_height_values_read":False,
       "source_zip_md5":lm.ORIGINAL_MD5,
       "quarantined_nonbiological_animal_IDs":["Test géodésie ornitela"],
       "horizontal_day_eligibility_by_cell_m":{"5000":{
           "admitted_bird_ids":cohort,
           "source_bird_ID_sha256":hashlib.sha256(
               "\n".join(sorted(cohort)).encode()).hexdigest()
       }}
    }
    with pytest.raises(ValueError,match="drift"):
        lm.original_preheight_bird_roster(source)
