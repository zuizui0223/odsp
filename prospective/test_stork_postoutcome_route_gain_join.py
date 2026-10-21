"""Post-outcome route opportunity diagnostic guards: no altitude is accessed."""
from collections import Counter
from prospective.stork_fine_route_recurrence_no_height import geometry,load_thinned_xy
from prospective.stork_postoutcome_route_gain_join import spearman,percentiles,join


def test_fine_self_route_exclusive_when_two_birds_use_distinct_nested_cells():
    traces=Counter({
        (bird,day,(0,0),fine):60
        for bird,fine in (("A",(1,1)),("B",(2,2)))
        for day in ("2013-08-10","2013-08-11")
    })
    r=geometry(traces)
    assert r["scored_fixes"]==240
    for v in r["birds"].values():
        assert v["self_fine_fraction"]==1
        assert v["other_fine_fraction"]==0
        assert v["fine_self_minus_other"]==1
        assert v["own_coarse_revisit_gap_days"]==1


def test_shared_micro_route_has_zero_exclusive_advantage():
    traces=Counter({
        (bird,day,(0,0),(1,1)):60
        for bird in ("A","B")
        for day in ("2013-08-10","2013-08-11")
    })
    v=geometry(traces)
    assert all(m["self_fine_fraction"]==1 for m in v["birds"].values())
    assert all(m["other_fine_fraction"]==1 for m in v["birds"].values())
    assert all(m["fine_self_minus_other"]==0 for m in v["birds"].values())


def test_source_height_column_string_ignored_even_if_unparseable():
    r={"individual-local-identifier":"A",
       "timestamp":"2013-08-10 09:00:00.000","location-long":"10.0",
       "location-lat":"49.0","ground-speed":"8",
       "height-above-ellipsoid":"HEIGHT_DO_NOT_PARSE"}
    first,summary=load_thinned_xy([r],2013)
    assert len(first)==1
    assert "height" not in str(first)
    assert summary["selected_flight_5min_fixes"]==1


def test_rank_and_pair_uncertainty_are_stable():
    assert abs(spearman([2,4,7,9],[10,20,30,40])-1)<1e-12
    assert abs(spearman([2,4,7,9],[40,30,20,10])+1)<1e-12
    assert spearman([1,1,1],[2,3,4]) is None
    assert percentiles([1,2,3,4,5])==[1.1,4.9]


def test_join_rejects_outcome_based_change_of_observed_bird_roster():
    def make(source,n,days,fixes):
        return {"source":source,"altitude_values_read":False,
           "geometry":{
             "birds":{f"b{i}":{"self_fine_fraction":i/(n+1),
                 "other_fine_fraction":.1,"fine_self_minus_other":i/(n+1)-.1,
                 "own_coarse_revisit_gap_days":2,"nested_fine_subcells_per_day":1,
                 "days":2,"scored_fixes":50} for i in range(n)},
             "bird_day_count":days,"scored_fixes":fixes,"eligible_roster_hash":"synthetic",
             "equal_bird_summary":{"self_fine_fraction":{"mean":.5}}
           }}
    g13=make("rotics2013",25,111,6951)
    g14=make("flack2014",11,33,2040)
    a={f"b{i}":{"age":"juv","days":2,"bins":50,"gain":i/25}
       for i in range(25)}
    b={f"b{i}":{"age":"nestling","days":2,"bins":50,"gain":i/11}
       for i in range(11)}
    d=join(g13,g14,a,b,nboot=10,seed=20261021)
    assert d["sources"]["rotics2013"]["birds"]==25
    assert d["cross_cohort"]["self_fine_fraction"]["causal_or_confirmatory"] is False
    del a["b0"]
    import pytest
    with pytest.raises(ValueError,match="bird roster"):
        join(g13,g14,a,b,nboot=10)
