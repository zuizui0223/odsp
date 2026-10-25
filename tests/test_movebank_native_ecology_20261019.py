"""Checks for geometry, source roster and coverage without inspecting animal movement."""
import csv
from datetime import date, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.movebank_native_ecology_20261019 import daylength, greedy_pairs, solar_period, parse_time, inspect_csv, PILOT

class Tests(unittest.TestCase):
    def test_earth_daylength(self):
        self.assertAlmostEqual(daylength(0,date(2020,6,21)),12.12,delta=0.25)
        self.assertGreater(daylength(60,date(2020,6,21)),18)
        self.assertLess(daylength(60,date(2020,12,21)),6)

    def test_solar_period(self):
        self.assertEqual(solar_period(datetime(2020,6,1,12),40,0)[1],"day")
        self.assertEqual(solar_period(datetime(2020,6,1,0),40,0)[1],"night")
        self.assertEqual(solar_period(datetime(2020,6,1,0),40,90)[0],date(2020,6,1))
        self.assertEqual(solar_period(datetime(2020,6,1,1),40,-90)[0],date(2020,5,31))

    def test_time_parsing(self):
        self.assertEqual(parse_time('2020-01-01T01:00:00+01:00'),datetime(2020,1,1))
        self.assertIsNone(parse_time('invalid'))

    def test_one_to_one_pairing_and_caliper(self):
        a={date(2021,5,1):1,date(2021,5,2):1}
        b={date(2021,8,10):1,date(2021,8,11):1}
        pairs=greedy_pairs(a,b,45,caliper_min=60)
        self.assertEqual(len({x[0] for x in pairs}),len(pairs))
        self.assertEqual(len({x[1] for x in pairs}),len(pairs))
        for da,db,gap in pairs:
            self.assertGreaterEqual((db-da).days,30)
            self.assertLessEqual(gap,60)

    def test_empty_support(self):
        self.assertEqual(greedy_pairs({}, {}, 45),[])

    def test_fixed_pilot_source_integrity(self):
        p=json.loads(PILOT.read_text())
        self.assertEqual(len(p['sources']),3)
        self.assertEqual(len({x['package_uuid'] for x in p['sources']}),3)
        self.assertEqual(len({x['original_csv_bitstream_uuid'] for x in p['sources']}),3)
        self.assertTrue(all(len(x['original_csv_md5'])==32 for x in p['sources']))

    def test_csv_missing_required_schema_is_hold(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'bad.csv'
            f.write_text('animal-id,timestamp\na,2020-05-01 12:00:00\n')
            self.assertEqual(inspect_csv(f)['status'],'source_schema_hold')

    def test_coverage_not_dependent_on_displacement(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'synthetic.csv'
            with f.open('w',newline='') as fd:
                w=csv.writer(fd);w.writerow(['timestamp','individual-local-identifier','location-lat','location-long'])
                for day in [date(2021,5,8),date(2021,5,9),date(2021,8,2),date(2021,8,3)]:
                    for hr in (9,10,11,21,22,23):
                        w.writerow([f'{day} {hr:02}:00:00','animal1',45,0])
            result=inspect_csv(f)
            self.assertEqual(result['status'],'coverage_evaluated')
            self.assertEqual(result['csv_rows'],24)
            self.assertEqual(result['distinct_individuals_with_valid_fixes'],1)
            self.assertEqual(result['individual_years_ge_10_pairs'],0)

if __name__=='__main__':unittest.main()
