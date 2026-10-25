"""Post-outcome DEM terrain-removal regressions on entirely synthetic rasters."""
import numpy as np
import rasterio
from rasterio.transform import from_origin
from collections import Counter

from prospective import france_gyps_dem_agl_sensitivity as z
from prospective import medgull_sensitivity as d1


def fake_dem(tmp_path,nodata=-9999):
    p=tmp_path/"Terrain_Causses_fake.tif"
    a=np.full((5,5),150,dtype=np.int16)
    a[0,0]=nodata
    with rasterio.open(p,"w",driver="GTiff",width=5,height=5,count=1,
                       dtype="int16",crs="EPSG:4326",
                       transform=from_origin(2.0,44.0,.1,.1),
                       nodata=nodata) as f:
        f.write(a,1)
    return p


def test_dem_samples_use_native_xy_only_never_altitude(tmp_path):
    p=fake_dem(tmp_path)
    # Inside pixel: lon 2.25 and lat 43.75; outside: lon 7.0.
    original={
       ("A","2020-05-01",1):("2020-05-01 08:05:00",2.25,43.75,"BAD_HEIGHT","NON_NUMERIC_BARO",2,9),
       ("A","2020-05-02",1):("2020-05-02 08:05:00",7.,43.75,"9999","9999",2,9),
    }
    dem,diag=z.sample_dem_for_source(p,original,{"A"},chunk_size=1)
    assert dem["A","2020-05-01",1]==150.
    assert dem["A","2020-05-02",1] is None
    assert diag["original_source_events_eligible_28_birds"]==2
    assert diag["fraction_geographically_covered"]==.5
    assert diag["dem_cover_gate_admitted"] is False
    assert diag["native_height_values_used_for_dem_coverage"] is False


def test_invalid_native_source_height_never_salvaged_by_dem_subtraction():
    key=("A","2020-05-01",1)
    source={key:("2020-05-01 08:05:00",2.25,43.75,
                 "8000","200","3.0","11")}
    transformed,quality=z.terrain_subtracted_source(source,{key:150.},{"A"})
    assert transformed[key][3] is None   # MSL 8000 out of frozen native range
    assert transformed[key][4]==50.0     # BARO 200 minus 150 = 50
    assert quality["native_GPS_missing_or_outside_fixed_bounds"]==1


def test_same_dem_reference_improves_height_topography_control():
    # Native MSL elevations can vary with local terrain without any change
    # in actual flight height AGL. Corrected residual shape must no longer
    # contain that terrain-induced spread.
    ground=np.array([150.,240.,180.,400.])
    agl=np.array([20.,20.,20.,20.])
    native=ground+agl
    assert np.sum(np.abs(d1.center_bins(native)-d1.center_bins(agl)))>0
    assert np.array_equal(d1.center_bins(agl),d1.center_bins([0.,0.,0.,0.]))


def test_null_inclusion_of_unavailable_is_conservative():
    panels={
      "GPS":{"terminal":"tested_before_two_source_Holm",
             "calibration":{"p_upper":.001,"observed_minus_valid_null_mean":.02}},
      "BAROMETRIC":{"terminal":"unavailable","reason":"source surface unknown",
             "calibration":{"p_upper":.03,"observed_minus_valid_null_mean":.02}}
    }
    z.apply_fixed_two_sensor_holm(panels)
    assert panels["GPS"]["Holm_p_upper"]==.002
    assert panels["BAROMETRIC"]["family_p_value"]==1
    assert panels["BAROMETRIC"]["Holm_p_upper"]==1


def test_original_source_result_id_and_bird_roster_fingerprints_frozen(monkeypatch):
    # Stipulate a synthetic source precisely matching frozen original 28-ID
    # SHA, without any numeric altitude data used for source acceptance.
    ids=[f"bird{i:02d}" for i in range(28)]
    import hashlib
    hashid=hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
    pre={"numeric_native_GPS_height_values_read":False,
         "selected_native_GPS_five_minute_events":742423,
         "selected_biological_animals":30,
         "horizontal_day_eligibility_by_cell_m":{"5000":{
           "admitted_bird_ids":ids,"source_bird_ID_sha256":hashid}}}
    old={"terminal":"paired_sensor_robust_individual_height_shape",
         "preheight_bird_roster_sha256":hashid,
         "source_archive_md5":z.original.SOURCE_MD5,
         "sensor_results":{
           "GPS":{"terminal":"supported_own_bird_altitude_shape",
                  "observed":{"eligible_birds":27,"eligible_bins":364520}},
           "BAROMETRIC":{"terminal":"supported_own_bird_altitude_shape",
                         "observed":{"eligible_birds":27,"eligible_bins":364520}}}}
    cross={"native_height_values_read":False,
           "source_independence_category":"DIFFERENT_STUDY_NAMES_AND_ZERO_EXACT_SOURCE_ANIMAL_IDS",
           "exact_bird_id_overlap_across_both_2026_Gyps_parents":0}
    monkeypatch.setattr(z.original,"FRENCH5_SHA",hashid)
    accepted=z.verify_original_primary(pre,cross,old)
    assert len(accepted)==28
    old["sensor_results"]["GPS"]["terminal"]="not_supported_own_bird_altitude_shape"
    import pytest
    with pytest.raises(ValueError,match="Original source sensor"):
        z.verify_original_primary(pre,cross,old)


def test_masked_original_dem_sample_does_not_get_zero_imputed(tmp_path):
    p=fake_dem(tmp_path)
    key=("A","2020-05-01",1)
    x={key:("2020-05-01 08:05:00",2.05,43.95,200.,300.,2,10)}
    out,q=z.sample_dem_for_source(p,x,{"A"})
    assert out[key] is None
    assert not q["dem_cover_gate_admitted"]
