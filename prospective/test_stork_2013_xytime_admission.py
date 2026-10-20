"""Prospective source-year 2013 override must be isolated and altitude blind."""
from prospective import stork_2014_xytime_source_screen as prior
from prospective.stork_2013_xytime_admission import run_2013_gps_support


def test_selected_2013_source_does_not_rewrite_frozen_2014(monkeypatch):
    assert prior.YEAR==2014
    calls=[]
    def mocked(gps_zip,ref):
        calls.append(prior.YEAR)
        return {
            "source_year":prior.YEAR,
            "gps_altitude_values_accessed":False,
            "GPS_time_speed_xy_rows":{"birds_with_thinned_flight":37},
            "horizontal_support_by_grid_m":{
                "5000":{"admitted":False,"birds_with_2_scorable_shared_cell_days":5},
                "50000":{"admitted":True,"birds_with_2_scorable_shared_cell_days":24},
                "100000":{"admitted":True,"birds_with_2_scorable_shared_cell_days":31},
            },
        }
    monkeypatch.setattr(prior,"from_archive",mocked)
    r=run_2013_gps_support("2013gps.zip","reference.csv")
    assert calls==[2013]
    assert prior.YEAR==2014
    assert r["closed_2014_outcome_changed"] is False
    assert r["gps_altitude_values_accessed"] is False
    assert r["horizontal_support_by_grid_m"]["5000"]["admitted"] is False


def test_selected_year_reverts_after_archive_failure(monkeypatch):
    def fail(*args):
        assert prior.YEAR==2013
        raise ValueError("source unavailable")
    monkeypatch.setattr(prior,"from_archive",fail)
    import pytest
    with pytest.raises(ValueError,match="source unavailable"):
        run_2013_gps_support("unused","unused")
    assert prior.YEAR==2014
