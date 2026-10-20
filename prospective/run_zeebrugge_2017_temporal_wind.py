#!/usr/bin/env python3
"""Next-calendar-year (2017) Zeebrugge CERRA site-wind altitude-shape transfer.

The 2016 kernel and the low/high wind definitions are unchanged. The 2017
native GPS altitude is accessed only after the separately committed 2017
outcome-blind support receipt, CERRA site/month climate statistics, exact ID
crosswalk and source fingerprints are checked.
"""
from __future__ import annotations

import argparse,csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np

from . import screen_zeebrugge_cerra_2016 as previous_source
from . import screen_zeebrugge_2017_cerra as source2017
from . import run_zeebrugge_2016_wind_shape as previous_runner
from . import zeebrugge_cerra_2016_wind_shape as previous_kernel

SEED=20261021
DRAW_N=999


def check_previous_2017_support(prior,first,ref,labels):
    if prior["2017_native_altitude_opened"] is not False:
        raise ValueError("2017 source support already used native height")
    if prior["GPS_md5"]!=source2017.SOURCE_MD5:
        raise ValueError("Frozen GPS archive source identity drift")
    reference=previous_source.reference_meta(ref)
    if reference["site_centers"]!=prior["anchor_2016_site_centers"]:
        raise ValueError("2016 anchored site centroids drift")
    mapped=previous_source.safe_crosswalk(ref,labels)
    if not mapped["accepted"]:
        raise ValueError("2017 individual/site reference join lost")
    weather,regimes=source2017.site_winds_2017(reference["site_centers"])
    expected=prior["CERRA_wind"]
    if set(expected)!=set(weather):
        raise ValueError("2017 site weather membership drift")
    for site,orig in expected.items():
        current=weather[site]
        for k in ("response_grid_latitude","response_grid_longitude"):
            if abs(orig[k]-current[k])>1e-5:
                raise ValueError("2017 CERRA coordinate drift")
        if orig["complete_weather_days"]!=current["complete_weather_days"]:
            raise ValueError("2017 CERRA day coverage drift")
        for month,values in orig["thresholds_by_month"].items():
            present=current["thresholds_by_month"].get(month)
            if present is None:
                raise ValueError("2017 CERRA month missing")
            for k in ("q25","q75","n_calendar_days"):
                if abs(present[k]-values[k])>1e-8:
                    raise ValueError("2017 CERRA wind threshold drift")
    climate_sha=hashlib.sha256(json.dumps(regimes,sort_keys=True).encode()).hexdigest()
    if climate_sha!=prior["CERRA_site_calendar_state_sha256"]:
        raise ValueError("2017 CERRA wind per-site date labels have drifted")
    support=previous_source.xysupport(first,mapped["site_by_bird"],regimes)
    original=prior["support"]
    for key in ("wind_both_regimes_birds","baseline_shared_cell_birds",
                "matched_wind_eligible_birds_sha256"):
        if support[key]!=original[key]:
            raise ValueError("2017 GPS/weather structural support drift "+key)
    if not support["wind_gate_admitted"]:
        raise ValueError("2017 preheight wind gate was not open")
    return mapped["site_by_bird"],weather,regimes,support


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--reference",required=True,type=Path)
    p.add_argument("--preheight-receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()

    previous_source.ensure_md5(args.gps,source2017.SOURCE_MD5,source2017.SOURCE_GPS)
    previous_source.ensure_md5(args.reference,source2017.REFERENCE_MD5,source2017.SOURCE_REFERENCE)
    prior=json.loads(args.preheight_receipt.read_text())
    with args.reference.open("rt",encoding="utf-8-sig",newline="") as fp:
        ref=list(csv.DictReader(fp))
    with gzip.open(args.gps,"rt",encoding="utf-8-sig",newline="") as fp:
        first,labels,_=source2017.find_2017_events(csv.DictReader(fp))
    sites,weather,regimes,support=check_previous_2017_support(prior,first,ref,labels)
    # The earlier height adapter does not select by height and is year-agnostic.
    # The same fixed altitude interval, bins and daily-centering are reused.
    sessions,quality=previous_runner.extract_height_from_frozen_events(args.gps,first)
    out={
        "analysis":"ZEEBRUGGE_2017_TEMPORAL_CERRA_WIND_SHAPE_V1",
        "source":"https://zenodo.org/records/22273603",
        "gps_md5":source2017.SOURCE_MD5,"reference_md5":source2017.REFERENCE_MD5,
        "year":2017,"preheight_wind_birds":prior["support"]["wind_both_regimes_birds"],
        "preheight_wind_fingerprint":prior["support"]["matched_wind_eligible_birds_sha256"],
        "frozen_source_receipt":"ZEEBRUGGE_2017_CERRA_PREHEIGHT_RECEIPT_V1.json",
        "frozen_plan":"prospective/ZEEBRUGGE_2017_TEMPORAL_WIND_PREHEIGHT_PLAN_V1.json",
        "reused_2016_kernel_sha256":hashlib.sha256(Path(previous_kernel.__file__).read_bytes()).hexdigest(),
        "quality":quality,"terminal":"unavailable",
        "novel_replication_status":"temporal next-year heldout; not independent dataset/study because birds/devices can overlap"
    }
    args.output.mkdir(parents=True,exist_ok=True)
    if quality["valid_fraction"] is None or quality["valid_fraction"]<.8:
        out["reason"]="frozen_height_quality_unavailable"
    else:
        packed=previous_kernel.pack(sessions,sites,regimes)
        observed=previous_kernel.score_packed(packed,regimes)
        out["observed"]=observed
        if observed["eligible_birds"]<10:
            out["reason"]="frozen_2017_scored_birds_below_ten"
        else:
            rng=np.random.default_rng(SEED)
            draws=[]
            for ix in range(DRAW_N):
                permuted=previous_kernel.permute_wind_labels(regimes,weather,rng)
                r=previous_kernel.score_packed(packed,permuted)
                valid=r["eligible_birds"]>=10 and r["mean_gain"] is not None
                draws.append({"permutation":ix+1,
                    "gain":r["mean_gain"] if valid else None,
                    "eligible_birds":r["eligible_birds"],
                    "eligible_days":r["eligible_bird_days"],
                    "eligible_fixes":r["scored_fixes"]})
                if (ix+1)%100==0:print("CERRA year-2017 randomizations",ix+1,flush=True)
            with (args.output/"wind_2017_null_draws.csv").open("w",newline="") as fp:
                w=csv.DictWriter(fp,fieldnames=list(draws[0]))
                w.writeheader();w.writerows(draws)
            calibration=previous_runner.calibrate(observed["mean_gain"],[
                {"gain":r["gain"]} for r in draws
            ])
            out["calibration"]=calibration
            out["null_birds_range"]=[min(r["eligible_birds"] for r in draws),
                                     max(r["eligible_birds"] for r in draws)]
            if calibration["valid"]<950:
                out["reason"]="frozen_2017_null_support_unavailable"
            else:
                out["terminal"]=("supported_wind_context_transfer" if
                    calibration["p_upper"]<.05 and calibration["observed_minus_null_mean"]>0
                    else "wind_context_transfer_not_supported")
    (args.output/"ZEEBRUGGE_2017_CERRA_WIND_SHAPE_RESULT_V1.json").write_text(
        json.dumps(out,indent=2,sort_keys=True)+"\n"
    )
    if "observed" in out:
        with (args.output/"2017_per_bird_wind_shape.csv").open("w",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=["bird","gain","low_days","high_days","scored_fixes"])
            writer.writeheader()
            for bird,d in sorted(out["observed"]["per_bird"].items()):
                writer.writerow({"bird":bird,**d})
    print(json.dumps({
        "terminal":out["terminal"],"reason":out.get("reason"),
        "valid_altitude_fraction":quality["valid_fraction"],
        "eligible_birds":out.get("observed",{}).get("eligible_birds"),
        "bird_days":out.get("observed",{}).get("eligible_bird_days"),
        "scored_fixes":out.get("observed",{}).get("scored_fixes"),
        "observed_gain":out.get("observed",{}).get("mean_gain"),
        "null_valid":out.get("calibration",{}).get("valid"),
        "p_upper":out.get("calibration",{}).get("p_upper"),
        "excess":out.get("calibration",{}).get("observed_minus_null_mean")
    },sort_keys=True))


if __name__=="__main__":
    main()
