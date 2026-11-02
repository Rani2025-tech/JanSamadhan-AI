import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")
os.environ.setdefault("JWT_SECRET", "mock_jwt_secret_for_testing_1234567890")
os.environ.setdefault("ADMIN_PASSWORD", "mock_admin_pass")
os.environ.setdefault("DEMO_SEED_ALLOWED", "1")

import backend.db.database as db_mod
import backend.db.grievances as grv_mod
from backend.main import app
from backend.api.routes import create_token
from scripts.seed_demo import seed_demo

class TestDashboardBackend(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_dash.db")
        db_mod.DB_PATH = self.test_db
        db_mod.init_db()
        grv_mod.init_grievance_tables()

        self.client = TestClient(app)

        self.admin_token = create_token("admin_usr", "ADMIN")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        self.water_dept = "Public Health Engineering / Water Board"
        self.official_water_token = create_token("water_usr", "DEPARTMENT_OFFICIAL", department=self.water_dept)
        self.official_water_headers = {"Authorization": f"Bearer {self.official_water_token}"}

        self.power_dept = "Power Distribution Company (DISCOM)"
        self.official_power_token = create_token("power_usr", "DEPARTMENT_OFFICIAL", department=self.power_dept)
        self.official_power_headers = {"Authorization": f"Bearer {self.official_power_token}"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_sample_ticket(self, department=None, category=None, status="Submitted", needs_review=0):
        data = {
            "citizen_name": "Test Citizen",
            "contact": "9876543210",
            "area": "Saheed Nagar",
            "location": "Saheed Nagar, Ward 4",
            "original_text": "Water leakage in front of school",
            "summary": "Water pipeline leakage",
            "language": "en",
            "department": department or self.water_dept,
            "category": category or "Water Supply",
            "priority": "High",
            "status": status,
            "needs_review": needs_review,
            "pin": "123456"
        }
        tid = grv_mod.create_grievance(data)
        if status != "Submitted" or needs_review != 0:
            conn = db_mod.get_conn()
            c = conn.cursor()
            db_mod._exec(c, f"UPDATE grievances SET status = {db_mod._ph()}, needs_review = {db_mod._ph()} WHERE ticket_id = {db_mod._ph()}",
                         (status, needs_review, tid))
            conn.commit()
            conn.close()
        return tid

    def test_routing_admin_only(self):
        """Routing endpoint requires ADMIN role (401 without auth, 403 for officials)."""
        tid = self._create_sample_ticket()

        payload = {
            "department": "Power Distribution Company (DISCOM)",
            "category": "Electricity",
            "note": "Re-routing to power department"
        }

        # 1. Unauthenticated -> 401
        res_no_auth = self.client.patch(f"/api/grievances/{tid}/routing", json=payload)
        self.assertEqual(res_no_auth.status_code, 401)

        # 2. Official role -> 403
        res_off = self.client.patch(f"/api/grievances/{tid}/routing", json=payload, headers=self.official_water_headers)
        self.assertEqual(res_off.status_code, 403)

        # 3. Admin role -> 200
        res_admin = self.client.patch(f"/api/grievances/{tid}/routing", json=payload, headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)

    def test_routing_validation(self):
        """Routing endpoint validates department/category and note length, rejecting 'Other / Needs Review'."""
        tid = self._create_sample_ticket()

        # 1. Target is "Other / Needs Review" -> 400
        res_other = self.client.patch(f"/api/grievances/{tid}/routing", json={
            "department": "General Administration / Grievance Cell",
            "category": "Other / Needs Review",
            "note": "Re-routing back to other"
        }, headers=self.admin_headers)
        self.assertEqual(res_other.status_code, 400)
        self.assertIn("Other / Needs Review", res_other.json().get("detail", ""))

        # 2. Invalid department / category combination -> 400
        res_inv = self.client.patch(f"/api/grievances/{tid}/routing", json={
            "department": "Nonexistent Department",
            "category": "Fake Category",
            "note": "Trying invalid target"
        }, headers=self.admin_headers)
        self.assertEqual(res_inv.status_code, 400)

        # 3. Note is too short (< 5 chars) -> 400 or 422
        res_short = self.client.patch(f"/api/grievances/{tid}/routing", json={
            "department": "Power Distribution Company (DISCOM)",
            "category": "Electricity",
            "note": "tiny"
        }, headers=self.admin_headers)
        self.assertIn(res_short.status_code, (400, 422))

        # 4. Non-existent ticket -> 404
        res_404 = self.client.patch("/api/grievances/GRV-99999/routing", json={
            "department": "Power Distribution Company (DISCOM)",
            "category": "Electricity",
            "note": "Valid note for missing ticket"
        }, headers=self.admin_headers)
        self.assertEqual(res_404.status_code, 404)

    def test_routing_success(self):
        """Routing updates department/category, clears needs_review, sets routing_reason, writes history, preserves status."""
        tid = self._create_sample_ticket(status="In Progress", needs_review=1)

        payload = {
            "department": "Power Distribution Company (DISCOM)",
            "category": "Electricity",
            "note": "Correctly routed to electrical engineering division"
        }
        res = self.client.patch(f"/api/grievances/{tid}/routing", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)

        # Verify database record
        updated = grv_mod.get_grievance(tid)
        self.assertEqual(updated["department"], "Power Distribution Company (DISCOM)")
        self.assertEqual(updated["category"], "Electricity")
        self.assertEqual(updated["needs_review"], 0)
        self.assertEqual(updated["status"], "In Progress")
        self.assertEqual(updated["routing_reason"], "Manually routed by admin")

        # Verify history row
        history = updated.get("history", [])
        self.assertGreaterEqual(len(history), 1)
        last_h = history[-1]
        self.assertIn("Re-routed from", last_h["note"])
        self.assertIn("Power Distribution Company (DISCOM)", last_h["note"])

    def test_flag_misrouted(self):
        """Official of ticket's department or Admin can flag misrouted; other departments 403; Resolved tickets 400."""
        tid = self._create_sample_ticket(department=self.water_dept, status="In Progress")

        # 1. Official of another department (Power) -> 403
        res_wrong_dept = self.client.post(f"/api/grievances/{tid}/flag-misrouted", json={
            "note": "This is not our issue, please re-route"
        }, headers=self.official_power_headers)
        self.assertEqual(res_wrong_dept.status_code, 403)

        # 2. Official of correct department (Water) -> 200
        res_correct = self.client.post(f"/api/grievances/{tid}/flag-misrouted", json={
            "note": "This belongs to power discom, transformer sparking"
        }, headers=self.official_water_headers)
        self.assertEqual(res_correct.status_code, 200)

        record = grv_mod.get_grievance(tid)
        self.assertEqual(record["needs_review"], 1)
        last_h = record["history"][-1]
        self.assertIn("Flagged as misrouted:", last_h["note"])

        # 3. Short note (< 5 chars) -> 400 or 422
        res_short = self.client.post(f"/api/grievances/{tid}/flag-misrouted", json={
            "note": "bad"
        }, headers=self.official_water_headers)
        self.assertIn(res_short.status_code, (400, 422))

        # 4. Resolved ticket cannot be flagged as misrouted -> 400
        resolved_tid = self._create_sample_ticket(department=self.water_dept, status="Resolved")
        res_resolved = self.client.post(f"/api/grievances/{resolved_tid}/flag-misrouted", json={
            "note": "Trying to flag closed ticket"
        }, headers=self.official_water_headers)
        self.assertEqual(res_resolved.status_code, 400)

        # 5. Admin can also flag
        admin_tid = self._create_sample_ticket(department=self.power_dept, status="Assigned")
        res_admin = self.client.post(f"/api/grievances/{admin_tid}/flag-misrouted", json={
            "note": "Admin flagging misrouted ticket"
        }, headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)

    def test_staff_list_fields_and_filter(self):
        """Staff listing includes required audit/routing fields and supports needs_review filter with scoping."""
        t1 = self._create_sample_ticket(department=self.water_dept, needs_review=1)
        t2 = self._create_sample_ticket(department=self.water_dept, needs_review=0)
        t3 = self._create_sample_ticket(department=self.power_dept, needs_review=1)

        # Admin fetches all
        res_all = self.client.get("/api/grievances/", headers=self.admin_headers)
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertGreaterEqual(len(data_all), 3)

        # Check required fields exist in rows
        sample = data_all[0]
        required_fields = [
            "needs_review", "escalation_level", "overdue", "hours_overdue",
            "cluster_id", "area", "location", "summary", "confidence",
            "created_at", "updated_at", "sla_due_at"
        ]
        for field in required_fields:
            self.assertIn(field, sample, f"Field '{field}' missing from staff list row")

        # Test needs_review=true filter
        res_rev_true = self.client.get("/api/grievances/?needs_review=true", headers=self.admin_headers)
        data_rev_true = res_rev_true.json()
        for item in data_rev_true:
            self.assertEqual(item["needs_review"], 1)

        # Test needs_review=false filter
        res_rev_false = self.client.get("/api/grievances/?needs_review=false", headers=self.admin_headers)
        data_rev_false = res_rev_false.json()
        for item in data_rev_false:
            self.assertEqual(item["needs_review"], 0)

        # Test Department Official scoping (Water official only sees Water tickets)
        res_water = self.client.get("/api/grievances/", headers=self.official_water_headers)
        self.assertEqual(res_water.status_code, 200)
        for item in res_water.json():
            self.assertEqual(item["department"], self.water_dept)

    def test_audit_log_endpoint(self):
        """Audit trail is Admin-only, newest-first, and returns joined ticket details with pagination."""
        tid = self._create_sample_ticket()
        grv_mod.update_status(tid, "Assigned", note="Audit test assignment", actor="Admin <admin@local>")

        # 1. Official -> 403
        res_off = self.client.get("/api/grievances/admin/audit", headers=self.official_water_headers)
        self.assertEqual(res_off.status_code, 403)

        # 2. Admin -> 200
        res_admin = self.client.get("/api/grievances/admin/audit?limit=10&offset=0", headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)
        audit_rows = res_admin.json()
        self.assertGreaterEqual(len(audit_rows), 1)

        row = audit_rows[0]
        for field in ("ticket_id", "department", "status", "note", "actor", "created_at"):
            self.assertIn(field, row, f"Audit field '{field}' missing")

    def test_seed_demo_script(self):
        """Validates seed_demo creates demo data with [Demo] prefix, PIN 123456, and reset cleans up."""
        # Run demo seed with count 12
        seed_demo(count=12, reset=True)

        # Check demo tickets exist
        res = self.client.get("/api/grievances/", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        rows = res.json()
        demo_rows = [r for r in rows if str(r.get("citizen_name", "")).startswith("[Demo]")]
        self.assertEqual(len(demo_rows), 12)

        # Verify PIN 123456 unlocks private view
        test_tid = demo_rows[0]["ticket_id"]
        res_unlock = self.client.post(f"/api/grievances/{test_tid}/private", json={"pin": "123456"})
        self.assertEqual(res_unlock.status_code, 200)
        unlocked = res_unlock.json()
        self.assertIn("citizen_name", unlocked)
        self.assertTrue(unlocked["citizen_name"].startswith("[Demo]"))

        # Verify reset removes all demo tickets
        seed_demo(count=0, reset=True)
        res_after = self.client.get("/api/grievances/", headers=self.admin_headers)
        rows_after = res_after.json()
        remaining_demo = [r for r in rows_after if str(r.get("citizen_name", "")).startswith("[Demo]")]
        self.assertEqual(len(remaining_demo), 0)

if __name__ == "__main__":
    unittest.main()

