from prospective.grus_grus_dryad_access_pilot import (
   metadata_of_pilot,maybe_timestamp,finite_number,NON_VERTICAL_HEADER
)
from pathlib import Path

def test_utc_timestamp_is_used_exactly():
    dt=maybe_timestamp("2018-10-03 23:59:00")
    assert dt.strftime("%Y-%m-%d")=="2018-10-03"
    assert maybe_timestamp("NA") is None

def test_only_nonvertical_xy_and_air_fields_for_pilot(tmp_path):
    csvfile=tmp_path/"pilot.csv"
    columns=["Tag","TimeCont","Latitude","Longitude","OverSeaOrLand",
             "running_Flap_rate","blh","sstDiff","windSpeed850",
             "msshf","Altitude_m","AleAboveTerrain","TerrainHeight"]
    rows=[",".join(columns)]
    for day in ("2018-10-01","2018-10-02"):
        for i in range(25):
            values=["B12",f"{day} 08:{i*2:02d}:00",
                    "51.3","31.2","0","0.3","800","4.5","12","5",
                    "NONNUMERIC_HEIGHT_DO_NOT_PARSE","NOT_AN_AGL_NUMBER","NOT_AN_ELEVATION"]
            rows.append(",".join(values))
    csvfile.write_text("\n".join(rows)+"\n")
    report=metadata_of_pilot(csvfile)
    assert report["schema_ok"]
    assert report["raw_GPS_5minute_bins"]==20
    assert report["distinct_days_with_GPS"]==2
    assert report["observed_native_height_or_AGL_numbers_read"] is False
    assert report["nonvertical_annotation_finite_fraction"]["blh"]==1

def test_no_faux_column_imputation(tmp_path):
    path=tmp_path/"bad.csv"
    path.write_text("Tag,TimeCont,Longitude,Latitude,Altitude_m\nA,2018-10-01,5,52,200\n")
    r=metadata_of_pilot(path)
    assert r["schema_ok"] is False
    assert "running_Flap_rate" in r["missing_nonvertical_fields"]

def test_height_column_is_never_named_as_input_column():
    assert not any("Altitude" in n or "TerrainHeight" in n or "AleAboveTerrain" in n
                   for n in NON_VERTICAL_HEADER)
