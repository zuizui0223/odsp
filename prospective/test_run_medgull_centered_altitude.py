"""Synthetic-only checks for the frozen MEDGULL biological endpoint."""
import csv
import gzip
from collections import Counter
from pathlib import Path

import numpy as np

from prospective.run_medgull_centered_altitude import (
    _assign_labels,
    extract_flight_sessions,
    run,
    score,
    N_BINS,
)


def artificial_sessions():
    out=[]
    for i in range(10):
        for d in ("2022-05-20","2022-05-21","2022-05-22"):
            arr=np.zeros(N_BINS,dtype=np.int32)
            low=i%5
            arr[low]=30
            arr[5+low]=30
            out.append({"id":f"b{i}","day":d,"month":5,
                        "valid":60, "hist":{(511,1140):arr}})
    return out


def test_frozen_self_vs_conspecific_alternative_and_label_null():
    events=artificial_sessions()
    orig=[x["id"] for x in events]
    val=score(events,orig)
    assert val["estimable"]
    assert val["eligible_birds"]==10
    assert val["eligible_scored_days"]==30
    assert val["mean_gain"] > 0
    shuffled, swaps = _assign_labels(events,seed=20261020)
    assert swaps > 0
    assert len({(lab,s["day"]) for lab,s in zip(shuffled,events)})==len(events)
    assert Counter((lab,s["month"]) for lab,s in zip(orig,events)) == Counter(
        (lab,s["month"]) for lab,s in zip(shuffled,events)
    )
    assert score(events,shuffled)["mean_gain"] < val["mean_gain"]


def test_non_numeric_height_declines_quality_not_faked(tmp_path:Path):
    fn=tmp_path/"MEDGULL_ANTWERPEN-gps-2022.csv.gz"
    with gzip.open(fn,"wt",newline="",encoding="utf-8") as f:
        columns=["timestamp","individual-local-identifier",
                 "location-long","location-lat","ground-speed",
                 "height-above-msl"]
        w=csv.DictWriter(f,fieldnames=columns)
        w.writeheader()
        for i in range(20):
            w.writerow({
                "timestamp":f"2022-05-20 08:{(i*2)%60:02d}:00.000",
                "individual-local-identifier":"a",
                "location-long":"4.42","location-lat":"51.24",
                "ground-speed":"10",
                "height-above-msl":"not_a_height",
            })
    sessions,q=extract_flight_sessions(fn)
    assert sessions == []
    assert not q["qc_pass"]
    assert q["valid_altitude_bins"]==0
    receipt=run(sessions,q,permutations=3,min_birds=1,min_valid_null=2)
    assert receipt["terminal"]=="altitude_quality_unavailable"
