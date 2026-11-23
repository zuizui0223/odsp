#!/usr/bin/env python3
"""Source-only original Zenodo XLSX sheet/header admission via stdlib ZIP/XML.

Reads sheet labels and the TEXT cells in the first row. Never reads numeric
visit, nectar, or capture responses, and never edits a workbook.
"""
from __future__ import annotations
import hashlib, io, json, posixpath
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

RECORD="10527420"
SOURCE_DOI="10.5281/zenodo.10527420"
FILES={
    "CameraTraps.xlsx":"473bb5273b8f2e5369b4bfca0385b829",
    "Mist-netting_bats.xlsx":"777acca28e0f59fc0103aac35daef92a",
    "Nectar measurements_Strata.xlsx":"85e2a40e1a61421e19f86219fff87f9a",
}
NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
BYTES_MAX=120_000

def original_workbook_structure(data:bytes)->dict:
    with ZipFile(io.BytesIO(data)) as z:
        names=set(z.namelist())
        if not {"xl/workbook.xml","xl/_rels/workbook.xml.rels"}.issubset(names):
            raise ValueError("file is not a source XLSX workbook")
        root=ET.fromstring(z.read("xl/workbook.xml"))
        relroot=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap={}
        for rel in relroot:
            target=rel.attrib.get("Target","")
            id_=rel.attrib.get("Id")
            if id_ and target:relmap[id_]=target
        shared=[]
        if "xl/sharedStrings.xml" in names:
            strings=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in strings.findall("m:si",NS):
                shared.append("".join(n.text or "" for n in si.findall(".//m:t",NS)))
        sheets=[]
        for se in root.findall("m:sheets/m:sheet",NS):
            name=se.attrib.get("name","")
            rid=se.attrib.get("{"+NS["r"]+"}id")
            if not name or not rid or rid not in relmap:
                raise ValueError("source sheet metadata missing")
            target=relmap[rid]
            if target.startswith("/"):target=target.lstrip("/")
            else:target=posixpath.normpath(posixpath.join("xl",target))
            if not target.startswith("xl/worksheets/") or target not in names:
                raise ValueError("source sheet target outside expected folder")
            tree=ET.fromstring(z.read(target))
            dim=tree.find("m:dimension",NS)
            dimension=dim.attrib.get("ref") if dim is not None else None
            data_node=tree.find("m:sheetData",NS)
            if data_node is None:raise ValueError("missing source sheetData")
            nrows=len(data_node.findall("m:row",NS))
            first=data_node.find("m:row",NS)
            labels=[]
            if first is not None:
                for c in first.findall("m:c",NS):
                    ref=c.attrib.get("r","")
                    typ=c.attrib.get("t")
                    label=None
                    if typ=="s":
                        v=c.find("m:v",NS)
                        idx=int(v.text) if v is not None and v.text is not None else -1
                        if idx<0 or idx>=len(shared):
                            raise ValueError("bad shared string index")
                        label=shared[idx]
                    elif typ=="inlineStr":
                        label="".join(x.text or "" for x in c.findall(".//m:t",NS))
                    # Numeric cells are not accessed, even in first row.
                    if label is not None:
                        labels.append({"cell":ref,"header_text":label[:150]})
            sheets.append({"sheet_name":name,
                "worksheet_dimension_declared":dimension,
                "physical_xml_rows":nrows,
                "first_row_text_labels_only":labels,
                "original_numeric_cells_opened":False})
        return {"worksheets":sheets,"number_of_sheets":len(sheets),
                "biological_numeric_response_opened":False}

def run():
    receipt={
        "source_doi":SOURCE_DOI,"original_record":"https://zenodo.org/records/"+RECORD,
        "original_numeric_visit_or_nectar_values_opened":False,
        "original_values_imported_for_analysis":False,
        "files":{},
    }
    for name,md5 in FILES.items():
        try:
            url=f"https://zenodo.org/records/{RECORD}/files/{quote(name)}?download=1"
            req=Request(url,headers={"User-Agent":"odsp-original-zenodo-nectar-metadata-v1/1.0"})
            with urlopen(req,timeout=120) as r:
                data=r.read(BYTES_MAX+1)
            if not 0<len(data)<=BYTES_MAX:
                raise ValueError("original file byte cap/empty source")
            actual=hashlib.md5(data).hexdigest()
            if actual!=md5:
                raise ValueError(f"original published MD5 mismatch: {actual}")
            receipt["files"][name]={
                "status":"source_header_metadata_pass",
                "expected_original_md5":md5,
                "file_sha256":hashlib.sha256(data).hexdigest(),
                "file_bytes":len(data),
                **original_workbook_structure(data)}
        except Exception as exc:
            receipt["files"][name]={
                "status":"source_access_or_workbook_stop",
                "exception":type(exc).__name__,
                "reason":str(exc)[:300],
                "original_numeric_cells_opened":False}
    receipt["status"]=(
        "three_original_workbooks_header_only_admitted"
        if all(x["status"]=="source_header_metadata_pass"
               for x in receipt["files"].values())
        else "one_or_more_original_source_access_or_structure_stop")
    return receipt

def main():
    result=run()
    p=Path("results/nectarivore_zenodo_source_v1.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
