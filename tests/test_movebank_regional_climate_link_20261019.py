"""Check environmental source arithmetic before real data; no source GPS values here."""
import unittest
from datetime import date
from scripts.movebank_regional_climate_link_20261019 import fixed_timezone,weather_rolling_30,link_weather
class Tests(unittest.TestCase):
    def test_fixed_solar_standard_timezone(self):
        self.assertEqual(fixed_timezone(-115.5),"Etc/GMT+8")
        self.assertEqual(fixed_timezone(-81),"Etc/GMT+5")
        self.assertEqual(fixed_timezone(-72.5),"Etc/GMT+5")
    def test_rolling_supply_minus_demand(self):
        base=date(2020,4,1)
        days={date.fromordinal(base.toordinal()+i):(10.0,5.0,2.0) for i in range(35)}
        d=date.fromordinal(base.toordinal()+29)
        self.assertEqual(weather_rolling_30(days,d),(10.0,90.0))
        self.assertIsNone(weather_rolling_30(days,base))
    def test_missingness_not_imputed(self):
        d=date(2020,5,1)
        self.assertIsNone(weather_rolling_30({d:(10.,0.,0.)},d))
    def test_equal_individual_weight(self):
        d0=date(2020,4,1);d1=date(2020,6,1)
        days={}
        for i in range(80):
            d=date.fromordinal(d0.toordinal()+i)
            days[d]=(float(i),1.0,0.0)
        years=[[[ (d0+__import__("datetime").timedelta(days=30),d1,.2) ]]]
        r=link_weather(years,days)
        self.assertEqual(r["individuals_with_complete_weather_and_displacement"],1)
        self.assertAlmostEqual(r["mean_observed_falling_minus_rising_relative_log1p_night_day_speed"],.2)
        self.assertAlmostEqual(r["mean_falling_minus_rising_regional_temperature_c"],31)
if __name__=="__main__":unittest.main()
