"""Bounded synthetic tests for the stationary negative control."""
from prospective.delta2021_stationary_shape import source_panels,run_panel
from prospective import medgull_sensitivity as engine
import numpy as np


def event(bird="A",day="2021-05-01",minute=0,z="12",sp="Larus fuscus",
          speed="0.1",lon="3.710",outlier="false"):
    return {
        "individual-taxon-canonical-name":sp,
        "individual-local-identifier":bird,
        "timestamp":f"{day} {8+minute//60:02d}:{minute%60:02d}:00.000",
        "location-long":lon,"location-lat":"51.630",
        "ground-speed":speed,"height-above-msl":z,
        "import-marked-outlier":outlier,
    }


def test_species_and_altitude_are_separated_before_scoring():
    rows=[event(sp="Larus fuscus"),event(sp="Larus argentatus",z="300")]
    panels,q=source_panels(rows)
    assert all(panels[t]==[] for t in panels)
    assert q["Larus fuscus"]["first_stationary_5minute_bins"]==1
    assert q["Larus argentatus"]["first_stationary_5minute_bins"]==1


def test_earliest_fix_is_selected_even_if_its_height_is_missing():
    rows=[
      event(z="",minute=0),
      event(z="200",minute=1),
    ]+[event(minute=i*5,z="100") for i in range(1,21)]
    panels,q=source_panels(rows)
    assert q["Larus fuscus"]["first_stationary_5minute_bins"]==21
    assert q["Larus fuscus"]["missing_height"]==1
    assert q["Larus fuscus"]["valid_height"]==20
    assert len(panels["Larus fuscus"])==1


def test_centered_shape_is_invariant_to_constant_tag_offset():
    def arr(bird,shift):
        return [event(bird=bird,minute=i*5,z=str(z+shift))
                for i,z in enumerate([0,30,60,90]*6)]
    panels,q=source_panels(arr("A",0)+arr("B",400))
    a,b=panels["Larus fuscus"]
    assert a["hist"].keys()==b["hist"].keys()
    cell=list(a["hist"])[0]
    assert np.array_equal(a["hist"][cell],b["hist"][cell])


def test_ten_repeat_birds_in_same_100m_cell_reach_scorable_support():
    rows=[]
    for bird in range(10):
        for date in ("2021-05-02","2021-05-03"):
            for i in range(60):
                height=(i%5)*10+(bird%4)*30
                rows.append(event(bird=f"bird{bird}",day=date,minute=i*5,z=str(height)))
    panels,q=source_panels(rows)
    x=engine.pack(panels["Larus fuscus"])
    sup=engine.support(x,1)
    scored=engine.evaluate(x,1,"balanced")
    assert sup["eligible_birds"]==10
    assert scored["eligible_birds"]==10
    assert scored["eligible_days"]==20
    assert np.array_equal(sup["day_scored_bins"],scored["day_scored_bins"])


def test_single_individual_cannot_be_assigned_a_positive_control():
    rows=[]
    for date in ("2021-05-02","2021-05-03"):
        for i in range(60):
            rows.append(event(day=date,minute=i*5,z=str(i)))
    panels,q=source_panels(rows)
    out,draws=run_panel(panels["Larus fuscus"],q["Larus fuscus"],"Larus fuscus",draws=3)
    assert out["terminal"]=="unavailable"
    assert out["reason"]=="minimum_ten_birds_for_comparator"
    assert draws==[]
