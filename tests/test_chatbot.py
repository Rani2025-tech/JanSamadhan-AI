import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.db.database as db_mod
import backend.db.grievances as grv_mod
from backend.core.chatbot import handle_message, normalize_digits
from backend.core.llm_wrapper import LLMUnavailable
from backend.core.messages import t

def fake_embed(text):
    v = np.zeros(384, dtype=np.float32)
    v[0] = 1.0
    return v

class TestChatbotFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.temp_dir.name, "test_chatbot.db")
        db_mod.DB_PATH = self.test_db
        grv_mod.init_grievance_tables()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("backend.core.embedder.embed_single", side_effect=fake_embed)
    def test_complaint_with_location_creates_ticket(self, mock_emb):
        """Complaint with identified location creates ticket immediately."""
        fake_u = {
            "language": "en",
            "english_text": "Live wire sparking near Market Hospital",
            "category": "Electricity",
            "location": "Market Hospital",
            "summary": "Live wire sparking near Market Hospital",
            "missing": [],
            "used_llm": True,
            "needs_review": False
        }
        with patch("backend.core.chatbot.understand", return_value=fake_u):
            reply, state, meta = handle_message("Live wire sparking near Market Hospital")
            self.assertIn("GRV-", reply)
            self.assertIn(meta["department"], reply)
            self.assertEqual(meta["priority"], "Critical")
            self.assertTrue(meta["ticket_id"].startswith("GRV-"))
            self.assertEqual(state["stage"], "idle")

    @patch("backend.core.embedder.embed_single", side_effect=fake_embed)
    def test_complaint_without_location_multi_turn(self, mock_emb):
        """Complaint without location asks once, then creates ticket on second turn."""
        fake_u_no_loc = {
            "language": "en",
            "english_text": "Sewage overflowing on street",
            "category": "Drainage & Sewage",
            "location": None,
            "summary": "Sewage overflowing on street",
            "missing": ["location"],
            "used_llm": True,
            "needs_review": False
        }
        with patch("backend.core.chatbot.understand", return_value=fake_u_no_loc):
            # Turn 1: First complaint message missing location
            reply1, state1, meta1 = handle_message("Sewage overflowing on street")
            self.assertEqual(state1["stage"], "awaiting_location")
            self.assertTrue(meta1.get("needs_location"))
            self.assertIn("location", reply1.lower())

            # Turn 2: User provides location
            reply2, state2, meta2 = handle_message("Ward 5 near Post Office", state=state1)
            self.assertEqual(state2["stage"], "idle")
            self.assertTrue(meta2.get("ticket_id", "").startswith("GRV-"))
            self.assertIn("GRV-", reply2)

    def test_status_lookup_ascii_and_indic_digits(self):
        """Status check works with ASCII, Devanagari and Odia numerals."""
        # Create a ticket in db directly
        tid = grv_mod.create_grievance({
            "citizen_name": "Ramesh",
            "original_text": "Potholes on road",
            "language": "en",
            "department": "Public Works Department",
            "category": "Roads & Potholes",
            "priority": "Medium",
            "status": "In Progress"
        })
        self.assertTrue(tid.startswith("GRV-"))
        num = tid.split("-")[1]

        # 1. ASCII format with hyphen and without hyphen
        reply1, _, meta1 = handle_message(f"Status of {tid}?")
        self.assertTrue(meta1["found"])
        self.assertIn("In Progress", reply1)
        self.assertIn("Public Works Department", reply1)

        reply2, _, meta2 = handle_message(f"GRV{num}")
        self.assertTrue(meta2["found"])

        # 2. Devanagari digits
        dev_digits = str.maketrans("0123456789", "०१२३४५६७८९")
        dev_tid = tid.translate(dev_digits)
        reply3, _, meta3 = handle_message(f"मेरी शिकायत {dev_tid} की स्थिति क्या है?")
        self.assertTrue(meta3["found"])
        self.assertEqual(meta3["ticket_id"], tid)

        # 3. Odia digits
        odia_digits = str.maketrans("0123456789", "୦୧୨୩୪୫୬୭୮୯")
        odia_tid = tid.translate(odia_digits)
        reply4, _, meta4 = handle_message(f"ମୋ ଅଭିଯୋଗ {odia_tid} ର ସ୍ଥିତି")
        self.assertTrue(meta4["found"])
        self.assertEqual(meta4["ticket_id"], tid)

    def test_unknown_ticket(self):
        """Querying an unknown ticket returns status_not_found."""
        reply, _, meta = handle_message("GRV-9999")
        self.assertFalse(meta.get("found"))
        self.assertIn("9999", reply)
        self.assertIn(t("status_not_found", ticket_id="GRV-9999")[:15], reply)

    def test_greeting_and_short_inputs_create_nothing(self):
        """Greetings, thanks, and ultra-short texts never create tickets."""
        for greet in ["Hello", "Namaste", "नमस्ते", "Good morning", "Thanks", "ଧନ୍ୟବାଦ"]:
            reply, state, meta = handle_message(greet)
            self.assertNotIn("ticket_id", meta)
            self.assertEqual(state["stage"], "idle")

        # Short input under 8 chars
        reply, state, meta = handle_message("Help me")
        self.assertNotIn("ticket_id", meta)
        self.assertIn(t("ask_describe")[:15], reply)

    @patch("backend.core.embedder.embed_single", side_effect=fake_embed)
    def test_llm_unavailable_creates_flagged_ticket(self, mock_emb):
        """When LLM is unavailable, zero-network fallback still registers flagged ticket."""
        with patch("backend.core.chatbot.understand", side_effect=LLMUnavailable("All keys exhausted")):
            reply, state, meta = handle_message("Major water pipe burst flooding the street")
            self.assertTrue(meta["ticket_id"].startswith("GRV-"))
            self.assertTrue(meta["needs_review"])
            self.assertIn("GRV-", reply)
            self.assertIn("manual verification", reply.lower())

    def test_clustering_of_three_similar_complaints(self):
        """Three similar complaints in the same category group into a cluster with report count 3."""
        # Use an identical embedding vector to simulate high similarity
        def cluster_embed(text):
            v = np.zeros(384, dtype=np.float32)
            v[0] = 1.0
            return v

        def mock_triage(u, original_text=""):
            return {
                "department": "Public Health Engineering / Water Board",
                "category": "Water Supply",
                "confidence": 0.95,
                "routing_reason": "Matched Water Supply",
                "priority": "Medium",
                "priority_reason": "Water issue",
                "needs_review": False
            }

        with patch("backend.core.embedder.embed_single", side_effect=cluster_embed), \
             patch("backend.core.chatbot.triage", side_effect=mock_triage):
            c1_u = {
                "language": "en", "english_text": "Water pipeline burst near Market",
                "category": "Water Supply", "location": "Market", "summary": "Water pipeline burst near Market",
                "missing": [], "used_llm": True, "needs_review": False
            }
            c2_u = {
                "language": "en", "english_text": "Water pipeline leaking heavily at Market",
                "category": "Water Supply", "location": "Market", "summary": "Water pipeline leaking heavily at Market",
                "missing": [], "used_llm": True, "needs_review": False
            }
            c3_u = {
                "language": "en", "english_text": "Water gushing from pipe near Market",
                "category": "Water Supply", "location": "Market", "summary": "Water gushing from pipe near Market",
                "missing": [], "used_llm": True, "needs_review": False
            }

            with patch("backend.core.chatbot.understand", return_value=c1_u):
                _, _, meta1 = handle_message("Water pipeline burst near Market")
            t1 = meta1["ticket_id"]
            self.assertIsNone(meta1["cluster"])

            with patch("backend.core.chatbot.understand", return_value=c2_u):
                reply2, _, meta2 = handle_message("Water pipeline leaking heavily at Market")
            t2 = meta2["ticket_id"]
            self.assertIsNotNone(meta2["cluster"])
            self.assertEqual(meta2["cluster"]["report_count"], 2)
            self.assertIn("2", reply2)

            with patch("backend.core.chatbot.understand", return_value=c3_u):
                reply3, _, meta3 = handle_message("Water gushing from pipe near Market")
            t3 = meta3["ticket_id"]
            self.assertIsNotNone(meta3["cluster"])
            self.assertEqual(meta3["cluster"]["report_count"], 3)
            self.assertIn("3", reply3)

            # Check cluster in DB
            clusters = grv_mod.list_clusters()
            self.assertEqual(len(clusters), 1)
            self.assertEqual(clusters[0]["report_count"], 3)

if __name__ == "__main__":
    unittest.main()
