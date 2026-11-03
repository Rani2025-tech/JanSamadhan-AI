import unittest
from ai.classifier import extract_location, extract_urgency, rule_based_extract
from ai.slot_filler import slot_filling_assistant

class TestSlotFillerAndLocation(unittest.TestCase):
    def test_puri_bus_stand_street_light(self):
        """Sentence 1: Street light not working near bus stand Puri since a week"""
        text = "Street light not working near bus stand Puri since a week"
        
        # Test classifier / extraction
        extracted = rule_based_extract(text)
        self.assertEqual(extracted["category"], "Electricity")
        self.assertEqual(extracted["urgency"], "Medium")
        self.assertTrue(extracted["location"]["has_location"])
        self.assertEqual(extracted["location"]["district"], "Puri")
        self.assertEqual(extracted["location"]["area"], "near bus stand")
        self.assertEqual(extracted["location"]["state"], "Odisha")

        # Test slot filler: must directly present confirmation card
        reply, state, slots, ready, card, faq, human = slot_filling_assistant.process_turn(
            text, "collecting", {}, "en"
        )
        self.assertEqual(state, "confirming")
        self.assertIsNotNone(card)
        self.assertEqual(card["district"], "Puri")
        self.assertIn("near bus stand", card["area"])
        self.assertEqual(card["category"], "Electricity")
        self.assertEqual(card["urgency"], "Medium")

    def test_water_is_not_coming_must_ask(self):
        """Sentence 2: Water is not coming (must ask for location)"""
        text = "Water is not coming"
        
        # Location extraction must report no location
        loc = extract_location(text)
        self.assertFalse(loc["has_location"])

        # Slot filler turn 1: must request location and not contain 'in Odisha'
        reply, state, slots, ready, card, faq, human = slot_filling_assistant.process_turn(
            text, "collecting", {}, "en"
        )
        self.assertEqual(state, "awaiting_location")
        self.assertIsNone(card)
        self.assertNotIn("in Odisha", reply)
        self.assertNotIn("of Odisha", reply)
        self.assertIn("district or city", reply)

        # Slot filler turn 2: User provides 'Pune, Kothrud'
        reply2, state2, slots2, ready2, card2, faq2, human2 = slot_filling_assistant.process_turn(
            "Pune, Kothrud", state, slots, "en"
        )
        self.assertEqual(state2, "confirming")
        self.assertIsNotNone(card2)
        self.assertEqual(card2["district"], "Pune")
        self.assertEqual(card2["state"], "Maharashtra")
        self.assertEqual(card2["category"], "Water Supply")
        self.assertEqual(card2["department"], "MJP")

    def test_pune_kothrud_light(self):
        """Sentence 3: Ward 12 Kothrud Pune re light nahi hai"""
        text = "Ward 12 Kothrud Pune re light nahi hai"
        
        extracted = rule_based_extract(text)
        self.assertEqual(extracted["category"], "Electricity")
        self.assertTrue(extracted["location"]["has_location"])
        self.assertEqual(extracted["location"]["district"], "Pune")
        self.assertEqual(extracted["location"]["state"], "Maharashtra")
        self.assertEqual(extracted["location"]["area"], "Ward 12 Kothrud")
        self.assertEqual(extracted["department"], "MSEDCL")

        reply, state, slots, ready, card, faq, human = slot_filling_assistant.process_turn(
            text, "collecting", {}, "en"
        )
        self.assertEqual(state, "confirming")
        self.assertIsNotNone(card)
        self.assertEqual(card["district"], "Pune")
        self.assertEqual(card["state"], "Maharashtra")
        self.assertEqual(card["department"], "MSEDCL")

    def test_lucknow_gomti_nagar_hindi(self):
        """Hindi native script: बिजली नहीं है, लखनऊ, गोमती नगर"""
        text = "बिजली नहीं है, लखनऊ, गोमती नगर"
        reply, state, slots, ready, card, faq, human = slot_filling_assistant.process_turn(
            text, "collecting", {}, "hi"
        )
        self.assertEqual(state, "confirming")
        self.assertIsNotNone(card)
        self.assertEqual(card["district"], "Lucknow")
        self.assertEqual(card["state"], "Uttar Pradesh")
        self.assertTrue("Gomti Nagar" in card["area"] or "गोमती नगर" in card["area"])
        self.assertEqual(card["department"], "UPPCL")
        self.assertIn("विभाग", reply)

    def test_odisha_odia_backward_compatibility(self):
        """Odisha Odia grievance remains fully functional"""
        text = "ପୁରୀ ବଡ଼ଦାଣ୍ଡରେ ପାଇପ ଫାଟି ପାଣି ବୋହୁଛି"
        extracted = rule_based_extract(text)
        self.assertEqual(extracted["language"], "Odia")
        self.assertEqual(extracted["category"], "Water Supply")
        self.assertEqual(extracted["location"]["district"], "Puri")
        self.assertEqual(extracted["location"]["state"], "Odisha")

if __name__ == "__main__":
    unittest.main()

