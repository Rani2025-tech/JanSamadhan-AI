import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")
os.environ.setdefault("JWT_SECRET", "mock_jwt_secret_for_testing_1234567890")
os.environ.setdefault("ADMIN_PASSWORD", "mock_admin_pass")

import backend.db.database as db_mod
import backend.db.grievances as grv_mod
from backend.main import app
from backend.api.routes import create_token

class TestGrievanceAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_api.db")
        db_mod.DB_PATH = self.test_db
        db_mod.init_db()
        grv_mod.init_grievance_tables()

        self.client = TestClient(app)
        self.admin_token = create_token("admin_usr", "admin")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.user_token = create_token("regular_usr", "user")
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_guest_chat_works_without_token(self):
        """Guest chat endpoint requires no auth token."""
        res = self.client.post("/api/grievances/chat", json={"message": "Namaste"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertIn("state", data)
        self.assertIn("meta", data)

    def test_admin_auth_protection(self):
        """Admin endpoints return 401 without auth, 403 for non-admin, and 200 for admin."""
        # Test 1: GET /api/grievances/admin/stats
        # No token -> 401
        res_no_auth = self.client.get("/api/grievances/admin/stats")
        self.assertEqual(res_no_auth.status_code, 401)

        # Citizen token -> 403
        res_user_auth = self.client.get("/api/grievances/admin/stats", headers=self.user_headers)
        self.assertEqual(res_user_auth.status_code, 403)

        # Admin token -> 200
        res_admin_auth = self.client.get("/api/grievances/admin/stats", headers=self.admin_headers)
        self.assertEqual(res_admin_auth.status_code, 200)

        # Test 2: GET /api/grievances/admin/clusters
        self.assertEqual(self.client.get("/api/grievances/admin/clusters").status_code, 401)
        self.assertEqual(self.client.get("/api/grievances/admin/clusters", headers=self.user_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/grievances/admin/clusters", headers=self.admin_headers).status_code, 200)

        # Test 3: GET /api/grievances/ (filtered list)
        self.assertEqual(self.client.get("/api/grievances/").status_code, 401)
        self.assertEqual(self.client.get("/api/grievances/", headers=self.user_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/grievances/", headers=self.admin_headers).status_code, 200)

    def test_get_ticket_masks_contact_for_guest(self):
        """Public ticket detail view hides contact and citizen name from unauthenticated guests."""
        tid = grv_mod.create_grievance({
            "citizen_name": "Sita Devi",
            "contact": "9876543210",
            "original_text": "Broken water valve near temple",
            "department": "Water Board",
            "category": "Water Supply",
            "priority": "Medium"
        })

        # Guest call (no auth)
        guest_res = self.client.get(f"/api/grievances/{tid}")
        self.assertEqual(guest_res.status_code, 200)
        guest_data = guest_res.json()
        self.assertNotIn("citizen_name", guest_data)
        self.assertNotIn("contact", guest_data)
        self.assertNotIn("original_text", guest_data)

        # Admin call (with admin token)
        admin_res = self.client.get(f"/api/grievances/{tid}", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        admin_data = admin_res.json()
        self.assertEqual(admin_data["citizen_name"], "Sita Devi")
        self.assertEqual(admin_data["contact"], "9876543210")

    def test_admin_patch_status(self):
        """Admin can update grievance status and append notes to history."""
        tid = grv_mod.create_grievance({
            "citizen_name": "Citizen",
            "original_text": "Garbage dump near school",
            "department": "Municipal Corporation - Solid Waste",
            "category": "Sanitation & Garbage"
        })

        # Unauthenticated patch fails with 401
        res_fail = self.client.patch(f"/api/grievances/{tid}/status", json={"status": "Assigned"})
        self.assertEqual(res_fail.status_code, 401)

        # Transition to Assigned first per state machine rules
        assign_res = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "Assigned", "note": "Assigned to department team"},
            headers=self.admin_headers
        )
        self.assertEqual(assign_res.status_code, 200)

        # Admin patch to In Progress succeeds
        res_ok = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "In Progress", "note": "Assigned sanitation crew A"},
            headers=self.admin_headers
        )
        self.assertEqual(res_ok.status_code, 200)

        # Verify updated record
        updated_rec = grv_mod.get_grievance(tid)
        self.assertEqual(updated_rec["status"], "In Progress")
        self.assertTrue(any("Assigned sanitation crew A" in h.get("note", "") for h in updated_rec["history"]))

    def test_low_rating_on_resolved_ticket_reopens_it(self):
        """Low feedback rating (<= 2) on a Resolved grievance automatically reopens it."""
        tid = grv_mod.create_grievance({
            "citizen_name": "Citizen",
            "original_text": "Streetlight flickering",
            "department": "Electricity",
            "category": "Electricity"
        })

        # Mark ticket as Resolved
        grv_mod.update_status(tid, "Resolved", note="Replaced bulb", actor="Inspector")
        self.assertEqual(grv_mod.get_grievance(tid)["status"], "Resolved")

        # Submit low rating of 1 with feedback
        fb_res = self.client.post(
            f"/api/grievances/{tid}/feedback",
            json={"rating": 1, "comment": "Light still flickers in the evening"}
        )
        self.assertEqual(fb_res.status_code, 200)
        self.assertTrue(fb_res.json()["reopened"])

        # Check DB state
        reopened_rec = grv_mod.get_grievance(tid)
        self.assertEqual(reopened_rec["status"], "Reopened")
        self.assertTrue(any("Reopened automatically" in h.get("note", "") for h in reopened_rec["history"]))

        # High rating on resolved ticket does NOT reopen
        tid2 = grv_mod.create_grievance({"original_text": "Pothole filled", "category": "Roads & Potholes"})
        grv_mod.update_status(tid2, "Resolved", note="Patched road")
        fb2 = self.client.post(f"/api/grievances/{tid2}/feedback", json={"rating": 5, "comment": "Great work!"})
        self.assertEqual(fb2.status_code, 200)
        self.assertFalse(fb2.json()["reopened"])
        self.assertEqual(grv_mod.get_grievance(tid2)["status"], "Resolved")

if __name__ == "__main__":
    unittest.main()
