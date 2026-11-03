import os
import json
import re
from typing import Dict, Any, List, Optional
import numpy as np

ROUTE_CONFIDENCE = 0.55
REVIEW_THRESHOLD = 0.45

_CATEGORIES_DATA: Optional[List[Dict[str, Any]]] = None
_CATEGORY_EMBEDDINGS: Optional[np.ndarray] = None
_CATEGORY_KEYWORDS: Dict[str, set] = {}

def _load_categories_data() -> List[Dict[str, Any]]:
    global _CATEGORIES_DATA, _CATEGORY_KEYWORDS
    if _CATEGORIES_DATA is None:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "departments.json"
        )
        with open(data_path, "r", encoding="utf-8") as f:
            _CATEGORIES_DATA = json.load(f)

        for cat in _CATEGORIES_DATA:
            cname = cat["category"]
            words = re.findall(r"\w+", (cat.get("description", "") + " " + " ".join(cat.get("examples", []))).lower())
            # Filter short/common words
            _CATEGORY_KEYWORDS[cname] = {w for w in words if len(w) > 3}
    return _CATEGORIES_DATA

def _get_category_embeddings() -> np.ndarray:
    global _CATEGORY_EMBEDDINGS
    if _CATEGORY_EMBEDDINGS is None:
        from backend.core.embedder import embed
        cats = _load_categories_data()
        texts = [
            f"{c['category']} - {c['department']}: {c.get('description', '')}. {' '.join(c.get('examples', []))}"
            for c in cats
        ]
        _CATEGORY_EMBEDDINGS = embed(texts)
    return _CATEGORY_EMBEDDINGS

def classify(english_text: str) -> Dict[str, Any]:
    """
    Classifies complaint text into civic category using local embedding similarity + keyword boosts.
    Returns: {category, department, confidence, reason, scores}
    """
    cats = _load_categories_data()
    cat_embeddings = _get_category_embeddings()

    from backend.core.embedder import embed_single
    query_emb = embed_single(english_text)

    # Cosine similarity with normalized embeddings
    raw_sims = np.dot(cat_embeddings, query_emb)

    # Keyword boost
    q_words = set(re.findall(r"\w+", english_text.lower()))
    boosted_sims = raw_sims.copy()
    matched_kw_map = {}

    for idx, c in enumerate(cats):
        cname = c["category"]
        kws = _CATEGORY_KEYWORDS.get(cname, set())
        overlap = q_words.intersection(kws)
        if overlap:
            boost = min(0.20, len(overlap) * 0.05)
            boosted_sims[idx] += boost
            matched_kw_map[cname] = list(overlap)[:3]

    # Softmax with temperature for confidence
    temp = 0.12
    exp_sims = np.exp((boosted_sims - np.max(boosted_sims)) / temp)
    probs = exp_sims / np.sum(exp_sims)

    top_indices = np.argsort(boosted_sims)[::-1]
    best_idx = top_indices[0]
    best_cat = cats[best_idx]["category"]
    best_dept = cats[best_idx]["department"]
    confidence = float(np.clip(probs[best_idx], 0.0, 0.99))

    top_scores = [
        {"category": cats[i]["category"], "score": round(float(probs[i]), 4)}
        for i in top_indices[:3]
    ]

    matched_words = matched_kw_map.get(best_cat, [])
    if matched_words:
        reason = f"High semantic match with {best_cat} (keywords: {', '.join(matched_words)})"
    else:
        reason = f"Semantic similarity match with {best_cat} operations ({round(float(raw_sims[best_idx]), 2)})"

    return {
        "category": best_cat,
        "department": best_dept,
        "confidence": round(confidence, 4),
        "reason": reason,
        "scores": top_scores
    }

def route(understood: Dict[str, Any]) -> Dict[str, Any]:
    """
    Arbitrates between LLM-extracted category and local classification.
    """
    cats = {c["category"]: c["department"] for c in _load_categories_data()}
    eng_text = understood.get("english_text", "")
    llm_cat = understood.get("category", "Other / Needs Review")
    used_llm = understood.get("used_llm", False)

    local_res = classify(eng_text)
    local_cat = local_res["category"]
    local_dept = local_res["department"]
    local_conf = local_res["confidence"]

    if not used_llm:
        final_cat = local_cat
        final_dept = local_dept
        final_conf = local_conf
        source = "local"
        needs_review = bool(local_conf < REVIEW_THRESHOLD or understood.get("needs_review", False))
        reason = f"Local router: {local_res['reason']}"
    else:
        if llm_cat == local_cat:
            final_cat = local_cat
            final_dept = local_dept
            final_conf = min(0.99, max(local_conf, 0.85) + 0.1)
            source = "agree"
            needs_review = bool(final_cat == "Other / Needs Review")
            reason = f"LLM and local classifier agreed on {final_cat}"
        else:
            # Disagreement
            if local_conf >= ROUTE_CONFIDENCE:
                final_cat = local_cat
                final_dept = local_dept
                final_conf = local_conf
                source = "conflict"
                needs_review = False
                reason = f"Conflict: chosen local classification over LLM ({local_res['reason']})"
            else:
                final_cat = llm_cat
                final_dept = cats.get(llm_cat, "General Administration / Grievance Cell")
                final_conf = round(local_conf - 0.05, 4)
                source = "conflict"
                needs_review = True
                reason = f"Conflict: LLM selected '{llm_cat}' while local scored '{local_cat}' ({local_conf})"

    if final_conf < REVIEW_THRESHOLD or final_cat == "Other / Needs Review":
        final_cat = "Other / Needs Review"
        final_dept = cats.get("Other / Needs Review", "General Administration / Grievance Cell")
        needs_review = True

    return {
        "category": final_cat,
        "department": final_dept,
        "confidence": round(float(final_conf), 4),
        "reason": reason,
        "needs_review": needs_review,
        "source": source
    }
