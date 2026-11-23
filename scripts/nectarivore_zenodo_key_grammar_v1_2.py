#!/usr/bin/env python3
"""Author source ID/effort grammar ONLY, after source-pairing scientific HOLD.

No animal/nectar response columns are read. Prints source plant ID strings
and original Explanation text, not ecological effects.
"""
from __future__ import annotations
from collections import Counter
import hashlib, io, json, posixpath, re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from scripts.nectarivore_zenodo_source_v1_1_pairs import original_files

RECORD="10527420"
META={
  "CameraTraps.xlsx":"473bb5273b8f2e5369b4bfca0385b829",
  "Nectar measurements_Strata.xlsx":"85e2a40e1a61421e19f86219fff87f9a",
  "Mist-netting_bats.xlsx":"777acca28e0f59fc0103aac35daef92a",
}
NAMESPACE="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS={"m":NAMESPACE}


def explanation_text(data:bytes):
    with ZipFile(io.BytesIO(data)) as z:
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        relationships=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        linked={rel.attrib.get("Id"):rel.attrib.get("Target") for rel in relationships}
        matches=[s for s in workbook.findall(".//m:sheet",NS)
                 if s.attrib.get("name")=="Explanation"]
        if len(matches)!=1:raise RuntimeError("Explanation source sheet missing")
        rid=matches[0].attrib.get("{"+RELS+"}id")
        raw=linked[rid]
        path=raw.lstrip("/") if raw.startswith("/") else posixpath.normpath(posixpath.join("xl",raw))
        if not path.startswith("xl/worksheets/"):raise RuntimeError("Explanation target invalid")
        root=ET.fromstring(z.read(path))
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            doc=ET.fromstring(z.read("xl/sharedStrings.xml"))
            strings=["".join(t.text or "" for t in si.findall(".//m:t",NS))
                     for si in doc.findall("m:si",NS)]
        field_explanations=[]
        rows=root.findall(".//m:sheetData/m:row",NS)
        for row in rows[:40]:
            entries=[]
            for c in row.findall("m:c",NS):
                t=c.attrib.get("t")
                desc=None
                if t=="s":
                    v=c.find("m:v",NS)
                    index=int(v.text) if v is not None and v.text else -1
                    if not 0<=index<len(strings):raise RuntimeError("bad explanation source string")
                    desc=strings[index]
                elif t=="inlineStr":
                    desc="".join(n.text or "" for n in c.findall(".//m:t",NS))
                # Never read numerical values.
                if desc:
                    entries.append(desc.strip()[:160])
            if entries:
                field_explanations.append(entries[:3])
        return field_explanations[:24]


def normalized_id(v):
    return re.sub(r"[\s_-]+","",str(v)).casefold()


def run():
    tables,files=original_files()
    cam=tables["CameraTraps.xlsx"]
    nectar=tables["Nectar measurements_Strata.xlsx"]
    net=tables["Mist-netting_bats.xlsx"]
    ids={}
    for name,data in (("camera",cam),("nectar",nectar),("mist",net)):
        vals=sorted({r["ML_ID"] for r in data if r.get("ML_ID")})
        ids[name]={"distinct_count":len(vals),"source_id_examples_first20":vals[:20],
                   "source_string_length_histogram":dict(Counter(len(v) for v in vals))}
    normalized_camera={normalized_id(x) for x in
                       (r["ML_ID"] for r in cam) if x}
    normalized_nectar={normalized_id(x) for x in
                       (r["ML_ID"] for r in nectar) if x}
    if len(normalized_camera)<len({r["ML_ID"] for r in cam if r["ML_ID"]}) or len(normalized_nectar)<len({r["ML_ID"] for r in nectar if r["ML_ID"]}):
        collision=True
    else:
        collision=False

    missing_hours=Counter()
    for r in cam:
        if not r["Hours"]:
            missing_hours[(r["Taxa"],r["Stratum"])]+=1
    explanations={}
    for name,expected in META.items():
        url=f"https://zenodo.org/records/{RECORD}/files/{quote(name)}?download=1"
        with urlopen(Request(url,headers={"User-Agent":"odsp-nectarivore-source-id-grammar-v1.2/1.0"}),timeout=120) as resp:
            data=resp.read(120_001)
        if hashlib.md5(data).hexdigest()!=expected:
            raise RuntimeError("original explanation workbook MD5 mismatch")
        explanations[name]=explanation_text(data)

    report={
        "status":"source_key_grammar_review_completed_no_biological_outcomes",
        "original_file_sha256s":{k:v["original_sha256"] for k,v in files.items()},
        "source_plant_ID_samples":ids,
        "simple_case_whitespace_hyphen_removed_ID_overlap":len(normalized_camera & normalized_nectar),
        "simple_key_normalization_has_duplicate_collisions":collision,
        "missing_camera_Hours_by_taxon_and_stratum":[
            {"taxon":t,"stratum":s,"missing_hours_rows":n}
            for(t,s),n in sorted(missing_hours.items())
        ],
        "nectar_metadata_year_labels":sorted({r["Year"] for r in nectar if r.get("Year")}),
        "original_author_explanation_text":explanations,
        "original_visit_counts_nectar_quantities_species_capture_frequencies_opened":False,
        "plant_pairs_model_not_authorized":True,
    }
    return report


def main():
    path=Path("results/nectarivore_zenodo_key_grammar_v1_2.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        report=run()
    except Exception as e:
        report={"status":"source_ID_diagnosis_access_or_grammar_stop",
                "reason":str(e)[:350],"exception":type(e).__name__,
                "original_visit_counts_nectar_quantities_species_capture_frequencies_opened":False}
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
