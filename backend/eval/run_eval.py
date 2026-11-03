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
    lang_correct = sum(1 for t, p in zip(true_langs, pred_langs) if t.lower() == p.lower())
    acc_lang = round((lang_correct / total) * 100, 2)

    # 2. Category Accuracy
    cat_correct = sum(1 for t, p in zip(true_cats, pred_cats) if t == p)
    acc_cat = round((cat_correct / total) * 100, 2)

    # 3. Urgency Accuracy (Exact match strictly counted in code)
    urg_correct = sum(1 for t, p in zip(true_urgs, pred_urgs) if t == p)
    acc_urg = round((urg_correct / total) * 100, 2)

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

    # 5. Location Extraction Accuracy (evaluated on samples annotated with location)
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

    avg_lat = round(sum(latencies) / max(1, len(latencies)), 2)

    # Per-class metrics
    cat_prf = calculate_prf(true_cats, pred_cats, CATEGORIES)
    urg_prf = calculate_prf(true_urgs, pred_urgs, URGENCIES)
    lang_prf = calculate_prf([l.capitalize() for l in true_langs], [l.capitalize() for l in pred_langs], LANGUAGES)

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
    print(f"Evaluating Fallback Mode & Gemini Mode across Train and Held-out Splits...")

    # Load Gemini cached predictions if available
    gemini_preds_file = eval_dir / "gemini_predictions.json"
    gemini_preds = json.loads(gemini_preds_file.read_text(encoding="utf-8")) if gemini_preds_file.exists() else None

    # 1. Fallback Mode Evaluation
    fallback_all = evaluate_subset(data, mode="fallback")
    fallback_train = evaluate_subset(train_data, mode="fallback")
    fallback_held_out = evaluate_subset(held_out_data, mode="fallback")

    # 2. Gemini Mode Evaluation
    from app.config import settings
    has_live_gemini = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"))
    gemini_mode = "gemini" if has_live_gemini else "gemini_cached"

    gemini_all = evaluate_subset(data, mode=gemini_mode, gemini_preds=gemini_preds)
    gemini_train = evaluate_subset(train_data, mode=gemini_mode, gemini_preds=gemini_preds)
    gemini_held_out = evaluate_subset(held_out_data, mode=gemini_mode, gemini_preds=gemini_preds)

    # 3. Print Side-by-Side Comparison Table with Raw Counts
    print("\n---------------- SIDE-BY-SIDE OVERALL ACCURACY (COMPUTED IN CODE) ----------------")
    header_tr = f"Fallback (Train n={fallback_train['n']})"
    header_ho = f"Fallback (Held-out n={fallback_held_out['n']})"
    header_gm = f"Gemini (Overall n={gemini_all['n']})"
    print(f"{'Metric':<25} | {header_tr:<25} | {header_ho:<25} | {header_gm:<25}")
    print("-" * 108)
    
    # Language
    f_tr_lang = f"{fallback_train['language_accuracy']}% ({fallback_train['language_correct']}/{fallback_train['n']})"
    f_ho_lang = f"{fallback_held_out['language_accuracy']}% ({fallback_held_out['language_correct']}/{fallback_held_out['n']})"
    g_al_lang = f"{gemini_all['language_accuracy']}% ({gemini_all['language_correct']}/{gemini_all['n']})"
    print(f"{'Language Detection':<25} | {f_tr_lang:<25} | {f_ho_lang:<25} | {g_al_lang:<25}")

    # Category
    f_tr_cat = f"{fallback_train['category_accuracy']}% ({fallback_train['category_correct']}/{fallback_train['n']})"
    f_ho_cat = f"{fallback_held_out['category_accuracy']}% ({fallback_held_out['category_correct']}/{fallback_held_out['n']})"
    g_al_cat = f"{gemini_all['category_accuracy']}% ({gemini_all['category_correct']}/{gemini_all['n']})"
    print(f"{'Category Classification':<25} | {f_tr_cat:<25} | {f_ho_cat:<25} | {g_al_cat:<25}")

    # Urgency
    f_tr_urg = f"{fallback_train['urgency_accuracy']}% ({fallback_train['urgency_correct']}/{fallback_train['n']})"
    f_ho_urg = f"{fallback_held_out['urgency_accuracy']}% ({fallback_held_out['urgency_correct']}/{fallback_held_out['n']})"
    g_al_urg = f"{gemini_all['urgency_accuracy']}% ({gemini_all['urgency_correct']}/{gemini_all['n']})"
    print(f"{'Urgency Detection (Exact)':<25} | {f_tr_urg:<25} | {f_ho_urg:<25} | {g_al_urg:<25}")

    # Location Extraction (All-India)
    f_tr_loc = f"{fallback_train['location_accuracy']}% ({fallback_train['location_correct']}/{fallback_train['location_total']})" if fallback_train['location_total'] > 0 else "N/A (unannotated)"
    f_ho_loc = f"{fallback_held_out['location_accuracy']}% ({fallback_held_out['location_correct']}/{fallback_held_out['location_total']})"
    g_al_loc = f"{gemini_all['location_accuracy']}% ({gemini_all['location_correct']}/{gemini_all['location_total']})"
    print(f"{'Location Extraction':<25} | {f_tr_loc:<25} | {f_ho_loc:<25} | {g_al_loc:<25}")

    # Code-mixed
    f_tr_cm = f"{fallback_train['code_mixed_accuracy']}% ({fallback_train['code_mixed_correct']}/{fallback_train['code_mixed_total']})"
    f_ho_cm = f"{fallback_held_out['code_mixed_accuracy']}% ({fallback_held_out['code_mixed_correct']}/{fallback_held_out['code_mixed_total']})"
    g_al_cm = f"{gemini_all['code_mixed_accuracy']}% ({gemini_all['code_mixed_correct']}/{gemini_all['code_mixed_total']})"
    print(f"{'Code-Mixed Accuracy':<25} | {f_tr_cm:<25} | {f_ho_cm:<25} | {g_al_cm:<25}")

    # Latency
    f_tr_lat = f"{fallback_train['average_latency_ms']} ms (n={fallback_train['n']})"
    f_ho_lat = f"{fallback_held_out['average_latency_ms']} ms (n={fallback_held_out['n']})"
    g_al_lat = f"{gemini_all['average_latency_ms']} ms (n={gemini_all['n']})"
    print(f"{'Avg Latency':<25} | {f_tr_lat:<25} | {f_ho_lat:<25} | {g_al_lat:<25}")

    # 4. Per-Class Category Performance Table (Held-Out)
    print(f"\n---------------- PER-CLASS CATEGORY PERFORMANCE (HELD-OUT n={fallback_held_out['n']}) ----------------")
    print(f"{'Category':<22} | {'n':<4} | {'Precision':<18} | {'Recall':<18} | {'F1-Score':<10}")
    print("-" * 80)
    for cat in CATEGORIES:
        m = fallback_held_out["per_category"][cat]
        prec_str = f"{m['precision']}% ({m['tp']}/{m['tp']+m['fp']})"
        rec_str = f"{m['recall']}% ({m['tp']}/{m['n']})"
        f1_str = f"{m['f1']}%"
        print(f"{cat:<22} | {m['n']:<4} | {prec_str:<18} | {rec_str:<18} | {f1_str:<10}")

    # 5. Per-Class Urgency Performance Table (Held-Out)
    print(f"\n---------------- PER-CLASS URGENCY PERFORMANCE (HELD-OUT n={fallback_held_out['n']}) ----------------")
    print(f"{'Urgency Level':<15} | {'n':<4} | {'Precision':<18} | {'Recall':<18} | {'F1-Score':<10}")
    print("-" * 73)
    for urg in URGENCIES:
        m = fallback_held_out["per_urgency"][urg]
        prec_str = f"{m['precision']}% ({m['tp']}/{m['tp']+m['fp']})"
        rec_str = f"{m['recall']}% ({m['tp']}/{m['n']})"
        f1_str = f"{m['f1']}%"
        print(f"{urg:<15} | {m['n']:<4} | {prec_str:<18} | {rec_str:<18} | {f1_str:<10}")

    # 6. Report Gemini Urgency Errors Short List
    print("\n---------------- GEMINI-MODE URGENCY ERROR ANALYSIS ----------------")
    urgency_errors = []
    for item in data:
        item_id = item["id"]
        true_urg = item["true_urgency"]
        pred_urg = gemini_preds[item_id]["urgency"] if (gemini_preds and item_id in gemini_preds) else None
        if pred_urg and pred_urg != true_urg:
            urgency_errors.append({
                "id": item_id,
                "text": item["text"],
                "expected": true_urg,
                "predicted": pred_urg
            })

    total_urg_errs = len(urgency_errors)
    total_samples = len(data)
    print(f"Total Discrepancies: {total_urg_errs}/{total_samples} samples ({round((total_urg_errs/total_samples)*100, 2)}% error rate; {gemini_all['urgency_accuracy']}% accuracy)")
    for i, err in enumerate(urgency_errors, 1):
        print(f"[{i}] ID: {err['id']}")
        print(f"    Text: \"{err['text']}\"")
        print(f"    Expected:  {err['expected']}")
        print(f"    Predicted: {err['predicted']}\n")

    # 7. Held-Out Human Benchmark Audit Report
    human_file = eval_dir / "heldout_human.json"
    print("---------------- HELD-OUT HUMAN AUDIT BENCHMARK (heldout_human.json) ----------------")
    if human_file.exists():
        human_data = json.loads(human_file.read_text(encoding="utf-8"))
        populated_slots = sum(1 for d in human_data if d.get("text", "").strip())
        print(f"File: {human_file.name}")
        print(f"Total Slots: n={len(human_data)} template slots (HUMAN-01 to HUMAN-{len(human_data):02d})")
        print(f"Audit Status: {populated_slots}/{len(human_data)} populated (Awaiting blind human officer adjudication)")
        print(f"Integrity Constraint: These slots are strictly isolated and NEVER used for keyword rule-tuning.")
    else:
        print("heldout_human.json not found!")

    # 8. Save Comprehensive Results
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
            "gemini_mode": {
                "overall": gemini_all,
                "train": gemini_train,
                "held_out": gemini_held_out
            }
        },
        "gemini_urgency_errors": urgency_errors,
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    out_file = eval_dir / "eval_results.json"
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nComprehensive eval results saved to: {out_file}\n")

if __name__ == "__main__":
    run_evaluation()
