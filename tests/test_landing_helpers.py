import os
import sys
import time
import unittest
from unittest.mock import patch, Mock

# Ensure project root and frontend are in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"))

from auth_helpers import (
    is_staff_session_valid,
    set_staff_session,
    clear_staff_session,
    valid_mobile,
    role_allowed
)
from landing_helpers import format_resolution_time, format_public_stats
from ui_text import ui
from icons import icon, ICONS

class TestLandingHelpers(unittest.TestCase):
    def test_is_staff_session_valid_success(self):
        """Verifies valid sessions for ADMIN and DEPARTMENT_OFFICIAL return True."""
        now = time.time()

        # 1. Valid ADMIN session
        admin_session = {
            "token": "valid_admin_token_xyz",
            "role": "ADMIN",
            "staff_name": "Chief Administrator",
            "department": None,
            "token_expires_at": now + 3600
        }
        self.assertTrue(is_staff_session_valid(admin_session))

        # 2. Valid DEPARTMENT_OFFICIAL session
        official_session = {
            "token": "valid_official_token_abc",
            "role": "DEPARTMENT_OFFICIAL",
            "staff_name": "Executive Engineer",
            "department": "Water Supply Department",
            "token_expires_at": now + 1800
        }
        self.assertTrue(is_staff_session_valid(official_session))

    def test_is_staff_session_valid_expired(self):
        """Verifies expired sessions return False and are purged from session state."""
        past_time = time.time() - 300  # 5 minutes ago
        expired_session = {
            "token": "expired_jwt_token",
            "role": "ADMIN",
            "staff_name": "Expired Admin",
            "department": None,
            "token_expires_at": past_time,
            "unlocked_tickets": {"GRV-1001": {"location": "Secret Ward"}},
            "unlocked_pins": {"GRV-1001": "123456"},
            "last_pin": "123456"
        }

        self.assertFalse(is_staff_session_valid(expired_session))
        # Expiry must clear staff keys and cached private citizen data
        self.assertNotIn("token", expired_session)
        self.assertNotIn("role", expired_session)
        self.assertNotIn("token_expires_at", expired_session)
        self.assertNotIn("unlocked_tickets", expired_session)
        self.assertNotIn("unlocked_pins", expired_session)
        self.assertNotIn("last_pin", expired_session)

    def test_is_staff_session_valid_missing(self):
        """Verifies empty or incomplete session states return False."""
        now = time.time()

        # Empty session
        self.assertFalse(is_staff_session_valid({}))

        # Missing token
        self.assertFalse(is_staff_session_valid({
            "role": "ADMIN",
            "token_expires_at": now + 3600
        }))

        # Missing role
        self.assertFalse(is_staff_session_valid({
            "token": "token_without_role",
            "token_expires_at": now + 3600
        }))

        # Missing token_expires_at
        self.assertFalse(is_staff_session_valid({
            "token": "token_without_expiry",
            "role": "ADMIN"
        }))

        # Unauthorized / non-staff role
        invalid_role_session = {
            "token": "guest_token",
            "role": "CITIZEN",
            "token_expires_at": now + 3600
        }
        self.assertFalse(is_staff_session_valid(invalid_role_session))
        self.assertNotIn("token", invalid_role_session)

    def test_clear_staff_session(self):
        """Verifies clear_staff_session removes all staff credentials and private tracking state."""
        session = {
            "token": "token123",
            "admin_token": "token123",
            "role": "ADMIN",
            "staff_name": "Admin",
            "department": "Engineering",
            "token_expires_at": time.time() + 1000,
            "unlocked_tickets": {"GRV-2002": {}},
            "unlocked_pins": {"GRV-2002": "654321"},
            "last_pin": "654321",
            "chat_state": {"stage": "idle"}  # un-related key should remain
        }
        clear_staff_session(session)
        self.assertNotIn("token", session)
        self.assertNotIn("role", session)
        self.assertNotIn("staff_name", session)
        self.assertNotIn("department", session)
        self.assertNotIn("token_expires_at", session)
        self.assertNotIn("unlocked_tickets", session)
        self.assertNotIn("unlocked_pins", session)
        self.assertNotIn("last_pin", session)
        self.assertIn("chat_state", session)

    def test_set_staff_session(self):
        """Verifies set_staff_session stores token, role, staff_name, department, and computed expiry."""
        session = {}
        login_payload = {
            "token": "jwt_sample_token",
            "role": "ADMIN",
            "name": "Jane Doe",
            "department": "Public Works",
            "expires_in": 7200
        }
        before = time.time()
        set_staff_session(login_payload, session)
        after = time.time()

        self.assertEqual(session["token"], "jwt_sample_token")
        self.assertEqual(session["role"], "ADMIN")
        self.assertEqual(session["staff_name"], "Jane Doe")
        self.assertEqual(session["department"], "Public Works")
        self.assertGreaterEqual(session["token_expires_at"], before + 7200)
        self.assertLessEqual(session["token_expires_at"], after + 7200)

    def test_format_resolution_time(self):
        """Validates SLA resolution time formatting under 48 hours and 48+ hours in days (1 decimal)."""
        # Under 48 hours -> in hours
        self.assertEqual(format_resolution_time(1), "1 hr")
        self.assertEqual(format_resolution_time(12), "12 hrs")
        self.assertEqual(format_resolution_time(24.0), "24 hrs")
        self.assertEqual(format_resolution_time(47), "47 hrs")

        # 48 hours and above -> in days with 1 decimal
        self.assertEqual(format_resolution_time(48), "2.0 days")
        self.assertEqual(format_resolution_time(60), "2.5 days")
        self.assertEqual(format_resolution_time(72.0), "3.0 days")
        self.assertEqual(format_resolution_time(100), "4.2 days")

        # Null or missing -> N/A
        self.assertEqual(format_resolution_time(None), "N/A")
        self.assertEqual(format_resolution_time("invalid"), "N/A")

    def test_format_public_stats(self):
        """Validates format_public_stats produces correct output and demo badge behavior."""
        raw_stats = {
            "total": 150,
            "resolved": 120,
            "open": 30,
            "avg_resolution_hours": 36.0,
            "overdue_count": 2,
            "demo": True
        }
        formatted = format_public_stats(raw_stats)
        self.assertEqual(formatted["total"], 150)
        self.assertEqual(formatted["resolved"], 120)
        self.assertEqual(formatted["open"], 30)
        self.assertEqual(formatted["avg_resolution_str"], "36 hrs")
        self.assertEqual(formatted["demo_label"], "Demo data")

        # When demo is False
        raw_prod = {
            "total": 50,
            "resolved": 40,
            "open": 10,
            "avg_resolution_hours": 72.0,
            "overdue_count": 0,
            "demo": False
        }
        formatted_prod = format_public_stats(raw_prod)
        self.assertEqual(formatted_prod["avg_resolution_str"], "3.0 days")
        self.assertEqual(formatted_prod["demo_label"], "")

    def test_valid_mobile(self):
        """Validates 10-digit Indian mobile number parsing and normalization."""
        # 1. Valid standard 10-digit
        self.assertEqual(valid_mobile("9876543210"), "9876543210")
        self.assertEqual(valid_mobile("8876543210"), "8876543210")
        self.assertEqual(valid_mobile("7876543210"), "7876543210")
        self.assertEqual(valid_mobile("6876543210"), "6876543210")

        # 2. With +91 prefix
        self.assertEqual(valid_mobile("+919876543210"), "9876543210")
        self.assertEqual(valid_mobile("+91 98765 43210"), "9876543210")

        # 3. With spaces and dashes
        self.assertEqual(valid_mobile(" 98765 43210 "), "9876543210")
        self.assertEqual(valid_mobile("98765-43210"), "9876543210")

        # 4. With leading 0 (11 digits starting with 0)
        self.assertEqual(valid_mobile("09876543210"), "9876543210")
        self.assertEqual(valid_mobile(" 0 9876543210 "), "9876543210")

        # 5. Too short
        self.assertIsNone(valid_mobile("98765"))
        self.assertIsNone(valid_mobile("987654321"))

        # 6. Starts with 5 (or < 6)
        self.assertIsNone(valid_mobile("5876543210"))
        self.assertIsNone(valid_mobile("+91 58765 43210"))
        self.assertIsNone(valid_mobile("05876543210"))
        self.assertIsNone(valid_mobile("1234567890"))

        # 7. Letters / alphanumeric
        self.assertIsNone(valid_mobile("98765abcde"))
        self.assertIsNone(valid_mobile("9876543210A"))
        self.assertIsNone(valid_mobile("abcdefghij"))

        # 8. Empty / None
        self.assertIsNone(valid_mobile(""))
        self.assertIsNone(valid_mobile(None))

    def test_role_allowed(self):
        """Validates role tab authorization mapping and case tolerance."""
        # 1. Matching cases
        self.assertTrue(role_allowed("citizen", "CITIZEN"))
        self.assertTrue(role_allowed("Citizen", "CITIZEN"))
        self.assertTrue(role_allowed("official", "DEPARTMENT_OFFICIAL"))
        self.assertTrue(role_allowed("Department official", "DEPARTMENT_OFFICIAL"))
        self.assertTrue(role_allowed("department official", "DEPARTMENT_OFFICIAL"))
        self.assertTrue(role_allowed("admin", "ADMIN"))
        self.assertTrue(role_allowed("Administrator", "ADMIN"))

        # 2. Lowercase server role tolerance
        self.assertTrue(role_allowed("official", "department_official"))
        self.assertTrue(role_allowed("admin", "admin"))
        self.assertTrue(role_allowed("citizen", "citizen"))

        # 3. Mismatching roles
        self.assertFalse(role_allowed("official", "ADMIN"))
        self.assertFalse(role_allowed("admin", "DEPARTMENT_OFFICIAL"))
        self.assertFalse(role_allowed("citizen", "ADMIN"))
        self.assertFalse(role_allowed("admin", "CITIZEN"))

        # 4. Unknown tab or role
        self.assertFalse(role_allowed("superadmin", "ADMIN"))
        self.assertFalse(role_allowed("guest", "CITIZEN"))
        self.assertFalse(role_allowed("unknown", "DEPARTMENT_OFFICIAL"))
        self.assertFalse(role_allowed("", "ADMIN"))
        self.assertFalse(role_allowed("admin", ""))
        self.assertFalse(role_allowed(None, "ADMIN"))
        self.assertFalse(role_allowed("admin", None))

    def test_home_ui_keys_no_otp_or_emojis_and_icons(self):
        """Verifies no English UI keys in home.py contain OTP/Register or emojis, and icons return SVGs."""
        home_keys = [
            "landing_headline", "landing_tagline", "demo_prototype",
            "citizen_title", "citizen_subtitle", "staff_title", "staff_subtitle",
            "ph_mobile", "invalid_mobile_msg", "btn_start_complaint", "or_text",
            "btn_track", "link_staff", "ph_email", "ph_password", "login_button",
            "link_citizen", "staff_note",
            # Phase 7c-10 new card keys
            "login_card_title", "login_card_subtitle", "role_citizen", "role_official", "role_admin",
            "label_mobile", "optional_text", "label_email", "label_password",
            "btn_demo_citizen", "btn_demo_official", "btn_demo_admin",
            "link_track_complaint", "privacy_safe_title", "privacy_safe_sub",
            "privacy_staff_title", "privacy_staff_sub", "staff_admin_created_note",
            "err_role_mismatch", "btn_send_otp", "link_have_account_login", "link_back_citizen"
        ]

        forbidden = ["register"]
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # Emoticons
            (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
            (0x1F680, 0x1F6FF),  # Transport and Map
            (0x1F1E0, 0x1F1FF),  # Flags
            (0x2700, 0x27BF),    # Dingbats
            (0x1F900, 0x1F9FF),  # Supplemental Symbols
            (0x2600, 0x26FF),    # Misc symbols
        ]

        def contains_emoji(s: str) -> bool:
            return any(start <= ord(ch) <= end for ch in s for start, end in emoji_ranges)

        for key in home_keys:
            text = ui(key, "en")
            for term in forbidden:
                self.assertNotIn(term, text.lower(), f"Key '{key}' contains forbidden term '{term}'")
            self.assertFalse(contains_emoji(text), f"Key '{key}' contains emoji in text: {text}")

        # Check all icons return valid svg string
        for icon_name in ICONS:
            svg = icon(icon_name)
            self.assertTrue(svg.startswith("<svg"), f"Icon '{icon_name}' does not start with <svg")
            self.assertTrue(svg.endswith("</svg>"), f"Icon '{icon_name}' does not end with </svg>")

    @patch("api_client._request_with_retry")
    def test_demo_login_error_mapping(self, mock_req):
        """Verifies api_client.demo_login maps 404 and 429 errors correctly."""
        import api_client

        # 1. 404 mapping
        mock_resp_404 = Mock()
        mock_resp_404.status_code = 404
        mock_resp_404.text = "Not found"
        mock_req.return_value = mock_resp_404

        with self.assertRaises(api_client.ApiError) as cm_404:
            api_client.demo_login("admin")
        self.assertEqual(cm_404.exception.status_code, 404)
        self.assertEqual(cm_404.exception.message, "Demo mode is not enabled on this server.")

        # 2. 429 mapping with Retry-After
        mock_resp_429 = Mock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {"Retry-After": "120"}
        mock_resp_429.text = "Too many requests"
        mock_req.return_value = mock_resp_429

        with self.assertRaises(api_client.ApiError) as cm_429:
            api_client.demo_login("official")
        self.assertEqual(cm_429.exception.status_code, 429)
        self.assertIn("120 seconds", cm_429.exception.message)

    def test_staff_session_demo_flag(self):
        """Verifies set_staff_session and clear_staff_session manage staff_demo flag."""
        session = {}
        login_data = {
            "token": "demo_jwt_token_123",
            "role": "ADMIN",
            "name": "Demo Administrator (demo)",
            "department": None,
            "expires_in": 1800,
            "demo": True
        }
        set_staff_session(login_data, session=session)
        self.assertTrue(session.get("staff_demo"))
        self.assertEqual(session.get("staff_name"), "Demo Administrator (demo)")

        clear_staff_session(session=session)
        self.assertNotIn("staff_demo", session)
        self.assertNotIn("token", session)

        session_normal = {}
        set_staff_session({"token": "normal_token", "role": "ADMIN"}, session=session_normal)
        self.assertFalse(session_normal.get("staff_demo"))

if __name__ == "__main__":
    unittest.main()

