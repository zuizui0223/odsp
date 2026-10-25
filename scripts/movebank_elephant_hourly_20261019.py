"""Etosha elephant alternative observed-hour GPS route; v0 stays insufficient.

This route uses only source timestamps to thin extremely high-frequency fixes,
then applies the unmodified, independently source-locked Southern v0 estimator.
The module's v0 loader is dependency-injected only inside this isolated runner
and restored even if a source error occurs.
"""
from collections import defaultdict
import argparse,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_southern_solar_mammal_20261019 import (
    CONTRACT as SOUTH_CONTRACT,safe_unzip_data_csv
)
from scripts import movebank_southern_solar_mammal_20261019 as south
from scripts.movebank_solar_movement_20261019 import load_events as unmodified_loader

CONTRACT=HERE/"research/MOVEBANK_ELEPHANT_HOURLY_V1_20261019.json"

def choose_one_per_utc_hour(events):
    """Timestamp-only selection; positions must not affect which fix is picked."""
    selected={}
    for t,lat,lon in events:
        h=t.replace(minute=0,second=0,microsecond=0)
        k=(t-h).total_seconds()
        if h not in selected or k<selected[h][0]:
            selected[h]=(k,(t,lat,lon))
    return [v[1] for h,v in sorted(selected.items())]

def thinned_loader(path):
    by_animal,n_rows,invalid=unmodified_loader(path)
    n_before=sum(len(v) for v in by_animal.values())
    selected={k:choose_one_per_utc_hour(v) for k,v in by_animal.items()}
    n_after=sum(len(v) for v in selected.values())
    thinned_loader.counts={"raw_valid_fixes":n_before,"timestamp_only_hour_samples":n_after,
                            "discarded_redundant_hourly_samples":n_before-n_after}
    return selected,n_rows,invalid

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    protocol=json.loads(CONTRACT.read_text())
    if protocol["version"]!="elephant-hourly-solar-v1":raise ValueError("Unfrozen route")
    src=next(x for x in json.loads(SOUTH_CONTRACT.read_text())["sources"] if x["label"]=="etosha_elephant")
    result={"source":"etosha_elephant","taxon":src["taxon"],"doi":src["doi"],"route":"v1_after_source_support_failure",
            "v0_result_unchanged":"insufficient_independent_animals","original_data_reused":True}
    z=args.out/"provider_original.zip";csvfile=args.out/"elephant_original.csv"
    try:
        originals=original_files(src["package_uuid"])
        fs=[x for x in originals if x["bitstream_uuid"]==src["provider_original_bitstream_uuid"]]
        if len(fs)!=1 or fs[0]["checksum"]["value"].lower()!=src["provider_original_md5"].lower():
            raise ValueError("Source bitstream UUID and MD5 changed")
        result["provider_digest_check"]=checksum_and_download(fs[0],z)
        result["uncompressed_original_csv_bytes"]=safe_unzip_data_csv(z,csvfile)
        old=south.load_events
        try:
            south.load_events=thinned_loader
            result.update(south.analyze_south(csvfile))
            result.update(thinned_loader.counts)
        finally:
            south.load_events=old
    except Exception as e:
        result.update(effect_status="source_hold",error=f"{type(e).__name__}: {e}",effect=None)
    finally:
        z.unlink(missing_ok=True);csvfile.unlink(missing_ok=True)
    result["caveat"]="Clock-hour time-only thinning changes observation measurement. Do not merge with original v0 or assert latent elephant activity."
    print("ETOSHA_ELEPHANT_HOURLY_ECOLOGY "+json.dumps(result,sort_keys=True),flush=True)
    (args.out/"etosha_elephant_hourly_result.json").write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
