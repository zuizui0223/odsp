#!/usr/bin/env python3
"""Inspect real published solar-time sensitivity overlap TSV/CSV, not original animal events.

Jeon & Lim (2026), Supplementary material 2. Zero requests to EcoBank
provider source/camera metadata. Print aggregate pairwise table only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

ZIP_URL="https://zenodo.org/records/21319406/files/oo_1559453.zip?download=1"
MD5="466ae68374ea02803653883466bfe77d"
SOURCE="10.3897/BDJ.14.e191556.suppl2"
MAX_ZIP=1_000_000
MAX_UNZIPPED=20_000_000
PROTECTED=re.compile(r"(?:lat|longitude|utm|gps|coordinates|station|site_id|address|location)",re.I)


def analyze(raw:bytes)->dict:
    if hashlib.md5(raw).hexdigest()!=MD5:
        raise ValueError("HOLD_SUPPLEMENT2_ZENODO_HASH_MISMATCH")
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("HOLD_SUPPLEMENT2_NOT_ZIP")
    inventory=[]
    tables=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist()
        paths=[i.filename for i in entries]
        if len(paths)!=len(set(paths)) or any(
            x.startswith(("/", "\\")) or "\\" in x or ".." in x.split("/") for x in paths
        ):
            raise ValueError("HOLD_SUPPLEMENT2_UNSAFE_PATH")
        if sum(i.file_size for i in entries)>MAX_UNZIPPED:
            raise ValueError("HOLD_SUPPLEMENT2_OVERSIZED")
        for info in entries:
            filename=info.filename
            if filename.endswith("/"):
                continue
            inventory.append({"name":filename,"bytes":info.file_size})
            if not filename.lower().endswith((".csv",".tsv")):
                continue
            try:
                data=z.read(info).decode("utf-8-sig")
            except UnicodeError as err:
                raise ValueError("HOLD_SUPPLEMENT2_ENCODING") from err
            sep="\t" if filename.lower().endswith(".tsv") else ","
            table=csv.DictReader(io.StringIO(data),delimiter=sep)
            fields=table.fieldnames or []
            rows=list(table)
            if not fields or len(fields)>25 or len(rows)>100 or any(None in r for r in rows):
                raise ValueError("HOLD_SUPPLEMENT2_AGGREGATE_GRAIN")
            if any(PROTECTED.search(f) for f in fields):
                tables.append({"member":filename,"columns":fields,"rows":None,"status":"HOLD_SENSITIVE_SOURCE_FIELD"})
            else:
                tables.append({"member":filename,"columns":fields,"rows":rows,"status":"PUB_AGGREGATE_TABLE","row_count":len(rows)})
    return {
        "status":"SOURCE_VERIFIED_PUBLISHED_SOLAR_TIME_AGGREGATE_ONLY",
        "source_doi":SOURCE,
        "zenodo_checksum_matched":True,
        "archive_sha256":hashlib.sha256(raw).hexdigest(),
        "inventory":inventory,
        "tables":tables,
        "original_EcoBank_event_and_operating_hours_read":False,
        "original_41_mirror_dates_tested":False,
        "independent_replication_claimed":False
    }


def main()->None:
    request=Request(ZIP_URL,headers={"User-Agent":"ODSP ecological public journal supplement QC/1.0"})
    try:
        with urlopen(request,timeout=30) as res:
            end=urlparse(res.geturl())
            if end.scheme!="https" or not (end.hostname=="zenodo.org" or end.hostname.endswith(".zenodo.org")):
                raise ValueError("HOLD_SUPPLEMENT2_CROSS_HOST")
            raw=res.read(MAX_ZIP+1)
        if len(raw)>MAX_ZIP:
            raise ValueError("HOLD_SUPPLEMENT2_MAX_BYTES")
        result=analyze(raw)
    except Exception as e:
        result={"status":"HOLD_SUPPLEMENT2_NOT_CHECKED","error_class":type(e).__name__,
                "original_EcoBank_event_and_operating_hours_read":False}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
