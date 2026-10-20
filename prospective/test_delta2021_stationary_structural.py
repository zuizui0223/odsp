from prospective.delta2021_stationary_structural import inspect_stationary


def event(animal="A",date="2021-05-02",minute=0,speed="0.1",lon="3.710",lat="51.630",height="DO_NOT_READ",taxon="Larus fuscus"):
    return {"timestamp":f"{date} {8+minute//60:02d}:{minute%60:02d}:00.000",
       "individual-local-identifier":animal,"individual-taxon-canonical-name":taxon,
       "location-long":lon,"location-lat":lat,"ground-speed":speed,
       "height-above-msl":height,"bar:barometric-height":"DO_NOT_READ"}


def test_two_days_10_birds_at_same_cell_are_eligible():
    rows=[]
    for bird in range(10):
        for date in ("2021-05-02","2021-05-03"):
            for t in range(25):
                rows.append(event(animal=f"bird{bird}",date=date,minute=t*5))
    output=inspect_stationary(rows)
    assert output["height_values_accessed"] is False
    p=output["species"]["Larus fuscus"]["primary_100m"]
    assert p["eligible_birds"]==10
    assert p["eligible_days"]==20


def test_one_bird_cannot_self_reference_as_other():
    rows=[]
    for date in ("2021-05-02","2021-05-03"):
        for t in range(25):rows.append(event(date=date,minute=t*5))
    out=inspect_stationary(rows)
    assert out["species"]["Larus fuscus"]["primary_100m"]["eligible_birds"]==0


def test_distant_individuals_do_not_count_at_100m():
    rows=[]
    for bird,lon in (("A","3.710"),("B","3.719")):
        for date in ("2021-05-02","2021-05-03"):
            for t in range(25):rows.append(event(animal=bird,date=date,minute=t*5,lon=lon))
    r=inspect_stationary(rows)["species"]["Larus fuscus"]["primary_100m"]
    assert r["eligible_birds"]==0


def test_duplicate_minutes_and_missing_height_not_reselected():
    rows=[event(height=""),event(minute=1,height="200")]
    out=inspect_stationary(rows)
    assert out["first_5min_events_by_species"]["Larus fuscus"]==1
    assert out["height_values_accessed"] is False


def test_species_do_not_share_reference():
    rows=[]
    for taxon in ("Larus fuscus","Larus argentatus"):
        for date in ("2021-05-02","2021-05-03"):
            for t in range(25):rows.append(event(taxon=taxon,date=date,minute=t*5))
    out=inspect_stationary(rows)
    assert all(out["species"][t]["primary_100m"]["eligible_birds"]==0 for t in ("Larus fuscus","Larus argentatus"))
