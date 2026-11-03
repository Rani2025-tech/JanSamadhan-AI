import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")
os.environ.setdefault("JWT_SECRET", "mock_jwt_secret_for_testing_1234567890")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass@2026")
os.environ.setdefault("ADMIN_EMAIL", "admin@jansamadhan.local")

import backend.db.database as db_mod
import backend.db.grievances as grv_mod

class TestEscalation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_escalation.db")
        db_mod.DB_PATH = self.test_db
        db_mod.init_db()
        grv_mod.init_grievance_tables()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sla_escalation_three_thresholds_idempotence_and_history(self):
        # Medium priority SLA window = 168 hours
        t0 = datetime(2026, 1, 1, 12, 0, 0)
        tid = grv_mod.create_grievance({
            "original_text": "Water leakage in sector 5",
            "department": "Public Health Engineering / Water Board",
            "category": "Water Supply",
            "priority": "Medium"
        })

        # Manually set sla_due_at to T0 for controlled time testing
        conn = db_mod.get_conn()
        c = conn.cursor()
        t0_str = t0.strftime("%Y-%m-%d %H:%M:%S")
        db_mod._exec(c, f"UPDATE grievances SET sla_due_at = {db_mod._ph()} WHERE ticket_id = {db_mod._ph()}", (t0_str, tid))
        conn.commit()
        conn.close()

        # Initial level is 0
        self.assertEqual(grv_mod.get_grievance(tid)["escalation_level"], 0)

        # ── Threshold 1: Overdue by 1 hour (0 < diff <= 0.5 * 168) -> Level 1 ──
        t1 = t0 + timedelta(hours=1)
        count = grv_mod.run_escalation(now=t1)
        self.assertEqual(count, 1)

        rec1 = grv_mod.get_grievance(tid, now=t1)
        self.assertEqual(rec1["escalation_level"], 1)
        self.assertTrue(rec1["overdue"])
        self.assertAlmostEqual(rec1["hours_overdue"], 1.0, places=1)

        # Idempotence check at T1: second run should make 0 changes
        count_repeat = grv_mod.run_escalation(now=t1)
        self.assertEqual(count_repeat, 0)
        rec1_rep = grv_mod.get_grievance(tid, now=t1)
        self.assertEqual(rec1_rep["escalation_level"], 1)

        # ── Threshold 2: Overdue by 90 hours (> 0.5 * 168 = 84h) -> Level 2 ──
        t2 = t0 + timedelta(hours=90)
        count2 = grv_mod.run_escalation(now=t2)
        self.assertEqual(count2, 1)

        rec2 = grv_mod.get_grievance(tid, now=t2)
        self.assertEqual(rec2["escalation_level"], 2)

        # ── Threshold 3: Overdue by 180 hours (> 1.0 * 168 = 168h) -> Level 3 ──
        t3 = t0 + timedelta(hours=180)
        count3 = grv_mod.run_escalation(now=t3)
        self.assertEqual(count3, 1)

        rec3 = grv_mod.get_grievance(tid, now=t3)
        self.assertEqual(rec3["escalation_level"], 3)

        # Idempotence check at T3
        self.assertEqual(grv_mod.run_escalation(now=t3), 0)

        # Verify history rows: exactly 3 escalation rows, one for each level
        escalation_history = [h for h in rec3["history"] if "SLA breached, escalated to level" in h.get("note", "")]
        self.assertEqual(len(escalation_history), 3)
        self.assertEqual(escalation_history[0]["note"], "SLA breached, escalated to level 1")
        self.assertEqual(escalation_history[1]["note"], "SLA breached, escalated to level 2")
        self.assertEqual(escalation_history[2]["note"], "SLA breached, escalated to level 3")
        self.assertTrue(all(h["actor"] == "System" for h in escalation_history))

    def test_reopened_ticket_resets_sla_and_escalation_level(self):
        tid = grv_mod.create_grievance({
            "original_text": "Street light dark",
            "department": "Municipal Corporation - Electrical Department",
            "priority": "Low",
            "status": "Submitted"
        })

        # Set escalation level 2 and an overdue SLA
        past_str = (datetime.utcnow() - timedelta(hours=50)).strftime("%Y-%m-%d %H:%M:%S")
        conn = db_mod.get_conn()
        c = conn.cursor()
        db_mod._exec(c, f"UPDATE grievances SET sla_due_at = {db_mod._ph()}, escalation_level = 2, status = 'Resolved' WHERE ticket_id = {db_mod._ph()}", (past_str, tid))
        conn.commit()
        conn.close()

        # Reopen ticket via status update
        grv_mod.update_status(tid, "Reopened", note="Issue reported again by resident", actor="Citizen")

        reopened_rec = grv_mod.get_grievance(tid)
        self.assertEqual(reopened_rec["status"], "Reopened")
        self.assertEqual(reopened_rec["escalation_level"], 0)

        # Fresh SLA due at must be in the future
        fresh_due = datetime.strptime(reopened_rec["sla_due_at"][:19], "%Y-%m-%d %H:%M:%S")
        self.assertGreater(fresh_due, datetime.utcnow())
        self.assertFalse(reopened_rec["overdue"])

    def test_overdue_filter_and_stats(self):
        # Create one non-overdue and one overdue ticket
        future_str = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        past_str = (datetime.utcnow() - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")

        tid_normal = grv_mod.create_grievance({"original_text": "Normal issue", "department": "Public Works Department"})
        tid_overdue = grv_mod.create_grievance({"original_text": "Overdue issue", "department": "Public Works Department"})

        conn = db_mod.get_conn()
        c = conn.cursor()
        db_mod._exec(c, f"UPDATE grievances SET sla_due_at = {db_mod._ph()} WHERE ticket_id = {db_mod._ph()}", (future_str, tid_normal))
        db_mod._exec(c, f"UPDATE grievances SET sla_due_at = {db_mod._ph()} WHERE ticket_id = {db_mod._ph()}", (past_str, tid_overdue))
        conn.commit()
        conn.close()

        # Test overdue=True filter
        overdue_list = grv_mod.list_grievances(overdue=True)
        overdue_ids = [t["ticket_id"] for t in overdue_list]
        self.assertIn(tid_overdue, overdue_ids)
        self.assertNotIn(tid_normal, overdue_ids)

        # Test overdue=False filter
        non_overdue_list = grv_mod.list_grievances(overdue=False)
        non_overdue_ids = [t["ticket_id"] for t in non_overdue_list]
        self.assertIn(tid_normal, non_overdue_ids)
        self.assertNotIn(tid_overdue, non_overdue_ids)

        # Test get_stats contains escalation and overdue counts
        stats = grv_mod.get_stats()
        self.assertIn("overdue_count", stats)
        self.assertGreaterEqual(stats["overdue_count"], 1)
        self.assertIn("overdue_by_dept", stats)
        self.assertIn("by_escalation_level", stats)
        self.assertIn(0, stats["by_escalation_level"])

if __name__ == "__main__":
    unittest.main()

