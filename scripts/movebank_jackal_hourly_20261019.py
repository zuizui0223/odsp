"""Etosha jackal hourly-v1 sensitivity: same UTC-clock-hour policy as elephants.

Do not retroactively change jackal native or elephant v1 source results.
"""
import argparse,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts import movebank_southern_solar_mammal_20261019 as south
from scripts.movebank_elephant_hourly_20261019 import thinned_loader
CONTRACT=HERE/"research/MOVEBANK_JACKAL_HOURLY_SENSITIVITY_V1_20261019.json"
SOUTH=HERE/"research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(CONTRACT.read_text())
    if freeze["version"]!="etosha-jackal-hourly-blind-sampling-v1":raise ValueError("Unregistered route")
    src=next(x for x in json.loads(SOUTH.read_text())["sources"] if x["label"]=="etosha_jackal")
    fpath=a.out/"jackal_original.csv"
    report={"source":"etosha_jackal","taxon":src["taxon"],"doi":src["doi"],"route":"hourly_v1_post_outcome_sensitivity",
        "original_jackal_native_v0":0.05484644894836822,
        "separate_elephant_hourly_v1":-0.15012724713090492,
        "biological_ceiling":"Same broad ecosystem, not matched field date/individual or causal species contrast."}
    try:
        files=original_files(src["package_uuid"])
        srcs=[x for x in files if x["bitstream_uuid"]==src["provider_original_bitstream_uuid"]]
        if len(srcs)!=1 or srcs[0]["checksum"]["value"].lower()!=src["provider_original_md5"].lower():
            raise ValueError("Provider checksum or ORIGINAL bitstream mismatch")
        report["provider_original_checked"]=checksum_and_download(srcs[0],fpath)
        old=south.load_events
        try:
            south.load_events=thinned_loader
            report.update(south.analyze_south(fpath))
            report.update(thinned_loader.counts)
        finally:south.load_events=old
    except Exception as e:
        report.update(effect_status="source_hold",effect=None,error=f"{type(e).__name__}: {e}")
    finally:fpath.unlink(missing_ok=True)
    print("ETOSHA_JACKAL_HOURLY_COMPARABILITY "+json.dumps(report,sort_keys=True),flush=True)
    (a.out/"jackal_hourly_grouped.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":main()
