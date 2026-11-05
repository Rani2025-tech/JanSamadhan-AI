import pytest
from pathlib import Path

from backend.ai.ml_baseline import predict, get_model, train_model

EXPECTED_CATEGORIES = [
    "Water Supply",
    "Road Infrastructure",
    "Electricity",
    "Sanitation",
    "Public Health",
    "Ration / PDS"
]


def test_model_loads_and_has_classes():
    model = get_model()
    assert model is not None
    assert hasattr(model, "predict_proba")
    assert len(model.classes_) == 6
    for expected_cat in EXPECTED_CATEGORIES:
        assert expected_cat in model.classes_


def test_predict_english():
    text = "Street light not working near bus stand Puri since a week"
    cat, conf = predict(text)
    assert isinstance(cat, str)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    assert cat in EXPECTED_CATEGORIES


def test_predict_odia():
    text = "ଆମ ୱାର୍ଡ ୭ ରେ ପିଇବା ପାଣି ପାଇପ୍ ଲିକ ହୋଇ ରାସ୍ତାରେ ବୋହୁଛି"
    cat, conf = predict(text)
    assert isinstance(cat, str)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    assert cat == "Water Supply"


def test_predict_hindi():
    text = "बिजली नहीं है, लखनऊ, गोमती नगर"
    cat, conf = predict(text)
    assert isinstance(cat, str)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    assert cat in EXPECTED_CATEGORIES


def test_predict_roman_hindi():
    text = "pani supply nahi aa raha, Cuttack mein 3 din se"
    cat, conf = predict(text)
    assert isinstance(cat, str)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    assert cat in EXPECTED_CATEGORIES


def test_predict_empty_or_whitespace():
    cat, conf = predict("")
    assert isinstance(cat, str)
    assert conf == 0.0

    cat_ws, conf_ws = predict("   ")
    assert isinstance(cat_ws, str)
    assert conf_ws == 0.0
