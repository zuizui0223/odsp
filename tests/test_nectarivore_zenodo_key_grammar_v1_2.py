import unittest
from scripts.nectarivore_zenodo_key_grammar_v1_2 import normalized_id

class KeyGrammarTests(unittest.TestCase):
    def test_normalize_only_orthography_not_biological_identity(self):
        self.assertEqual(normalized_id(" ML_01 "),normalized_id("ml-01"))
    def test_distinct_original_ids_remain_distinct(self):
        self.assertNotEqual(normalized_id("Plant1"),normalized_id("Plant2"))
    def test_keys_are_not_species_or_nectar_outcomes(self):
        self.assertNotEqual(normalized_id("ML_1"),normalized_id("ML_11"))

if __name__=="__main__":
    unittest.main()
