"""
AI & Redressal NLP Benchmark Suite
==================================
Comprehensive evaluation and latency benchmarking across:
  1. Rule-based Multilingual Classifier (Offline Fallback Engine)
  2. scikit-learn Category Baseline (TF-IDF char n-grams + Logistic Regression)
  3. Google Gemini Multimodal Reasoning Engine (Live API if configured, otherwise skipped)

Generates:
  - backend/eval/reports/benchmark_report.md
  - backend/eval/reports/benchmark_report.json
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

# Resolve backend path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ai.classifier import rule_based_extract
from ai.ml_baseline import predict as predict_sklearn
from app.config import settings

EVAL_DIR = Path(__file__).resolve().parent
REPORTS_DIR = EVAL_DIR / "reports"
DATASET_FILE = EVAL_DIR / "labeled_dataset.json"

CATEGORIES = [
    "Water Supply",
    "Road Infrastructure",
    "Electricity",
    "Sanitation",
    "Public Health",
    "Ration / PDS"
]

LANGUAGES = ["Odia", "Hindi", "Bengali", "Telugu", "Tamil", "Marathi", "English"]


def load_dataset(subset_size: Optional[int] = None) -> List[Dict[str, Any]]:
    """Loads benchmark dataset, optionally slicing to a subset for smoke tests."""
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_FILE}")
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if subset_size is not None and subset_size > 0:
        return data[:subset_size]
    return data


def benchmark_method(
    name: str,
    predict_fn,
    dataset: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Runs accuracy, latency (mean & p95), confusion matrix, and error analysis for a classifier."""
    total = len(dataset)
    if total == 0:
        return {}

    latencies = []
    correct_count = 0
    errors = []

    # Per-language and per-category tracking
    by_lang = {l: {"total": 0, "correct": 0} for l in LANGUAGES}
    by_cat = {c: {"total": 0, "correct": 0} for c in CATEGORIES}

    # Confusion matrix
    cat_to_idx = {c: i for i, c in enumerate(CATEGORIES)}
    matrix = [[0 for _ in range(len(CATEGORIES))] for _ in range(len(CATEGORIES))]

    for item in dataset:
        text = item["text"]
        true_cat = item["true_category"]
        lang = item.get("true_language", "English")

        t0 = time.perf_counter()
        pred_cat, conf = predict_fn(text)
        t_elapsed = (time.perf_counter() - t0) * 1000.0  # ms
        latencies.append(t_elapsed)

        is_match = (pred_cat == true_cat)
        if is_match:
            correct_count += 1
        else:
            errors.append({
                "id": item.get("id", "N/A"),
                "language": lang,
                "input": text,
                "expected": true_cat,
                "predicted": pred_cat,
                "confidence": round(float(conf), 4) if conf is not None else None
            })

        # Track per-language
        if lang in by_lang:
            by_lang[lang]["total"] += 1
            if is_match:
                by_lang[lang]["correct"] += 1

        # Track per-category
        if true_cat in by_cat:
            by_cat[true_cat]["total"] += 1
            if is_match:
                by_cat[true_cat]["correct"] += 1

        # Track confusion matrix
        if true_cat in cat_to_idx and pred_cat in cat_to_idx:
            matrix[cat_to_idx[true_cat]][cat_to_idx[pred_cat]] += 1

    mean_lat = float(np.mean(latencies)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_lat = float(np.percentile(latencies, 99)) if latencies else 0.0
    acc = round((correct_count / total) * 100.0, 2)

    # Compute language accuracy percentages
    lang_breakdown = {}
    for l, d in by_lang.items():
        tot = d["total"]
        cor = d["correct"]
        lang_breakdown[l] = {
            "total": tot,
            "correct": cor,
            "accuracy": round((cor / tot) * 100.0, 2) if tot > 0 else None
        }

    # Compute category accuracy percentages
    cat_breakdown = {}
    for c, d in by_cat.items():
        tot = d["total"]
        cor = d["correct"]
        cat_breakdown[c] = {
            "total": tot,
            "correct": cor,
            "accuracy": round((cor / tot) * 100.0, 2) if tot > 0 else None
        }

    return {
        "method_name": name,
        "sample_size": total,
        "correct": correct_count,
        "accuracy": acc,
        "latency_ms": {
            "mean": round(mean_lat, 2),
            "p95": round(p95_lat, 2),
            "p99": round(p99_lat, 2)
        },
        "by_language": lang_breakdown,
        "by_category": cat_breakdown,
        "confusion_matrix": {
            "labels": CATEGORIES,
            "matrix": matrix
        },
        "errors": errors
    }


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Generates an evaluation benchmark report in GitHub-flavored Markdown."""
    lines = [
        "# JanSamadhan AI & NLP Benchmark Suite Report",
        "",
        f"**Generated:** {report_data['timestamp']}  ",
        f"**Benchmark Dataset Size:** n={report_data['sample_size']} complaints across 7 Indian languages  ",
        "",
        "---",
        "",
        "## 1. Overall Category Classification & Latency",
        "",
        "| Classifier / Engine | Accuracy | Raw Correct | Mean Latency | p95 Latency | Operational Notes |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |"
    ]

    for m_name, res in report_data["methods"].items():
        lat = res["latency_ms"]
        if "rules" in m_name.lower():
            notes = "Zero network dependency, keyword slot-filler"
        elif "sklearn" in m_name.lower() or "scikit-learn" in m_name.lower():
            notes = "scikit-learn TF-IDF char n-grams + LogisticRegression"
        else:
            notes = "Cloud LLM (structured JSON mode)"
        lines.append(
            f"| **{m_name}** | **{res['accuracy']}%** | {res['correct']}/{res['sample_size']} | {lat['mean']} ms | {lat['p95']} ms | {notes} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Per-Language Accuracy Breakdown",
        "",
        "| Language | " + " | ".join(f"**{m}**" for m in report_data["methods"].keys()) + " |",
        "| :--- | " + " | ".join(":---:" for _ in report_data["methods"]) + " |"
    ])

    for lang in LANGUAGES:
        cols = []
        for m_name, res in report_data["methods"].items():
            l_info = res["by_language"].get(lang, {})
            tot = l_info.get("total", 0)
            if tot > 0:
                cols.append(f"{l_info['accuracy']}% ({l_info['correct']}/{tot})")
            else:
                cols.append("—")
        lines.append(f"| **{lang}** | " + " | ".join(cols) + " |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Per-Category Accuracy Breakdown",
        "",
        "| Civic Category | " + " | ".join(f"**{m}**" for m in report_data["methods"].keys()) + " |",
        "| :--- | " + " | ".join(":---:" for _ in report_data["methods"]) + " |"
    ])

    for cat in CATEGORIES:
        cols = []
        for m_name, res in report_data["methods"].items():
            c_info = res["by_category"].get(cat, {})
            tot = c_info.get("total", 0)
            if tot > 0:
                cols.append(f"{c_info['accuracy']}% ({c_info['correct']}/{tot})")
            else:
                cols.append("—")
        lines.append(f"| **{cat}** | " + " | ".join(cols) + " |")

    # Error Analysis Section
    lines.extend([
        "",
        "---",
        "",
        "## 4. Error Analysis (Discrepancy Samples)",
        ""
    ])

    for m_name, res in report_data["methods"].items():
        err_list = res.get("errors", [])
        lines.append(f"### {m_name} (Errors: {len(err_list)}/{res['sample_size']})")
        if not err_list:
            lines.append("No classification discrepancies encountered on this test slice.\n")
        else:
            lines.append("| ID | Language | Input Text | Expected Category | Predicted | Conf |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :---: |")
            for err in err_list[:10]:  # Limit top 10 for readability
                conf_str = f"{err['confidence']:.2%}" if err.get("confidence") is not None else "—"
                lines.append(f"| {err['id']} | {err['language']} | \"{err['input'][:50]}...\" | {err['expected']} | {err['predicted']} | {conf_str} |")
            if len(err_list) > 10:
                lines.append(f"\n*... and {len(err_list) - 10} additional discrepancies recorded in JSON report.*")
            lines.append("")

    return "\n".join(lines)


def run_benchmark(subset_size: Optional[int] = None) -> Dict[str, Any]:
    """Runs complete benchmark suite across available classifiers and saves reports."""
    dataset = load_dataset(subset_size=subset_size)
    print(f"\n[Benchmark Suite] Initializing benchmark run on n={len(dataset)} complaints...")

    methods_results = {}

    # 1. Rule-based offline classifier
    def predict_rules(text: str):
        res = rule_based_extract(text)
        return res["category"], res.get("confidence", 0.90)

    print(" -> Benchmarking Rule-based Classifier...")
    methods_results["Rules (Offline Fallback)"] = benchmark_method(
        "Rules (Offline Fallback)",
        predict_rules,
        dataset
    )

    # 2. scikit-learn baseline
    print(" -> Benchmarking scikit-learn Category Baseline...")
    methods_results["scikit-learn Baseline"] = benchmark_method(
        "scikit-learn Baseline",
        predict_sklearn,
        dataset
    )

    # 3. Gemini LLM (Run live if API key configured and valid, otherwise skip or use cache)
    has_gemini = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"))
    if has_gemini:
        try:
            from ai.extractor import extract
            print(" -> Benchmarking Live Google Gemini API...")
            def predict_gemini(text: str):
                res = extract(text)
                return res.category, getattr(res, "confidence", 0.95)

            methods_results["Gemini Live LLM"] = benchmark_method(
                "Gemini Live LLM",
                predict_gemini,
                dataset[:15] if subset_size is None else dataset  # Keep live API benchmark bounded to avoid quota rate-limiting
            )
        except Exception as e:
            print(f" -> Skipping live Gemini benchmark: {e}")
    else:
        # Check if pre-cached predictions exist for offline Gemini benchmark
        cached_file = EVAL_DIR / "gemini_predictions.json"
        if cached_file.exists():
            cached_data = json.loads(cached_file.read_text(encoding="utf-8"))
            print(" -> Benchmarking Gemini via Golden Evaluation Cache (No Live Key Required)...")
            def predict_cached(text: str):
                for item_id, gp in cached_data.items():
                    if gp.get("text") == text:
                        return gp.get("category", "Water Supply"), 0.95
                return "Water Supply", 0.50

            methods_results["Gemini Model (Golden Cache)"] = benchmark_method(
                "Gemini Model (Golden Cache)",
                predict_cached,
                dataset
            )
        else:
            print(" -> Skipping Gemini benchmark (GEMINI_API_KEY not configured).")

    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sample_size": len(dataset),
        "methods": methods_results
    }

    # Write JSON and Markdown reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "benchmark_report.json"
    md_path = REPORTS_DIR / "benchmark_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    md_content = generate_markdown_report(report_data)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[Benchmark Suite] Reports successfully saved:")
    print(f"  - Markdown: {md_path}")
    print(f"  - JSON:     {json_path}\n")

    return report_data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="JanSamadhan AI Benchmark Suite")
    parser.add_argument("--subset", type=int, default=None, help="Evaluate on an n-sample subset")
    args = parser.parse_args()
    run_benchmark(subset_size=args.subset)
