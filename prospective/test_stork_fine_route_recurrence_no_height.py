"""Fixed source-independent tests of fine 5km within 50km path recurrence."""
from collections import Counter

from prospective.stork_fine_route_recurrence_no_height import (
    geometry, load_thinned_xy, make_counter
)


def test_two_birds_repeating_distinct_fine_routes_have_self_only_recurrence():
    counts=Counter()
    for bird, fine in (("A",(1,1)),("B",(2,2))):
        for day in ("2013-08-10","2013-08-11"):
            counts[bird,day,(0,0),fine]=60
    r=geometry(counts)
    assert r["bird_day_count"]==4
    assert r["scored_fixes"]==240
    assert len(r["birds"])==2
    for bird in ("A","B"):
        assert r["birds"][bird]["self_fine_fraction"]==1
        assert r["birds"][bird]["other_fine_fraction"]==0
        assert r["birds"][bird]["fine_self_minus_other"]==1
        assert r["birds"][bird]["own_coarse_revisit_gap_days"]==1


def test_shared_fine_route_in_same_coarse_cell_has_no_individual_exclusivity():
    counts=Counter({
        (b,d,(0,0),(1,1)):60
        for b in ("A","B")
        for d in ("2013-08-10","2013-08-11")
    })
    r=geometry(counts)
    assert r["scored_fixes"]==240
    assert all(x["self_fine_fraction"]==1 for x in r["birds"].values())
    assert all(x["other_fine_fraction"]==1 for x in r["birds"].values())
    assert all(x["fine_self_minus_other"]==0 for x in r["birds"].values())


def test_one_bird_two_days_is_not_falsely_given_other_bird_source_support():
    counts=Counter({("A",d,(0,0),(1,1)):60 for d in ("2013-08-10","2013-08-11")})
    r=geometry(counts)
    assert r["coarse_support"]["birds_with_2_scorable_shared_cell_days"]==0
    assert len(r["birds"])==0
    assert r["scored_fixes"]==0


def test_height_nonnumeric_and_source_visible_false_are_ignored():
    def fix(bird,stamp,height="DO_NOT_READ",visible="true"):
        return {"individual-local-identifier":bird,"timestamp":stamp,
                "location-long":"10.3","location-lat":"49.3",
                "ground-speed":"8","height-above-ellipsoid":height,
                "visible":visible}
    records=[
        fix("A","2013-08-10 08:00:00.000",height="NOT_A_NUMBER"),
        fix("A","2013-08-10 08:01:00.000",height="NO_FALLBACK"),
        fix("B","2013-08-10 08:04:00.000",visible="false"),
        fix("C","2014-08-10 08:00:00.000"),
    ]
    first,quality=load_thinned_xy(records,2013)
    assert len(first)==1
    assert ("A","2013-08-10",96) in first
    assert quality["selected_flight_5min_fixes"]==1
    assert "height-above-ellipsoid" not in str(first)
    fine=make_counter(first)
    assert sum(fine.values())==1


def test_different_50km_cells_never_create_fake_fine_overlap():
    counts=Counter()
    for b,c in (("A",(0,0)),("B",(1,1))):
        for d in ("2013-08-10","2013-08-11"):
            counts[b,d,c,(1,1)]=60
    r=geometry(counts)
    assert r["coarse_support"]["birds_with_2_scorable_shared_cell_days"]==0
