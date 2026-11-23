#!/usr/bin/env python3
"""Independent liana×stratum source-category/effort audit, NO response numbers.

Reads only whitelisted source metadata cell columns from three hash-verified
original Zenodo XLSX workbooks. Uses ZIP/XML for static source intake only;
does not edit XLSX, infer response counts, or fit any ecological model.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import hashlib, io, json, math, posixpath, re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

RECORD="10527420"
FILES={
 "CameraTraps.xlsx":("473bb5273b8f2e5369b4bfca0385b829",
   "b96a6c13e6826c284a32457cd680382cd855ad5bf34959e5695b7a2cfae84d1a",
   "Data",("ML_ID","Taxa","Stratum","Hours","Inflorescences")),
 "Mist-netting_bats.xlsx":("777acca28e0f59fc0103aac35daef92a",
   "9c5e402cc7cc6cd95b0e4ab1f5a306b0cc821905cd0ec27c619ca4b6af90b780",
   "Mist-netting",("ML_ID","Type","Species","Net","Height","Feeding_guild")),
 "Nectar measurements_Strata.xlsx":("85e2a40e1a61421e19f86219fff87f9a",
   "29eb9197c9c28b8083c2a646ed5e3389bffa764566a6fdc8c673e6c0f43647cc",
   "Nectar measurements",("ML_ID","Stratum","Year","Height")),
}
M="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS={"m":M}


def column_number(ref):
    chars=re.match(r"^[A-Z]+",ref or "")
    if not chars:raise ValueError("bad source cell coordinate")
    n=0
    for ch in chars.group():n=n*26+(ord(ch)-64)
    return n-1


def read_source_allowed_columns(blob,sheetname,allowed):
    with ZipFile(io.BytesIO(blob)) as zip_:
        workbook=ET.fromstring(zip_.read("xl/workbook.xml"))
        relations=ET.fromstring(zip_.read("xl/_rels/workbook.xml.rels"))
        ids={r.attrib["Id"]:r.attrib.get("Target","") for r in relations}
        named=[e for e in workbook.findall(".//m:sheet",NS)
               if e.attrib.get("name")==sheetname]
        if len(named)!=1:raise ValueError("declared data sheet not unique")
        rid=named[0].attrib.get("{"+R+"}id")
        if rid not in ids:raise ValueError("original sheet relation absent")
        target=ids[rid]
        target=target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl",target))
        if not target.startswith("xl/worksheets/"):
            raise ValueError("unexpected workbook sheet target")
        root=ET.fromstring(zip_.read(target))
        shared=[]
        if "xl/sharedStrings.xml" in zip_.namelist():
            sst=ET.fromstring(zip_.read("xl/sharedStrings.xml"))
            for si in sst.findall("m:si",NS):
                shared.append("".join(t.text or "" for t in si.findall(".//m:t",NS)))

        def value(c):
            typ=c.attrib.get("t","n")
            if typ=="s":
                n=c.find("m:v",NS)
                idx=int(n.text) if n is not None and n.text is not None else -1
                if idx<0 or idx>=len(shared):raise ValueError("source sharedStrings index")
                return shared[idx].strip()
            if typ=="inlineStr":
                return "".join(t.text or "" for t in c.findall(".//m:t",NS)).strip()
            node=c.find("m:v",NS)
            return (node.text or "").strip() if node is not None else ""

        sheet_data=root.find("m:sheetData",NS)
        if sheet_data is None:raise ValueError("source Data worksheet empty")
        rows=sheet_data.findall("m:row",NS)
        if not rows:raise ValueError("no source header row")
        header={column_number(c.attrib["r"]):value(c)
                for c in rows[0].findall("m:c",NS)}
        name_to_col={v:k for k,v in header.items()}
        if len(name_to_col)!=len(header) or not set(allowed).issubset(name_to_col):
            raise ValueError("source name/column structure mismatch")
        keep={name_to_col[f]:f for f in allowed}
        output=[]
        for xmlrow in rows[1:]:
            item={k:"" for k in allowed}
            for c in xmlrow.findall("m:c",NS):
                position=column_number(c.attrib.get("r",""))
                if position in keep:
                    # *Never* access biological response columns: original
                    # Abundance, Capture_rate and nectar quantity/pH/sugar
                    # positions are not in the keep map.
                    item[keep[position]]=value(c)
            if any(item.values()):output.append(item)
        return output


def original_files():
    tables={}
    sources={}
    for name,(md5,sha,sheet,keep) in FILES.items():
        url=f"https://zenodo.org/records/{RECORD}/files/{quote(name)}?download=1"
        with urlopen(Request(url,headers={
            "User-Agent":"odsp-nectar-resource-category-source-v1.1/1.0",
        }),timeout=120) as r:
            data=r.read(120_001)
        if hashlib.md5(data).hexdigest()!=md5 or hashlib.sha256(data).hexdigest()!=sha:
            raise ValueError("original v2 published file digest mismatch")
        sources[name]={"original_md5":md5,"original_sha256":sha,"byte_length":len(data),
                       "allowed_context_columns":list(keep)}
        tables[name]=read_source_allowed_columns(data,sheet,keep)
    return tables,sources


def admitted_source_structure(tables,sources):
    cam=tables["CameraTraps.xlsx"]
    net=tables["Mist-netting_bats.xlsx"]
    nectar=tables["Nectar measurements_Strata.xlsx"]

    def keypairs(rows):
        return {(r["ML_ID"],r["Stratum"]) for r in rows
                if r.get("ML_ID") and r.get("Stratum")}
    cam_pairs=keypairs(cam)
    nectar_pairs=keypairs(nectar)
    common=cam_pairs & nectar_pairs
    by_id=defaultdict(set)
    for plant,stratum in common:by_id[plant].add(stratum)
    paired2=sum(len(strata)>=2 for strata in by_id.values())
    paired3=sum(len(strata)>=3 for strata in by_id.values())
    cam_ids={r["ML_ID"] for r in cam if r["ML_ID"]}
    nectar_ids={r["ML_ID"] for r in nectar if r["ML_ID"]}
    net_ids={r["ML_ID"] for r in net if r["ML_ID"]}
    cam_effort_nonpositive=0
    cam_effort_missing=0
    for row in cam:
        val=row["Hours"]
        try:
            value=float(val)
            if not math.isfinite(value) or value<=0:
                cam_effort_nonpositive+=1
        except (ValueError,TypeError):
            cam_effort_missing+=1
    cam_blank_ids=sum(not r.get("ML_ID") for r in cam)
    nectar_blank_ids=sum(not r.get("ML_ID") for r in nectar)
    cam_taxa=sorted({r["Taxa"] for r in cam if r["Taxa"]})
    cam_strata=sorted({r["Stratum"] for r in cam if r["Stratum"]})
    nec_strata=sorted({r["Stratum"] for r in nectar if r["Stratum"]})
    return {
      "status":"source_plant_level_pairing_and_effort_admitted"
        if paired2>=5 and not(cam_effort_missing or cam_effort_nonpositive or cam_blank_ids or nectar_blank_ids)
        else "source_plant_level_pairing_or_effort_hold",
      "original_files":sources,
      "camera_data_rows":len(cam),
      "bat_net_data_rows":len(net),
      "nectar_data_rows":len(nectar),
      "camera_taxon_labels":cam_taxa,
      "camera_stratum_labels":cam_strata,
      "nectar_stratum_labels":nec_strata,
      "camera_distinct_plant_ids":len(cam_ids),
      "nectar_distinct_plant_ids":len(nectar_ids),
      "mistnet_distinct_plant_or_site_ids":len(net_ids),
      "plant_IDs_shared_between_visits_and_nectar":len(cam_ids & nectar_ids),
      "paired_visit_nectar_exact_ID_stratum_units":len(common),
      "paired_visit_nectar_plant_IDs":len(by_id),
      "paired_plant_IDs_with_ge2_strata":paired2,
      "paired_plant_IDs_with_ge3_strata":paired3,
      "camera_site_stratum_source_units":len(cam_pairs),
      "nectar_site_stratum_source_units":len(nectar_pairs),
      "missing_camera_plant_IDs":cam_blank_ids,
      "missing_nectar_plant_IDs":nectar_blank_ids,
      "missing_camera_Hours_exposure":cam_effort_missing,
      "nonpositive_camera_Hours_exposure":cam_effort_nonpositive,
      "response_Abundance_or_Capture_rate_or_nectar_values_opened":False,
      "no_causal_resource_or_species_niche_effect_tested":True,
    }


def main():
    report={"status":"source_access_or_schema_stop",
            "response_Abundance_or_Capture_rate_or_nectar_values_opened":False}
    try:
        tables,sources=original_files()
        report=admitted_source_structure(tables,sources)
    except Exception as err:
        report["exception"]=type(err).__name__
        report["reason"]=str(err)[:400]
    path=Path("results/nectarivore_zenodo_source_v1_1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
