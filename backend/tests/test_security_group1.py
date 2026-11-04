import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from app.config import settings
from app.routes.auth import create_access_token, hash_password, auth_limiter
from app.database import SessionLocal
from app.models import User, Complaint, Notification

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_users():
    auth_limiter.otp_fails.clear()
    auth_limiter.admin_fails.clear()

    db = SessionLocal()
    try:
        # Ensure Citizen B exists
        user_b = db.query(User).filter(User.id == "USR-TEST-B").first()
        if not user_b:
            user_b = User(
                id="USR-TEST-B",
                name="Citizen B",
                phone="9123456780",
                role="citizen",
                language="en"
            )
            db.add(user_b)

        # Ensure User State Tester exists
        user_tester = db.query(User).filter(User.id == "USR-STATE-TESTER").first()
        if not user_tester:
            user_tester = User(
                id="USR-STATE-TESTER",
                name="State Tester",
                phone="9111222333",
                role="citizen",
                language="en"
            )
            db.add(user_tester)

        # Ensure a clean test complaint exists
        test_comp = db.query(Complaint).filter(Complaint.id == "GRV-STATE-TEST").first()
        if not test_comp:
            test_comp = Complaint(
                id="GRV-STATE-TEST",
                title="Pipeline test",
                description="Testing state transitions",
                category="Water Supply",
                department="PHED",
                urgency="Medium",
                language="English",
                status="Submitted",
                state="Odisha",
                district="Cuttack",
                area="CDA",
                submitted_date="01 Nov 2026",
                expected_date="08 Nov 2026",
                days_remaining=7,
                user_id="USR-STATE-TESTER",
                citizen_phone="9111222333"
            )
            db.add(test_comp)
        else:
            test_comp.status = "Submitted"
            test_comp.feedback_rating = None

        db.commit()
    finally:
        db.close()

def test_admin_login_strict_and_hashed():
    # 1. Non-existent ID with correct password -> 401
    res = client.post("/api/auth/admin-login", json={
        "id_or_email": "NON_EXISTENT_OFFICER",
        "password": settings.ADMIN_PASSWORD
    })
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"

    # 2. Correct ID with wrong password -> 401
    res = client.post("/api/auth/admin-login", json={
        "id_or_email": settings.ADMIN_EMPLOYEE_ID,
        "password": "WrongPassword@123"
    })
    assert res.status_code == 401

    # 3. Correct ID with correct password -> 200 + token
    res = client.post("/api/auth/admin-login", json={
        "id_or_email": settings.ADMIN_EMPLOYEE_ID,
        "password": settings.ADMIN_PASSWORD
    })
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["user"]["role"] == "admin"

def test_otp_rate_limiting():
    phone = "9988776655"
    for i in range(4):
        res = client.post("/api/auth/verify-otp", json={"mobile": phone, "otp": "999999"})
        assert res.status_code == 400

    # 5th failed attempt -> 429 Too Many Requests
    res = client.post("/api/auth/verify-otp", json={"mobile": phone, "otp": "999999"})
    assert res.status_code == 429, f"Expected 429 on 5th failure, got {res.status_code}"

def test_admin_ip_rate_limiting():
    for i in range(4):
        res = client.post("/api/auth/admin-login", json={
            "id_or_email": settings.ADMIN_EMPLOYEE_ID,
            "password": "WrongPassword"
        })
        assert res.status_code == 401

    res = client.post("/api/auth/admin-login", json={
        "id_or_email": settings.ADMIN_EMPLOYEE_ID,
        "password": "WrongPassword"
    })
    assert res.status_code == 429, f"Expected 429 on 5th failed admin login, got {res.status_code}"

def test_complaints_list_requires_auth_and_scopes_data():
    # Anonymous -> 401
    res = client.get("/api/complaints")
    assert res.status_code == 401

    # Malformed JWT -> 401
    res = client.get("/api/complaints", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res.status_code == 401

    # Citizen B token (registered user)
    token_b = create_access_token("USR-TEST-B", "citizen")

    # Citizen B querying complaints while passing user_id="USR-STATE-TESTER" (Rani Nayak)
    res = client.get("/api/complaints?user_id=USR-8921", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 200
    data = res.json()
    # Citizen B must NOT see Rani Nayak's complaints (user_id param ignored for non-admins)
    for c in data:
        assert c["citizenPhone"] != "9876543210"
        assert c["id"] not in ["GRV-1042", "GRV-0987", "GRV-0951"]

def test_admin_endpoints_role_guard():
    token_guest = create_access_token("GUEST-0001", "guest")
    token_citizen = create_access_token("USR-8921", "citizen")
    token_admin = create_access_token("EMP-4402", "admin")

    # 1. Anonymous on admin stats -> 401
    res = client.get("/api/admin/stats")
    assert res.status_code == 401

    # 2. Guest on admin stats -> 403
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token_guest}"})
    assert res.status_code == 403

    # 3. Citizen on admin stats -> 403
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token_citizen}"})
    assert res.status_code == 403

    # 4. Admin on admin stats -> 200
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200

def test_notification_read_isolation():
    token_b = create_access_token("USR-TEST-B", "citizen")
    # NOTIF-1 belongs to USR-8921 (Rani Nayak)
    res = client.put("/api/notifications/NOTIF-1/read", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403

    # Anonymous -> 401
    res = client.put("/api/notifications/NOTIF-1/read")
    assert res.status_code == 401

def test_status_update_admin_only_and_state_machine():
    token_citizen = create_access_token("USR-8921", "citizen")
    token_admin = create_access_token("EMP-4402", "admin")

    # Citizen trying to update status -> 403
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "Assigned",
        "officer_note": "Citizen trying to change status"
    }, headers={"Authorization": f"Bearer {token_citizen}"})
    assert res.status_code == 403

    # Admin invalid status string -> 400
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "FakeStatus",
        "officer_note": "Testing invalid status"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 400

    # Admin invalid skip (Submitted -> In Progress directly, skipping Assigned) -> 400
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "In Progress",
        "officer_note": "Skipping assigned"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 400

    # Step 1: Submitted -> Assigned -> 200
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "Assigned",
        "officer_note": "Assigned to nodal officer"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200

    # Step 2: Assigned -> In Progress -> 200
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "In Progress",
        "officer_note": "Field team deployed"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200

    # Step 3: In Progress -> Resolved -> 200
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "Resolved",
        "officer_note": "Pipe repaired"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200

    # Reopen without remark -> 400
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "In Progress",
        "officer_note": ""
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 400

    # Reopen with remark -> 200
    res = client.put("/api/complaints/GRV-STATE-TEST/status", json={
        "status": "In Progress",
        "officer_note": "Citizen reported recurrence, reopening ticket"
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200

def test_feedback_rules():
    token_owner = create_access_token("USR-STATE-TESTER", "citizen")
    token_b = create_access_token("USR-TEST-B", "citizen")

    # 1. Rating out of range (ge=1, le=5) -> 400 or 422
    res = client.post("/api/complaints/GRV-STATE-TEST/feedback", json={"rating": 6}, headers={"Authorization": f"Bearer {token_owner}"})
    assert res.status_code in [400, 422]

    # 2. Cannot submit feedback on unresolved complaint (GRV-STATE-TEST is currently In Progress) -> 400
    res = client.post("/api/complaints/GRV-STATE-TEST/feedback", json={"rating": 5}, headers={"Authorization": f"Bearer {token_owner}"})
    assert res.status_code == 400

    # 3. User B trying on User A's resolved complaint (GRV-0987 is Resolved) -> 403
    res = client.post("/api/complaints/GRV-0987/feedback", json={"rating": 5}, headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403
