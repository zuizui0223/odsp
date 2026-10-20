#!/usr/bin/env python3
"""New 2013 altitude-blind support admission, preserving closed 2014 test.

Reuses the exact previously executed scanner, modifying only an isolated
source-year parameter in this process. The same threshold/geometry/logic is
otherwise untouched and no altitude fields are accessed.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from . import stork_2014_xytime_source_screen as prior

NEW_YEAR=2013
CLOSED_YEAR=2014


def run_2013_gps_support(gps_zip,reference):
    if prior.YEAR!=CLOSED_YEAR:
        raise AssertionError("Base scanner default source year unexpectedly changed")
    try:
        prior.YEAR=NEW_YEAR
        report=prior.from_archive(gps_zip,reference)
    finally:
        prior.YEAR=CLOSED_YEAR
    if report["source_year"]!=NEW_YEAR:
        raise AssertionError("New prospective 2013 source not loaded")
    report["analysis"]="WHITE_STORK_2013_ALTITUDE_BLIND_XYTIME_GATE_V1"
    report["provenance_year_inventory_run"]=39407501404
    report["closed_2014_outcome_changed"]=False
    report["source_year_selected_before_native_height_access"]=True
    report["source_selection_rule"]="latest available archive year with >=10 flying-speed bird IDs; 2013 metadata showed 74"
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gps-zip",required=True,type=Path)
    parser.add_argument("--reference",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=run_2013_gps_support(args.gps_zip,args.reference)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "year":result["source_year"],
      "flight_birds":result["GPS_time_speed_xy_rows"]["birds_with_thinned_flight"],
      "5km_birds":result["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"],
      "50km_birds":result["horizontal_support_by_grid_m"]["50000"]["birds_with_2_scorable_shared_cell_days"],
      "100km_birds":result["horizontal_support_by_grid_m"]["100000"]["birds_with_2_scorable_shared_cell_days"],
      "primary_5km_admitted":result["horizontal_support_by_grid_m"]["5000"]["admitted"],
      "altitude_read":False},sort_keys=True))


if __name__=="__main__":
    main()
