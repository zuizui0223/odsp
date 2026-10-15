#!/usr/bin/env python3
"""Inspect PUBLIC Zenodo journal supplementary table, never original EcoBank ZIP.

Source is Jeon & Lim (2026) Supplementary material 3, not the original
station×timestamp×hour operation data. Print only safe aggregate TSV cells
after checking the Zenodo-provided MD5 and guarding against location leaks.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
import re
import urllib.request
from urllib.parse import urlparse
from zipfile import ZipFile, is_zipfile
import argparse

DOI = "10.3897/BDJ.14.e191556.suppl3"
RECORD_URL = "https://zenodo.org/records/21319408"
ZIP_URL = RECORD_URL + "/files/oo_1559451.zip?download=1"
ZENODO_MD5 = "085afc8382ae5668edfa8ad74122a68e"
MAX_ZIP_BYTES = 2_000_000
MAX_UNCOMPRESSED_BYTES = 10_000_000
MAX_ROWS = 250
MAX_COLS = 30
SENSITIVE = re.compile(r"(^|[ _-])(lat|latitude|lon|long|longitude|utm|gps|coord|easting|northing|station|siteid|cameraid|grid|address|location)([ _-]|$)", re.I)
TAXA = ("Goral", "Water deer", "Roe deer", "Wild boar")


def verified_zip_members(raw: bytes) -> tuple[list[dict], list[dict]]:
    checksum = hashlib.md5(raw).hexdigest()
    if checksum != ZENODO_MD5:
        raise ValueError("HOLD_PUBLISHED_ZENODO_MD5_MISMATCH")
    if not is_zipfile(io.BytesIO(raw)):
        raise ValueError("HOLD_NOT_ZIP")
    inventory = []
    datasets = []
    with ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)):
            raise ValueError("HOLD_DUPLICATE_ZIP_PATHS")
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("HOLD_PUBLISHED_ZIP_TOO_LARGE")
        for info in infos:
            name = info.filename
            if name.startswith(("/", "\\")) or "\\" in name or ".." in name.split("/"):
                raise ValueError("HOLD_UNSAFE_ZIP_PATH")
            if not name.endswith("/"):
                inventory.append({"member_name":name, "bytes":info.file_size, "suffix":name.rsplit(".",1)[-1].lower()})
            if not name.lower().endswith((".tsv", ".csv")):
                continue
            try:
                content = z.read(info).decode("utf-8-sig")
            except UnicodeError as err:
                raise ValueError("HOLD_AGGREGATE_TABLE_ENCODING") from err
            delimiter = "\t" if name.lower().endswith(".tsv") else ","
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            cols = reader.fieldnames or []
            if not cols or len(cols) > MAX_COLS or len(cols) != len(set(cols)):
                raise ValueError("HOLD_UNEXPECTED_PUBLISHED_TSV_HEADERS")
            rows = list(reader)
            if len(rows) > MAX_ROWS or any(None in x for x in rows):
                raise ValueError("HOLD_UNEXPECTED_PUBLISHED_TABLE_GRAIN")
            if any(SENSITIVE.search(h) for h in cols):
                datasets.append({"member_name":name,"status":"HOLD_GEO_OR_STATION_IDENTIFIERS",
                                 "columns":cols,"row_count":len(rows),"rows":None})
            else:
                datasets.append({"member_name":name,"status":"PUBLISHED_AGGREGATE_TABLE_ONLY",
                                 "columns":cols,"row_count":len(rows),"rows":rows})
    return inventory, datasets


def inspect(raw: bytes) -> dict:
    inventory,tables=verified_zip_members(raw)
    return {
        "status":"VERIFIED_ZENODO_SUPPL3_NOT_ECOBANK_ORIGINAL",
        "original_source_2022_41_pairs_loaded":False,
        "original_source_operating_hours_loaded":False,
        "new_biological_hypothesis_tested":False,
        "public_supplement_doi":DOI,
        "public_zenodo_record":RECORD_URL,
        "zenodo_published_md5_matches":True,
        "supplement_zip_sha256":hashlib.sha256(raw).hexdigest(),
        "members":inventory,
        "tables":tables,
        "warning":"Only whole-period published summary. Station-level, seasonal and source event/effort records NOT present or inferred."
    }


def download() -> bytes:
    request = urllib.request.Request(ZIP_URL,headers={"User-Agent":"ODSP ecological published aggregate reproducibility/1.0","Accept":"application/zip"})
    with urllib.request.urlopen(request,timeout=35) as f:
        final=urlparse(f.geturl())
        if final.scheme!="https" or not (final.hostname=="zenodo.org" or final.hostname.endswith(".zenodo.org")):
            raise ValueError("HOLD_ZENODO_UNEXPECTED_REDIRECT")
        data=f.read(MAX_ZIP_BYTES+1)
    if len(data)>MAX_ZIP_BYTES:
        raise ValueError("HOLD_ZENODO_DOWNLOAD_OVERSIZED")
    return data


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--offline-zip",help="Inspect a separately fetched original published SUPPLEMENT 3 ZIP, not EcoBank event records")
    args=p.parse_args()
    try:
        raw=open(args.offline_zip,"rb").read(MAX_ZIP_BYTES+1) if args.offline_zip else download()
        result=inspect(raw)
    except Exception as error:
        # Avoid printing private URLs, untrusted server text, tokens, or local path.
        result={
            "status":"HOLD_ZENODO_SUPPL3_NOT_VERIFIED",
            "error_class":type(error).__name__,
            "source_member_reads":False,
            "biological_effect_computed":False,
        }
    print(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
