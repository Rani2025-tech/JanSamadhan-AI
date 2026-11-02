import os
import sys
import unittest

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"))

from components import (
    normalize_ticket_id,
    normalize_pin,
    ticket_card,
    understanding_card,
    understanding_card_from_meta,
    pin_notice,
    stepper,
    build_receipt,
    priority_chip,
    status_pill,
    overdue_chip,
    escalation_chip
)

class TestFrontendHelpers(unittest.TestCase):
    def test_normalize_ticket_id(self):
        """Validates ticket ID normalization across ASCII, Devanagari, Odia, and invalid inputs."""
        # Standard ASCII
        self.assertEqual(normalize_ticket_id("GRV-1001"), "GRV-1001")
        self.assertEqual(normalize_ticket_id("grv-1042"), "GRV-1042")
        self.assertEqual(normalize_ticket_id("grv1042"), "GRV-1042")
        self.assertEqual(normalize_ticket_id("  GRV 2050  "), "GRV-2050")

        # Devanagari Numerals (०-९)
        self.assertEqual(normalize_ticket_id("GRV-१०४२"), "GRV-1042")
        self.assertEqual(normalize_ticket_id("grv१०४२"), "GRV-1042")

        # Odia Numerals (୦-୯)
        self.assertEqual(normalize_ticket_id("GRV-୧୦୪୨"), "GRV-1042")
        self.assertEqual(normalize_ticket_id("grv୧୦୪୨"), "GRV-1042")

        # Mixed string context
        self.assertEqual(normalize_ticket_id("My ticket is GRV-3001 thanks"), "GRV-3001")

        # Invalid / garbage inputs
        self.assertIsNone(normalize_ticket_id("garbage text"))
        self.assertIsNone(normalize_ticket_id(""))
        self.assertIsNone(normalize_ticket_id(None))
        self.assertIsNone(normalize_ticket_id("GRV-12"))  # under 3 digits
        self.assertIsNone(normalize_ticket_id("TKT-1001"))

    def test_normalize_pin(self):
        """Validates 6-digit tracking PIN normalization across ASCII, Devanagari, Odia, whitespace, and invalid inputs."""
        self.assertEqual(normalize_pin("123456"), "123456")
        self.assertEqual(normalize_pin("१२३४५६"), "123456")
        self.assertEqual(normalize_pin("୧୨୩୪୫୬"), "123456")
        self.assertEqual(normalize_pin(" 12 34 56 "), "123456")
        self.assertEqual(normalize_pin("  987654  "), "987654")

        # Invalid lengths / characters
        self.assertIsNone(normalize_pin("12345"))  # 5 digits
        self.assertIsNone(normalize_pin("1234567"))  # 7 digits
        self.assertIsNone(normalize_pin("12345A"))  # alphanumeric
        self.assertIsNone(normalize_pin(""))
        self.assertIsNone(normalize_pin(None))
        self.assertIsNone(normalize_pin("abcdef"))

    def test_html_escaping_in_cards(self):
        """Verifies dynamic inputs in ticket_card and understanding_card are escaped against XSS."""
        malicious_ticket = {
            "ticket_id": "GRV-1001",
            "department": "Water Board <script>alert('dept')</script>",
            "category": "Water <img src=x onerror=alert(1)>",
            "location": "Ward 4 <b onmouseover=alert('loc')>",
            "summary": "Pipe burst <script>alert('xss')</script>",
            "confidence": 0.95,
            "priority": "High",
            "status": "In Progress"
        }

        # Check understanding_card
        u_html = understanding_card(malicious_ticket, lang="en")
        self.assertNotIn("<script>", u_html)
        self.assertNotIn("<img", u_html)
        self.assertNotIn("<b onmouseover", u_html)
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", u_html)

        # Check ticket_card
        t_html = ticket_card(malicious_ticket, lang="en")
        self.assertNotIn("<script>", t_html)
        self.assertNotIn("<b onmouseover", t_html)
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", t_html)

    def test_understanding_card_from_meta_escaping(self):
        """Ensures understanding_card_from_meta safely escapes all dynamic metadata."""
        malicious_meta = {
            "ticket_id": "GRV-9999",
            "department": "Sanitation <script>alert('dept')</script>",
            "category": "Waste <img src=x onerror=alert(1)>",
            "location": "Sector 5 <svg onload=alert(2)>",
            "summary": "Garbage dump <script>alert('meta')</script>",
            "confidence": 0.99,
            "priority": "Critical"
        }
        card_html = understanding_card_from_meta(malicious_meta, lang="en")
        self.assertNotIn("<script>", card_html)
        self.assertNotIn("<img", card_html)
        self.assertNotIn("<svg", card_html)
        self.assertIn("&lt;script&gt;alert(&#x27;meta&#x27;)&lt;/script&gt;", card_html)
        self.assertIn("GRV-9999", card_html)

    def test_pin_notice(self):
        """Verifies PIN notice security callout contains both ticket ID and 6-digit PIN."""
        notice_html = pin_notice("654321", "GRV-1001", "en")
        self.assertIn("654321", notice_html)
        self.assertIn("GRV-1001", notice_html)
        self.assertIn("pin-code", notice_html)

    def test_public_ticket_tolerance(self):
        """Ensures ticket_card, stepper, and build_receipt tolerate public ticket shape without crashing."""
        public_ticket = {
            "ticket_id": "GRV-2002",
            "status": "In Progress",
            "department": "Electricity Department",
            "category": "Power Outage",
            "priority": "High",
            "created_at": "2026-10-31 10:00:00",
            "updated_at": "2026-10-31 12:00:00",
            "sla_due_at": "2026-11-01 10:00:00",
            "overdue": False,
            "report_count": 1,
            "cluster_report_count": 1,
            "history": [
                {"status": "Submitted", "note": "Registered", "created_at": "2026-10-31 10:00:00", "actor": "System"},
                {"status": "In Progress", "note": "Technician dispatched", "created_at": "2026-10-31 12:00:00", "actor": "Department staff"}
            ]
        }

        # 1. ticket_card tolerates omitted summary and location
        card_html = ticket_card(public_ticket, lang="en")
        self.assertIn("GRV-2002", card_html)
        self.assertIn("Protected", card_html)
        self.assertIn("Electricity Department", card_html)

        # 2. stepper tolerates history
        step_html = stepper(public_ticket["status"], public_ticket["history"], lang="en")
        self.assertIn("step-current", step_html)

        # 3. build_receipt without private data
        receipt = build_receipt(public_ticket, lang="en")
        self.assertIn("GRV-2002", receipt)
        self.assertNotIn("Tracking PIN:", receipt)

    def test_stepper_step_index_per_status(self):
        """Verifies progression index and reopened note in stepper component."""
        hist = [
            {"status": "Submitted", "created_at": "2026-10-31 10:00:00"},
            {"status": "Assigned", "created_at": "2026-10-31 11:00:00"},
            {"status": "In Progress", "created_at": "2026-10-31 12:00:00"}
        ]

        # 1. Submitted (index 0 current)
        step_sub = stepper("Submitted", hist, "en")
        self.assertIn("step-current", step_sub)
        self.assertIn("Submitted", step_sub)

        # 2. Assigned (index 0 done, index 1 current)
        step_asg = stepper("Assigned", hist, "en")
        self.assertIn("step-done", step_asg)
        self.assertIn("step-current", step_asg)

        # 3. In Progress (index 2 current)
        step_prog = stepper("In Progress", hist, "en")
        self.assertIn("step-current", step_prog)

        # 4. Reopened (index 2 current with note)
        step_reopened = stepper("Reopened", hist, "en")
        self.assertIn("step-current", step_reopened)
        self.assertIn("reopened", step_reopened.lower())

        # 5. Resolved (index 3 current)
        step_res = stepper("Resolved", hist, "en")
        self.assertIn("step-current", step_res)
        self.assertIn("✓", step_res)

    def test_build_receipt(self):
        """Ensures receipt generation formats ticket ID, department, and summary properly."""
        ticket_data = {
            "ticket_id": "GRV-5542",
            "department": "Public Works Department",
            "category": "Roads & Potholes",
            "location": "Near Hospital Gate 2",
            "status": "Assigned",
            "priority": "High",
            "sla_due_at": "2026-11-02 18:00:00",
            "created_at": "2026-10-31 18:00:00",
            "confidence": 0.92,
            "summary": "Severe pothole causing vehicle damage",
            "original_text": "Huge pothole outside hospital gate"
        }

        receipt = build_receipt(ticket_data, "en")
        self.assertIn("GRV-5542", receipt)
        self.assertIn("Public Works Department", receipt)
        self.assertIn("Roads & Potholes", receipt)
        self.assertIn("Near Hospital Gate 2", receipt)
        self.assertIn("High", receipt)
        self.assertIn("Severe pothole causing vehicle damage", receipt)
        self.assertIn("JANSAMADHAN GRIEVANCE RECEIPT", receipt)
        self.assertNotIn("Tracking PIN:", receipt)

    def test_build_receipt_conditional_pin(self):
        """Verifies receipt conditionally includes Tracking PIN only when explicitly passed."""
        ticket_data = {
            "ticket_id": "GRV-7777",
            "department": "Water Supply Department",
            "category": "Contaminated Water",
            "location": "Block C",
            "status": "Submitted",
            "priority": "Critical"
        }

        # Without PIN
        receipt_no_pin = build_receipt(ticket_data, "en", pin=None)
        self.assertNotIn("Tracking PIN:", receipt_no_pin)

        # With PIN
        receipt_with_pin = build_receipt(ticket_data, "en", pin="654321")
        self.assertIn("Tracking PIN:", receipt_with_pin)
        self.assertIn("654321", receipt_with_pin)

if __name__ == "__main__":
    unittest.main()
