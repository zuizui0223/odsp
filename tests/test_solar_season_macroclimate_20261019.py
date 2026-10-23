import importlib
import importlib.util
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
MODULE='scripts.solar_season_macroclimate_20261019'
class TestMacroclimate(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), 'Macroclimate implementation is not present yet')
        self.m=importlib.import_module(MODULE)
    def test_roster_is_order_invariant_and_not_weather_selected(self):
        c=[{'latitude':x,'longitude':y,'eligible_land':True} for x in (-30,30) for y in (-100,-70,10,40,90,120)]
        a=self.m.select_sites(c); b=self.m.select_sites(list(reversed(c)))
        self.assertEqual(a,b); self.assertEqual(len(a),6)
        self.assertEqual(len({(r['latitude'],r['sector']) for r in a}),6)
    def test_hemispheric_summer_and_one_to_one_photoperiod(self):
        for lat,month in ((45,6),(-30,12)):
            p=self.m.astronomical_pairs(lat,2020)
            self.assertGreater(len(p),60)
            self.assertEqual(len({r[0] for r in p}),len(p)); self.assertEqual(len({r[1] for r in p}),len(p))
            self.assertTrue(all(r[0]<date(2020,month,21)<r[1] for r in p))
            self.assertTrue(all(r[4]<=2 for r in p))
    def test_assignment_is_maximum_cardinality_for_all_3x3_graphs(self):
        for mask in range(512):
            costs=[[0 if mask & (1<<(i*3+j)) else 10 for j in range(3)] for i in range(3)]
            def brute(i,used):
                if i==3:return 0
                return max([brute(i+1,used)]+[1+brute(i+1,used|{j}) for j in range(3) if j not in used and costs[i][j]<=2])
            self.assertEqual(len(self.m.assign_pairs(costs,2)),brute(0,set()))
    def test_constant_climate_has_no_branch_change(self):
        start=date(2019,1,1)
        days={str(start+timedelta(days=i)):{'tmean':20.,'tmax':25.,'precip30':30.,'balance30':-30.} for i in range(900)}
        site={'site_id':'fixture','latitude':45.,'longitude':0.}
        _,s=self.m.compare_cycle(site,2020,days)
        self.assertEqual(s['status'],'qualified')
        self.assertTrue(all(s[k]==0 for k in ('delta_tmean','delta_tmax','delta_precip30','delta_balance30')))
    def test_missing_climate_is_not_zero_or_an_alternative_date(self):
        site={'site_id':'fixture','latitude':45.,'longitude':0.}
        p,s=self.m.compare_cycle(site,2020,{})
        self.assertEqual(len(p),len(self.m.astronomical_pairs(45.,2020)))
        self.assertEqual(s['valid_pairs'],0); self.assertEqual(s['status'],'insufficient_climate_support'); self.assertIsNone(s['delta_tmean'])
    def test_fixed_timezone_has_correct_etc_gmt_sign(self):
        self.assertEqual(self.m.fixed_timezone(35.),('Etc/GMT-2',7200))
        self.assertEqual(self.m.fixed_timezone(-70.),('Etc/GMT+5',-18000))
        self.assertEqual(self.m.fixed_timezone(0.),('Etc/GMT',0))
    def test_database_values_have_numeric_types_and_nulls(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.sqlite'
            self.m.write_database(p,{'example':[{'site_id':'x','value':1.25,'missing':None,'n':2}]})
            con=sqlite3.connect(p)
            self.assertEqual(con.execute('select value, missing, n from example').fetchone(),(1.25,None,2)); con.close()
if __name__=='__main__':unittest.main()
