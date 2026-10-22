#!/usr/bin/env python3
"""Original public French Gyps GPS ZIP: source ledger, headers only.

The entire 2019-2021 archived GPS bundle is verified by official md5, but
NO altitude value, missingness or per-bird outcome is opened. Files are
classified from official ZIP central directory and CSV HEADERS only.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from pathlib import Path

SOURCE_NAME="windTurbineAvoidance.zip"
EXPECTED_MD5="b18cc8004d311d19ff24060f655178bf"
EXPECTED_BYTES=1093170227
DOI="10.48579/PRO/IOSZNM"

def check_source(path):
    if path.name!=SOURCE_NAME or path.stat().st_size!=EXPECTED_BYTES:
        raise ValueError("Source archive name/byte size changed")
    h=hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    if h.hexdigest()!=EXPECTED_MD5:
        raise ValueError("Original archive MD5 mismatch")
    return h.hexdigest()

def detect_fields(header):
    names=[str(z).strip() for z in header]
    lower=[z.lower() for z in names]
    def matched(parts):
        return [col for col,lo in zip(names,lower) if
                any(p in lo for p in parts)]
    timestamp=matched(("timestamp","datetime","date.time","date_time","time.utc","gps.time"))
    longitude=matched(("longitude","location.long","lon","utm.x","coord_x","easting"))
    latitude=matched(("latitude","location.lat","lat","utm.y","coord_y","northing"))
    animal=matched(("animal-id","animal.id","individual","bird","tag-id","tag.id","taglocal","id"))
    height=matched(("height","altitude","alt.msl","alt.ellipsoid","agl"))
    speed=matched(("speed","velocity","ground.speed"))
    return {
        "columns":names,
        "timestamp_columns":timestamp,
        "longitude_columns":longitude,
        "latitude_columns":latitude,
        "animal_or_tag_columns":animal,
        "height_column_names_only":height,
        "speed_column_names_only":speed,
        "could_support_native_3d_tracking":bool(timestamp and longitude and latitude and height),
        "numeric_native_height_values_opened":False
    }

def inspect_archive(path):
    digest=check_source(path)
    meta=[]
    with zipfile.ZipFile(path) as archive:
        # Full-file MD5 is checked first; avoid unnecessarily decoding every 1GB
        # compressed member just to inspect the source directory/header.
        members=[i for i in archive.infolist() if not i.is_dir()
                 and not i.filename.startswith("__MACOSX/")
                 and not i.filename.rsplit("/",1)[-1].startswith("._")]
        for info in members:
            item={
                "filename":info.filename,
                "uncompressed_bytes":info.file_size,
                "compressed_bytes":info.compress_size,
                "CRC32":f"{info.CRC:08x}",
                "is_csv":info.filename.lower().endswith((".csv",".tsv",".txt")),
                "encrypted":bool(info.flag_bits & 1)
            }
            if item["encrypted"]:
                item["header_read_status"]="ENCRYPTED_UNAVAILABLE"
            elif info.filename.lower().endswith((".csv",".tsv")):
                with archive.open(info) as raw:
                    stream=io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline="")
                    try:
                        firstline=stream.readline()
                        delimiter=max((",",";","\t"),key=lambda sep:firstline.count(sep))
                        line=next(csv.reader([firstline],delimiter=delimiter))
                    except StopIteration:line=[]
                    item["data_columns"]=detect_fields(line)
                    item["header_read_status"]="HEADER_ONLY"
            else:
                item["header_read_status"]="NOT_CSV"
            meta.append(item)

    usable=[m for m in meta if m.get("data_columns",{}).get("could_support_native_3d_tracking")]
    gps_like=[m for m in meta if
              m.get("data_columns",{}).get("timestamp_columns") and
              m.get("data_columns",{}).get("longitude_columns") and
              m.get("data_columns",{}).get("latitude_columns")]
    return {
        "analysis":"FRANCE_GRIFFON_2019_2021_ORIGINAL_ZIP_HEADERS_V1",
        "stage":"ORIGINAL_PUBLIC_DATA_ARCHIVE_HEADERS_ONLY_PREHEIGHT",
        "source_DOI":DOI,"source_md5":digest,
        "original_archive_bytes":path.stat().st_size,
        "study_name":"Eurasian griffon vulture in France ID_PROG 961",
        "reported_original_tracking_years":[2019,2020,2021],
        "total_archived_nonMAC_files":len(meta),
        "potential_GPS_x_y_timestamp_CSVs":len(gps_like),
        "potential_GPS_x_y_height_CSVs":len(usable),
        "source_files":meta,
        "animal_specific_altitude_value_read":False,
        "native_altitude_missingness_checked":False,
        "individual_eligibility_computed":False,
        "reanalysis_of_original_wind_turbine_avoidance":False,
        "boundary":"ZIP CSV headers and member identities only. Native height field existence does NOT confirm useable animal/day/flight data or independence from already analysed Movebank study parents."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=inspect_archive(args.source)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_md5":out["source_md5"],
        "archived_files":out["total_archived_nonMAC_files"],
        "gps_xytime_files":out["potential_GPS_x_y_timestamp_CSVs"],
        "gps_xytime_height_files":out["potential_GPS_x_y_height_CSVs"],
        "numeric_height_opened":False
    },sort_keys=True))

if __name__=="__main__":
    main()
