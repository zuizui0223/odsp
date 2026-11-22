import unittest
import xml.etree.ElementTree as ET

from scripts import froidevaux2014_pmc_oai_table_v2 as source


def mock_oai(body):
    return ("""<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
    <GetRecord><record><metadata>"""
    + body +
    """</metadata></record></GetRecord></OAI-PMH>""").encode()


class PMCSourceV2Tests(unittest.TestCase):
    def test_extracts_one_original_fulltext_not_metadata_only(self):
        orig=mock_oai('<article><front><article-meta><article-id pub-id-type="doi">'
          '10.1002/ece3.1296</article-id></article-meta></front>'
          '<body><table-wrap><caption><p>Test</p></caption></table-wrap></body></article>')
        parsed=source.extract_jats(orig)
        root=ET.fromstring(parsed)
        self.assertEqual(root.tag,"article")
        self.assertEqual(root.find(".//article-id").text,"10.1002/ece3.1296")
        self.assertEqual(len(root.findall(".//table-wrap")),1)

    def test_oai_error_stops_without_source_response(self):
        orig=b'<OAI-PMH><error code="cannotDisseminateFormat">not accessible</error></OAI-PMH>'
        with self.assertRaisesRegex(RuntimeError,"OAI"):
            source.extract_jats(orig)

    def test_wrong_original_doi_stops(self):
        orig=mock_oai('<article><front><article-meta><article-id pub-id-type="doi">'
          '10.1002/not-the-froidevaux-article</article-id></article-meta></front></article>')
        with self.assertRaisesRegex(RuntimeError,"DOI"):
            source.extract_jats(orig)

    def test_no_full_article_stops(self):
        orig=mock_oai('<journal-meta><publisher-name>Publisher</publisher-name></journal-meta>')
        with self.assertRaisesRegex(RuntimeError,"JATS"):
            source.extract_jats(orig)


if __name__=="__main__":
    unittest.main()
