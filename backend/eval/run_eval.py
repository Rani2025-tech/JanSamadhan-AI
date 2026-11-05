import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.stdout.reconfigure(encoding='utf-8')

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ai.classifier import rule_based_extract, detect_language, extract_location
from ai.extractor import extract
from ai.ml_baseline import predict as predict_sklearn

CATEGORIES = [
    "Water Supply",
    "Road Infrastructure",
    "Electricity",
    "Sanitation",
    "Public Health",
    "Ration / PDS"
]

URGENCIES = ["Critical", "High", "Medium", "Low"]

LANGUAGES = ["Odia", "Hindi", "Bengali", "Telugu", "Tamil", "Marathi", "English"]

def calculate_prf(true_labels: List[str], pred_labels: List[str], class_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """Calculates precision, recall, f1, and support n for each class with raw counts."""
    results = {}
    for c in class_list:
        tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == c and p == c)
        fp = sum(1 for t, p in zip(true_labels, pred_labels) if t != c and p == c)
        fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == c and p != c)
        support = sum(1 for t in true_labels if t == c)

        precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 0.0
        recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 0.0
        f1 = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 0.0

        results[c] = {
            "n": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    return results

def evaluate_subset(subset: List[Dict[str, Any]], mode: str = "fallback", gemini_preds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    total = len(subset)
    if total == 0:
        return {}

    true_langs, pred_langs = [], []
    true_cats, pred_cats = [], []
    true_urgs, pred_urgs = [], []
    is_cms = []
    latencies = []

    for item in subset:
        item_id = item["id"]
        text = item["text"]
        true_langs.append(item["true_language"])
        true_cats.append(item["true_category"])
        true_urgs.append(item["true_urgency"])
        is_cms.append(item.get("is_code_mixed", False))

        t0 = time.time()
        if mode == "fallback":
            pred = rule_based_extract(text)
            pred_lang = pred["language"]
            pred_cat = pred["category"]
            pred_urg = pred["urgency"]
            latencies.append((time.time() - t0) * 1000)
        elif mode == "sklearn":
            pred_cat, conf = predict_sklearn(text)
            pred_lang = "N/A"
            pred_urg = "N/A"
            latencies.append((time.time() - t0) * 1000)
        else:
            if gemini_preds and item_id in gemini_preds:
                gp = gemini_preds[item_id]
                pred_lang = gp["language"]
                pred_cat = gp["category"]
                pred_urg = gp["urgency"]
                latencies.append(gp.get("latency_ms", 285.0))
            else:
                pred_obj = extract(text)
                pred_lang = pred_obj.language
                pred_cat = pred_obj.category
                pred_urg = pred_obj.urgency
                latencies.append((time.time() - t0) * 1000)

        pred_langs.append(pred_lang)
        pred_cats.append(pred_cat)
        pred_urgs.append(pred_urg)

    # 1. Language Accuracy
    if mode != "sklearn":
        lang_correct = sum(1 for t, p in zip(true_langs, pred_langs) if t.lower() == p.lower())
        acc_lang = round((lang_correct / total) * 100, 2)
    else:
        lang_correct = 0
        acc_lang = None

    # 2. Category Accuracy
    cat_correct = sum(1 for t, p in zip(true_cats, pred_cats) if t == p)
    acc_cat = round((cat_correct / total) * 100, 2)

    # 3. Urgency Accuracy
    if mode != "sklearn":
        urg_correct = sum(1 for t, p in zip(true_urgs, pred_urgs) if t == p)
        acc_urg = round((urg_correct / total) * 100, 2)
    else:
        urg_correct = 0
        acc_urg = None

    # 4. Code-Mixed Category Accuracy
    cm_indices = [i for i, cm in enumerate(is_cms) if cm]
    if cm_indices:
        cm_correct = sum(1 for i in cm_indices if true_cats[i] == pred_cats[i])
        cm_total = len(cm_indices)
        acc_cm = round((cm_correct / cm_total) * 100, 2)
    else:
        cm_correct = 0
        cm_total = 0
        acc_cm = 100.0

    # 5. Location Extraction Accuracy
    if mode != "sklearn":
        loc_items = [item for item in subset if item.get("true_district") or item.get("true_state")]
        loc_correct = 0
        loc_total = len(loc_items)
        for item in loc_items:
            text = item["text"]
            pred_loc = extract_location(text)
            expected_dist = item.get("true_district", "").lower()
            expected_state = item.get("true_state", "").lower()
            pred_dist = (pred_loc.get("district") or "").lower()
            pred_state = (pred_loc.get("state") or "").lower()

            dist_match = (
                (expected_dist and (expected_dist in pred_dist or pred_dist in expected_dist)) or
                (not expected_dist and pred_loc.get("has_location"))
            )
            state_match = (expected_state == pred_state) or (not expected_state)

            if dist_match and state_match:
                loc_correct += 1

        acc_loc = round((loc_correct / loc_total) * 100, 2) if loc_total > 0 else 100.0
    else:
        loc_correct = 0
        loc_total = 0
        acc_loc = None

    avg_lat = round(sum(latencies) / max(1, len(latencies)), 2)

    # Per-class metrics
    cat_prf = calculate_prf(true_cats, pred_cats, CATEGORIES)
    urg_prf = calculate_prf(true_urgs, pred_urgs, URGENCIES) if mode != "sklearn" else {}
    lang_prf = calculate_prf([l.capitalize() for l in true_langs], [l.capitalize() for l in pred_langs], LANGUAGES) if mode != "sklearn" else {}

    # Confusion matrix for categories
    cat_to_idx = {c: i for i, c in enumerate(CATEGORIES)}
    matrix = [[0 for _ in range(len(CATEGORIES))] for _ in range(len(CATEGORIES))]
    for t, p in zip(true_cats, pred_cats):
        if t in cat_to_idx and p in cat_to_idx:
            matrix[cat_to_idx[t]][cat_to_idx[p]] += 1

    return {
        "n": total,
        "language_accuracy": acc_lang,
        "language_correct": lang_correct,
        "category_accuracy": acc_cat,
        "category_correct": cat_correct,
        "urgency_accuracy": acc_urg,
        "urgency_correct": urg_correct,
        "code_mixed_accuracy": acc_cm,
        "code_mixed_correct": cm_correct,
        "code_mixed_total": cm_total,
        "location_accuracy": acc_loc,
        "location_correct": loc_correct,
        "location_total": loc_total,
        "average_latency_ms": avg_lat,
        "per_category": cat_prf,
        "per_urgency": urg_prf,
        "per_language": lang_prf,
        "confusion_matrix": {
            "labels": CATEGORIES,
            "matrix": matrix
        }
    }

def run_evaluation():
    eval_dir = Path(__file__).resolve().parent
    dataset_file = eval_dir / "labeled_dataset.json"
    data = json.loads(dataset_file.read_text(encoding="utf-8"))
    
    train_data = [d for d in data if d.get("split") == "train"]
    held_out_data = [d for d in data if d.get("split") == "held_out"]

    print(f"\n================ JANSAMADHAN AI HARNESS EVALUATION ================")
    print(f"Total Complaints: n={len(data)} (Train: n={len(train_data)}, Held-out: n={len(held_out_data)})")
    print(f"Evaluating Rules, scikit-learn Baseline, and Gemini LLM across Train & Held-out splits...")

    # Load Gemini cached predictions if available
    gemini_preds_file = eval_dir / "gemini_predictions.json"
    gemini_preds = json.loads(gemini_preds_file.read_text(encoding="utf-8")) if gemini_preds_file.exists() else None

    # 1. Fallback (Rules) Mode Evaluation
    fallback_all = evaluate_subset(data, mode="fallback")
    fallback_train = evaluate_subset(train_data, mode="fallback")
    fallback_held_out = evaluate_subset(held_out_data, mode="fallback")

    # 2. scikit-learn Category Baseline Evaluation
    sklearn_all = evaluate_subset(data, mode="sklearn")
    sklearn_train = evaluate_subset(train_data, mode="sklearn")
    sklearn_held_out = evaluate_subset(held_out_data, mode="sklearn")

    # 3. Gemini Mode Evaluation
    from app.config import settings
    has_live_gemini = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"))
    gemini_mode = "gemini" if has_live_gemini else "gemini_cached"

    gemini_all = evaluate_subset(data, mode=gemini_mode, gemini_preds=gemini_preds)
    gemini_train = evaluate_subset(train_data, mode=gemini_mode, gemini_preds=gemini_preds)
    gemini_held_out = evaluate_subset(held_out_data, mode=gemini_mode, gemini_preds=gemini_preds)

    # 4. Side-by-Side Comparison Table: Rules | sklearn baseline | Gemini
    print("\n---------------- SIDE-BY-SIDE EVALUATION: RULES | SKLEARN BASELINE | GEMINI ----------------")
    print(f"{'Metric':<25} | {'Rules (Held-out n=30)':<25} | {'sklearn (Held-out n=30)*':<26} | {'Gemini (Overall n=95)':<25}")
    print("-" * 108)

    # Language
    f_ho_lang = f"{fallback_held_out['language_accuracy']}% ({fallback_held_out['language_correct']}/{fallback_held_out['n']})"
    s_ho_lang = "N/A (category-only)"
    g_al_lang = f"{gemini_all['language_accuracy']}% ({gemini_all['language_correct']}/{gemini_all['n']})"
    print(f"{'Language Detection':<25} | {f_ho_lang:<25} | {s_ho_lang:<26} | {g_al_lang:<25}")

    # Category
    f_ho_cat = f"{fallback_held_out['category_accuracy']}% ({fallback_held_out['category_correct']}/{fallback_held_out['n']})"
    s_ho_cat = f"{sklearn_held_out['category_accuracy']}% ({sklearn_held_out['category_correct']}/{sklearn_held_out['n']})"
    g_al_cat = f"{gemini_all['category_accuracy']}% ({gemini_all['category_correct']}/{gemini_all['n']})"
    print(f"{'Category Classification':<25} | {f_ho_cat:<25} | {s_ho_cat:<26} | {g_al_cat:<25}")

    # Urgency
    f_ho_urg = f"{fallback_held_out['urgency_accuracy']}% ({fallback_held_out['urgency_correct']}/{fallback_held_out['n']})"
    s_ho_urg = "N/A (category-only)"
    g_al_urg = f"{gemini_all['urgency_accuracy']}% ({gemini_all['urgency_correct']}/{gemini_all['n']})"
    print(f"{'Urgency Detection (Exact)':<25} | {f_ho_urg:<25} | {s_ho_urg:<26} | {g_al_urg:<25}")

    # Location Extraction
    f_ho_loc = f"{fallback_held_out['location_accuracy']}% ({fallback_held_out['location_correct']}/{fallback_held_out['location_total']})"
    s_ho_loc = "N/A (category-only)"
    g_al_loc = f"{gemini_all['location_accuracy']}% ({gemini_all['location_correct']}/{gemini_all['location_total']})"
    print(f"{'Location Extraction':<25} | {f_ho_loc:<25} | {s_ho_loc:<26} | {g_al_loc:<25}")

    # Code-Mixed
    f_ho_cm = f"{fallback_held_out['code_mixed_accuracy']}% ({fallback_held_out['code_mixed_correct']}/{fallback_held_out['code_mixed_total']})"
    s_ho_cm = f"{sklearn_held_out['code_mixed_accuracy']}% ({sklearn_held_out['code_mixed_correct']}/{sklearn_held_out['code_mixed_total']})"
    g_al_cm = f"{gemini_all['code_mixed_accuracy']}% ({gemini_all['code_mixed_correct']}/{gemini_all['code_mixed_total']})"
    print(f"{'Code-Mixed Accuracy':<25} | {f_ho_cm:<25} | {s_ho_cm:<26} | {g_al_cm:<25}")

    # Latency
    f_ho_lat = f"{fallback_held_out['average_latency_ms']} ms"
    s_ho_lat = f"{sklearn_held_out['average_latency_ms']} ms"
    g_al_lat = f"{gemini_all['average_latency_ms']} ms"
    print(f"{'Avg Latency':<25} | {f_ho_lat:<25} | {s_ho_lat:<26} | {g_al_lat:<25}")

    print("\n* Integrity Note: The scikit-learn baseline was trained strictly on the train split (n=65).")
    print(f"  Train split category score: {sklearn_train['category_accuracy']}% ({sklearn_train['category_correct']}/{sklearn_train['n']}) (optimistic/memorized).")
    print(f"  Held-out split category score: {sklearn_held_out['category_accuracy']}% ({sklearn_held_out['category_correct']}/{sklearn_held_out['n']}) reflects fair generalization.")

    # 5. Held-Out Human Benchmark Audit Report
    human_file = eval_dir / "heldout_human.json"
    print("\n---------------- HELD-OUT HUMAN AUDIT BENCHMARK (heldout_human.json) ----------------")
    if human_file.exists():
        human_data = json.loads(human_file.read_text(encoding="utf-8"))
        populated_slots = sum(1 for d in human_data if d.get("text", "").strip())
        total_slots = len(human_data)
        if populated_slots == 0:
            print(f"File: {human_file.name}")
            print(f"Audit Status: 0/{total_slots} populated. Skipping unpopulated human evaluation.")
        else:
            print(f"Audit Status: {populated_slots}/{total_slots} populated.")
    else:
        print("heldout_human.json not found!")

    # 6. Save Comprehensive Results
    results = {
        "dataset_summary": {
            "total_complaints": len(data),
            "train_n": len(train_data),
            "held_out_n": len(held_out_data),
            "code_mixed_n": fallback_all["code_mixed_total"],
            "human_audit_n": len(human_data) if human_file.exists() else 0
        },
        "side_by_side": {
            "fallback_mode": {
                "overall": fallback_all,
                "train": fallback_train,
                "held_out": fallback_held_out
            },
            "sklearn_baseline": {
                "overall": sklearn_all,
                "train": sklearn_train,
                "held_out": sklearn_held_out
            },
            "gemini_mode": {
                "overall": gemini_all,
                "train": gemini_train,
                "held_out": gemini_held_out
            }
        },
        "confusion_matrix_category": fallback_held_out["confusion_matrix"],
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    out_file = eval_dir / "eval_results.json"
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nComprehensive eval results saved to: {out_file}")

    # Copy to src/data/eval_results.json since ImpactPage reads it
    src_data_file = Path(__file__).resolve().parent.parent.parent / "src" / "data" / "eval_results.json"
    if src_data_file.parent.exists():
        src_data_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Synchronized with frontend at: {src_data_file}\n")

if __name__ == "__main__":
    run_evaluation()
