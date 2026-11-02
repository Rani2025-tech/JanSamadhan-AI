import os
import sys
import tempfile
import unittest
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

class TestAuthRoles(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_auth_roles.db")
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

    # Case 1: signup 410
    def test_01_signup_returns_410(self):
        res = self.client.post("/api/auth/signup", json={
            "name": "Citizen User",
            "email": "citizen@example.com",
            "password": "Password123"
        })
        self.assertEqual(res.status_code, 410)
        self.assertIn("detail", res.json())

    # Case 2: admin login & role
    def test_02_admin_login_and_role(self):
        res = self.client.post("/api/auth/login", json={
            "email": "admin@jansamadhan.local",
            "password": "AdminPass@2026"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["role"], "ADMIN")
        self.assertIn("token", data)
        self.assertIn("expires_in", data)

    # Case 3: wrong password & unknown email identical 401s
    def test_03_wrong_password_and_unknown_email_identical_401s(self):
        res_wrong_pw = self.client.post("/api/auth/login", json={
            "email": "admin@jansamadhan.local",
            "password": "WrongPassword123"
        })
        res_unknown_email = self.client.post("/api/auth/login", json={
            "email": "nonexistent_official@example.com",
            "password": "AnyPassword123"
        })
        self.assertEqual(res_wrong_pw.status_code, 401)
        self.assertEqual(res_unknown_email.status_code, 401)
        self.assertEqual(res_wrong_pw.json()["detail"], res_unknown_email.json()["detail"])

    # Case 4: 6th attempt 429
    def test_04_sixth_attempt_triggers_429(self):
        email = "rate_limit_target@jansamadhan.local"
        for _ in range(5):
            r = self.client.post("/api/auth/login", json={"email": email, "password": "bad_password"})
            self.assertEqual(r.status_code, 401)

        r6 = self.client.post("/api/auth/login", json={"email": email, "password": "bad_password"})
        self.assertEqual(r6.status_code, 429)
        self.assertEqual(r6.headers.get("Retry-After"), "600")

    # Case 5: deactivated blocked
    def test_05_deactivated_user_blocked(self):
        staff = db_mod.create_staff_user(
            name="Inactive Official",
            email="inactive_official@jansamadhan.local",
            password="Password@123",
            department="Public Works Department"
        )
        # Deactivate user
        db_mod.update_staff_user(staff["id"], active=0)

        # Login is blocked with 401
        login_res = self.client.post("/api/auth/login", json={
            "email": "inactive_official@jansamadhan.local",
            "password": "Password@123"
        })
        self.assertEqual(login_res.status_code, 401)

        # Existing token for deactivated account is also rejected on protected endpoint
        deactivated_token = create_token(staff["id"], "DEPARTMENT_OFFICIAL", department="Public Works Department")
        auth_res = self.client.get("/api/grievances/", headers={"Authorization": f"Bearer {deactivated_token}"})
        self.assertEqual(auth_res.status_code, 401)

    # Case 6: staff creation & department validation
    def test_06_staff_creation_and_department_validation(self):
        # Valid creation
        res_valid = self.client.post("/api/staff", json={
            "name": "Water Board Official",
            "email": "water_official_test@jansamadhan.local",
            "password": "Password@1234",
            "department": "Public Health Engineering / Water Board"
        }, headers=self.admin_headers)
        self.assertEqual(res_valid.status_code, 200)
        self.assertEqual(res_valid.json()["role"], "DEPARTMENT_OFFICIAL")
        self.assertEqual(res_valid.json()["department"], "Public Health Engineering / Water Board")

        # Invalid department
        res_invalid_dept = self.client.post("/api/staff", json={
            "name": "Fake Official",
            "email": "fake_official@jansamadhan.local",
            "password": "Password@1234",
            "department": "Fake Magic Space Department"
        }, headers=self.admin_headers)
        self.assertEqual(res_invalid_dept.status_code, 400)

        # Password < 8 characters
        res_short_pw = self.client.post("/api/staff", json={
            "name": "Short Password Official",
            "email": "short_pw_official@jansamadhan.local",
            "password": "short",
            "department": "Public Health Engineering / Water Board"
        }, headers=self.admin_headers)
        self.assertEqual(res_short_pw.status_code, 400)

    # Case 7: department scoping on list & patch (403)
    def test_07_department_scoping_on_list_and_patch_403(self):
        water_staff = db_mod.create_staff_user(
            name="Water Officer",
            email="water_officer@jansamadhan.local",
            password="Password@123",
            department="Public Health Engineering / Water Board"
        )
        water_token = create_token(water_staff["id"], "DEPARTMENT_OFFICIAL", department="Public Health Engineering / Water Board")
        water_headers = {"Authorization": f"Bearer {water_token}"}

        tid_water = grv_mod.create_grievance({
            "citizen_name": "Citizen A",
            "original_text": "Broken pipe leaking on main road",
            "department": "Public Health Engineering / Water Board",
            "status": "Submitted"
        })
        tid_power = grv_mod.create_grievance({
            "citizen_name": "Citizen B",
            "original_text": "Transformer sparked and blackout",
            "department": "Power Distribution Company (DISCOM)",
            "status": "Submitted"
        })

        # List is scoped: Water official only sees grievances belonging to Water Board
        list_res = self.client.get("/api/grievances/", headers=water_headers)
        self.assertEqual(list_res.status_code, 200)
        tickets = list_res.json()
        self.assertTrue(any(t["ticket_id"] == tid_water for t in tickets))
        self.assertFalse(any(t["ticket_id"] == tid_power for t in tickets))

        # Patching grievance belonging to another department returns 403 Forbidden
        patch_other_res = self.client.patch(
            f"/api/grievances/{tid_power}/status",
            json={"status": "Assigned"},
            headers=water_headers
        )
        self.assertEqual(patch_other_res.status_code, 403)

        # Patching grievance belonging to own department succeeds
        patch_own_res = self.client.patch(
            f"/api/grievances/{tid_water}/status",
            json={"status": "Assigned"},
            headers=water_headers
        )
        self.assertEqual(patch_own_res.status_code, 200)

    # Case 8: transition rules (400)
    def test_08_transition_rules_400(self):
        tid = grv_mod.create_grievance({
            "original_text": "Pothole repair needed",
            "department": "Public Works Department",
            "status": "Submitted"
        })

        # Direct jump from Submitted -> Resolved is invalid -> 400
        res_invalid_jump = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "Resolved", "note": "Resolved without assignment"},
            headers=self.admin_headers
        )
        self.assertEqual(res_invalid_jump.status_code, 400)

        # Submitted -> Assigned is valid
        r1 = self.client.patch(f"/api/grievances/{tid}/status", json={"status": "Assigned"}, headers=self.admin_headers)
        self.assertEqual(r1.status_code, 200)

        # Assigned -> In Progress is valid
        r2 = self.client.patch(f"/api/grievances/{tid}/status", json={"status": "In Progress"}, headers=self.admin_headers)
        self.assertEqual(r2.status_code, 200)

        # In Progress -> Assigned is invalid -> 400
        r3 = self.client.patch(f"/api/grievances/{tid}/status", json={"status": "Assigned"}, headers=self.admin_headers)
        self.assertEqual(r3.status_code, 400)

    # Case 9: resolve note requirement (400)
    def test_09_resolve_note_requirement_400(self):
        tid = grv_mod.create_grievance({
            "original_text": "Garbage pile near market",
            "department": "Municipal Corporation - Solid Waste",
            "status": "In Progress"
        })

        # Resolving without note -> 400
        r_empty = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "Resolved", "note": ""},
            headers=self.admin_headers
        )
        self.assertEqual(r_empty.status_code, 400)

        # Resolving with note < 5 characters -> 400
        r_short = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "Resolved", "note": "Done"},
            headers=self.admin_headers
        )
        self.assertEqual(r_short.status_code, 400)

        # Resolving with note >= 5 characters -> 200
        r_valid = self.client.patch(
            f"/api/grievances/{tid}/status",
            json={"status": "Resolved", "note": "Garbage cleared and sanitized by sanitation team."},
            headers=self.admin_headers
        )
        self.assertEqual(r_valid.status_code, 200)

    # Case 10: expired token (401)
    def test_10_expired_token_returns_401(self):
        expired_token = create_token(self.admin_user["id"], "ADMIN", expires_hours=-2)
        res = self.client.get("/api/grievances/", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("detail", res.json())

    # Case 11: missing token (401)
    def test_11_missing_token_returns_401(self):
        res = self.client.get("/api/grievances/")
        self.assertEqual(res.status_code, 401)

    # Case 12: staff cannot call /api/staff (403)
    def test_12_staff_cannot_call_staff_management_endpoints_403(self):
        staff = db_mod.create_staff_user(
            name="Official A",
            email="official_a@jansamadhan.local",
            password="Password@123",
            department="State Police / Traffic Police"
        )
        staff_token = create_token(staff["id"], "DEPARTMENT_OFFICIAL", department="State Police / Traffic Police")
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # GET /api/staff -> 403
        res_get = self.client.get("/api/staff", headers=staff_headers)
        self.assertEqual(res_get.status_code, 403)

        # POST /api/staff -> 403
        res_post = self.client.post("/api/staff", json={
            "name": "Rogue Official",
            "email": "rogue@jansamadhan.local",
            "password": "Password@1234",
            "department": "State Police / Traffic Police"
        }, headers=staff_headers)
        self.assertEqual(res_post.status_code, 403)

        # PATCH /api/staff/{id} -> 403
        res_patch = self.client.patch(f"/api/staff/{staff['id']}", json={"active": 0}, headers=staff_headers)
        self.assertEqual(res_patch.status_code, 403)

if __name__ == "__main__":
    unittest.main()

