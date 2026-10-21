"""Synthetic regression suite for source-frozen 4-Gyps height experiment."""
from collections import defaultdict
import csv,gzip
import numpy as np
import pytest

from prospective.run_gyps_thermal_50km_height import (
  PANEL_SPECS,validate_preheight,wind_states_from_selected,
  selected_native_height,make_study_profiles,fixed_four_panel_holm,
  original_metadata_source
)
from prospective.gyps_thermal_height_kernel import center_bins


def test_prespecified_family_is_three_taxa_four_separate_source_studies():
    assert len(PANEL_SPECS)==4
    assert len(set(k[0] for k in PANEL_SPECS))==4
    assert len(set(k[1] for k in PANEL_SPECS))==3
    assert all(v["birds"]>=10 for v in PANEL_SPECS.values())
    assert all(len(v["sha"])==64 for v in PANEL_SPECS.values())


def test_thermal_labels_from_source_median_do_not_consult_height():
    key=("122120597","Gyps fulvus")
    meta={}
    for d,state in [("2018-05-01",0),("2018-05-02",0),
                    ("2018-05-03",1),("2018-05-04",1)]:
        for i in range(25):
            meta[("Movebank",key[0],key[1],"bird1",d,i)]=(
               f"{d} 08:{i:02d}:00",10.,50.,
               2. if state==0 else 20., 0.,5.,.5,.1)
    prior={key:{"thermal_50000":{"thresholds_by_month":{"2018-05":[2.,20.]}}}}
    actual=wind_states_from_selected(meta,prior)[key]
    assert [actual["bird1",d] for d in sorted({k[4] for k in meta})]==[0,0,1,1]


def test_height_adapter_centering_constant_tag_bias_does_not_reclassify():
    panel=("122120597","Gyps fulvus")
    meta={};heights={}
    for k,h in enumerate([0.,20.,60.,100.]):
        key=("Movebank",panel[0],panel[1],"bird1","2018-05-01",k)
        meta[key]=(f"2018-05-01 08:0{k}:00",10.,50.,2.,0.,5.,.4,.3)
        heights[key]=h
    sessions,q=make_study_profiles(panel,meta,heights,{},defaultdict(set),{})
    assert q["height_valid_fraction"]==1
    h=sessions[0]["hists"]
    assert sum(int(x.sum()) for x in h.values())==4
    assert np.array_equal(center_bins([0,20,60,100]),center_bins([2000,2020,2060,2100]))


def test_native_bad_height_is_unavailable_without_rescue():
    panel=("122120597","Gyps fulvus")
    meta={};heights={}
    for i in range(20):
        key=("Movebank",panel[0],panel[1],"bird1","2018-05-01",i)
        meta[key]=(f"2018-05-01 09:{i:02d}:00",10.,50.,2.,0.,5.,.4,.3)
        heights[key]=None if i>=2 else 200.
    s,q=make_study_profiles(panel,meta,heights,{},defaultdict(set),{})
    assert s is None
    assert q["native_height_valid"]==2
    assert q["height_valid_fraction"]==.1


def test_holm_includes_unavailable_source_studies():
    keys=sorted(PANEL_SPECS)
    rows={k:{"terminal":"tested_prior_to_Holm_adjustment",
             "p_upper":p,"calibration":{"observed_minus_null_mean":.1}}
         for k,p in zip(keys,[.001,.020,.050,.10])}
    rows[keys[-1]]["terminal"]="unavailable"
    rows[keys[-1]]["p_upper"]=1.
    fixed_four_panel_holm(rows)
    assert abs(rows[keys[0]]["holm_p_upper"]-.004)<1e-9
    assert abs(rows[keys[1]]["holm_p_upper"]-.060)<1e-9
    assert rows[keys[0]]["terminal"]=="supported_50km_thermal_height_shape"
    assert rows[keys[1]]["terminal"]=="not_supported_50km_thermal_height_shape"
    assert rows[keys[-1]]["terminal"]=="unavailable"
    assert rows[keys[-1]]["multiplicity_placeholder_p"]==1.0
    assert rows[keys[-1]]["holm_p_upper"]==1.0


def test_earliest_fix_selected_before_height_available(tmp_path):
    cols=["data_source","study_id","study_name","species","animal_id",
        "timestamp","lon","lat","segment_id","tag_id","thermal_uplift",
        "orographic_uplift","wind_speed_1000m","flap_probability","vedba",
        "height"]
    p=tmp_path/"fake.tsv.gz"
    def row(time,h):
        return dict(data_source="Movebank",study_id="122120597",
            study_name="test",species="Gyps fulvus",animal_id="b",
            timestamp=time,lon="10",lat="50",segment_id="s",
            tag_id="t",thermal_uplift="2",orographic_uplift="0.1",
            wind_speed_1000m="5",flap_probability="0.4",vedba="0.2",
            height=h)
    with gzip.open(p,"wt",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,delimiter="\t")
        w.writeheader()
        w.writerow(row("2018-05-01 08:00:00","NA"))
        w.writerow(row("2018-05-01 08:01:00","500"))
    m,ids,c=original_metadata_source(p)
    assert len(m)==1
    h,t,pr=selected_native_height(p,m)
    assert len(h)==1 and next(iter(h.values())) is None


def test_any_preheight_roster_drift_blocks_native_height_read():
    with pytest.raises(ValueError,match="not altitude-blind"):
        validate_preheight({}, {}, {
          "numerical_altitude_values_accessed_for_screen": True
        })
