"""Eight new provider-authenticated Movebank source cohorts, same fixed v0 GPS analysis.

Runs without changing thresholds or looking at animal effect directions to select sources.
The original three-source receipt and analysis file remain immutable.
"""
import argparse
import json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_solar_movement_20261019 import analyze_file

MANIFEST=HERE/"research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    doc=json.loads(MANIFEST.read_text())
    if doc["version"]!="independent-published-source-extension-v0" or len(doc["sources"])!=8:
        raise ValueError("The eight-source manifest was altered")
    results=[]
    for s in doc["sources"]:
        row={"label":s["label"],"taxon":s["taxon"],"doi":s["doi"],"package_uuid":s["package_uuid"]}
        file=a.out/(s["label"]+".csv")
        try:
            candidates=[f for f in original_files(s["package_uuid"]) if f["bitstream_uuid"]==s["original_csv_bitstream_uuid"]]
            if len(candidates)!=1 or candidates[0]["checksum"]["value"]!=s["original_csv_md5"]:
                raise ValueError("Native source bitstream or provider MD5 changed")
            row["download"]=checksum_and_download(candidates[0],file)
            row.update(analyze_file(file))
        except Exception as ex:
            row.update(effect_status="source_hold",reason=f"{type(ex).__name__}: {ex}")
        finally:file.unlink(missing_ok=True)
        results.append(row)
        print("EXTENSION_SOURCE_MOVEMENT "+json.dumps(row,sort_keys=True),flush=True)
    result={"version":doc["version"],"scope":"Same preregistered source-qualified GPS effect; an archive may share recruitment or contain zero eligible individuals.","sources":results}
    (a.out/"all_eight_grouped_results.json").write_text(json.dumps(result,indent=2)+"\n")
    print("EXTENSION_SUMMARY "+json.dumps({"sources":len(results),
          "qualified_sources":sum(x.get("effect_status")=="exploratory_population_description" for x in results),
          "source_hold":sum(x.get("effect_status")=="source_hold" for x in results),
          "insufficient_sources":sum(x.get("effect_status")=="insufficient_independent_animals" for x in results)},sort_keys=True),flush=True)

if __name__=="__main__":main()
