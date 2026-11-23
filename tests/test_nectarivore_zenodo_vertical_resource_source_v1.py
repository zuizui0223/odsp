import io
import unittest
from zipfile import ZipFile
from scripts import nectarivore_zenodo_vertical_resource_source_v1 as s

def toy_workbook():
    mem=io.BytesIO()
    with ZipFile(mem,"w") as z:
        z.writestr("xl/workbook.xml",
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
          ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml",
          '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<si><t>Plant ID</t></si><si><t>Forest stratum</t></si></sst>')
        z.writestr("xl/worksheets/sheet1.xml",
          '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<dimension ref="A1:C3"/><sheetData><row r="1">'
          '<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
          '<c r="C1"><v>983765.2</v></c></row><row r="2">'
          '<c r="A2" t="s"><v>0</v></c><c r="C2"><v>123456.78</v></c>'
          '</row></sheetData></worksheet>')
    return mem.getvalue()

class OriginalWorkbookSourceTests(unittest.TestCase):
    def test_only_first_row_source_text_and_no_numeric_response(self):
        report=s.original_workbook_structure(toy_workbook())
        self.assertEqual(report["number_of_sheets"],1)
        tab=report["worksheets"][0]
        self.assertEqual(tab["worksheet_dimension_declared"],"A1:C3")
        self.assertEqual(tab["physical_xml_rows"],2)
        self.assertEqual([x["header_text"] for x in tab["first_row_text_labels_only"]],
                         ["Plant ID","Forest stratum"])
        self.assertNotIn("123456.78",str(report))
        self.assertNotIn("983765.2",str(report))
        self.assertFalse(report["biological_numeric_response_opened"])

    def test_wrong_format_fails(self):
        with self.assertRaises(ValueError):
            s.original_workbook_structure(b"not-an-xlsx")

if __name__=="__main__":
    unittest.main()
