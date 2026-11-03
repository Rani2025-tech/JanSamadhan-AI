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
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass@2026")
os.environ.setdefault("ADMIN_EMAIL", "admin@jansamadhan.local")

import backend.db.database as db_mod
import backend.db.grievances as grv_mod
from backend.main import app
from backend.api.routes import create_token
from backend.core.chatbot import handle_message

class TestPinPrivacy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_pin_privacy.db")
        db_mod.DB_PATH = self.test_db
        db_mod.init_db()
        grv_mod.init_grievance_tables()
        db_mod.ensure_admin()

        self.client = TestClient(app)
        self.admin_user = db_mod.get_user_by_email("admin@jansamadhan.local")
        self.admin_token = create_token(self.admin_user["id"], "ADMIN")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("backend.core.chatbot.understand")
    @patch("backend.core.chatbot.triage")
    def test_pin_created_hashed_and_appears_once(self, mock_triage, mock_understand):
        mock_understand.return_value = {
            "language": "en",
            "english_text": "Water pipeline burst on 2nd Avenue",
            "category": "Water Supply",
            "location": "2nd Avenue",
            "summary": "Water pipeline burst on 2nd Avenue",
            "missing": [],
            "used_llm": False,
            "needs_review": False
        }
        mock_triage.return_value = {
            "department": "Public Health Engineering / Water Board",
            "category": "Water Supply",
            "confidence": 0.95,
            "routing_reason": "Direct pipeline issue",
            "priority": "High",
            "priority_reason": "Water loss hazard",
            "needs_review": False
        }

        # Submit chat complaint
        res = self.client.post("/api/grievances/chat", json={
            "message": "Water pipeline burst on 2nd Avenue causing flooding"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        meta = data.get("meta", {})
        ticket_id = meta.get("ticket_id")
        pin = meta.get("pin")

        # 1. Plain PIN appears in meta and reply text
        self.assertIsNotNone(pin)
        self.assertEqual(len(pin), 6)
        self.assertIn(pin, data.get("reply", ""))
        self.assertEqual(meta.get("category"), "Water Supply")
        self.assertEqual(meta.get("location"), "2nd Avenue")
        self.assertIn("summary", meta)
        self.assertIn("confidence", meta)

        # 2. Database stores only bcrypt hash, never plain PIN
        raw = grv_mod.get_grievance(ticket_id)
        self.assertIn("pin_hash", raw)
        self.assertNotEqual(raw["pin_hash"], pin)
        self.assertTrue(raw["pin_hash"].startswith("$2b$") or raw["pin_hash"].startswith("$2a$"))

        # 3. Public GET does not contain pin or pin_hash
        public_res = self.client.get(f"/api/grievances/{ticket_id}")
        self.assertEqual(public_res.status_code, 200)
        pub_data = public_res.json()
        self.assertNotIn("pin", pub_data)
        self.assertNotIn("pin_hash", pub_data)

        # 4. Staff GET also does not contain pin_hash
        staff_res = self.client.get(f"/api/grievances/{ticket_id}", headers=self.admin_headers)
        self.assertEqual(staff_res.status_code, 200)
        self.assertNotIn("pin_hash", staff_res.json())

    def test_public_view_masks_private_fields_and_actors(self):
        tid = grv_mod.create_grievance({
            "citizen_name": "Ramesh Kumar",
            "contact": "9876543210",
            "original_text": "Illegal liquor shop operating near school",
            "summary": "Illegal shop near school",
            "location": "Near City High School",
            "department": "State Police / Traffic Police",
            "category": "Police & Public Safety",
            "priority": "High",
            "pin": "123456"
        })
        grv_mod.update_status(tid, "Assigned", note="Assigned to local station officer", actor="Inspector John")

        # Public (unauthenticated) caller
        res = self.client.get(f"/api/grievances/{tid}")
        self.assertEqual(res.status_code, 200)
        pub = res.json()

        # Private fields must be hidden
        for forbidden in ["original_text", "translated_text", "summary", "location", "citizen_name", "contact", "pin_hash"]:
            self.assertNotIn(forbidden, pub)

        # Public fields must be present
        for expected in ["ticket_id", "status", "department", "category", "priority", "created_at", "updated_at", "sla_due_at", "overdue", "report_count", "history"]:
            self.assertIn(expected, pub)

        # Actor in history must be masked
        for h in pub["history"]:
            self.assertIn(h["actor"], ["Department staff", "System"])
            self.assertNotIn("Inspector John", h["actor"])
            self.assertNotIn("Ramesh", h["actor"])

        # Staff caller sees full fields with real actors
        staff_res = self.client.get(f"/api/grievances/{tid}", headers=self.admin_headers)
        self.assertEqual(staff_res.status_code, 200)
        staff_data = staff_res.json()
        self.assertEqual(staff_data["citizen_name"], "Ramesh Kumar")
        self.assertEqual(staff_data["contact"], "9876543210")
        self.assertEqual(staff_data["location"], "Near City High School")
        self.assertTrue(any("Inspector John" in h.get("actor", "") for h in staff_data["history"]))

    def test_private_view_with_pin_and_rate_limiting(self):
        tid = grv_mod.create_grievance({
            "citizen_name": "Priya Sharma",
            "contact": "9123456789",
            "original_text": "Pothole caused scooter accident",
            "summary": "Pothole scooter accident",
            "location": "Ring Road Junction",
            "department": "Public Works Department",
            "category": "Roads & Potholes",
            "pin": "654321"
        })

        # Correct PIN returns full private citizen fields
        ok_res = self.client.post(f"/api/grievances/{tid}/private", json={"pin": "654321"})
        self.assertEqual(ok_res.status_code, 200)
        data = ok_res.json()
        self.assertEqual(data["citizen_name"], "Priya Sharma")
        self.assertEqual(data["contact"], "9123456789")
        self.assertEqual(data["location"], "Ring Road Junction")
        self.assertEqual(data["original_text"], "Pothole caused scooter accident")
        self.assertNotIn("pin_hash", data)

        # 5 wrong attempts return 403
        for _ in range(5):
            bad_res = self.client.post(f"/api/grievances/{tid}/private", json={"pin": "000000"})
            self.assertEqual(bad_res.status_code, 403)
            self.assertIn("Access denied", bad_res.json()["detail"])

        # 6th attempt returns 429 with Retry-After
        r6 = self.client.post(f"/api/grievances/{tid}/private", json={"pin": "000000"})
        self.assertEqual(r6.status_code, 429)
        self.assertEqual(r6.headers.get("Retry-After"), "600")

    def test_ticket_without_pin_cannot_be_unlocked(self):
        # Ticket created without pin (legacy ticket)
        tid = grv_mod.create_grievance({
            "citizen_name": "Old User",
            "original_text": "Old complaint without PIN",
            "department": "Public Works Department"
        })
        res = self.client.post(f"/api/grievances/{tid}/private", json={"pin": "123456"})
        self.assertEqual(res.status_code, 403)

    def test_admin_pin_reset_and_officials_forbidden(self):
        tid = grv_mod.create_grievance({
            "original_text": "Garbage dump issue",
            "department": "Municipal Corporation - Solid Waste",
            "pin": "111111"
        })

        # Official attempting PIN reset -> 403
        staff = db_mod.create_staff_user("Waste Officer", "waste_officer@test.local", "Password123", "Municipal Corporation - Solid Waste")
        staff_token = create_token(staff["id"], "DEPARTMENT_OFFICIAL", department="Municipal Corporation - Solid Waste")
        officer_res = self.client.post(f"/api/grievances/{tid}/reset-pin", headers={"Authorization": f"Bearer {staff_token}"})
        self.assertEqual(officer_res.status_code, 403)

        # Admin resets PIN
        admin_res = self.client.post(f"/api/grievances/{tid}/reset-pin", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        new_pin = admin_res.json()["pin"]
        self.assertEqual(len(new_pin), 6)
        self.assertNotEqual(new_pin, "111111")

        # History row written
        rec = grv_mod.get_grievance(tid)
        self.assertTrue(any(h.get("note") == "PIN reset" for h in rec["history"]))

        # Old PIN fails, new PIN unlocks
        self.assertEqual(self.client.post(f"/api/grievances/{tid}/private", json={"pin": "111111"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/grievances/{tid}/private", json={"pin": new_pin}).status_code, 200)

    @patch("backend.core.chatbot.understand")
    @patch("backend.core.chatbot.triage")
    def test_contact_validation_in_state(self, mock_triage, mock_understand):
        mock_understand.return_value = {
            "language": "en", "english_text": "Street light issue", "category": "Street Lighting",
            "location": "Ward 5", "summary": "Street light broken", "missing": [], "needs_review": False
        }
        mock_triage.return_value = {
            "department": "Municipal Corporation - Electrical Department",
            "category": "Street Lighting", "confidence": 0.9, "priority": "Low", "needs_review": False
        }

        # Valid contact: 10 digits starting with 6-9
        reply, state, meta = handle_message("Street light broken", state={"contact": " +91 98765-43210 "})
        tid1 = meta["ticket_id"]
        self.assertEqual(grv_mod.get_grievance(tid1)["contact"], "9876543210")

        # Invalid contact: ignored silently
        reply, state, meta = handle_message("Street light broken again", state={"contact": "123456"})
        tid2 = meta["ticket_id"]
        self.assertIsNone(grv_mod.get_grievance(tid2)["contact"])

    def test_public_stats_shape_and_not_shadowed(self):
        # Ensure public-stats route is not shadowed by /{ticket_id}
        res = self.client.get("/api/grievances/public-stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Validate shape
        self.assertIn("total", data)
        self.assertIn("resolved", data)
        self.assertIn("open", data)
        self.assertIn("overdue_count", data)
        self.assertIn("by_status", data)
        self.assertIn("demo", data)

        # No private or ticket-level fields
        for forbidden in ["ticket_id", "original_text", "citizen_name", "history", "contact"]:
            self.assertNotIn(forbidden, data)

    def test_chat_rate_limiting_429(self):
        # Override CHAT_RATE_PER_MIN for test
        with patch.dict(os.environ, {"CHAT_RATE_PER_MIN": "2"}):
            ip = "192.168.1.100"
            headers = {"X-Forwarded-For": ip}
            # Enable TRUST_PROXY to test IP extraction from X-Forwarded-For
            with patch.dict(os.environ, {"TRUST_PROXY": "1"}):
                r1 = self.client.post("/api/grievances/chat", json={"message": "Namaste"}, headers=headers)
                self.assertEqual(r1.status_code, 200)
                r2 = self.client.post("/api/grievances/chat", json={"message": "Hello"}, headers=headers)
                self.assertEqual(r2.status_code, 200)
                # 3rd request exceeds limit of 2/min
                r3 = self.client.post("/api/grievances/chat", json={"message": "Help"}, headers=headers)
                self.assertEqual(r3.status_code, 429)
                self.assertEqual(r3.headers.get("Retry-After"), "60")

if __name__ == "__main__":
    unittest.main()

