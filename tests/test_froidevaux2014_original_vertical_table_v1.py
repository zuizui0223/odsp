import math
import unittest
from unittest.mock import patch
from scripts import froidevaux2014_original_vertical_table_v1 as m

class FroidevauxPublishedTableTests(unittest.TestCase):
    def test_known_truth_binary_information(self):
        r=m.metrics([(90,10),(10,90)])
        target=math.log(2)+.9*math.log(.9)+.1*math.log(.1)
        self.assertAlmostEqual(r["observed_label_stratum_information_nats"],target,places=12)
        self.assertAlmostEqual(r["observed_recording_stratum_entropy_nats"],math.log(2),places=12)
        self.assertEqual(r["ground_plus_canopy_sequences"],200)
        self.assertLess(r["independent_information_identity_reconciliation_abs"],1e-12)

    def test_uniform_stratum_distribution_no_label_information(self):
        r=m.metrics([(10,20),(30,60),(5,10)])
        self.assertAlmostEqual(r["observed_label_stratum_information_nats"],0,places=12)
        self.assertAlmostEqual(r["observed_label_information_fraction_of_stratum_entropy"],0,places=12)

    def test_source_table_parser_metadata_gates(self):
        rows=[
          ["Alpha alpha","MRE","9","90.0","4","40.0","2","20.0","15","100.0"],
          ["Pipistrellus pipistrellus","SRE","1","10.0","6","60.0","8","80.0","15","100.0"],
        ]
        def line(values):
            return "<tr>"+"".join(f"<td>{v}</td>" for v in values)+"</tr>"
        xml=("<article><body><table-wrap><label>Table 1</label>"
             "<caption><p>Number of sequences per bat species recorded in each microhabitat</p></caption>"
             "<table><tbody>"+"".join(line(row) for row in rows)+
             line(["Total","","10","","10","","10","","30",""])+
             "</tbody></table></table-wrap></body></article>").encode()
        with (patch.object(m,"EXPECTED_ROWS",2),
              patch.object(m,"EXPECTED_SUMS",{"gap":10,"ground":10,"canopy":10}),
              patch.object(m,"EXPECTED_ALL",30)):
            table,summary=m.parse_primary_table(xml)
        self.assertEqual(len(table),2)
        self.assertEqual(table[0]["ground"],4)
        self.assertEqual(table[1]["canopy"],8)
        self.assertTrue(summary["total_source_row_was_detected"])

    def test_wrong_source_total_fails_closed(self):
        xml=("<article><table-wrap><caption><p>Number of sequences per bat species "
             "recorded in each microhabitat</p></caption><table><tbody>"
             "<tr><td>Pipistrellus pipistrellus</td><td>MRE</td>"
             "<td>1</td><td>1%</td><td>2</td><td>2%</td><td>3</td>"
             "<td>3%</td><td>900</td><td>100%</td></tr>"
             "</tbody></table></table-wrap></article>").encode()
        with patch.object(m,"EXPECTED_ROWS",1):
            with self.assertRaisesRegex(RuntimeError,"does not reconcile"):
                m.parse_primary_table(xml)

if __name__=="__main__":
    unittest.main()
