#!/usr/bin/env python3
"""Outcome-blind macro source eligibility, using only source segment metadata.

Audit study, species, individual, dates, flight-segment count, and predictor
field completeness. No pointwise RDS, GPS altitude, vertical dispersion or
ecological response is opened. Data.zip official MD5 is pinned.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ZIP_FILENAME="Data.zip"
ZIP_MD5="e1f116e6576cf20e54dad16d2c91a26d"
ZIP_SIZE=551470630
SEGMENT_FILE="BIOLOGGING_finalSummaryDataset_perSegment_fromFix+COTvariables_Feb2025.csv"
POINT_FILE="FinalDf_perPoint_VedbaGs_flappingProbs_ENV.rds"
REQUIRED={
    "studyName","studyID","individualID","species","segmentID",
    "segm_timeStart","totNlocs","dataSource",
    "avg_thermUplift","avg_oroUplift","avg_windSpeed_1000m",
    "avg_windSupp_1000m","avg_probFlap"
}
PREDICTORS=["avg_thermUplift","avg_oroUplift",
            "avg_windSpeed_1000m","avg_windSupp_1000m","avg_probFlap"]


def checksum(path):
    if path.name!=ZIP_FILENAME or path.stat().st_size!=ZIP_SIZE:
        raise ValueError("Frozen official Data.zip name/size mismatch")
    md5=hashlib.md5()
    with path.open("rb") as fd:
        for block in iter(lambda:fd.read(1048576),b""):
            md5.update(block)
    if md5.hexdigest()!=ZIP_MD5:
        raise ValueError("Frozen archive MD5 mismatch")
    return md5.hexdigest()


def find_member(infos,name):
    found=[r for r in infos if not r.is_dir()
           and (r.filename==name or r.filename.endswith("/"+name))
           and not r.filename.startswith("__MACOSX/")
           and not r.filename.rsplit("/",1)[-1].startswith("._")]
    if len(found)!=1:
        raise ValueError(f"Expected one {name}, found {[r.filename for r in found]}")
    return found[0]


def finite(x):
    try:y=float(x)
    except (ValueError,TypeError):return None
    return y if math.isfinite(y) else None


def audit_segments(reader):
    col=set(reader.fieldnames or ())
    if not REQUIRED<=col:
        raise ValueError("Source segment schema missing: "+str(sorted(REQUIRED-col)))
    panel=defaultdict(lambda:{
        "individuals":set(),"segments":set(),"days":set(),"years":Counter(),
        "predictor_nonmissing":Counter(),"rows":0,"nfix":0})
    day_fix=Counter()
    day_segments=Counter()
    rows=0;bad_fields=0;bad_fix_count=0;bad_date=0
    for r in reader:
        rows+=1
        study=(r["studyID"] or r["studyName"] or "").strip()
        species=(r["species"] or "").strip()
        bird=(r["individualID"] or "").strip()
        seg=(r["segmentID"] or "").strip()
        source=(r["dataSource"] or "").strip()
        date=(r["segm_timeStart"] or "")[:10]
        if not(study and species and bird and seg):
            bad_fields+=1;continue
        if not(len(date)==10 and date[4]=="-" and date[7]=="-"):
            bad_date+=1;continue
        try: year,month,day=int(date[:4]),int(date[5:7]),int(date[8:10])
        except (ValueError,TypeError):
            bad_date+=1;continue
        if not(2000<=year<=2030 and 1<=month<=12 and 1<=day<=31):
            bad_date+=1;continue
        fix=finite(r["totNlocs"])
        if fix is None or fix<0 or int(fix)!=fix:
            bad_fix_count+=1;continue
        fix=int(fix)
        key=(source,study,species)
        v=panel[key]
        v["individuals"].add(bird)
        v["segments"].add(seg)
        v["days"].add(date)
        v["years"][str(year)]+=1
        v["rows"]+=1;v["nfix"]+=fix
        for col in PREDICTORS:
            if finite(r[col]) is not None:
                v["predictor_nonmissing"][col]+=1
        day_fix[key,bird,date]+=fix
        day_segments[key,bird,date]+=1

    by_bird_days=defaultdict(Counter)
    by_bird_strict=defaultdict(Counter)
    source_day_counts=Counter()
    for (key,bird,date),count in day_fix.items():
        if count>=20:
            by_bird_days[key][bird]+=1
            source_day_counts[key]+=1
            if day_segments[key,bird,date]>=2:
                by_bird_strict[key][bird]+=1

    result=[]
    for key,v in sorted(panel.items()):
        source,study,species=key
        qualifying={bird for bird,n in by_bird_days[key].items() if n>=2}
        strict={bird for bird,n in by_bird_strict[key].items() if n>=2}
        result.append({
            "dataSource":source,"studyID":study,"species":species,
            "source_birds":len(v["individuals"]),"source_segments":len(v["segments"]),
            "source_segment_rows":v["rows"],
            "source_tracking_days":len(v["days"]),
            "years":dict(sorted(v["years"].items())),
            "source_sum_point_fixes_in_segments":v["nfix"],
            "eligible_birds_two_days_ge20_fixes":len(qualifying),
            "eligible_birds_two_days_each_2segments_ge20fixes":len(strict),
            "eligible_bird_days_ge20_fixes":source_day_counts[key],
            "candidate_source_panel":len(qualifying)>=10,
            "eligible_bird_id_sha256":hashlib.sha256("\n".join(sorted(qualifying)).encode()).hexdigest(),
            "predictor_nonmissing_segments":dict(sorted(v["predictor_nonmissing"].items())),
            "predictor_valid_fraction":{
                p:v["predictor_nonmissing"][p]/v["rows"] if v["rows"] else None
                for p in PREDICTORS
            }
        })
    return {
       "stage":"SEGMENT_METADATA_ONLY_BEFORE_VERTICAL_RESPONSE",
       "source_segment_rows":rows,
       "rows_missing_study_or_bird_or_segment":bad_fields,
       "rows_bad_date":bad_date,
       "rows_bad_segment_fix_count":bad_fix_count,
       "source_taxa":len({r["species"] for r in result}),
       "source_studies":len({r["studyID"] for r in result}),
       "source_study_species_panels":len(result),
       "candidate_panels_ge10_birds":sum(r["candidate_source_panel"] for r in result),
       "candidate_taxa_ge10_birds":len({r["species"] for r in result if r["candidate_source_panel"]}),
       "panels":result,
       "per_point_RDS_opened":False,
       "native_altitude_read":False,
       "native_altitude_completeness_tested":False,
       "ecological_outcomes_computed":False,
       "limitation":"Only precomputed commuting flight segments; not whole-animal GPS occupancy; flight sampling and individual-day support not yet verified from pointwise native RDS."
    }


def catalog_archive(zip_path):
    source_md5=checksum(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        files=[x for x in zf.infolist()
               if not x.is_dir() and not x.filename.startswith("__MACOSX/")]
        info_seg=find_member(files,SEGMENT_FILE)
        info_point=find_member(files,POINT_FILE)
        with zf.open(info_seg) as inner:
            with io.TextIOWrapper(inner,encoding="utf-8-sig",newline="") as fp:
                result=audit_segments(csv.DictReader(fp))
        result.update({
            "source_doi":"10.5281/zenodo.21915776",
            "source_zip_md5":source_md5,
            "source_zip_bytes":zip_path.stat().st_size,
            "source_segment_member":info_seg.filename,
            "source_perpoint_RDS_member":info_point.filename,
            "source_segment_csv_uncompressed_bytes":info_seg.file_size,
            "source_point_RDS_uncompressed_bytes":info_point.file_size,
            "source_point_RDS_compressed_bytes":info_point.compress_size,
            "archive_members": [{
                "file":p.filename,"bytes_uncompressed":p.file_size,
                "bytes_compressed":p.compress_size,"crc32":f"{p.CRC:08x}"
            } for p in files],
        })
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    data=catalog_archive(a.zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
        "source_studies":data["source_studies"],
        "source_taxa":data["source_taxa"],
        "study_species_panels":data["source_study_species_panels"],
        "candidate_panels":data["candidate_panels_ge10_birds"],
        "candidate_taxa":data["candidate_taxa_ge10_birds"],
        "point_RDS_uncompressed_MB":round(data["source_point_RDS_uncompressed_bytes"]/1e6,1),
        "source_height_read":data["native_altitude_read"]
    },sort_keys=True))


if __name__=="__main__":
    main()
