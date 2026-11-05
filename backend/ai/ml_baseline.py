"""
scikit-learn Baseline Classifier for Grievance Category
======================================================
Architecture:
  - Character n-gram TF-IDF Vectorizer (n-grams: 2 to 5, sublinear_tf=True)
  - Logistic Regression Classifier (multinomial, balanced class weights)

Evaluation Baseline Protocol:
  - Trained STRICTLY on the 'train' split of backend/eval/labeled_dataset.json (n=65).
  - Held-out synthetic (n=30) and held-out human splits are NEVER used in training.
  - Model artifact: backend/ai/models/category_baseline.joblib
  - Used for evaluation comparisons against rules and Gemini LLM. Not wired into live production routes.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# Paths
AI_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AI_DIR.parent
MODELS_DIR = AI_DIR / "models"
MODEL_FILE = MODELS_DIR / "category_baseline.joblib"
DATASET_FILE = BACKEND_DIR / "eval" / "labeled_dataset.json"

# In-memory cache for loaded model
_CACHED_PIPELINE: Optional[Pipeline] = None


def build_pipeline() -> Pipeline:
    """Builds the TF-IDF char n-gram + Logistic Regression pipeline."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            sublinear_tf=True,
            min_df=1
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])


def load_train_data():
    """Loads strictly the 'train' split from labeled_dataset.json."""
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_FILE}")

    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Strictly filter for train split
    train_samples = [d for d in data if d.get("split") == "train"]
    if not train_samples:
        raise ValueError(f"No samples with split='train' found in {DATASET_FILE}")

    X = [d["text"] for d in train_samples]
    y = [d["true_category"] for d in train_samples]
    return X, y, len(train_samples)


def train_model(save: bool = True) -> Pipeline:
    """Trains the baseline classifier on train data and saves artifact."""
    global _CACHED_PIPELINE
    X, y, n_train = load_train_data()

    pipeline = build_pipeline()
    pipeline.fit(X, y)

    if save:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, MODEL_FILE)
        print(f"[ML Baseline] Trained on {n_train} samples. Model saved to: {MODEL_FILE}")

    _CACHED_PIPELINE = pipeline
    return pipeline


def get_model() -> Pipeline:
    """Gets the cached model, loads from disk, or auto-trains if absent."""
    global _CACHED_PIPELINE
    if _CACHED_PIPELINE is not None:
        return _CACHED_PIPELINE

    if MODEL_FILE.exists():
        try:
            _CACHED_PIPELINE = joblib.load(MODEL_FILE)
            return _CACHED_PIPELINE
        except Exception as e:
            print(f"[ML Baseline] Warning: Failed to load {MODEL_FILE} ({e}). Retraining...")

    # Auto-train if not present
    return train_model(save=True)


def predict(text: str) -> Tuple[str, float]:
    """
    Predicts complaint category and confidence for an input string.
    
    Args:
        text: Raw grievance text (native script, romanized, or mixed).
        
    Returns:
        Tuple of (category_name: str, confidence_score: float)
    """
    if not text or not text.strip():
        return ("Water Supply", 0.0)

    model = get_model()
    probs = model.predict_proba([text])[0]
    best_idx = int(np.argmax(probs))
    category = str(model.classes_[best_idx])
    confidence = float(probs[best_idx])
    return (category, round(confidence, 4))


def main():
    parser = argparse.ArgumentParser(description="scikit-learn Category Baseline")
    parser.add_argument("--train", action="store_true", help="Train the model on the train split and save to disk")
    parser.add_argument("--predict", type=str, help="Predict category for a text input")
    args = parser.parse_args()

    if args.train:
        train_model(save=True)
    elif args.predict:
        cat, conf = predict(args.predict)
        print(f"Text: \"{args.predict}\"")
        print(f"Predicted Category: {cat}")
        print(f"Confidence: {conf:.2%}")
    else:
        # Default behavior: train if needed and print test sample predictions
        model = get_model()
        test_samples = [
            ("English", "Street light not working near bus stand Puri since a week"),
            ("Odia", "ଆମ ୱାର୍ଡ ୭ ରେ ପିଇବା ପାଣି ପାଇପ୍ ଲିକ ହୋଇ ରାସ୍ତାରେ ବୋହୁଛି"),
            ("Hindi", "बिजली नहीं है, लखनऊ, गोमती नगर"),
            ("Roman Hindi", "pani supply nahi aa raha, Cuttack mein 3 din se")
        ]
        print(f"[ML Baseline] Ready with {len(model.classes_)} classes: {list(model.classes_)}\n")
        for lang, sample in test_samples:
            cat, conf = predict(sample)
            print(f"[{lang}] \"{sample}\" -> {cat} ({conf:.1%})")


if __name__ == "__main__":
    main()
