import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from app.database import SessionLocal
from app.models import User, Complaint, Notification, ChatSession
from app.routes.auth import create_access_token

client = TestClient(app)

def test_user_isolation_complaints():
    # 1. Login or get token for Rani Nayak (phone 9876543210, id USR-8921)
    db = SessionLocal()
    rani = db.query(User).filter(User.phone == "9876543210").first()
    assert rani is not None, "Rani Nayak should exist in seeded database"
    rani_token = create_access_token(rani.id, "citizen")

    # Verify OTP for brand new user
    res_b = client.post("/api/auth/verify-otp", json={"mobile": "9800112233", "otp": "123456"})
    assert res_b.status_code == 200
    user_b_token = res_b.json()["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # 2. Query complaints for Rani Nayak -> Should see her 3 demo complaints
    res_rani_comp = client.get("/api/complaints", headers={"Authorization": f"Bearer {rani_token}"})
    assert res_rani_comp.status_code == 200
    rani_comp_ids = [c["id"] for c in res_rani_comp.json()]
    assert "GRV-1042" in rani_comp_ids
    assert "GRV-0987" in rani_comp_ids
    assert "GRV-0951" in rani_comp_ids
    assert len(rani_comp_ids) == 3, f"Rani should see only her 3 complaints, got {len(rani_comp_ids)}"

    # 3. Query complaints for User B -> Must be exactly 0 complaints!
    res_b_comp = client.get("/api/complaints", headers={"Authorization": f"Bearer {user_b_token}"})
    assert res_b_comp.status_code == 200
    assert len(res_b_comp.json()) == 0, f"New user must have 0 complaints, got {len(res_b_comp.json())}"

    # 4. User B tries to read Rani's complaint directly by ID -> MUST return 403 Forbidden!
    res_forbidden = client.get("/api/complaints/GRV-1042", headers={"Authorization": f"Bearer {user_b_token}"})
    assert res_forbidden.status_code == 403, f"Expected 403 Forbidden for cross-user complaint access, got {res_forbidden.status_code}"

    # 5. Rani can read her own complaint GRV-1042
    res_owner = client.get("/api/complaints/GRV-1042", headers={"Authorization": f"Bearer {rani_token}"})
    assert res_owner.status_code == 200
    assert res_owner.json()["id"] == "GRV-1042"

    # 6. Admin can read all complaints
    admin = db.query(User).filter(User.role == "admin").first()
    admin_token = create_access_token(admin.id, "admin")
    res_admin = client.get("/api/complaints", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert len(res_admin.json()) >= 70

    # 7. Clean up User B test record
    db.query(User).filter(User.id == user_b_id).delete()
    db.commit()
    db.close()

def test_user_isolation_notifications():
    db = SessionLocal()
    rani = db.query(User).filter(User.phone == "9876543210").first()
    rani_token = create_access_token(rani.id, "citizen")

    # New user
    res_b = client.post("/api/auth/verify-otp", json={"mobile": "9811223344", "otp": "123456"})
    user_b_token = res_b.json()["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # User B notifications: only platform announcements, ZERO user updates!
    res_b_notif = client.get("/api/notifications", headers={"Authorization": f"Bearer {user_b_token}"})
    assert res_b_notif.status_code == 200
    b_updates = [n for n in res_b_notif.json() if n["type"] == "update"]
    assert len(b_updates) == 0, f"New user should have 0 updates, got {len(b_updates)}"

    # Rani should see her update for GRV-1042
    res_rani_notif = client.get("/api/notifications", headers={"Authorization": f"Bearer {rani_token}"})
    assert res_rani_notif.status_code == 200
    rani_updates = [n for n in res_rani_notif.json() if n["type"] == "update"]
    assert len(rani_updates) >= 1
    assert any(n["relatedGrvId"] == "GRV-1042" for n in rani_updates)

    # Clean up
    db.query(User).filter(User.id == user_b_id).delete()
    db.commit()
    db.close()

def test_user_isolation_chat():
    db = SessionLocal()
    rani = db.query(User).filter(User.phone == "9876543210").first()
    rani_token = create_access_token(rani.id, "citizen")

    res_b = client.post("/api/auth/verify-otp", json={"mobile": "9822334455", "otp": "123456"})
    user_b_token = res_b.json()["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # Rani creates a chat session
    session_id = f"CHAT-TEST-RANI-{rani.id}"
    res_chat = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "My street light is broken", "language": "en"},
        headers={"Authorization": f"Bearer {rani_token}"}
    )
    assert res_chat.status_code == 200

    # User B tries to read Rani's chat session -> MUST return 403 Forbidden!
    res_b_read = client.get(
        f"/api/chat/session/{session_id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert res_b_read.status_code == 403, f"Expected 403 Forbidden for cross-user chat access, got {res_b_read.status_code}"

    # Clean up
    db.query(ChatSession).filter(ChatSession.id == session_id).delete()
    db.query(User).filter(User.id == user_b_id).delete()
    db.commit()
    db.close()

