"""
JanSamadhan Offline NLP & Grievance Triage CLI
==============================================
Runs offline multilingual extraction and category prediction from terminal.
Combines rule-based slot filling and scikit-learn TF-IDF baseline without network calls.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Ensure backend root is on sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ai.classifier import rule_based_extract
from ai.ml_baseline import predict as predict_sklearn


def triage_text(text: str) -> Dict[str, Any]:
    """Extracts grievance attributes via offline rules and scikit-learn baseline."""
    clean_text = text.strip() if text else ""
    if not clean_text:
        return {
            "text": "",
            "language": "Unknown",
            "category": "Unknown",
            "department": "Unknown",
            "urgency": "Unknown",
            "location": "None",
            "state": "Unknown",
            "confidence": 0.0,
            "sklearn_category": "Unknown",
            "sklearn_confidence": 0.0
        }

    # 1. Rule-based offline extraction
    rules = rule_based_extract(clean_text)
    loc_parts = []
    if rules.get("area"):
        loc_parts.append(rules["area"])
    if rules.get("district"):
        loc_parts.append(rules["district"])
    loc_str = ", ".join(loc_parts) if loc_parts else "Not detected"

    # 2. scikit-learn baseline prediction
    sk_cat, sk_conf = predict_sklearn(clean_text)

    return {
        "text": clean_text,
        "language": rules.get("language", "English"),
        "category": rules.get("category", "General"),
        "department": rules.get("department", "General Administration"),
        "urgency": rules.get("urgency", "Medium"),
        "location": loc_str,
        "district": rules.get("district") or "Not detected",
        "state": rules.get("state") or "National / Unspecified",
        "confidence": rules.get("confidence", 0.85),
        "sklearn_category": sk_cat,
        "sklearn_confidence": sk_conf
    }


def format_triage_output(res: Dict[str, Any]) -> str:
    """Formats triage dictionary into human-readable terminal output."""
    lines = [
        "",
        "=" * 60,
        "  JANSAMADHAN AI OFFLINE GRIEVANCE TRIAGE",
        "=" * 60,
        f"  Input Text:      \"{res['text'][:75]}{'...' if len(res['text']) > 75 else ''}\"",
        "-" * 60,
        f"  Language:        {res['language']}",
        f"  Category:        {res['category']} (Dept: {res['department']})",
        f"  Urgency:         {res['urgency']}",
        f"  District / Area: {res['location']}",
        f"  State:           {res['state']}",
        f"  Rule Confidence: {res['confidence']:.1%}",
        "-" * 60,
        f"  [scikit-learn]   Category: {res['sklearn_category']} (Conf: {res['sklearn_confidence']:.1%})",
        "=" * 60,
        ""
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="JanSamadhan Offline Grievance Triage CLI")
    parser.add_argument("text", nargs="?", type=str, help="Grievance text in any supported language")
    args = parser.parse_args()

    if not args.text:
        print("\nUsage: python backend/cli.py \"<your grievance statement>\"")
        print("Example: python backend/cli.py \"pani supply nahi aa raha, Cuttack mein 3 din se\"\n")
        return

    result = triage_text(args.text)
    print(format_triage_output(result))


if __name__ == "__main__":
    main()
