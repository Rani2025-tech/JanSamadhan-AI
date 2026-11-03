from typing import Dict, Any, List, Optional
import numpy as np

from backend.core import embedder
from backend.db.grievances import (
    list_grievances,
    get_grievance,
    create_cluster,
    attach_to_cluster,
    list_clusters
)

DUPLICATE_THRESHOLD = 0.80

def find_duplicates(english_text: str, category: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Finds open grievances in the same category matching cosine similarity threshold.
    Adjusts threshold if locations match or conflict.
    """
    if not english_text:
        return []

    # Get open candidate tickets in the same category
    candidates = list_grievances(limit=200)
    open_candidates = [c for c in candidates if c.get("status") != "Resolved" and c.get("category") == category]
    if not open_candidates:
        return []

    query_emb = embedder.embed_single(english_text)
    duplicates = []

    for cand in open_candidates:
        cand_text = cand.get("summary") or cand.get("english_text") or cand.get("original_text", "")
        if not cand_text:
            continue

        cand_emb = embedder.embed_single(cand_text)
        sim = float(np.dot(query_emb, cand_emb))

        cand_loc = cand.get("location") or cand.get("area")
        needed_threshold = DUPLICATE_THRESHOLD

        if location and cand_loc:
            if location.strip().lower() == cand_loc.strip().lower():
                needed_threshold -= 0.05
            else:
                needed_threshold += 0.05

        if sim >= needed_threshold:
            duplicates.append({
                "ticket_id": cand["ticket_id"],
                "similarity": round(sim, 4)
            })

    duplicates.sort(key=lambda x: x["similarity"], reverse=True)
    return duplicates

def assign_cluster(
    ticket_id: str,
    english_text: str,
    category: str,
    department: str,
    location: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Checks for near-duplicate complaints and groups them into civic clusters.
    Returns {cluster_id, report_count, is_new} or None if no duplicate found.
    """
    dups = find_duplicates(english_text, category, location)
    dups = [d for d in dups if d.get("ticket_id") != ticket_id]
    if not dups:
        return None

    top_dup = dups[0]
    matched_tid = top_dup["ticket_id"]
    matched_record = get_grievance(matched_tid)
    if not matched_record:
        return None

    existing_cluster_id = matched_record.get("cluster_id")

    if existing_cluster_id:
        attach_to_cluster(ticket_id, existing_cluster_id)
        # Find updated count
        all_clusters = list_clusters()
        c_info = next((c for c in all_clusters if c["cluster_id"] == existing_cluster_id), None)
        count = c_info["report_count"] if c_info else 2
        return {
            "cluster_id": existing_cluster_id,
            "report_count": count,
            "is_new": False
        }
    else:
        area_str = location or matched_record.get("area") or "General Area"
        cluster_id = create_cluster(
            department=department,
            category=category,
            area=area_str,
            representative_ticket_id=matched_tid
        )
        attach_to_cluster(ticket_id, cluster_id)
        return {
            "cluster_id": cluster_id,
            "report_count": 2,
            "is_new": True
        }
