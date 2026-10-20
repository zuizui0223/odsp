from zipfile import ZipFile
from pathlib import Path

import pytest

from prospective.flack_stork_2014_xytime_preflight import get_source_csv_names
from prospective import stork_2014_xytime_source_screen as core


def row(animal,day,bin5=0,z="DO_NOT_READ",speed="11"):
    hr=7+bin5//12;minute=5*(bin5%12)
    return {
        "individual-local-identifier":animal,
        "timestamp":f"{day} {hr:02d}:{minute:02d}:00.000",
        "location-long":"9.4",
        "location-lat":"48.1",
        "ground-speed":speed,
        "height-above-ellipsoid":z,
        "visible":"true",
    }


def test_first_selected_5min_fix_independent_of_bad_altitude():
    events=[row("A","2014-08-13",0,z="IS_NOT_A_NUMBER"),
            {**row("A","2014-08-13",0,z="1000"),"timestamp":"2014-08-13 07:01:00.000"},
            row("B","2014-08-13",0,z="MISSING")] 
    result=core.audit(events,{"A":"nestling","B":"nestling"})
    assert result["GPS_time_speed_xy_rows"]["thinned_flight_5min_bins"]==2
    assert result["gps_altitude_values_accessed"] is False


def test_new_study_with_bird_id_repeats_can_pass_50km_without_z():
    rows=[]
    for a in range(10):
        for day in ("2014-08-12","2014-08-13"):
            for minute in range(60):
                rows.append(row(f"stork{a}",day,minute,z="BAD_HEIGHT"))
    result=core.audit(rows)
    assert result["horizontal_support_by_grid_m"]["50000"]["admitted"] is True
    assert result["horizontal_support_by_grid_m"]["50000"]["birds_with_2_scorable_shared_cell_days"]==10
    assert result["GPS_altitude_shape_tested"] is False


def test_gps_zip_member_skips_mac_resource_fork(tmp_path:Path):
    p=tmp_path/"sample.zip"
    with ZipFile(p,"w") as z:
        z.writestr("__MACOSX/._flight.csv","inert")
        z.writestr("._flight.csv","inert")
        z.writestr("folder/flight.csv","col_a,col_b\nx,y\n")
    with ZipFile(p) as z:
        assert get_source_csv_names(z)=="folder/flight.csv"


def test_gps_zip_member_refuses_ambiguous_multiple_files(tmp_path:Path):
    p=tmp_path/"ambiguous.zip"
    with ZipFile(p,"w") as z:
        z.writestr("one.csv","a")
        z.writestr("two.csv","b")
    with ZipFile(p) as z:
        with pytest.raises(ValueError,match="one"):
            get_source_csv_names(z)
