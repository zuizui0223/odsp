from prospective.stork_archive_calendar_inventory import inspect_calendar


def row(year,bird="A",month=8,speed="10",height="NOT_READ",visible="true"):
    return {
        "timestamp":f"{year}-{month:02d}-02 12:00:00.000",
        "individual-local-identifier":bird,
        "location-long":"12.2","location-lat":"50.6",
        "ground-speed":speed,
        "visible":visible,
        "height-above-ellipsoid":height
    }


def test_calendar_counts_missing_frozen_2014_separately_from_existing_years():
    rows=[row(2011,"A"),row(2012,"B"),row(2013,"C"),row(2013,"D")]
    r=inspect_calendar(rows,{})
    assert r["raw_total_rows"]==4
    assert set(r["year_counts"])=={2011,2012,2013}
    assert r["preoutcome_latest_year_10plus_birds"] is None
    assert r["GPS_height_values_read"] is False


def test_new_phase_selects_latest_year_above_ten_without_altitude():
    r=inspect_calendar(
        [row(2011,str(i)) for i in range(25)]+
        [row(2012,str(i)) for i in range(9)]+
        [row(2013,str(i)) for i in range(11)]+
        [row(2014,str(i),speed="0") for i in range(100)],
        {str(i):"juv" for i in range(50)}
    )
    assert r["preoutcome_latest_year_10plus_birds"]==2013
    assert r["year_counts"][2014]["distinct_birds_with_flight_speed_GPS"]==0
    assert r["year_counts"][2013]["distinct_flight_birds_by_age_label"]["juv"]==11


def test_metadata_does_not_rescue_2014_outcome():
    r=inspect_calendar([row(2013,"A",height="NAN_undetected")],{})
    assert not r["GPS_height_values_read"]
    assert not r["ecological_outcome_tested"]
    assert "2014 unavailable" in r["old_2014_hypothesis_terminal"]
