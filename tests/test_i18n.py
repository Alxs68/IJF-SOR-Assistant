import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from i18n import t, DEFAULT_LANGUAGE, TRANSLATIONS


class TestInternationalization(unittest.TestCase):

    def test_default_language_is_spanish(self):
        self.assertEqual(DEFAULT_LANGUAGE, "es")

    def test_english_and_spanish_catalogs_present(self):
        self.assertIn("en", TRANSLATIONS)
        self.assertIn("es", TRANSLATIONS)

    def test_key_completeness_and_official_terms(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        es_keys = set(TRANSLATIONS["es"].keys())
        self.assertEqual(en_keys, es_keys, f"Discrepancy in i18n keys: {en_keys ^ es_keys}")

        # Official judo terminology preserved in both languages
        for lang in ["es", "en"]:
            covered = TRANSLATIONS[lang]["scope_covered_body"]
            for term in ["Osaekomi", "Mate", "Hansoku-make", "Sokuteiki"]:
                self.assertIn(term, covered)

        # Title by default (Spanish) vs English
        self.assertEqual(t("app_title"), "Asistente SOR IJF")
        self.assertEqual(t("app_title", "es"), "Asistente SOR IJF")
        self.assertEqual(t("app_title", "en"), "IJF SOR Assistant")

    def test_language_switching_and_fallback(self):
        # Switching between Spanish and English
        self.assertEqual(t("welcome_title", "es"), "Bienvenido")
        self.assertEqual(t("welcome_title", "en"), "Welcome")
        self.assertEqual(t("send_btn", "es"), "Enviar 📤")
        self.assertEqual(t("send_btn", "en"), "Submit 📤")

        # Unknown language falls back to DEFAULT_LANGUAGE ('es')
        self.assertEqual(t("welcome_title", "fr"), "Bienvenido")

    def test_translation_interpolation(self):
        msg_es = t("pdf_viewer_title", "es", article="Art. 18.2", page=190)
        self.assertEqual(msg_es, "📄 Visor Oficial: Art. 18.2 (Pág. 190)")

        msg_en = t("pdf_viewer_title", "en", article="Art. 18.2", page=190)
        self.assertEqual(msg_en, "📄 Official Viewer: Art. 18.2 (Page 190)")

    def test_example_queries_bilingual(self):
        ex_en = t("example_queries", "en")
        ex_es = t("example_queries", "es")
        self.assertEqual(len(ex_en), len(ex_es))
        self.assertTrue(ex_en[1].startswith("What is"))
        self.assertTrue(ex_es[1].startswith("¿Se permite"))

    def test_session_state_preference_simulation(self):
        # Simulate session state persistence
        session_state = {}
        # Initial launch defaults to Spanish
        if "ui_lang" not in session_state:
            session_state["ui_lang"] = DEFAULT_LANGUAGE
        self.assertEqual(session_state["ui_lang"], "es")

        # User chooses English
        session_state["ui_lang"] = "en"
        self.assertEqual(session_state["ui_lang"], "en")

        # In subsequent render / interaction, user choice persists and is not overwritten
        if "ui_lang" not in session_state:
            session_state["ui_lang"] = DEFAULT_LANGUAGE
        self.assertEqual(session_state["ui_lang"], "en")

        # User switches back to Spanish
        session_state["ui_lang"] = "es"
        self.assertEqual(session_state["ui_lang"], "es")


if __name__ == "__main__":
    unittest.main()
