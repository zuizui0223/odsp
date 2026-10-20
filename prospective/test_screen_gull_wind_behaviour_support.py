from prospective.screen_gull_wind_behaviour_support import source_metadata_gate


def row(bird,day,minute=0,wind="2",project="HG_TEXEL",mode="Flap",speed="10",stamp=None):
    h=8+minute//60
    m=minute%60
    return {
        "ID":"some-event", "device_info_serial":bird,"date_time":stamp or f"{day} {h:02d}:{m:02d}:00",
        "project":project,"longitude":"4.74","latitude":"52.99",
        "speed_2d":speed,"class_name":mode,"wspeed":wind,
        "altitude":"UNPARSEABLE_HEIGHT_ONLY","altitude_adl":"UNPARSEABLE_HEIGHT_ONLY",
    }


def test_preoutcome_two_wind_regimes_across_days_and_10_birds():
    r=[]
    for i in range(10):
        for day,wind in [("2015-05-15","2"),("2015-05-16","2"),("2015-05-17","10"),("2015-05-18","10")]:
            for k in range(30):
                r.append(row(f"bird{i}",day,minute=k*5,wind=wind))
    out=source_metadata_gate(r)
    assert out["height_or_shape_values_read"] is False
    assert out["projects"]["HG_TEXEL"]["flight_modes"]["flap"]["candidate_birds"]==10
    assert out["projects"]["HG_TEXEL"]["flight_modes"]["soar"]["candidate_birds"]==0
    assert out["projects"]["HG_TEXEL"]["wind_quartiles_by_year"][2015]["q25"]==2
    assert out["projects"]["HG_TEXEL"]["wind_quartiles_by_year"][2015]["q75"]==10


def test_distinct_source_project_no_taxa_pooling():
    r=[]
    for project in ("HG_TEXEL","LBBG_TEXEL"):
        for bird in ("A","B"):
            for day,wind in [("2016-05-16","2"),("2016-05-17","2"),("2016-05-18","10"),("2016-05-19","10")]:
                for i in range(30):r.append(row(bird,day,minute=i*5,wind=wind,project=project))
    out=source_metadata_gate(r)
    assert set(out["projects"])=={"HG_TEXEL","LBBG_TEXEL"}
    assert all(p["flight_modes"]["flap"]["candidate_birds"]==2 for p in out["projects"].values())


def test_earliest_flight_fix_not_replaced_by_later_weather_fix():
    r=[row("A","2016-05-18",minute=0,wind=""),
       row("A","2016-05-18",minute=1,wind="10")]
    out=source_metadata_gate(r)
    assert out["counts"]["selected_5min_bins"]==1
    assert out["counts"]["selected_missing_wind"]==1
    assert out["projects"]["HG_TEXEL"]["median_weather_bird_days"]==0


def test_one_bird_not_inferable_by_self_reference():
    r=[]
    for day,w in [("2016-05-16","2"),("2016-05-17","2"),("2016-05-18","10"),("2016-05-19","10")]:
        r.extend([row("A",day,minute=k*5,wind=w) for k in range(30)])
    out=source_metadata_gate(r)
    assert out["projects"]["HG_TEXEL"]["flight_modes"]["flap"]["candidate_birds"]==1
    assert out["projects"]["HG_TEXEL"]["flight_modes"]["flap"]["admitted"] is False
