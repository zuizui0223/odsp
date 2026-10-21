from prospective.scacco_point_xy_thermal_support import (
    selected_points,summarize,shared_cells,normalized_source
)
from math import isclose
import csv
import io

COLS=["study_id","study_name","species","animal_id","timestamp","lon","lat",
      "segment_id","data_source","flap_probability","vedba",
      "wind_speed_1000m","orographic_uplift","thermal_uplift"]

def row(bird,day,bin5=0,wstar="2",study="122120597",species="Species x"):
    hour=8+bin5//12;minute=(bin5%12)*5
    return dict(study_id=study,study_name="Study X",species=species,animal_id=bird,
                timestamp=f"{day} {hour:02d}:{minute:02d}:00",
                lon="10.3",lat="50.5",segment_id=f"{bird}-{day}",
                data_source="Movebank",flap_probability="0.4",vedba="0.2",
                wind_speed_1000m="5",orographic_uplift=".3",thermal_uplift=wstar,
                height_gener="THIS MUST NOT READ")

def test_two_days_shared_cell_and_no_vertical_use():
    data=[row(f"b{i}",date,k,wstar=w)
          for i in range(10)
          for date,w in [("2018-05-01","2"),("2018-05-02","2"),("2018-05-03","12"),("2018-05-04","12")]
          for k in range(30)]
    first,c,source=selected_points(data)
    result=summarize(first,c,source)
    assert result["source_species"]==1
    p=result["catalog_panels"][0]
    assert p["horizontal_5000"]["scorable_birds"]==10
    assert p["horizontal_5000"]["admitted_identity_source"]
    assert p["thermal_5000"]["birds_with_two_qualifying_low_and_high_days"]==10
    assert result["panels_new_independent_5km_thermal_eligible"]==1
    assert result["numerical_altitude_values_accessed_for_screen"] is False

def test_known_original_parent_flagged_not_independent():
    data=[row(f"b{i}",day,k,study="332044860")
          for i in range(10) for day in ("2018-05-01","2018-05-02")
          for k in range(30)]
    first,c,ids=selected_points(data)
    panel=summarize(first,c,ids)["catalog_panels"][0]
    assert panel["horizontal_5000"]["admitted_identity_source"]
    assert not panel["independent_new_parent_candidate"]

def test_mixed_study_id_source_fallback_never_claims_numeric_study():
    s,idn,known=normalized_source({"study_id":"NA","study_name":"A marine project",
                                    "data_source":"External"})
    assert idn=="NAME-ONLY:A marine project"
    assert not known

def test_same_date_other_flocks_do_not_create_fake_other_day_reference():
    data=[row(f"b{i}","2018-05-01",k)
          for i in range(11) for k in range(30)]
    first,c,ids=selected_points(data)
    x=summarize(first,c,ids)["catalog_panels"][0]
    assert x["horizontal_5000"]["scorable_birds"]==0

def test_first_fix_wins_even_if_later_has_climate_value():
    data=[row("b0","2018-05-01",0,wstar="NA")]
    late=row("b0","2018-05-01",0,wstar="100")
    late["timestamp"]="2018-05-01 08:01:00"
    data.append(late)
    first,c,ids=selected_points(data)
    assert len(first)==1
    assert next(iter(first.values()))[3] is None

def test_two_species_do_not_share_other_bird_cohort_reference():
    data=[row(f"b{i}",date,k,species=sp)
          for sp in ("A","B") for i in range(10)
          for date in ("2018-05-01","2018-05-02") for k in range(30)]
    first,c,ids=selected_points(data)
    out=summarize(first,c,ids)
    assert len(out["catalog_panels"])==2
    assert all(p["horizontal_5000"]["scorable_birds"]==10 for p in out["catalog_panels"])
