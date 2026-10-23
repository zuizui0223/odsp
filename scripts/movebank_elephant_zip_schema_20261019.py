"""Inspect provider-verified elephant source ZIP schema without reading GPS outcomes."""
import csv
import io
import json
import zipfile
from pathlib import Path
import tempfile
from scripts.movebank_native_ecology_20261019 import original_files, checksum_and_download, HERE

P=HERE/"research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"
def main():
    c=json.loads(P.read_text())
    src=next(x for x in c["sources"] if x["label"]=="etosha_elephant")
    files=original_files(src["package_uuid"])
    match=[x for x in files if x["bitstream_uuid"]==src["provider_original_bitstream_uuid"]]
    if len(match)!=1 or match[0]["checksum"]["value"]!=src["provider_original_md5"]:
        raise ValueError("Source MD5/UUID changed")
    with tempfile.TemporaryDirectory() as td:
        zpath=Path(td)/"original.zip"
        receipt=checksum_and_download(match[0],zpath)
        with zipfile.ZipFile(zpath) as z:
            members=[]
            for m in z.infolist():
                if m.is_dir(): continue
                row={"filename":m.filename,"size":m.file_size,"compressed_size":m.compress_size,"crc32":hex(m.CRC)}
                if m.filename.lower().endswith(".csv"):
                    with z.open(m) as f:
                        # Read exactly one CSV header; never open a GPS outcome row.
                        header=f.readline(20000).decode("utf-8-sig",errors="replace").strip()
                    row["csv_header"]=next(csv.reader([header]))
                members.append(row)
        print("SOURCE_ONLY_ELEPHANT_ZIP_SCHEMA "+json.dumps(
            {"source":"Etosha elephant original public Movebank ZIP","provider_verified":receipt,"members":members,
             "statement":"Source metadata and CSV HEADERS ONLY; animal GPS rows and displacement values not accessed"},
            sort_keys=True))
if __name__=="__main__":main()
