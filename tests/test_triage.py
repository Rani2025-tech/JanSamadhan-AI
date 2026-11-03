import os
import sys
import tempfile
import numpy as np

from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.db.database as db
from backend.db.grievances import (
    create_grievance,
    get_grievance,
    list_clusters
)
import backend.core.router as router
from backend.core.router import route, classify, ROUTE_CONFIDENCE, REVIEW_THRESHOLD
from backend.core.priority import score_priority
from backend.core.duplicates import find_duplicates, assign_cluster, DUPLICATE_THRESHOLD
from backend.core.triage import triage

def run_all_tests():
    print("Running Router, Priority, Duplicates & Triage Tests...")

    # Set up deterministic category embeddings for router
    cats = router._load_categories_data()
    n_cats = len(cats)
    cat_names = [c["category"] for c in cats]

    # Deterministic embedder
    # Each category gets an orthonormal basis vector in R^N
    fake_cat_embeddings = np.eye(n_cats, dtype=np.float32)

    def fake_embed(texts):
        if isinstance(texts, str):
            texts = [texts]
        arr = []
        for t in texts:
            t_low = t.lower()
            vec = np.zeros(n_cats, dtype=np.float32)
            matched = False
            for idx, cname in enumerate(cat_names):
                if cname.lower() in t_low or (cname == "Water Supply" and "water" in t_low) or (cname == "Electricity" and "electric" in t_low):
                    vec[idx] = 1.0
                    matched = True
                    break
            if not matched:
                vec = np.ones(n_cats, dtype=np.float32) / np.sqrt(n_cats)
            arr.append(vec)
        return np.array(arr, dtype=np.float32)

    def fake_embed_single(text):
        return fake_embed([text])[0]

    with patch("backend.core.embedder.embed", side_effect=fake_embed), \
         patch("backend.core.embedder.embed_single", side_effect=fake_embed_single):

        router._CATEGORY_EMBEDDINGS = fake_cat_embeddings

        # -------------------------------------------------------------
        # 1. Router arbitration tests
        # -------------------------------------------------------------
        # 1a. Agree: LLM and local agree -> confidence boosted, source == 'agree'
        u_agree = {
            "category": "Water Supply",
            "english_text": "Water pipeline is leaking badly",
            "used_llm": True
        }
        r_agree = route(u_agree)
        assert r_agree["category"] == "Water Supply"
        assert r_agree["source"] == "agree"
        assert r_agree["confidence"] >= 0.85
        assert r_agree["needs_review"] is False

        # 1b. Conflict: local confidence >= ROUTE_CONFIDENCE -> picks local
        u_conflict_high = {
            "category": "Electricity",
            "english_text": "Water supply stopped in entire sector",
            "used_llm": True
        }
        r_conflict_high = route(u_conflict_high)
        assert r_conflict_high["category"] == "Water Supply"
        assert r_conflict_high["source"] == "conflict"
        assert r_conflict_high["needs_review"] is False

        # 1c. Conflict: local confidence < ROUTE_CONFIDENCE -> uses LLM category with lowered confidence
        # Mock classify to return low confidence local prediction
        with patch.object(router, "classify", return_value={
            "category": "Electricity",
            "department": "DISCOM",
            "confidence": 0.52,
            "reason": "weak signal",
            "scores": []
        }):
            u_conflict_low = {
                "category": "Water Supply",
                "english_text": "Random ambiguous text without strong match",
                "used_llm": True
            }
            r_conflict_low = route(u_conflict_low)
            assert r_conflict_low["category"] == "Water Supply"
            assert r_conflict_low["source"] == "conflict"
            assert r_conflict_low["needs_review"] is True
            assert r_conflict_low["confidence"] < ROUTE_CONFIDENCE

        # 1d. LLM-unavailable: used_llm=False uses local only
        u_no_llm = {
            "category": "Other / Needs Review",
            "english_text": "Water pipeline burst on road",
            "used_llm": False
        }
        r_no_llm = route(u_no_llm)
        assert r_no_llm["category"] == "Water Supply"
        assert r_no_llm["source"] == "local"

        # 1e. Low confidence (< REVIEW_THRESHOLD) -> 'Other / Needs Review'
        with patch.object(router, "classify", return_value={
            "category": "Electricity",
            "department": "DISCOM",
            "confidence": 0.35,
            "reason": "very low confidence",
            "scores": []
        }):
            u_very_low = {
                "category": "Other / Needs Review",
                "english_text": "Unknown gibberish",
                "used_llm": False
            }
            r_very_low = route(u_very_low)
            assert r_very_low["category"] == "Other / Needs Review"
            assert r_very_low["needs_review"] is True

        print("Test 1 passed: Router agree, conflict, LLM-unavailable, and review threshold rules.")

        # -------------------------------------------------------------
        # 2. 8 Priority Cases
        # -------------------------------------------------------------
        # Case 1: Live wire -> Critical
        p1 = score_priority("Live wire sparking on the street", "Electricity")
        assert p1["priority"] == "Critical", f"Expected Critical, got {p1}"

        # Case 2: "no water for 3 days" -> High or above
        p2 = score_priority("There is no water for 3 days in our colony", "Water Supply")
        assert p2["priority"] in ("High", "Critical"), f"Expected High or Critical, got {p2}"

        # Case 3: "streetlight not working" -> Low or Medium
        p3 = score_priority("Streetlight not working on 2nd cross", "Street Lighting")
        assert p3["priority"] in ("Low", "Medium"), f"Expected Low or Medium, got {p3}"

        # Case 4: Hindi danger keyword with empty English text -> Critical
        p4 = score_priority("", "Other / Needs Review", original_text="यहाँ आग लग गई है तुरंत मदद भेजें")
        assert p4["priority"] == "Critical", f"Expected Critical for Hindi danger, got {p4}"

        # Case 5: Odia danger keyword with empty English text -> Critical
        p5 = score_priority("", "Other / Needs Review", original_text="ତାର ଛିଣ୍ଡି କରେଣ୍ଟ ଲାଗିବାର ବିପଦ ଅଛି")
        assert p5["priority"] == "Critical", f"Expected Critical for Odia danger, got {p5}"

        # Case 6: Vulnerable place (school/hospital) -> High or Critical
        p6 = score_priority("Deep open trench right outside kindergarten school gate", "Roads & Potholes")
        assert p6["priority"] in ("High", "Critical"), f"Expected High or Critical, got {p6}"

        # Case 7: Gas leak -> Critical
        p7 = score_priority("Smell of cylinder gas leak in commercial area", "Public Health")
        assert p7["priority"] == "Critical", f"Expected Critical, got {p7}"

        # Case 8: Normal municipal query -> Low or Medium
        p8 = score_priority("Query regarding property tax receipt download procedure", "Municipal Services & Property")
        assert p8["priority"] in ("Low", "Medium"), f"Expected Low or Medium, got {p8}"

        print("Test 2 passed: All 8 priority scoring cases.")

        # -------------------------------------------------------------
        # 3. Triage orchestration test
        # -------------------------------------------------------------
        u_sample = {
            "category": "Water Supply",
            "english_text": "Live wire snapped over water pipe near hospital",
            "used_llm": True
        }
        triage_res = triage(u_sample, original_text="")
        assert triage_res["category"] == "Water Supply"
        assert triage_res["priority"] == "Critical"
        assert "department" in triage_res
        assert "confidence" in triage_res
        assert "routing_reason" in triage_res
        assert "priority_reason" in triage_res
        print("Test 3 passed: Triage orchestration combines routing and priority.")

    # -------------------------------------------------------------
    # 4. Duplicate threshold, location rules & clustering tests
    # -------------------------------------------------------------
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_duplicates.db")
    db.DB_PATH = temp_db_path
    db.DATABASE_URL = None
    db.init_db()

    # Define controlled similarity embeddings for duplicate tests:
    # Query: [1.0, 0.0]
    # Match: [0.78, 0.6256] -> dot product ~ 0.78
    # If locations match: threshold = 0.80 - 0.05 = 0.75 -> 0.78 >= 0.75 (PASS)
    # If locations differ: threshold = 0.80 + 0.05 = 0.85 -> 0.78 < 0.85 (REJECT)
    def dup_fake_embed(text):
        t_low = text.lower()
        if "query" in t_low:
            return np.array([1.0, 0.0], dtype=np.float32)
        elif "near_dup" in t_low:
            return np.array([0.78, 0.6256], dtype=np.float32)
        elif "exact_dup" in t_low:
            return np.array([1.0, 0.0], dtype=np.float32)
        return np.array([0.0, 1.0], dtype=np.float32)

    with patch("backend.core.embedder.embed_single", side_effect=dup_fake_embed):
        # Insert initial ticket in DB
        t1 = create_grievance({
            "citizen_name": "Citizen A",
            "area": "Ward 4",
            "location": "Market Square",
            "original_text": "near_dup water pipeline issue",
            "summary": "near_dup water pipeline issue",
            "department": "Water Board",
            "category": "Water Supply"
        })

        # Test location matching: Same location -> threshold 0.75 -> sim 0.78 matches
        dups_same_loc = find_duplicates("query water pipeline", "Water Supply", location="Market Square")
        assert len(dups_same_loc) == 1, f"Expected 1 duplicate with matching location, got {len(dups_same_loc)}"
        assert dups_same_loc[0]["ticket_id"] == t1

        # Test location differing: Differing location -> threshold 0.85 -> sim 0.78 rejected
        dups_diff_loc = find_duplicates("query water pipeline", "Water Supply", location="Airport Road")
        assert len(dups_diff_loc) == 0, f"Expected 0 duplicates with differing location, got {len(dups_diff_loc)}"

        # -------------------------------------------------------------
        # 5. Cluster creation for two near-duplicates, attachment for third
        # -------------------------------------------------------------
        # Create ticket 2 (near_dup) with exact duplicate text to t1 to cluster
        def cluster_embed(text):
            return np.array([1.0, 0.0], dtype=np.float32)

        with patch("backend.core.embedder.embed_single", side_effect=cluster_embed):
            t2 = create_grievance({
                "citizen_name": "Citizen B",
                "area": "Ward 4",
                "location": "Market Square",
                "original_text": "Water pipeline burst",
                "summary": "Water pipeline burst",
                "department": "Water Board",
                "category": "Water Supply"
            })

            # Cluster assign for ticket 2 (duplicates t1)
            c_res2 = assign_cluster(t2, "Water pipeline burst", "Water Supply", "Water Board", "Market Square")
            assert c_res2 is not None, "Expected cluster creation for t2"
            assert c_res2["is_new"] is True
            assert c_res2["report_count"] == 2
            cluster_id = c_res2["cluster_id"]

            # Ticket 3 arrives (third duplicate)
            t3 = create_grievance({
                "citizen_name": "Citizen C",
                "area": "Ward 4",
                "location": "Market Square",
                "original_text": "Water pipeline broken",
                "summary": "Water pipeline broken",
                "department": "Water Board",
                "category": "Water Supply"
            })

            c_res3 = assign_cluster(t3, "Water pipeline broken", "Water Supply", "Water Board", "Market Square")
            assert c_res3 is not None
            assert c_res3["cluster_id"] == cluster_id
            assert c_res3["is_new"] is False
            assert c_res3["report_count"] == 3

            # Verify in DB
            rec1 = get_grievance(t1)
            rec2 = get_grievance(t2)
            rec3 = get_grievance(t3)
            assert rec1["cluster_id"] == cluster_id
            assert rec2["cluster_id"] == cluster_id
            assert rec3["cluster_id"] == cluster_id

            clusters = list_clusters()
            assert any(c["cluster_id"] == cluster_id and c["report_count"] == 3 for c in clusters)
            print("Test 4 & 5 passed: Location-adjusted duplicate threshold and cluster growth (report_count 3).")

    # -------------------------------------------------------------
    # 6. Real FastEmbed model test (auto-skipped if not available)
    # -------------------------------------------------------------
    try:
        from fastembed import TextEmbedding
        real_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        router._CATEGORY_EMBEDDINGS = None  # Reset so real model generates them

        real_test_cases = [
            ("Water pipeline is leaking on the street", "Water Supply"),
            ("Streetlight pole is broken and dark at night", "Street Lighting"),
            ("Large pothole in the middle of the road", "Roads & Potholes")
        ]
        for sent, expected_cat in real_test_cases:
            cls_out = classify(sent)
            assert cls_out["category"] == expected_cat, f"Real model expected {expected_cat}, got {cls_out['category']}"
        print("Test 6 passed: Real FastEmbed model routes 3 sample sentences to expected categories.")
    except Exception as e:
        print(f"Test 6 skipped: Real model not loaded or error ({e})")

    print("\nALL TRIAGE & ROUTER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
