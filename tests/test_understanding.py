import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.language import detect_script, detect_language, from_english
from backend.core.understanding import understand
from backend.core.messages import t
from backend.core.llm_wrapper import LLMUnavailable

def run_all_tests():
    print("Running Language & Understanding Tests...")

    # 1. detect_script tests
    odia_sample = "ପାଣି ଯୋଗାଣ ବନ୍ଦ ଅଛି"
    deva_sample = "सड़क पर बड़ा गड्ढा है"
    eng_sample = "Streetlight is not working on main road"
    mixed_sample = "Ward 12 ରେ water supply leak ହୋଇଛି"

    assert detect_script(odia_sample) == "odia", f"Expected odia, got {detect_script(odia_sample)}"
    assert detect_script(deva_sample) == "devanagari", f"Expected devanagari, got {detect_script(deva_sample)}"
    assert detect_script(eng_sample) == "latin", f"Expected latin, got {detect_script(eng_sample)}"
    assert detect_script(mixed_sample) == "mixed", f"Expected mixed, got {detect_script(mixed_sample)}"
    print("Test 1 passed: detect_script correctly identifies Odia, Devanagari, Latin, and Mixed scripts.")

    # detect_language tests
    assert detect_language(odia_sample)["code"] == "or"
    assert detect_language(deva_sample)["code"] == "hi"
    assert detect_language(eng_sample)["code"] == "en"
    assert detect_language(mixed_sample)["mixed"] is True
    print("Test 1b passed: detect_language handles scripts and mixed detection.")

    # 2. understand() on English, Hindi, Odia, Hinglish using mocked chat_json
    mock_en_res = {
        "language": "en",
        "mixed": False,
        "english_text": "Streetlight is not working on 5th Avenue.",
        "category": "Street Lighting",
        "location": "5th Avenue",
        "summary": "Non-working streetlight on 5th Avenue",
        "missing": [],
        "needs_review": False
    }

    mock_hi_res = {
        "language": "hi",
        "mixed": False,
        "english_text": "Water pipeline is leaking on Gandhi Road.",
        "category": "Water Supply",
        "location": "Gandhi Road",
        "summary": "Water pipeline leaking on Gandhi Road",
        "missing": [],
        "needs_review": False
    }

    mock_or_res = {
        "language": "or",
        "mixed": False,
        "english_text": "Garbage has not been picked up in Ward 7.",
        "category": "Sanitation & Garbage",
        "location": "Ward 7",
        "summary": "Garbage accumulation in Ward 7",
        "missing": [],
        "needs_review": False
    }

    mock_hinglish_res = {
        "language": "hi",
        "mixed": True,
        "english_text": "Road is completely broken near City Hospital.",
        "category": "Roads & Potholes",
        "location": "City Hospital",
        "summary": "Broken road near City Hospital",
        "missing": [],
        "needs_review": False
    }

    with patch("backend.core.understanding.chat_json") as mock_json:
        # English
        mock_json.return_value = mock_en_res
        u_en = understand("Streetlight is not working on 5th Avenue.")
        assert u_en["category"] == "Street Lighting"
        assert u_en["location"] == "5th Avenue"
        assert u_en["used_llm"] is True
        assert u_en["needs_review"] is False

        # Hindi
        mock_json.return_value = mock_hi_res
        u_hi = understand("गांधी रोड पर पानी का पाइप लीक हो रहा है")
        assert u_hi["category"] == "Water Supply"
        assert u_hi["language"] == "hi"
        assert u_hi["location"] == "Gandhi Road"

        # Odia
        mock_json.return_value = mock_or_res
        u_or = understand("ୱାର୍ଡ ୭ ରେ ଅଳିଆ ଉଠାଯାଇ ନାହିଁ")
        assert u_or["category"] == "Sanitation & Garbage"
        assert u_or["language"] == "or"

        # Hinglish
        mock_json.return_value = mock_hinglish_res
        u_hing = understand("City Hospital ke paas road bohot kharab hai")
        assert u_hing["category"] == "Roads & Potholes"
        assert u_hing["mixed"] is True
    print("Test 2 passed: understand() successfully parses English, Hindi, Odia, and Hinglish inputs.")

    # 3. Invalid category is coerced to 'Other / Needs Review' with needs_review=True
    mock_invalid_cat = {
        "language": "en",
        "mixed": False,
        "english_text": "Alien spaceship landed in park.",
        "category": "Extraterrestrial Affairs",
        "location": "Central Park",
        "summary": "Alien landing reported",
        "missing": [],
        "needs_review": False
    }

    with patch("backend.core.understanding.chat_json", return_value=mock_invalid_cat):
        u_inv = understand("Alien spaceship landed in park.")
        assert u_inv["category"] == "Other / Needs Review"
        assert u_inv["needs_review"] is True
    print("Test 3 passed: Invalid category coerced to 'Other / Needs Review' with needs_review=True.")

    # 4. LLMUnavailable fallback works without crashing
    with patch("backend.core.understanding.chat_json", side_effect=LLMUnavailable("Out of quota")):
        u_fallback = understand("Emergency sewer blockage in Market Lane")
        assert u_fallback["used_llm"] is False
        assert u_fallback["category"] == "Other / Needs Review"
        assert u_fallback["needs_review"] is True
        assert u_fallback["english_text"] == "Emergency sewer blockage in Market Lane"
        assert "location" in u_fallback["missing"]
    print("Test 4 passed: LLMUnavailable fallback returns zero-network safe structure.")

    # 5. t() key translation and fallback to English
    assert "Namaste" in t("greeting", "en")
    assert "नमस्ते" in t("greeting", "hi")
    assert "ନମସ୍କାର" in t("greeting", "or")

    # Fallback for unknown language
    assert t("greeting", "fr") == t("greeting", "en")
    # Fallback for unknown key
    assert t("unknown_custom_key", "hi") == "unknown_custom_key"
    # Interpolation
    msg = t("ticket_created", "en", ticket_id="GRV-1001", department="Water Supply", priority="Critical")
    assert "GRV-1001" in msg and "Water Supply" in msg and "Critical" in msg
    print("Test 5 passed: t() translates keys, formats variables, and falls back to English.")

    print("\nALL UNDERSTANDING & LANGUAGE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()

