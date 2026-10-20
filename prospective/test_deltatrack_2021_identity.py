import pytest
from prospective.deltatrack_2021_identity import build_panels, verify_source, TAXA

def event(t='2021-05-02 10:00:00.000', bird='A', taxon=TAXA[0], height='100', speed='10', outlier='false'):
    return {'timestamp':t, 'individual-local-identifier':bird,
            'individual-taxon-canonical-name':taxon,
            'location-long':'3.72','location-lat':'51.62',
            'ground-speed':speed,'height-above-msl':height,
            'import-marked-outlier':outlier}

def test_species_are_not_pooled_even_when_ids_match():
    panels,q=build_panels([event(),event(taxon=TAXA[1],height='200')])
    assert set(panels)==set(TAXA)
    assert all(len(panels[t])==1 for t in TAXA)
    assert all(q[t]['five_minute_bins']==1 for t in TAXA)

def test_first_moving_fix_chosen_before_height_qc():
    rows=[event(height=''),event(t='2021-05-02 10:01:00.000',height='200')]
    panels,q=build_panels(rows)
    assert q[TAXA[0]]['five_minute_bins']==1
    assert q[TAXA[0]]['missing_height']==1
    assert panels[TAXA[0]]==[]

def test_daily_centering_removes_additive_height_offset():
    rows=[]
    for bird,offset in [('A',0),('B',350)]:
        for i,h in enumerate([20,45,60,100]):
            rows.append(event(t=f'2021-05-02 10:{i*5:02d}:00.000',bird=bird,height=str(h+offset)))
    panels,q=build_panels(rows)
    a,b=panels[TAXA[0]]
    assert list(a['hist'])==list(b['hist'])
    for c in a['hist']:
        assert (a['hist'][c]==b['hist'][c]).all()

def test_frozen_window_speed_and_provider_outliers():
    rows=[event(),event(t='2020-05-02 10:00:00.000'),
          event(t='2021-04-02 10:00:00.000'),event(bird='B',speed='0'),
          event(bird='C',speed='nan'),event(bird='D',outlier='true')]
    panels,q=build_panels(rows)
    assert q[TAXA[0]]['five_minute_bins']==1
    assert q[TAXA[0]]['valid_height_bins']==1

def test_short_donor_days_preserved_and_range_not_clipped():
    rows=[event(height='-301'),event(bird='B',height='3001'),event(bird='C',height='200')]
    panels,q=build_panels(rows)
    assert q[TAXA[0]]['out_of_bounds']==2
    assert q[TAXA[0]]['valid_height_bins']==1
    assert len(panels[TAXA[0]])==1
    assert panels[TAXA[0]][0]['animal']=='C'

def test_hash_guard_never_accepts_arbitrary_source(tmp_path):
    p=tmp_path/'DELTATRACK-gps-2021.csv.gz';p.write_bytes(b'not the frozen source')
    with pytest.raises(ValueError,match='checksum'):
        verify_source(p)
