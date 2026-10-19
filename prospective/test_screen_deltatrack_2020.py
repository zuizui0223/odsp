"""Synthetic mixed-species test: no altitude outcome is read or pooled."""
import csv
import gzip
from pathlib import Path

from prospective.screen_deltatrack_2020 import audit


def test_two_species_never_pool(tmp_path: Path):
    path=tmp_path/"DELTATRACK-gps-2020.csv.gz"
    with gzip.open(path,"wt",newline="",encoding="utf-8") as f:
        cols=["timestamp","individual-local-identifier","individual-taxon-canonical-name",
              "location-long","location-lat","ground-speed","height-above-msl"]
        w=csv.DictWriter(f,fieldnames=cols)
        w.writeheader()
        for species in ("Larus argentatus","Larus fuscus"):
            for bird in ("a","b"):
                for date in ("2020-05-14","2020-05-15"):
                    for i in range(60):
                        hour=7+i//12
                        minute=(i%12)*5
                        w.writerow({
                            "timestamp":f"{date} {hour:02d}:{minute:02d}:00.000",
                            "individual-local-identifier":f"{species}::{bird}",
                            "individual-taxon-canonical-name":species,
                            "location-long":"3.71",
                            "location-lat":"51.63",
                            "ground-speed":"8",
                            "height-above-msl":"DO_NOT_READ_VERTICAL",
                        })
    result=audit(path)
    assert result["source_total_rows"]==480
    assert not result["altitude_values_opened"]
    assert not result["altitude_outcomes_tested"]
    for species in ("Larus argentatus","Larus fuscus"):
        sub=result["species"][species]
        assert sub["animals_with_two_scorable_days"]==2
        assert sub["scorable_days"]==4
        assert sub["flight_proxy_unique_5min_bins"]==240
        assert not sub["structural_species_potential"]
