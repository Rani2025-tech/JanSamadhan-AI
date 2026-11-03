import os
import sys
import json
import unittest

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "frontend"))

from frontend.ui_text import ui, label as ui_label, supported_languages as frontend_supported_languages
from backend.core.messages import t, label as bot_label, supported_languages as backend_supported_languages
from backend.core.language import detect_script, detect_language

class TestLocales(unittest.TestCase):
    def setUp(self):
        self.locales_dir = os.path.join(repo_root, "locales")
        self.lang_file = os.path.join(self.locales_dir, "languages.json")

    def test_languages_json_and_files_exist(self):
        """Verifies every language in languages.json exists and has a corresponding <code.json> file."""
        self.assertTrue(os.path.isfile(self.lang_file), "languages.json must exist")
        with open(self.lang_file, "r", encoding="utf-8") as f:
            langs = json.load(f)

        expected_order = ["en", "hi", "mr", "ta", "bn", "or"]
        actual_order = [l["code"] for l in langs]
        self.assertEqual(actual_order, expected_order, f"Language order must match: {expected_order}")

        for l in langs:
            for field in ["code", "name", "native", "script", "reviewed"]:
                self.assertIn(field, l, f"Field '{field}' missing in language dict {l}")
            code = l["code"]
            code_file = os.path.join(self.locales_dir, f"{code}.json")
            self.assertTrue(os.path.isfile(code_file), f"Locale file {code}.json must exist")

    def test_loaders_never_raise(self):
        """Verifies loaders never raise on missing keys, missing files, or unknown languages."""
        # frontend ui()
        self.assertEqual(ui("completely_missing_key_xyz", "en"), "completely_missing_key_xyz")
        self.assertEqual(ui("completely_missing_key_xyz", "klingon"), "completely_missing_key_xyz")
        self.assertEqual(ui("", "en"), "")
        self.assertEqual(ui("app_name", "klingon"), ui("app_name", "en"))

        # backend t()
        self.assertEqual(t("completely_missing_bot_key_xyz", "en"), "completely_missing_bot_key_xyz")
        self.assertEqual(t("completely_missing_bot_key_xyz", "klingon"), "completely_missing_bot_key_xyz")
        self.assertEqual(t("", "en"), "")
        self.assertEqual(t("greeting", "klingon"), t("greeting", "en"))

    def test_per_key_english_fallback(self):
        """Verifies per-key English fallback works for mr, ta, and bn while their sections are empty."""
        en_app_name = ui("app_name", "en")
        en_greeting = t("greeting", "en")

        for code in ["mr", "ta", "bn"]:
            self.assertEqual(ui("app_name", code), en_app_name, f"ui('app_name', '{code}') should fall back to English")
            self.assertEqual(t("greeting", code), en_greeting, f"t('greeting', '{code}') should fall back to English")

    def test_label_fallback(self):
        """Verifies label() falls back to English when translation is missing or language unknown."""
        # Category fallback
        self.assertEqual(ui_label("categories", "Water Supply", "en"), "Water Supply")
        self.assertEqual(ui_label("categories", "Water Supply", "mr"), "Water Supply")
        self.assertEqual(bot_label("categories", "Electricity", "ta"), "Electricity")

        # Department fallback
        self.assertEqual(ui_label("departments", "General Administration", "bn"), "General Administration")
        self.assertEqual(bot_label("departments", "General Administration", "or"), "General Administration")

        # Status and priority
        self.assertEqual(ui_label("statuses", "Submitted", "en"), "Submitted")
        self.assertEqual(bot_label("priorities", "Critical", "en"), "Critical")

        # Missing label or empty string
        self.assertEqual(ui_label("categories", "", "en"), "")
        self.assertEqual(ui_label("unknown_kind", "Nonexistent", "en"), "Nonexistent")

    def test_key_parity_report(self):
        """
        Reports missing key counts per language.
        Fails if 'en' is missing any key present in 'hi' or 'or'.
        Does NOT fail if mr, ta, or bn are missing keys.
        """
        en_file = os.path.join(self.locales_dir, "en.json")
        with open(en_file, "r", encoding="utf-8") as f:
            en_doc = json.load(f)

        en_ui_keys = set(en_doc.get("ui", {}).keys())
        en_bot_keys = set(en_doc.get("bot", {}).keys())

        print("\n--- Key Parity Report ---")
        for code in ["en", "hi", "or", "mr", "ta", "bn"]:
            path = os.path.join(self.locales_dir, f"{code}.json")
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            ui_keys = set(doc.get("ui", {}).keys())
            bot_keys = set(doc.get("bot", {}).keys())

            missing_ui = en_ui_keys - ui_keys
            missing_bot = en_bot_keys - bot_keys
            print(f"[{code}] UI keys: {len(ui_keys)} (missing vs en: {len(missing_ui)}), Bot keys: {len(bot_keys)} (missing vs en: {len(missing_bot)})")

            if code in ["hi", "or"]:
                extra_ui = ui_keys - en_ui_keys
                extra_bot = bot_keys - en_bot_keys
                self.assertFalse(extra_ui, f"{code}.json has extra UI keys not in en.json: {extra_ui}")
                self.assertFalse(extra_bot, f"{code}.json has extra Bot keys not in en.json: {extra_bot}")

    def test_detect_script_and_language(self):
        """
        Verifies detect_script and detect_language across Tamil, Bengali, Telugu (other),
        Odia, Devanagari (with ui_lang mr, hi, none), Latin, and empty text.
        """
        tamil_text = "குடிநீர் விநியோகம் நிறுத்தப்பட்டுள்ளது"
        bengali_text = "পানীয় জল সরবরাহ বন্ধ রয়েছে"
        telugu_text = "మంచినీటి సరఫరా నిలిచిపోయింది"
        odia_text = "ପାଣି ଯୋଗାଣ ବନ୍ଦ ଅଛି"
        deva_text = "पानी की आपूर्ति बंद है"
        latin_text = "Water supply is disrupted in sector 4"

        # Scripts
        self.assertEqual(detect_script(tamil_text), "tamil")
        self.assertEqual(detect_script(bengali_text), "bengali")
        self.assertEqual(detect_script(telugu_text), "telugu")
        self.assertEqual(detect_script(odia_text), "odia")
        self.assertEqual(detect_script(deva_text), "devanagari")
        self.assertEqual(detect_script(latin_text), "latin")
        self.assertEqual(detect_script(""), "latin")

        # Languages
        self.assertEqual(detect_language(tamil_text)["code"], "ta")
        self.assertEqual(detect_language(bengali_text)["code"], "bn")
        self.assertEqual(detect_language(telugu_text)["code"], "other")  # Telugu is not in supported languages
        self.assertEqual(detect_language(odia_text)["code"], "or")

        # Devanagari with ui_lang
        self.assertEqual(detect_language(deva_text, ui_lang="mr")["code"], "mr")
        self.assertEqual(detect_language(deva_text, ui_lang="hi")["code"], "hi")
        self.assertEqual(detect_language(deva_text, ui_lang=None)["code"], "hi")
        self.assertEqual(detect_language(deva_text, ui_lang="en")["code"], "hi")

        # Latin and empty text
        self.assertEqual(detect_language(latin_text)["code"], "en")
        self.assertEqual(detect_language("")["code"], "en")
        self.assertEqual(detect_language("   ")["code"], "en")

if __name__ == "__main__":
    unittest.main()

