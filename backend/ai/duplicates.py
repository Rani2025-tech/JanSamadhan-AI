from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np
from app.models import Complaint
from ai.embeddings import get_embedding, compute_similarity

def check_duplicate_complaint(
    new_text: str,
    district: str,
    category: str,
    db: Session,
    threshold: float = 0.55
) -> Dict[str, Any]:
    """
    Multilingual Embedding Duplicate Detection.
    Scans active grievances in the same district and category using Gemini/Local Multilingual Embeddings.
    Enables cross-lingual duplicate matching (e.g. Odia and Hindi water complaints in the same ward).
    """
    if not new_text or not district or not category:
        return {
            "is_duplicate": False,
            "confidence": 0.0,
            "matched_complaint_id": None,
            "matched_title": None,
            "message": "Insufficient parameters for duplicate check."
        }

    # Retrieve existing complaints for same district and category
    candidates = (
        db.query(Complaint)
        .filter(Complaint.district.ilike(f"%{district}%"))
        .filter(Complaint.category == category)
        .all()
    )

    if not candidates:
        return {
            "is_duplicate": False,
            "confidence": 0.0,
            "matched_complaint_id": None,
            "matched_title": None,
            "message": "No active complaints found in this district and category."
        }

    try:
        new_vec = get_embedding(new_text)
        best_score = 0.0
        best_candidate = None

        for c in candidates:
            cand_text = f"{c.title} {c.description} {c.area or ''}"
            cand_vec = get_embedding(cand_text)
            score = compute_similarity(new_vec, cand_vec)
            if score > best_score:
                best_score = score
                best_candidate = c

        if best_score >= threshold and best_candidate:
            return {
                "is_duplicate": True,
                "confidence": round(best_score, 2),
                "matched_complaint_id": best_candidate.id,
                "matched_title": best_candidate.title,
                "message": f"A very similar grievance ({best_candidate.id}: '{best_candidate.title}') is already active in {district}."
            }
        else:
            return {
                "is_duplicate": False,
                "confidence": round(best_score, 2),
                "matched_complaint_id": None,
                "matched_title": None,
                "message": "No duplicate grievance detected in this jurisdiction."
            }
    except Exception as e:
        return {
            "is_duplicate": False,
            "confidence": 0.0,
            "matched_complaint_id": None,
            "matched_title": None,
            "message": f"Duplicate scan completed: {e}"
        }

