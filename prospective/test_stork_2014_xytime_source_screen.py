"""No-altitude structural source tests for migratory stork comparative ecology."""
from prospective.stork_2014_xytime_source_screen import audit,eligible_support,read_reference
from collections import Counter


def gps(bird,day,minute=0,height="THIS_FIELD_MUST_NOT_BE_READ",speed="10"):
    hr=8+minute//60;mi=minute%60
    return {
        "individual-local-identifier":bird,
        "timestamp":f"{day} {hr:02d}:{mi:02d}:00.000",
        "location-long":"10.1",
        "location-lat":"51.25",
        "ground-speed":speed,
        "height-above-ellipsoid":height,
        "visible":"true",
    }


def test_stork_source_never_reads_numeric_height():
    rows=[]
    for bird in ("A","B","C"):
        for day in ("2014-08-01","2014-08-02"):
            for i in range(60):
                rows.append(gps(bird,day,i*5,height="NOT_NUMERIC"))
    r=audit(rows,{"A":"juvenile","B":"adult","C":"adult"})
    assert r["gps_altitude_values_accessed"] is False
    assert r["GPS_altitude_missingness_accessed"] is False
    assert r["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"]==3
    assert r["horizontal_support_by_grid_m"]["5000"]["admitted"] is False


def test_absent_overlapping_other_bird_yields_no_fake_comparator():
    rows=[gps("A","2014-08-01",i*5) for i in range(60)]
    rows+= [gps("A","2014-08-02",i*5) for i in range(60)]
    o=audit(rows)
    assert o["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"]==0


def test_not_pooled_across_individual_days_and_years():
    rows=[
        gps(bird,date,i*5)
        for bird in ("A","B")
        for date in ("2014-08-02","2014-08-03","2015-08-02")
        for i in range(60)
    ]
    o=audit(rows)
    assert o["GPS_time_speed_xy_rows"]["thinned_flight_5min_bins"]==240
    assert o["GPS_time_speed_xy_rows"]["outside_frozen_2014_autumn"]==120
    assert o["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"]==2


def test_parent_age_metadata_identity_is_exact():
    stage,meta=read_reference(iter([
        {"animal-id":"A","tag-id":"ta","animal-life-stage":"juvenile"},
        {"animal-id":"B","tag-id":"tb","animal-life-stage":"adult"},
        {"animal-id":"B","tag-id":"tb2","animal-life-stage":"adult"},
    ]))
    assert meta["reference_rows"]==3
    assert meta["unique_birds"]==2
    assert meta["birds_multiple_tags"]==1
    assert stage=={"A":"juvenile","B":"adult"}


def test_visible_false_or_invalid_velocity_excluded_before_thinning():
    q=[gps("A","2014-09-05",0),
       {**gps("B","2014-09-05",0),"visible":"false"},
       gps("C","2014-09-05",0,speed="nan")]
    o=audit(q)
    assert o["GPS_time_speed_xy_rows"]["thinned_flight_5min_bins"]==1
    assert o["GPS_time_speed_xy_rows"]["source_outlier"]==1


def test_reference_count_algebra_requires_other_individual():
    profile=Counter({("A","2014-08-01",(1,1)):60,
                     ("A","2014-08-02",(1,1)):60})
    r=eligible_support(profile)
    assert r["birds_with_2_scorable_shared_cell_days"]==0
