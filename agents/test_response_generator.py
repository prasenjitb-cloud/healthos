"""
test_response_generator.py

Unit tests for ResponseGeneratorAgent covering:
- Cases A through H
- Input validation and irrelevance handling (handle_user_input)
- SLM integration and fact preservation checks
- End-to-end multi-turn conversation flow
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from response_generator_agent import ResponseGeneratorAgent
from booking_connector import BookingConnector
from state_schema import create_empty_schema, merge_schema_update


class TestResponseGeneratorAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connector = BookingConnector()
        cls.agent = ResponseGeneratorAgent(cls.connector)

    def setUp(self):
        # Ensure doctor 2 slots are available in-memory for deterministic testing
        for s in self.connector.slots:
            if s.get("doctor_id") == 2:
                s["available"] = True
        self.connector._build_indexes()

    def test_case_a_missing_symptoms(self):
        schema = create_empty_schema()
        schema["task"] = "symptom_based_booking"
        action_plan = {"action": "ASK_USER", "dependency": "symptoms"}
        
        response = self.agent.generate(schema, action_plan)
        self.assertIn("symptoms are you experiencing", response.lower())

    def test_case_b_missing_department(self):
        schema = create_empty_schema()
        schema["task"] = "department_booking"
        action_plan = {"action": "ASK_USER", "dependency": "department"}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("Available departments:", response)
        self.assertIn("Cardiology", response)
        self.assertIn("Dermatology", response)

    def test_case_c_missing_doctor_with_department(self):
        schema = create_empty_schema()
        schema["task"] = "department_booking"
        schema["department_section"]["department"] = "Cardiology"
        action_plan = {"action": "ASK_USER", "dependency": "doctor_name"}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("I found the following doctors in Cardiology:", response)
        self.assertIn("Dr. Kiran Mehta", response)

    def test_case_d_missing_slot_with_selected_doctor(self):
        schema = create_empty_schema()
        schema["task"] = "direct_booking"
        schema["booking_section"]["doctor_name"] = "Dr. Kiran Mehta"
        action_plan = {"action": "ASK_USER", "dependency": "time_slot"}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("Dr. Kiran Mehta has the following available appointment slots:", response)
        self.assertIn("at 09:30", response)

    def test_case_e_invalid_doctor_name(self):
        schema = create_empty_schema()
        schema["task"] = "direct_booking"
        schema["booking_section"]["doctor_name"] = "Dr. UnknownPerson"
        schema["booking_section"]["doctor_valid"] = False
        action_plan = {"action": "ASK_USER", "dependency": "doctor_name"}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("I couldn't find 'Dr. UnknownPerson' in our available doctor list.", response)
        self.assertIn("Dr. Kiran Mehta", response)

    def test_case_f_complete_booking_confirmation(self):
        schema = create_empty_schema()
        schema["task"] = "department_booking"
        schema["department_section"]["department"] = "Cardiology"
        schema["booking_section"] = {
            "doctor_name": "Dr. Kiran Mehta",
            "date": "2026-02-11",
            "time_slot": "09:30",
            "hospital": "Apollo Clinic",
            "selected_doctor": {
                "doctor_id": 2,
                "name": "Dr. Kiran Mehta",
                "specialization": "Cardiology",
                "hospital": "Apollo Clinic",
                "location": "Hyderabad",
            },
            "selected_slot": {
                "slot_id": 201,
                "date": "2026-02-11",
                "time": "09:30",
            },
            "booking_slot_id": 201,
        }
        action_plan = {"action": "COMPLETE", "dependency": None}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("✅ Your appointment has been confirmed!", response)
        self.assertIn("Dr. Kiran Mehta", response)
        self.assertIn("Apollo Clinic, Hyderabad", response)
        self.assertIn("2026-02-11", response)
        self.assertIn("09:30", response)
        self.assertIn("201", response)

    def test_case_g_emergency(self):
        schema = create_empty_schema()
        schema["task"] = "emergency"
        action_plan = {"action": "EMERGENCY", "dependency": None}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("🚨 This sounds like a medical emergency.", response)
        self.assertIn("108 / 112", response)

    def test_case_h_run_system(self):
        schema = create_empty_schema()
        schema["task"] = "symptom_based_booking"
        action_plan = {"action": "RUN_SYSTEM", "dependency": "department"}

        response = self.agent.generate(schema, action_plan)
        self.assertIn("Analyzing your symptoms to find the right specialist", response)

    def test_handle_user_input_doctor_resolution(self):
        schema = create_empty_schema()
        schema["current_dependency"] = "doctor_name"
        schema["booking_section"]["doctor_candidates"] = self.connector.get_doctors_for_department("Cardiology")

        # 1. Valid index "1"
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "1")
        self.assertTrue(is_valid)
        self.assertIsNone(clarif)
        self.assertEqual(patch["booking_section"]["doctor_name"], "Dr. Kiran Mehta")

        # 2. Valid name token "kiran"
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "kiran")
        self.assertTrue(is_valid)
        self.assertEqual(patch["booking_section"]["doctor_name"], "Dr. Kiran Mehta")

        # 3. Invalid name / out of bounds
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "xyz random doctor")
        self.assertFalse(is_valid)
        self.assertIn("couldn't find 'xyz random doctor'", clarif)

    def test_handle_user_input_slot_resolution(self):
        schema = create_empty_schema()
        schema["current_dependency"] = "time_slot"
        schema["booking_section"]["slot_candidates"] = self.connector.get_slots_for_doctor(2)

        # 1. Valid slot index "1"
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "1")
        self.assertTrue(is_valid)
        self.assertIsNone(clarif)
        self.assertEqual(patch["booking_section"]["time_slot"], "09:30")

        # 2. Valid time "9:30 AM"
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "9:30 AM")
        self.assertTrue(is_valid)
        self.assertEqual(patch["booking_section"]["time_slot"], "09:30")

        # 3. Invalid slot
        is_valid, clarif, patch = self.agent.handle_user_input(schema, "whenever")
        self.assertFalse(is_valid)
        self.assertIn("couldn't find a slot matching 'whenever'", clarif)

    def test_slm_fact_preservation(self):
        base = "Appointment confirmed with Dr. Kiran Mehta on 2026-02-11 at 09:30 (Slot ID: 201)."
        
        # SLM output preserving all facts
        good_enhanced = "Great! Your appointment with Dr. Kiran Mehta is set for 2026-02-11 at 09:30 with Slot ID 201."
        self.assertTrue(self.agent._verify_facts_preserved(base, good_enhanced))

        # SLM output dropping slot ID
        bad_enhanced = "Great! Your appointment with Dr. Kiran Mehta is set for 2026-02-11 at 09:30."
        self.assertFalse(self.agent._verify_facts_preserved(base, bad_enhanced))

        # SLM output dropping time
        bad_time = "Great! Your appointment with Dr. Kiran Mehta is set for 2026-02-11 (Slot ID: 201)."
        self.assertFalse(self.agent._verify_facts_preserved(base, bad_time))


if __name__ == "__main__":
    unittest.main()
