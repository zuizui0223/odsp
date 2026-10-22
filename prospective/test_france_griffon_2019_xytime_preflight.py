from collections import Counter,defaultdict
from prospective.france_griffon_2019_xytime_preflight import (
    select_rows,analyze,fixed_support
)


HEADERS=[
"timestamp","individual-local-identifier","tag-local-identifier",
"individual-taxon-canonical-name","location-long","location-lat",
"ground-speed","visible","import-marked-outlier","gps:hdop",
"gps:satellite-count","height-above-msl","bar:barometric-height",
"study-name"
]
def record(bird,day,timebin,tag=None,height="THIS IS NOT A NUMBER"):
    hour=8+timebin//12;minute=5*(timebin%12)
    return [
        f"{day} {hour:02d}:{minute:02d}:00.000",
        bird,tag or bird,"Gyps fulvus","2.8","43.9",
        "9","true","false","2.5","10",
        height,"ALSO_NOT_NUMERIC","French Gyps source"
    ]


def run(rows,year):
    first={};cnt=Counter();tags=defaultdict(set);names=defaultdict(set)
    select_rows(iter([HEADERS]+rows),first,cnt,tags,names,year)
    return first,cnt,tags,names


def test_10_different_birds_two_days_shared_cell_with_non_numeric_heights():
    rows=[record(f"bird{i}",day,k)
          for i in range(10) for day in ("2019-06-11","2019-06-12")
          for k in range(30)]
    first,c,t,n=run(rows,2019)
    out=analyze(first,c,t,n)
    assert out["selected_biological_animals"]==10
    assert out["selected_animal_days"]==20
    assert out["horizontal_day_eligibility_by_cell_m"]["5000"]["admitted"]
    assert out["horizontal_day_eligibility_by_cell_m"]["5000"]["bird_days_scored"]==20
    assert out["numeric_native_GPS_height_values_read"] is False
    assert out["numeric_barometric_height_values_read"] is False


def test_same_date_other_bird_is_not_reference():
    rows=[record(f"bird{i}","2019-06-11",k)
          for i in range(10) for k in range(30)]
    first,c,t,n=run(rows,2019)
    out=analyze(first,c,t,n)
    assert out["horizontal_day_eligibility_by_cell_m"]["5000"]["n_unique_birds_with_qualifying_day_events"]==0


def test_no_outcome_conditioned_later_record_fallback():
    a=record("bird1","2019-06-11",0,height="NOT_NUMERIC")
    b=record("bird1","2019-06-11",0,height="500")
    b[0]="2019-06-11 08:01:00.000"
    first,c,t,n=run([a,b],2019)
    assert len(first)==1
    assert next(iter(first.values()))[0]=="2019-06-11 08:00:00.000"


def test_bird_retagging_not_double_counted_as_two_animals():
    rows=[]
    for i,day in enumerate(("2019-06-11","2019-06-12")):
        for k in range(30):
            rows.append(record("samebird",day,k,tag=f"t{i}"))
    first,c,t,n=run(rows,2019)
    report=analyze(first,c,t,n)
    assert report["selected_biological_animals"]==1
    assert report["animals_with_more_than_one_tag_ID"]==1
    assert report["n_distinct_tag_IDs"]==2


def test_two_source_years_in_same_file_never_rescued():
    first,c,t,n=run([record("bird1","2020-05-11",0),
                     record("bird1","2019-05-11",0)],2019)
    assert len(first)==1
    assert c["unexpected_year_or_time"]==1


def test_exact_geodesy_instrument_test_id_is_quarantined_before_source_population():
    rows=[
       record("Test géodésie ornitela","2019-06-11",i)
       for i in range(30)
    ]
    rows += [
       record(f"bird{i}",day,k)
       for i in range(10)
       for day in ("2019-06-11","2019-06-12")
       for k in range(30)
    ]
    first,c,t,n=run(rows,2019)
    report=analyze(first,c,t,n)
    assert report["selected_biological_animals"]==10
    assert c["nonbiological_instrument_test_rows_quarantined"]==30
    assert "Test géodésie ornitela" not in report["selected_animal_IDs"]
    assert report["horizontal_day_eligibility_by_cell_m"]["5000"]["n_unique_birds_with_qualifying_day_events"]==10


def test_tag_shared_by_two_birds_is_reported_as_ambiguity_not_new_individual():
    rows=[
       record(bird,day,i,tag="SAME_NATIVE_TAG")
       for bird in ("b0","b1") for day in ("2019-06-11","2019-06-12")
       for i in range(30)
    ]
    first,c,t,n=run(rows,2019)
    q=analyze(first,c,t,n)
    assert q["selected_biological_animals"]==2
    assert q["n_distinct_tag_IDs"]==1
    assert q["tags_aliased_to_multiple_biological_bird_IDs"]=={
        "SAME_NATIVE_TAG":["b0","b1"]
    }
