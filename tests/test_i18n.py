import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from i18n import t, DEFAULT_LANGUAGE, TRANSLATIONS


class TestInternationalization(unittest.TestCase):

    def test_default_language_is_english(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")

    def test_english_and_spanish_catalogs_present(self):
        self.assertIn("en", TRANSLATIONS)
        self.assertIn("es", TRANSLATIONS)

    def test_key_completeness_and_official_terms(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        es_keys = set(TRANSLATIONS["es"].keys())
        self.assertEqual(en_keys, es_keys, f"Discrepancy in i18n keys: {en_keys ^ es_keys}")

        # Official judo terminology preserved in English
        en_covered = TRANSLATIONS["en"]["scope_covered_body"]
        for term in ["Ippon", "Waza-ari", "Osaekomi", "Mate", "Kansetsu-waza", "Hansoku-make", "Sokuteiki"]:
            self.assertIn(term, en_covered)

        # Title is in English by default
        self.assertEqual(t("app_title", "en"), "IJF SOR Assistant")
        self.assertEqual(t("app_title", "es"), "Asistente SOR IJF")

    def test_translation_interpolation(self):
        msg_en = t("pdf_viewer_title", "en", article="Art. 18.2", page=190)
        self.assertEqual(msg_en, "📄 Official Viewer: Art. 18.2 (Page 190)")

        msg_es = t("pdf_viewer_title", "es", article="Art. 18.2", page=190)
        self.assertEqual(msg_es, "📄 Visor Oficial: Art. 18.2 (Pág. 190)")

    def test_example_queries_bilingual(self):
        ex_en = t("example_queries", "en")
        ex_es = t("example_queries", "es")
        self.assertEqual(len(ex_en), len(ex_es))
        self.assertTrue(ex_en[1].startswith("What is"))
        self.assertTrue(ex_es[1].startswith("¿Se permite"))


if __name__ == "__main__":
    unittest.main()
