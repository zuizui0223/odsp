"""Synthetic checks; no real altitude outcomes are used in this test module."""
from collections import Counter
import numpy as np
import pytest
import medgull_sensitivity as m


def row(a,d,counts,cell=(1,1)):
    return {'animal':a,'day':d,'hist':{cell:np.array(counts,dtype=np.int64)}}


def fixture():
    # Repeated narrow-versus-wide patterns, every bird observed on every date.
    return [row(str(a),f'2022-05-{d:02d}',
                [30 if k in (a%5,a%5+5) else 0 for k in range(10)])
            for a in range(10) for d in range(1,5)]


def test_identity_fixture_and_unified_support():
    x=m.pack(fixture())
    for w in ('pooled','balanced'):
        r=m.evaluate(x,1,w)
        s=m.support(x,1)
        assert r['eligible_birds']==10
        assert r['eligible_days']==40
        assert r['mean_gain']>0
        np.testing.assert_array_equal(r['day_scored_bins'],s['day_scored_bins'])
        assert r['eligible_ids']==s['eligible_ids']


def test_single_bird_is_never_its_own_other_reference():
    x=m.pack([r for r in fixture() if r['animal']=='0'])
    r=m.evaluate(x,1,'pooled')
    assert r['eligible_birds']==0
    assert r['mean_gain'] is None


def test_short_donors_are_distinct_from_evaluation_days():
    rows=[]
    for a in ('A','B'):
        for d,c,n in ((1,(1,1),60),(2,(2,2),60),(3,(1,1),10),(4,(2,2),10)):
            rows.append(row(a,f'2022-05-{d:02d}',[0,0,0,0,n//2,n-n//2,0,0,0,0],c))
    x=m.pack(rows)
    assert m.evaluate(x,1,'pooled')['eligible_birds']==2
    assert m.evaluate(x,50,'pooled')['eligible_birds']==0
    assert m.evaluate(x,1,'pooled')['eligible_days']==4


def test_no_identity_fixture_gives_zero_gain():
    rows=[row(str(a),f'2022-05-{d:02d}',[6]*10) for a in range(4) for d in range(1,4)]
    for w in ('pooled','balanced'):
        assert abs(m.evaluate(m.pack(rows),1,w)['mean_gain'])<1e-12


def test_balanced_reference_equal_birds_and_equal_days():
    rows=[]
    for a,n,k in [('A',60,0),('B',600,0),('C',60,9)]:
        for d in (1,2,3):
            h=[0]*10; h[k]=n
            rows.append(row(a,f'2022-05-{d:02d}',h))
    x=m.pack(rows)
    balanced=m.evaluate(x,1,'balanced')
    pool=m.evaluate(x,1,'pooled')
    expected=np.log((60+.5)/(60+5))-np.log(.5*((600+.5)/(600+5)+.5/(60+5)))
    assert balanced['per_bird']['A']['gain']==pytest.approx(expected)
    assert balanced['per_bird']['A']['gain']>pool['per_bird']['A']['gain']


def test_exact_date_permutation_preserves_bird_presence():
    x=m.pack(fixture()); y=m.permute_labels(x,np.random.default_rng(24))
    assert len(set(zip(y,x['day_index'])))==len(y)
    assert Counter(zip(y,x['day_index']))==Counter(zip(x['labels'],x['day_index']))
    assert not np.array_equal(y,x['labels'])


def test_centering_additive_shift_invariance():
    h=np.array([3,10,25,42,100,130],dtype=float)
    assert len(m.center_bins(h))==6
    np.testing.assert_array_equal(m.center_bins(h),m.center_bins(h+2000))


def test_incomplete_null_uses_bounds_and_all_draws():
    r=m.calibrate(1.0,[0.0,2.0,None],requested=3)
    assert r['p_lower']==.5
    assert r['p_upper']==.75
    assert r['valid']==2


def test_identical_support_regardless_of_bin_relabelling():
    a=fixture(); b=[dict(r,hist={c:v[::-1] for c,v in r['hist'].items()}) for r in a]
    np.testing.assert_array_equal(m.support(m.pack(a),1)['day_scored_bins'],m.support(m.pack(b),1)['day_scored_bins'])


def test_pinned_source_quality_is_json_serializable():
    import json
    from pathlib import Path
    source=Path(__file__).resolve().parents[1]/'source/MEDGULL_ANTWERPEN-gps-2022.csv.gz'
    if not source.exists():pytest.skip('Pinned real-data integration fixture not present')
    _,q=m.load_source(source)
    assert type(q['long_sessions']) is int
    json.dumps(q)
