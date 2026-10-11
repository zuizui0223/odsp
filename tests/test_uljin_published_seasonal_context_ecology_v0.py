"""Published seasonal occupancy detection is NOT matched-daylength diel activity."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"ULJIN_PUBLISHED_SEASONAL_DETECTABILITY_SPECIES_CONTEXT_V0.json").read_text())


def test_exact_four_published_occupancy_detection_coefficients_preserved():
    data=C["published_season_summer_vs_winter_detection_logit"]
    assert [r["species"] for r in data]==[
        "Goral","Water deer","Roe deer","Wild boar"
    ]
    beta={r["species"]:r["beta"] for r in data}
    assert beta=={
        "Goral":.886,"Water deer":1.234,
        "Roe deer":.030,"Wild boar":-.888,
    }
    assert all(r["ci95"][0]<r["beta"]<r["ci95"][1] for r in data)
    assert next(r["ci95"] for r in data if r["species"]=="Water deer")==[
        .493,1.974]
    assert next(r["ci95"] for r in data if r["species"]=="Wild boar")==[
        -1.372,-.404]


def test_annual_published_season_p_not_an_original_biological_time_refuge_result():
    assert C["status"]==(
        "PUBLISHED_CONTEXT_ONLY_NO_ORIGINAL_MATCHED_DATE_EVENT_OR_OPERATION_HOURS"
    )
    assert C["yearly_model"].find("WINTER reference")>=0
    assert C["original_41pairs_data_available"] is False
    assert C["authentic_hourly_camera_on_off_available"] is False
    assert len(C["interpretation_guard"])==6
    assert "NOT hourly" in C["interpretation_guard"][0]
    assert "not" in C["interpretation_guard"][1].lower()
    assert "cannot" in C["interpretation_guard"][2]
