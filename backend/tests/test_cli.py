import pytest
from backend.cli import triage_text, format_triage_output


def test_triage_text_valid_complaint():
    sample = "पानी की पाइपलाइन टूट गई है, कटक में तीन दिन से पानी नहीं आ रहा"
    res = triage_text(sample)

    assert res["language"] == "Hindi"
    assert res["category"] == "Water Supply"
    assert res["department"] == "PHED"
    assert res["state"] in ["Odisha", "National / Unspecified"]
    assert "Cuttack" in res["location"] or res["district"] in ["Cuttack", "Not detected"]
    assert 0.0 <= res["confidence"] <= 1.0

    # scikit-learn fields present
    assert "sklearn_category" in res
    assert "sklearn_confidence" in res
    assert isinstance(res["sklearn_category"], str)
    assert 0.0 <= res["sklearn_confidence"] <= 1.0


def test_triage_text_empty_input():
    res = triage_text("")
    assert res["language"] == "Unknown"
    assert res["category"] == "Unknown"
    assert res["confidence"] == 0.0
    assert res["sklearn_confidence"] == 0.0


def test_format_triage_output():
    sample = "Street light not working near bus stand Puri since a week"
    res = triage_text(sample)
    formatted = format_triage_output(res)

    assert "JANSAMADHAN AI OFFLINE GRIEVANCE TRIAGE" in formatted
    assert "Language:" in formatted
    assert "Category:" in formatted
    assert "scikit-learn" in formatted
