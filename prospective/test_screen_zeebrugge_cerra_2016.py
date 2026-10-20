from prospective.screen_zeebrugge_cerra_2016 import (
    reference_meta,safe_crosswalk,screen_fixes,xysupport
)


def ref(animal,site="ZEEB_KLVL",tag=None,year="2016"):
    return {"animal-id":str(animal),"tag-id":str(tag or animal),
        "tag-serial-no":str(tag or animal),"animal-ring-id":str(animal),
        "study-site":site,"deploy-on-latitude":"51.35",
        "deploy-on-longitude":"3.17",
        "deploy-on-date":f"{year}-05-02 00:00:00"}


def fix(animal,day,minute=0,tag=None,height="NOT_READ",speed="10"):
    hour=8+minute//60
    mi=minute%60
    return {
        "timestamp":f"{day} {hour:02d}:{mi:02d}:00.000",
        "individual-taxon-canonical-name":"Larus fuscus",
        "individual-local-identifier":str(animal),
        "tag-local-identifier":str(tag or animal),
        "location-long":"3.17","location-lat":"51.35",
        "ground-speed":speed,"height-above-msl":height,
        "bar:barometric-pressure":"NOT_READ",
    }


def test_one_to_one_reference_tag_and_bird_maps_exactly():
    refs=[ref(str(i)) for i in range(10)]
    observed={str(i):{(str(i),str(i))} for i in range(10)}
    out=safe_crosswalk(refs,observed)
    assert out["accepted"]
    assert out["site_by_bird"]=={str(i):"ZEEB_KLVL" for i in range(10)}
    assert out["methods"]["animal_local__animal-id"]["fraction"]==1.0


def test_unrecognized_source_identifiers_declined_not_guessed():
    refs=[ref(str(i)) for i in range(10)]
    observed={f"x{i}":{(f"x{i}",f"z{i}")} for i in range(10)}
    out=safe_crosswalk(refs,observed)
    assert out["accepted"] is False
    assert out["site_by_bird"]=={}


def test_source_height_is_unread_even_if_string_unparseable():
    rows=[fix("A","2016-05-15",minute=0,height="INVALID"),
          fix("A","2016-05-15",minute=1,height="VALID_WOULD_BE_SKIPPED")]
    first,obs,diag=screen_fixes(rows)
    assert len(first)==1
    assert diag["counts"]["unique_flight_5min_bins"]==1
    assert obs["A"]=={("A","A")}


def test_wind_days_same_bird_other_day_scored_without_altitude():
    first={}
    regime={"ZEEB_KLVL":{}}
    for day,state in [
       ("2016-05-15","low"),("2016-05-16","low"),
       ("2016-05-17","high"),("2016-05-18","high")
    ]:
        regime["ZEEB_KLVL"][day]=state
        for i in range(10):
            for b in range(60):
                first[str(i),day,b]=(f"{day} 08:{b:02d}:00","3.17","51.35")
    # UTC bin values can repeat any timestamp format, only x/y matter.
    sites={str(i):"ZEEB_KLVL" for i in range(10)}
    first={k:(time,float(x),float(y)) for k,(time,x,y) in first.items()}
    out=xysupport(first,sites,regime)
    assert out["wind_gate_admitted"]
    assert out["wind_both_regimes_birds"]==10
    assert out["baseline_shared_cell_birds"]==10
    assert out["height_values_accessed"] is False


def test_site_centroid_from_start_2016_only():
    rows=[ref("a","S1",year="2015")]+[ref(str(i),"S1",year="2016") for i in range(3)]
    r=reference_meta(rows)
    assert r["site_centers"]["S1"]["new_deployments_2016"]==3
    assert r["unique_reference_animals"]==4
