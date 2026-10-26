"""Known-input and known-truth tests for independent-study macroecology."""
import json
import math
import unittest
from copy import deepcopy

from scripts.analyze_solar_irradiance_direction_macro_gradient_v0 import (
    AUDIT, EARLY, LATE, COVARIATES, build_rows, load, ranks, run, spearman,
    within_study_context_pairs,
)


class SolarIrradianceMacroEcologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_early = load(EARLY)
        cls.original_late = load(LATE)
        cls.original_audit = load(AUDIT)
        cls.result = run(draws=100)

    def test_rank_signs_and_ties_are_exact(self):
        self.assertEqual(ranks([10, 10, 20, 30]), [1.5, 1.5, 3.0, 4.0])
        self.assertAlmostEqual(spearman([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3], [6, 4, 2]), -1.0)
        self.assertIsNone(spearman([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(spearman([1, 2], [1, 2]))

    def test_original_source_manifest_is_complete_and_does_not_impute_nulls(self):
        o = self.result
        self.assertEqual(o["source_denominator"], {
            "earlier": 24, "external": 24, "total": 48,
            "defined_source_radiation_slopes": 20,
            "undefined_source_radiation_slopes": 28,
        })
        frame = o["source_sample_support"]
        self.assertEqual(len(frame), 48)
        self.assertEqual(len({r["source_hash"] for r in frame}), 48)
        self.assertEqual(sum(x["shortwave_coefficient_status"] == "DEFINED" for x in frame), 20)
        self.assertTrue(all(len(r["source_hash"]) == 12 for r in frame))

    def test_climate_ranks_reproduce_exact_original_archived_source_effects(self):
        b = self.result["between_original_study_source_correlations"]
        exp = {
            "mean_shortwave_Wm2": (0.07518796992481203, 0.3090909090909091, -0.24848484848484848),
            "mean_temperature_C": (0.4481203007518797, 0.41818181818181815, 0.3696969696969697),
            "mean_wind_sun_cos": (0.4992481203007519, 0.2606060606060606, 0.7454545454545455),
            "abs_latitude_15degree_band_midpoint": (-0.5636570566668524, -0.810287391340663, -0.15731330124142318),
        }
        for v, expected in exp.items():
            for group, val in zip(("pooled", "earlier", "external"), expected):
                self.assertEqual(b[v][group]["source_studies"], 20 if group == "pooled" else 10)
                self.assertAlmostEqual(b[v][group]["spearman_rho"], val, places=12)

    def test_study_pairs_do_not_pseudoreplicate_goose_taxa(self):
        a, p, frame = build_rows(self.original_early, self.original_late, self.original_audit)
        self.assertEqual(len(a), 20)
        self.assertEqual(len(p), 14)
        self.assertEqual(len(frame), 48)
        r = self.result["within_original_study_same_taxon_context_comparisons"]
        self.assertEqual(r["mean_shortwave_Wm2"]["same_taxon_original_context_pairs"], 14)
        self.assertEqual(r["mean_shortwave_Wm2"]["original_study_sources"], 12)
        self.assertEqual(r["abs_latitude_15degree_band_midpoint"]["same_taxon_original_context_pairs"], 1)
        self.assertIsNone(r["abs_latitude_15degree_band_midpoint"]["original_study_resampling_95"])

    def test_high_vs_low_pair_contrast_is_input_order_invariant(self):
        c1 = {"slope": -0.08, **{field: 100.0 for field in COVARIATES.values()}}
        c2 = {"slope": 0.02, **{field: 120.0 for field in COVARIATES.values()}}
        p = [{"source_hash": f"source{i}", "cohort": "earlier",
              "taxon": "Testus", "first": c1, "second": c2} for i in range(5)]
        x = within_study_context_pairs(p, draws=100)
        for r in p:
            r["first"], r["second"] = r["second"], r["first"]
        y = within_study_context_pairs(p, draws=100)
        self.assertEqual(x, y)
        self.assertAlmostEqual(x["mean_shortwave_Wm2"]["mean_change_in_shortwave_slope_in_higher_context"], 0.1)

    def test_original_registered_nonreplication_is_immutable(self):
        self.assertEqual(self.result["preregistered_external_verdict_UNCHANGED"],
                         "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE")
        d = deepcopy(self.original_audit)
        d["prior_frozen_external_replication_decision_UNCHANGED"] = "REPLICATED"
        # The runner must fail instead of reclassifying a previous experiment.
        self.assertNotEqual(d["prior_frozen_external_replication_decision_UNCHANGED"],
                            self.result["preregistered_external_verdict_UNCHANGED"])

    def test_output_has_no_raw_animal_identifiers_or_telemetry(self):
        out = json.dumps(self.result)
        for prohibited in ('"animal_id"', '"tagged_animal_id"', '"longitude"',
                           '"raw_gps"', '"timestamp"', '"source_package_uuid"',
                           '"original_UTC_observation_year"'):
            self.assertNotIn(prohibited, out)
        self.assertNotIn("NaN", out)
        self.assertNotIn("Infinity", out)


if __name__ == "__main__":
    unittest.main()
