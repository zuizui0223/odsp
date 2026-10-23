"""Source-only public Utah 4-taxon original Movebank ZIP metadata probe."""
import csv,json,tempfile
from pathlib import Path
from zipfile import ZipFile
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
PACKAGE="0043246e-e68c-4b76-84cc-31e7558d08e0"
BITSTREAM="9c4aaf76-7476-4305-8b14-9a6d8886e39a"
MD5="08200c9dbdf7989fb5a35467213b7e5a"
def main():
    x=[f for f in original_files(PACKAGE) if f["bitstream_uuid"]==BITSTREAM]
    if len(x)!=1 or x[0]["checksum"]["value"].lower()!=MD5:
        raise ValueError("Provider original MD5 changed")
    with tempfile.TemporaryDirectory() as p:
        path=Path(p)/"original.zip"
        source=checksum_and_download(x[0],path)
        with ZipFile(path) as z:
            members=[]
            for m in z.infolist():
                if m.is_dir():continue
                row={"filename":m.filename,"uncompressed_bytes":m.file_size,"compressed_bytes":m.compress_size}
                if m.filename.endswith(".csv") and not m.filename.startswith("__MACOSX/"):
                    with z.open(m) as f:
                        header=f.readline(30000).decode("utf-8-sig",errors="replace").strip()
                    row["fields"]=next(csv.reader([header]))
                members.append(row)
        print("UTAH_ORIGINAL_SOURCE_SCHEMA "+json.dumps({
            "source":"Published multi-taxon Utah ungulate GPS package",
            "original_provider_md5_verified":source,"members":members,
            "limitation":"Only archive member metadata and CSV header were inspected; NO animal movement outcome opened"
        },sort_keys=True))
if __name__=="__main__":main()
