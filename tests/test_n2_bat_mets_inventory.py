from scripts.n2_bat_mets_inventory import parse_mets_inventory


def test_parse_mets_inventory_lists_files_without_content():
    xml = b'''<?xml version="1.0"?>
    <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink">
      <mets:fileSec>
        <mets:fileGrp USE="CONTENT">
          <mets:file ID="f1" MIMETYPE="text/csv" SIZE="123" CHECKSUM="abc" CHECKSUMTYPE="MD5">
            <mets:FLocat LOCTYPE="URL" xlink:href="https://example.org/bitstream/handle/x/events.csv?sequence=1"/>
          </mets:file>
        </mets:fileGrp>
      </mets:fileSec>
    </mets:mets>'''
    files = parse_mets_inventory(xml)
    assert files == [{
        "file_group_use": "CONTENT",
        "file_id": "f1",
        "mime_type": "text/csv",
        "size_bytes": 123,
        "checksum": "abc",
        "checksum_type": "MD5",
        "loctype": "URL",
        "href": "https://example.org/bitstream/handle/x/events.csv?sequence=1",
        "filename": "events.csv",
    }]
    assert "content" not in files[0]
