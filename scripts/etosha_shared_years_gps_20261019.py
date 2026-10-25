"""Compare precisely the shared 2009–2010 Etosha solar-year mammal cohorts.

This is a new post-outcome restricted-source question. Reproduce full-source
source-locked hourly v1 results EXACTLY before opening the restricted means.
"""
import argparse,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,solar_period
from scripts.movebank_southern_solar_mammal_20261019 import safe_unzip_data_csv,southern_solar_cycle
from scripts import movebank_southern_solar_mammal_20261019 as south
from scripts.movebank_elephant_hourly_20261019 import thinned_loader

CONTRACT=HERE/"research/ETOSHA_COMMON_YEARS_GPS_V0_20261019.json"
SOURCES=HERE/"research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"

def shared_year_loader(path):
    tracks,rows,invalid=thinned_loader(path)
    kept={}
    for animal,fixes in tracks.items():
        filtered=[]
        for t,lat,lon in fixes:
            local,part=solar_period(t,lat,lon)
            year,branch=southern_solar_cycle(local)
            if year in (2009,2010):
                filtered.append((t,lat,lon))
        if filtered:kept[animal]=filtered
    shared_year_loader.counts={
        "original_raw_rows":rows,"source_invalid_rows":invalid,
        "source_hour_samples":thinned_loader.counts["timestamp_only_hour_samples"],
        "hour_samples_with_southern_solar_year_in_2009_2010":sum(len(v) for v in kept.values())}
    return kept,rows,invalid

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    reg=json.loads(CONTRACT.read_text())
    if reg["version"]!="etosha-common-years-2009-2010-hourly-gps-v0" or reg["years"]!=[2009,2010]:
        raise ValueError("Unregistered restricted source comparison")
    source={x["label"]:x for x in json.loads(SOURCES.read_text())["sources"]}
    expected={"etosha_elephant":-0.15012724713090492,"etosha_jackal":0.04478579444771083}
    outputs=[]
    for label in ("etosha_elephant","etosha_jackal"):
        s=source[label]
        out={"source":label,"taxon":s["taxon"],"doi":s["doi"],"fixed_shared_solar_years":[2009,2010],
             "frozen_full_source_hourly_effect":expected[label]}
        raw=args.out/(label+".zip_or_csv");csv=args.out/(label+".csv")
        try:
            files=[x for x in original_files(s["package_uuid"]) if x["bitstream_uuid"]==s["provider_original_bitstream_uuid"]]
            if len(files)!=1 or files[0]["checksum"]["value"].lower()!=s["provider_original_md5"].lower():
                raise ValueError("Original MD5/bitstream identity mismatch")
            out["provider_original_verified"]=checksum_and_download(files[0],raw)
            if s["provider_filename"].endswith(".zip"):safe_unzip_data_csv(raw,csv)
            else:raw.replace(csv)
            original_loader=south.load_events
            try:
                south.load_events=thinned_loader
                reproduced=south.analyze_south(csv)
                if reproduced.get("effect_status")!="exploratory_population_description":
                    raise ValueError("Full source original hourly result unexpectedly ineligible")
                x=reproduced["effect"]["mean_falling_minus_rising_log1p_night_over_day_kmh"]
                if abs(x-expected[label])>1e-12:
                    raise ValueError("Full source frozen behavioral estimate changed")
                out["previously_validated_whole_source_reproduced"]=True
                south.load_events=shared_year_loader
                out.update(south.analyze_south(csv))
                out["fixed_year_clock_selection_counts"]=shared_year_loader.counts
            finally:
                south.load_events=original_loader
        except Exception as ex:
            out.update(effect_status="source_hold",effect=None,error=f"{type(ex).__name__}: {ex}")
        finally:
            raw.unlink(missing_ok=True);csv.unlink(missing_ok=True)
        print("ETOSHA_SHARED_2009_2010_GPS "+json.dumps(out,sort_keys=True),flush=True)
        outputs.append(out)
    result={"description":"Post-outcome same-solar-year Etosha original-archive time-only hourly GPS comparison, not causal ecological selection",
       "sources":outputs,"years":[2009,2010]}
    (args.out/"etosha_2009_2010_hourly_gps_groups.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
