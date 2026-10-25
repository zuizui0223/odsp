"""No source substitutions, GPS identity leaks or response-based admission."""
import csv
from datetime import datetime,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.global_solar_azimuth_12_new_original_events_v1 import (
    StrictSourceHold,check_manifest,load_source_taxa,analyze_original_source
)


class RegistryBlindOriginalGPSTest(unittest.TestCase):

    def test_complete_twelve_manifest_and_metadata_holds(self):
        sources=check_manifest()
        self.assertEqual(len(sources),12)
        self.assertEqual(sum(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE"
                             for x in sources),8)
        self.assertEqual(sum(x["status"]=="SOURCE_HOLD" for x in sources),4)

    def test_explicit_prior_original_file_hold_stays_hold(self):
        hold=next(x for x in check_manifest() if x["status"]=="SOURCE_HOLD")
        with TemporaryDirectory() as tmp:
            with patch("scripts.global_solar_azimuth_12_new_original_events_v1.original_files",
                       side_effect=AssertionError("MUST NOT look up replacement source")):
                result=analyze_original_source(hold,Path(tmp))
        self.assertEqual(result["source_state"],"SOURCE_HOLD")
        self.assertEqual(len(result["source_taxa"]),len(hold["original_species_labels"]))

    def test_timestamp_only_hour_selection_and_taxon_preservation(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.csv"
            with p.open("w",encoding="utf8",newline="") as fd:
                w=csv.writer(fd)
                w.writerow(["timestamp","individual-local-identifier","location-lat",
                            "location-long","individual-taxon-canonical-name"])
                origin=datetime(2020,1,1,12)
                for i in range(3):
                    w.writerow([(origin+timedelta(hours=i,minutes=49)).isoformat(),"private A",
                                10,21+i*0.05,"Taxon one"])
                    w.writerow([(origin+timedelta(hours=i,minutes=5)).isoformat(),"private A",
                                10,20+i*0.05,"Taxon one"])
                    w.writerow([(origin+timedelta(hours=i,minutes=5)).isoformat(),"private B",
                                11,22+i*0.03,"Taxon two"])
            taxa,coverage,totals=load_source_taxa(p,"source.csv",["Taxon one","Taxon two"])
            self.assertEqual(totals["original_total_rows"],9)
            self.assertEqual(coverage["Taxon one"]["original_taxon_rows"],6)
            self.assertEqual(coverage["Taxon two"]["original_taxon_rows"],3)
            self.assertEqual(coverage["Taxon one"]["hour_selected_fixes"],3)
            self.assertEqual(len(taxa["Taxon one"]["private A"]),3)
            self.assertEqual(taxa["Taxon one"]["private A"][origin][2],20)

    def test_no_missing_multi_species_column_fallback(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.csv"
            p.write_text("timestamp,location-lat,location-long,individual-local-identifier\n"
                         "2020-01-01T12:00:00,10,20,A\n")
            with self.assertRaisesRegex(StrictSourceHold,"taxon column"):
                load_source_taxa(p,"source.csv",["Taxon one","Taxon two"])

    def test_ambiguous_archive_members_cannot_be_selected_postoutcome(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.zip"
            with ZipFile(p,"w") as z:
                z.writestr("a.csv","timestamp,location-lat\n")
                z.writestr("b.csv","timestamp,location-lat\n")
            with self.assertRaisesRegex(StrictSourceHold,"one primary original CSV"):
                load_source_taxa(p,"source.zip",["Taxon one"])


if __name__=="__main__":
    unittest.main()
