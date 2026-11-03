import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"))

from staff_helpers import (
    format_ist,
    sla_label,
    allowed_next_statuses,
    build_filters,
    IST
)

class TestStaffHelpers(unittest.TestCase):
    def test_format_ist(self):
        # 1. Aware datetime in UTC
        aware_utc = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(format_ist(aware_utc), "15 Oct 2026, 15:30")

        # 2. Naive datetime treated as UTC
        naive_dt = datetime(2026, 10, 15, 10, 0)
        self.assertEqual(format_ist(naive_dt), "15 Oct 2026, 15:30")

        # 3. Naive SQL string treated as UTC
        sql_str = "2026-10-15 10:00:00"
        self.assertEqual(format_ist(sql_str), "15 Oct 2026, 15:30")

        # 4. ISO string with Z
        iso_str = "2026-10-15T10:00:00Z"
        self.assertEqual(format_ist(iso_str), "15 Oct 2026, 15:30")

        # 5. None
        self.assertEqual(format_ist(None), "-")

        # 6. Bad string
        self.assertEqual(format_ist("not-a-valid-timestamp"), "-")
        self.assertEqual(format_ist(""), "-")

    def test_sla_label(self):
        base_now = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)

        # 1. Resolved status
        self.assertEqual(sla_label("2026-10-15 08:00:00", "Resolved", now=base_now), "Resolved")
        self.assertEqual(sla_label("2026-10-15 18:00:00", "resolved", now=base_now), "Resolved")

        # 2. Due soon in hours (< 24 hours)
        due_5h20m = base_now + timedelta(hours=5, minutes=20)
        self.assertEqual(sla_label(due_5h20m, "In Progress", now=base_now), "Due in 5h 20m")

        # 3. Due in days (>= 24 hours)
        due_2d3h = base_now + timedelta(days=2, hours=3)
        self.assertEqual(sla_label(due_2d3h, "Submitted", now=base_now), "Due in 2d 3h")

        # 4. Overdue by hours (< 24 hours overdue)
        overdue_4h = base_now - timedelta(hours=4)
        self.assertEqual(sla_label(overdue_4h, "Assigned", now=base_now), "Overdue by 4h")

        # 5. Overdue by days (>= 24 hours overdue)
        overdue_1d6h = base_now - timedelta(days=1, hours=6)
        self.assertEqual(sla_label(overdue_1d6h, "In Progress", now=base_now), "Overdue by 1d 6h")

        # 6. Missing / None due date
        self.assertEqual(sla_label(None, "Submitted", now=base_now), "-")
        self.assertEqual(sla_label("invalid", "Submitted", now=base_now), "-")

    def test_allowed_next_statuses(self):
        # Submitted -> Assigned
        self.assertEqual(allowed_next_statuses("Submitted"), ["Assigned"])
        self.assertEqual(allowed_next_statuses("submitted"), ["Assigned"])

        # Assigned -> In Progress
        self.assertEqual(allowed_next_statuses("Assigned"), ["In Progress"])
        self.assertEqual(allowed_next_statuses("assigned"), ["In Progress"])

        # In Progress -> Resolved
        self.assertEqual(allowed_next_statuses("In Progress"), ["Resolved"])
        self.assertEqual(allowed_next_statuses("in progress"), ["Resolved"])

        # Reopened -> Assigned, In Progress
        self.assertEqual(allowed_next_statuses("Reopened"), ["Assigned", "In Progress"])
        self.assertEqual(allowed_next_statuses("reopened"), ["Assigned", "In Progress"])

        # Resolved -> []
        self.assertEqual(allowed_next_statuses("Resolved"), [])
        self.assertEqual(allowed_next_statuses("resolved"), [])

        # Empty / Unknown -> []
        self.assertEqual(allowed_next_statuses(None), [])
        self.assertEqual(allowed_next_statuses(""), [])
        self.assertEqual(allowed_next_statuses("Closed"), [])

    def test_build_filters(self):
        # 1. Drops empty and 'All'
        f = build_filters(
            status="All",
            priority="Critical",
            department="All",
            area="",
            language=None,
            limit=50
        )
        self.assertEqual(f, {"priority": "Critical", "limit": 50})

        # 2. Maps boolean flags
        f_bools = build_filters(
            overdue_only=True,
            needs_review_only=True,
            status="Submitted"
        )
        self.assertEqual(f_bools, {
            "overdue": True,
            "needs_review": True,
            "status": "Submitted"
        })

        # 3. Drops False booleans
        f_false = build_filters(
            overdue_only=False,
            needs_review_only=False,
            area="Saheed Nagar"
        )
        self.assertEqual(f_false, {"area": "Saheed Nagar"})

if __name__ == "__main__":
    unittest.main()

