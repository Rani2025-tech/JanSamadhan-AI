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


class TestDemoMode(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_demo_mode.db")
        db_mod.DB_PATH = self.test_db
        grv_mod.DB_PATH = self.test_db
        db_mod.init_db()
        grv_mod.init_grievance_tables()
        db_mod.ensure_admin()

        self.client = TestClient(app)

        # Real admin credentials
        self.admin_user = db_mod.get_user_by_email("admin@jansamadhan.local")
        self.real_admin_token = create_token(self.admin_user["id"], "ADMIN")
        self.real_admin_headers = {"Authorization": f"Bearer {self.real_admin_token}"}

    def tearDown(self):
        self.temp_dir.cleanup()

    # 1. demo-login returns 404 when DEMO_MODE is off; ensure_demo_accounts creates nothing when off
    def test_01_demo_login_404_when_disabled(self):
        os.environ["DEMO_MODE"] = "0"
        res = self.client.post("/api/auth/demo-login", json={"role": "admin"})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Demo mode is disabled")

        # ensure_demo_accounts does nothing when DEMO_MODE != 1
        db_mod.ensure_demo_accounts()
        self.assertIsNone(db_mod.get_user_by_email("demo.admin@jansamadhan.demo"))
        self.assertIsNone(db_mod.get_user_by_email("demo.official@jansamadhan.demo"))

    # 2. with DEMO_MODE=1, both roles succeed, return demo: true and short expiry
    def test_02_demo_login_both_roles_succeed_with_expected_expiry(self):
        os.environ["DEMO_MODE"] = "1"
        os.environ["DEMO_TOKEN_MINUTES"] = "30"

        # Admin login
        res_admin = self.client.post("/api/auth/demo-login", json={"role": "admin"})
        self.assertEqual(res_admin.status_code, 200)
        data_admin = res_admin.json()
        self.assertTrue(data_admin.get("demo"))
        self.assertEqual(data_admin.get("role"), "ADMIN")
        self.assertEqual(data_admin.get("name"), "Demo Administrator (demo)")
        self.assertEqual(data_admin.get("expires_in"), 30 * 60)
        self.assertIn("token", data_admin)

        # Official login
        res_off = self.client.post("/api/auth/demo-login", json={"role": "official"})
        self.assertEqual(res_off.status_code, 200)
        data_off = res_off.json()
        self.assertTrue(data_off.get("demo"))
        self.assertEqual(data_off.get("role"), "DEPARTMENT_OFFICIAL")
        self.assertEqual(data_off.get("name"), "Demo Official (demo)")
        self.assertEqual(data_off.get("expires_in"), 30 * 60)
        expected_dept = db_mod.get_demo_official_department()
        self.assertEqual(data_off.get("department"), expected_dept)
        self.assertIn("token", data_off)

    # 3. invalid role returns 422
    def test_03_invalid_role_returns_422(self):
        os.environ["DEMO_MODE"] = "1"
        res = self.client.post("/api/auth/demo-login", json={"role": "superadmin"})
        self.assertEqual(res.status_code, 422)

    # 4. the 21st request from one IP returns 429
    def test_04_rate_limiting_429(self):
        os.environ["DEMO_MODE"] = "1"
        # 20 requests succeed
        for i in range(20):
            res = self.client.post("/api/auth/demo-login", json={"role": "admin"})
            self.assertEqual(res.status_code, 200, f"Request {i+1} failed with {res.status_code}")

        # 21st request returns 429
        res_21 = self.client.post("/api/auth/demo-login", json={"role": "admin"})
        self.assertEqual(res_21.status_code, 429)
        self.assertIn("Retry-After", res_21.headers)

    # 5. normal login refuses demo accounts with generic 401
    def test_05_normal_login_refuses_demo_accounts(self):
        os.environ["DEMO_MODE"] = "1"
        db_mod.ensure_demo_accounts()

        # Try normal login with demo admin
        res_demo_login = self.client.post("/api/auth/login", json={
            "email": "demo.admin@jansamadhan.demo",
            "password": "anyPassword123"
        })
        self.assertEqual(res_demo_login.status_code, 401)
        self.assertEqual(res_demo_login.json()["detail"], "Invalid email or password")

        # Try normal login with demo official
        res_off_login = self.client.post("/api/auth/login", json={
            "email": "demo.official@jansamadhan.demo",
            "password": "anyPassword123"
        })
        self.assertEqual(res_off_login.status_code, 401)
        self.assertEqual(res_off_login.json()["detail"], "Invalid email or password")

    # 6. demo admin can list all tickets and PATCH status (actor ends with (demo))
    def test_06_demo_admin_can_list_and_patch_status(self):
        os.environ["DEMO_MODE"] = "1"
        t_id = grv_mod.create_grievance({
            "department": "Public Health Engineering / Water Board",
            "category": "Water Supply",
            "description": "Broken main water valve leaking",
            "priority": "Medium",
            "pin": "654321"
        })

        res_login = self.client.post("/api/auth/demo-login", json={"role": "admin"})
        token = res_login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List tickets
        res_list = self.client.get("/api/grievances/", headers=headers)
        self.assertEqual(res_list.status_code, 200)
        items = res_list.json()
        self.assertTrue(any(item["ticket_id"] == t_id for item in items))

        # PATCH status to Assigned
        res_patch = self.client.patch(f"/api/grievances/{t_id}/status", json={
            "status": "Assigned",
            "note": "Assigned to zonal engineer"
        }, headers=headers)
        self.assertEqual(res_patch.status_code, 200)

        # Verify audit/history actor is "Demo Administrator (demo)"
        details = self.client.get(f"/api/grievances/{t_id}", headers=headers).json()
        latest_history = details["history"][-1]
        self.assertEqual(latest_history["actor"], "Demo Administrator (demo)")

    # 7. demo admin gets 403 on POST /api/staff, GET /api/staff, PATCH /api/staff/{id} and reset-pin
    def test_07_demo_admin_gets_403_on_restricted_endpoints(self):
        os.environ["DEMO_MODE"] = "1"
        t_id = grv_mod.create_grievance({
            "department": "Public Health Engineering / Water Board",
            "category": "Water Supply",
            "description": "Water pipeline burst near market",
            "priority": "High",
            "pin": "112233"
        })

        res_login = self.client.post("/api/auth/demo-login", json={"role": "admin"})
        token = res_login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # POST /api/staff -> 403
        res_post = self.client.post("/api/staff", json={
            "name": "Test Officer",
            "email": "officer@jansamadhan.local",
            "password": "Password123",
            "department": "Public Health Engineering / Water Board"
        }, headers=headers)
        self.assertEqual(res_post.status_code, 403)
        self.assertEqual(res_post.json()["detail"], "Not available in demo mode")

        # GET /api/staff -> 403
        res_get = self.client.get("/api/staff", headers=headers)
        self.assertEqual(res_get.status_code, 403)
        self.assertEqual(res_get.json()["detail"], "Not available in demo mode")

        # PATCH /api/staff/{id} -> 403
        res_patch = self.client.patch("/api/staff/dummy-id", json={
            "department": "Public Health Engineering / Water Board"
        }, headers=headers)
        self.assertEqual(res_patch.status_code, 403)
        self.assertEqual(res_patch.json()["detail"], "Not available in demo mode")

        # POST /{ticket_id}/reset-pin -> 403
        res_reset = self.client.post(f"/api/grievances/{t_id}/reset-pin", headers=headers)
        self.assertEqual(res_reset.status_code, 403)
        self.assertEqual(res_reset.json()["detail"], "Not available in demo mode")

    # 8. demo official sees only its department and gets 403 on another department's ticket
    def test_08_demo_official_scoped_to_department(self):
        os.environ["DEMO_MODE"] = "1"
        demo_dept = db_mod.get_demo_official_department()

        # Ticket in demo department
        t_own = grv_mod.create_grievance({
            "department": demo_dept,
            "category": "Water Supply",
            "description": "Water pressure low in sector 4",
            "priority": "Low",
            "pin": "223344"
        })
        # Ticket in another department
        t_other = grv_mod.create_grievance({
            "department": "Electricity / Power Distribution",
            "category": "Electricity Supply",
            "description": "Transformer spark in street 5",
            "priority": "High",
            "pin": "556677"
        })

        res_login = self.client.post("/api/auth/demo-login", json={"role": "official"})
        token = res_login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List tickets: sees t_own, does not see t_other
        res_list = self.client.get("/api/grievances/", headers=headers)
        self.assertEqual(res_list.status_code, 200)
        items = res_list.json()
        ids = [item["ticket_id"] for item in items]
        self.assertIn(t_own, ids)
        self.assertNotIn(t_other, ids)

        # PATCH status on other department's ticket returns 403
        res_patch_other = self.client.patch(f"/api/grievances/{t_other}/status", json={
            "status": "Assigned",
            "note": "Trying to update other dept"
        }, headers=headers)
        self.assertEqual(res_patch_other.status_code, 403)

        # PATCH status on own department ticket succeeds
        res_patch_own = self.client.patch(f"/api/grievances/{t_own}/status", json={
            "status": "Assigned",
            "note": "Assigned to water works maintenance unit"
        }, headers=headers)
        self.assertEqual(res_patch_own.status_code, 200)

        # Verify history actor is "Demo Official (demo)"
        details = self.client.get(f"/api/grievances/{t_own}", headers=headers).json()
        latest_history = details["history"][-1]
        self.assertEqual(latest_history["actor"], "Demo Official (demo)")

    # 9. ensure_demo_accounts is idempotent
    def test_09_ensure_demo_accounts_idempotent(self):
        os.environ["DEMO_MODE"] = "1"
        db_mod.ensure_demo_accounts()
        u1 = db_mod.get_user_by_email("demo.admin@jansamadhan.demo")
        self.assertIsNotNone(u1)
        self.assertEqual(u1["is_demo"], 1)

        # Run again
        db_mod.ensure_demo_accounts()
        u2 = db_mod.get_user_by_email("demo.admin@jansamadhan.demo")
        self.assertEqual(u1["id"], u2["id"])

    # 10. real admin and official tokens are unaffected by forbid_demo
    def test_10_real_staff_tokens_unaffected_by_forbid_demo(self):
        # Real admin can access GET /api/staff
        res_staff = self.client.get("/api/staff", headers=self.real_admin_headers)
        self.assertEqual(res_staff.status_code, 200)

        # Real admin can reset pin
        t_id = grv_mod.create_grievance({
            "department": "Public Health Engineering / Water Board",
            "category": "Water Supply",
            "description": "Pipe leaking",
            "priority": "Medium",
            "pin": "998877"
        })
        res_reset = self.client.post(f"/api/grievances/{t_id}/reset-pin", headers=self.real_admin_headers)
        self.assertEqual(res_reset.status_code, 200)
        self.assertIn("pin", res_reset.json())


if __name__ == "__main__":
    unittest.main()

