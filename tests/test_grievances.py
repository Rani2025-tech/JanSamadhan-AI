import os
import sys
import tempfile
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.db.database as db
from backend.db.grievances import (
    create_grievance,
    get_grievance,
    list_grievances,
    update_status,
    add_feedback,
    find_open_in_area,
    create_cluster,
    attach_to_cluster,
    list_clusters,
    get_stats,
    SLA_HOURS
)

def run_tests():
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_jansamadhan.db")
    db.DB_PATH = temp_db_path
    db.DATABASE_URL = None

    print(f"Initializing test DB at: {temp_db_path}")
    db.init_db()

    # 1. Create 3 grievances with new columns
    g1 = {
        "citizen_name": "Ramesh Kumar",
        "contact": "9876543210",
        "area": "Ward 12",
        "location": "Near Main Market Gate",
        "original_text": "Water pipeline burst causing major flooding",
        "summary": "Water pipeline burst causing flood",
        "language": "en",
        "department": "Water Supply",
        "category": "Pipeline",
        "confidence": 0.95,
        "priority": "Critical",
        "needs_review": 0
    }

    g2 = {
        "citizen_name": "Sunita Devi",
        "contact": "9876543211",
        "area": "Ward 5",
        "location": "Opposite City High School",
        "original_text": "Dangerous road pothole near school",
        "summary": "Pothole near school",
        "language": "hi",
        "department": "Roads",
        "category": "Pothole",
        "confidence": 0.90,
        "priority": "High",
        "needs_review": 0
    }

    g3 = {
        "citizen_name": "Amit Patel",
        "contact": "9876543212",
        "area": "Ward 12",
        "location": "Street 4 Pole 18",
        "original_text": "Streetlight not working since 3 days",
        "summary": "Non-functional streetlight",
        "language": "en",
        "department": "Electricity",
        "category": "Streetlight",
        "confidence": 0.88,
        "priority": "Medium",
        "needs_review": 1
    }

    t1 = create_grievance(g1)
    t2 = create_grievance(g2)
    t3 = create_grievance(g3)

    print(f"Created tickets: {t1}, {t2}, {t3}")

    # Assert new sequential ticket ID format starting at 1001
    assert t1 == "GRV-1001", f"Expected GRV-1001, got {t1}"
    assert t2 == "GRV-1002", f"Expected GRV-1002, got {t2}"
    assert t3 == "GRV-1003", f"Expected GRV-1003, got {t3}"

    # Assert new columns retrieved
    rec1 = get_grievance(t1)
    assert rec1["summary"] == "Water pipeline burst causing flood"
    assert rec1["location"] == "Near Main Market Gate"
    assert rec1["needs_review"] == 0

    rec3 = get_grievance(t3)
    assert rec3["needs_review"] == 1

    # Assert SLA calculation
    c_time = datetime.strptime(rec1["created_at"][:19], "%Y-%m-%d %H:%M:%S")
    sla_time = datetime.strptime(rec1["sla_due_at"][:19], "%Y-%m-%d %H:%M:%S")
    diff_hours = round((sla_time - c_time).total_seconds() / 3600.0)
    assert diff_hours == 24, f"Expected 24h SLA for Critical, got {diff_hours}h"

    # 2. Test clusters
    cid = create_cluster(department="Water Supply", category="Pipeline", area="Ward 12", representative_ticket_id=t1)
    assert cid.startswith("CLU-")
    rec1_after_clu = get_grievance(t1)
    assert rec1_after_clu["cluster_id"] == cid

    # Attach another ticket to cluster
    attached = attach_to_cluster(t3, cid)
    assert attached is True
    rec3_after_clu = get_grievance(t3)
    assert rec3_after_clu["cluster_id"] == cid

    clusters = list_clusters()
    assert len(clusters) == 1
    assert clusters[0]["report_count"] == 2

    # 3. Update status & test feedback reopen
    update_status(t1, "Resolved", "Pipeline fixed", "Civic Worker")
    fb = add_feedback(t1, rating=2, comment="Still dripping slightly")
    rec1_reopened = get_grievance(t1)
    assert rec1_reopened["status"] == "Reopened"

    # 4. Assert updated get_stats()
    stats = get_stats()
    assert "hotspots" in stats
    assert "Ward 12" in stats["hotspots"]
    assert stats["hotspots"]["Ward 12"] == 2
    assert "clusters" in stats
    assert stats["clusters"]["total_clusters"] == 1
    assert "avg_resolution_by_dept" in stats

    print("ALL PATCH TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
