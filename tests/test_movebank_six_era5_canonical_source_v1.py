"""Separate first-source remediation tests for Open-Meteo mutable JSON response metadata."""
import copy
import hashlib
import json
import math
import unittest
from scripts.movebank_six_source_within_animal_era5_canonical_v1 import (
    canonical_climate_payload,canonical_bytes,validate_first_regional_ERA5
)

def fake_api(generation_time:float):
    return {
        "latitude":42.5, "longitude":-110.5,"elevation":2100.0,
        "timezone":"Etc/GMT+7","utc_offset_seconds":-25200,
        "generationtime_ms":generation_time,
        "daily_units":{"temperature_2m_mean":"°C",
                       "precipitation_sum":"mm",
                       "et0_fao_evapotranspiration":"mm"},
        "daily":{"time":["2020-03-01","2020-03-02"],
                 "temperature_2m_mean":[1.5,3.1],
                 "precipitation_sum":[0.1,2.4],
                 "et0_fao_evapotranspiration":[1.2,1.4]},
    }

class CanonicalWeatherSourceV1(unittest.TestCase):
    def test_volatile_generationtime_changes_raw_sha_not_scientific_sha(self):
        first=fake_api(2.084970474243164)
        second=fake_api(2.16829776763916)
        self.assertNotEqual(hashlib.sha256(json.dumps(first).encode()).hexdigest(),
                            hashlib.sha256(json.dumps(second).encode()).hexdigest())
        self.assertEqual(canonical_bytes(canonical_climate_payload(first)),
                         canonical_bytes(canonical_climate_payload(second)))

    def test_any_change_to_day_or_ERA5_temperature_water_changes_digest(self):
        original=fake_api(1)
        mutated=copy.deepcopy(original)
        mutated["daily"]["temperature_2m_mean"][1]+=0.1
        self.assertNotEqual(canonical_bytes(canonical_climate_payload(original)),
                            canonical_bytes(canonical_climate_payload(mutated)))
        mutated=fake_api(2)
        mutated["daily"]["time"][0]="2020-02-29"
        self.assertNotEqual(canonical_bytes(canonical_climate_payload(original)),
                            canonical_bytes(canonical_climate_payload(mutated)))

    def test_invalid_original_weather_units_are_not_silently_changed(self):
        broken=fake_api(1)
        broken["daily_units"]["precipitation_sum"]="cm"
        with self.assertRaisesRegex(ValueError,"HOLD_ERA5_ORIGINAL_DAILY_SOURCE_UNITS"):
            canonical_climate_payload(broken)

    def test_exact_original_climate_means_required_not_just_metadata(self):
        expected={"n":2,"t":4.12,"w":-22.45,"e":.011,"sha":["old-volatile"]}
        prior={"status":"descriptive_coarse_region_weather_link",
               "individuals_with_complete_weather_and_displacement":2,
               "mean_falling_minus_rising_regional_temperature_c":4.12,
               "mean_falling_minus_rising_regional_p_minus_et0_30d_mm":-22.45,
               "mean_observed_falling_minus_rising_relative_log1p_night_day_speed":.011,
               "missing_weather_date_pairs":0}
        src=[{"new_v1_canonical_daily_content_sha256":"source-data-content"}]
        self.assertTrue(validate_first_regional_ERA5(prior,src,expected))
        bad={**prior,"mean_falling_minus_rising_regional_temperature_c":4.2}
        with self.assertRaisesRegex(ValueError,"HOLD_FIRST_ORIGINAL_ERA5_GROUP_SCIENTIFIC_VALUES_DRIFT"):
            validate_first_regional_ERA5(bad,src,expected)
        with self.assertRaisesRegex(ValueError,"HOLD_FIRST_ERA5_CHUNK_ROSTER_CHANGED"):
            validate_first_regional_ERA5(prior,[],expected)

if __name__=="__main__":unittest.main()
