"""New original GPS source untouched 24-sample ecological replication gates."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from scripts.run_solar_radiation_external_24_sources_v0 import (
    verify_external_frozen_frame,source_original_analysis
)


class SolarRadiationExternalSourceOriginalTests(unittest.TestCase):

    def test_complete_preoutcome_source_manifest_before_original_GPS(self):
        c,sources=verify_external_frozen_frame()
        self.assertEqual(len(sources),24)
        self.assertEqual(c["version"],"external-24-original-GPS-solar-radiation-validation-v0")
        self.assertEqual(len({x["original_taxon"] for x in sources}),24)
        self.assertTrue(all(x["original_source_status"]=="ORIGINAL_FILE_METADATA_QUALIFIED"
                            for x in sources))
        self.assertTrue(all(x["original_gps_event_rows_read"]==0 for x in sources))

    def test_no_alternative_if_original_source_hold(self):
        _,sources=verify_external_frozen_frame()
        x=dict(sources[0])
        x["original_source_status"]="SOURCE_METADATA_HOLD"
        with TemporaryDirectory() as tmp:
            with patch("scripts.run_solar_radiation_external_24_sources_v0.original_files",
                       side_effect=AssertionError("MUST NOT open alternative original files")):
                result=source_original_analysis(x,Path(tmp))
        self.assertEqual(result["source_status"],"SOURCE_HOLD")
        self.assertEqual(result["source_weather_gridyear_attempts"],0)

    @patch("scripts.run_solar_radiation_external_24_sources_v0.original_directional_grid_years")
    @patch("scripts.run_solar_radiation_external_24_sources_v0.analyze_taxon")
    @patch("scripts.run_solar_radiation_external_24_sources_v0.load_source_taxa")
    @patch("scripts.run_solar_radiation_external_24_sources_v0.checksum_and_download")
    @patch("scripts.run_solar_radiation_external_24_sources_v0.original_files")
    def test_no_fabricated_environment_when_no_suitable_original_support(
            self,files,download,loader,analyzer,chooser):
        _,sources=verify_external_frozen_frame()
        source=sources[0]
        orig=source["original_file"]
        files.return_value=[{"bitstream_uuid":orig["bitstream_uuid"],
                             "bytes":orig["bytes"],
                             "checksum":orig["provider_checksum"]}]
        download.return_value={"provider_checksum_verified":True}
        loader.return_value=({source["original_taxon"]:{"originalID":{}}},
                             {source["original_taxon"]:{"original_taxon_rows":0,"source_individuals":1}},
                             {"original_total_rows":0})
        analyzer.return_value={"status":"insufficient_independent_animals",
                              "supported_individuals":0}
        chooser.return_value=([],{"original_directional_gridyears":0,
                                  "support_qualified_gridyears":0,
                                  "selected_top_two_gridyears":0})
        with TemporaryDirectory() as tmp:
            with patch("scripts.run_solar_radiation_external_24_sources_v0.get_original_hourly_response",
                       side_effect=AssertionError("NO WEATHER API without GPS support")):
                row=source_original_analysis(source,Path(tmp))
        self.assertEqual(row["source_status"],"ORIGINAL_SOURCE_FIRST_GPS_AND_ERA5_OBSERVATIONS_COMPLETED")
        self.assertEqual(row["source_weather_gridyear_attempts"],0)
        self.assertEqual(row["source_original_GPS_first_directional_result"]["supported_individuals"],0)
        self.assertEqual(len(row["source_taxa"][0]["source_gridyear_weather_contexts"]),0)
        self.assertNotIn("originalID",str(row))


if __name__=="__main__":
    unittest.main()
