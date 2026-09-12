#!/usr/bin/env python3
"""Fail-closed structural validation for the N2 MEE anonymous review DOCX."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DC = "http://purl.org/dc/elements/1.1/"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NS = {"w": W, "dc": DC, "cp": CP}
Q = lambda local: f"{{{W}}}{local}"
TITLE = "State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions"


def _read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError as exc:
        raise AssertionError(f"required DOCX part missing: {name}") from exc


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def _page_field_paragraphs(archive: zipfile.ZipFile, footer_names: list[str]) -> list[ET.Element]:
    paragraphs: list[ET.Element] = []
    for name in footer_names:
        footer = _read_xml(archive, name)
        for paragraph in footer.findall(".//w:p", NS):
            instructions = "".join(node.text or "" for node in paragraph.findall(".//w:instrText", NS))
            if "PAGE" in instructions:
                paragraphs.append(paragraph)
    return paragraphs


def validate(docx_path: Path) -> dict[str, object]:
    if not docx_path.exists():
        raise FileNotFoundError(docx_path)

    checks: dict[str, bool] = {}
    with zipfile.ZipFile(docx_path) as archive:
        names = set(archive.namelist())
        checks["valid_docx_zip"] = True
        checks["document_xml_present"] = "word/document.xml" in names
        checks["styles_xml_present"] = "word/styles.xml" in names
        checks["core_xml_present"] = "docProps/core.xml" in names

        document = _read_xml(archive, "word/document.xml")
        paragraphs = document.findall(".//w:body//w:p", NS)
        nonempty = [p for p in paragraphs if _paragraph_text(p)]
        double_spaced = []
        for paragraph in nonempty:
            spacing = paragraph.find("./w:pPr/w:spacing", NS)
            double_spaced.append(
                spacing is not None
                and spacing.get(Q("line")) == "480"
                and spacing.get(Q("lineRule"), "auto") == "auto"
            )
        checks["all_nonempty_main_paragraphs_double_spaced"] = bool(nonempty) and all(double_spaced)

        sections = document.findall(".//w:sectPr", NS)
        checks["section_present"] = bool(sections)
        checks["continuous_line_numbering"] = bool(sections) and all(
            (ln := section.find("./w:lnNumType", NS)) is not None
            and ln.get(Q("countBy")) == "1"
            and ln.get(Q("restart")) == "continuous"
            for section in sections
        )
        checks["single_column"] = bool(sections) and all(
            (cols := section.find("./w:cols", NS)) is not None
            and cols.get(Q("num")) == "1"
            for section in sections
        )

        footer_names = sorted(name for name in names if name.startswith("word/footer") and name.endswith(".xml"))
        page_paragraphs = _page_field_paragraphs(archive, footer_names)
        checks["page_number_field_present"] = bool(page_paragraphs)
        checks["page_number_paragraph_suppresses_line_numbering"] = bool(page_paragraphs) and all(
            paragraph.find("./w:pPr/w:suppressLineNumbers", NS) is not None
            for paragraph in page_paragraphs
        )

        core = _read_xml(archive, "docProps/core.xml")
        creator = core.find("dc:creator", NS)
        modified = core.find("cp:lastModifiedBy", NS)
        checks["author_metadata_blank"] = (creator is None or not (creator.text or "").strip()) and (
            modified is None or not (modified.text or "").strip()
        )

        text = "\n".join(_paragraph_text(p) for p in paragraphs)
        checks["manuscript_title_present"] = TITLE in text
        checks["numbered_abstract_parts_present"] = all(f"{number}." in text for number in range(1, 5))
        checks["peer_review_data_code_section_present"] = "Data and code for peer review" in text
        checks["author_placeholders_absent"] = "[AUTHOR" not in text and "[CORRESPONDING AUTHOR" not in text

    failed = [name for name, passed in checks.items() if not passed]
    result = {
        "schema_version": 1,
        "docx": docx_path.as_posix(),
        "checks": checks,
        "passed": not failed,
        "failed_checks": failed,
        "nonempty_main_paragraph_count": len(nonempty),
    }
    if failed:
        raise AssertionError("DOCX validation failed: " + ", ".join(failed))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()
    result = validate(args.docx)
    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
