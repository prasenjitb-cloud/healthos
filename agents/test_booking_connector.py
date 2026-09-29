"""
test_booking_connector.py

Unit tests for BookingConnector:
- File loading and dynamic path resolution
- Doctor lookup by department (exact, partial, numeric)
- Doctor name validation and normalization
- Doctor choice resolution (index and name)
- Slot lookup, time normalization, and slot choice resolution
- Booking execution with atomic state persistence
- Formatting utilities
"""

import unittest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from booking_connector import BookingConnector


class TestBookingConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connector = BookingConnector()

    def test_initialization_and_indexes(self):
        self.assertGreater(len(self.connector.doctors), 0)
        self.assertGreater(len(self.connector.slots), 0)
        self.assertIn(1, self.connector.doctors_by_id)
        self.assertIn("cardiology", self.connector.doctors_by_spec)

    def test_get_available_departments(self):
        depts = self.connector.get_available_departments()
        self.assertIn("Cardiology", depts)
        self.assertIn("Dermatology", depts)
        self.assertIn("Neurology", depts)

    def test_get_doctors_for_department(self):
        # Exact match
        cardio_docs = self.connector.get_doctors_for_department("Cardiology")
        self.assertTrue(any(d["name"] == "Dr. Kiran Mehta" for d in cardio_docs))

        # Case-insensitive match
        derma_docs = self.connector.get_doctors_for_department("dermatology")
        self.assertTrue(any(d["name"] == "Dr. Pooja Sharma" for d in derma_docs))

        # Partial match
        neuro_docs = self.connector.get_doctors_for_department("neuro")
        self.assertTrue(any(d["name"] == "Dr. Ananya Rao" for d in neuro_docs))

        # Non-existent department
        empty_docs = self.connector.get_doctors_for_department("Aeronautics")
        self.assertEqual(empty_docs, [])

    def test_validate_doctor_name(self):
        # With title
        valid, doc = self.connector.validate_doctor_name("Dr. Kiran Mehta")
        self.assertTrue(valid)
        self.assertEqual(doc["doctor_id"], 2)

        # Without title
        valid, doc = self.connector.validate_doctor_name("Kiran Mehta")
        self.assertTrue(valid)
        self.assertEqual(doc["name"], "Dr. Kiran Mehta")

        # Single token (first name)
        valid, doc = self.connector.validate_doctor_name("Kiran")
        self.assertTrue(valid)

        # Lowercase
        valid, doc = self.connector.validate_doctor_name("dr. pooja sharma")
        self.assertTrue(valid)
        self.assertEqual(doc["doctor_id"], 4)

        # Invalid doctor name
        valid, doc = self.connector.validate_doctor_name("Dr. Fake Nonexistent")
        self.assertFalse(valid)
        self.assertIsNone(doc)

    def test_resolve_doctor_choice(self):
        candidates = self.connector.get_doctors_for_department("Cardiology")
        self.assertGreater(len(candidates), 0)

        # 1-based index
        choice = self.connector.resolve_doctor_choice("1", candidates)
        self.assertIsNotNone(choice)
        self.assertEqual(choice, candidates[0])

        # Out-of-range index
        out_of_range = self.connector.resolve_doctor_choice("99", candidates)
        self.assertIsNone(out_of_range)

        # Zero index (invalid in 1-based)
        zero_choice = self.connector.resolve_doctor_choice("0", candidates)
        self.assertIsNone(zero_choice)

        # Name match
        name_choice = self.connector.resolve_doctor_choice("Kiran", candidates)
        self.assertIsNotNone(name_choice)
        self.assertEqual(name_choice["name"], "Dr. Kiran Mehta")

    def test_slot_time_normalization(self):
        norm = self.connector._normalize_time("9:30 AM")
        self.assertEqual(norm, "09:30")

        norm = self.connector._normalize_time("9 AM")
        self.assertEqual(norm, "09:00")

        norm = self.connector._normalize_time("2:30 PM")
        self.assertEqual(norm, "14:30")

        norm = self.connector._normalize_time("09:30")
        self.assertEqual(norm, "09:30")

        norm = self.connector._normalize_time("invalid")
        self.assertIsNone(norm)

    def test_resolve_slot_choice(self):
        # Doctor 2 has slots 201, 202, 203
        slots = self.connector.get_slots_for_doctor(2, only_available=False)
        self.assertGreater(len(slots), 0)

        # 1-based index
        slot_1 = self.connector.resolve_slot_choice("1", slots)
        self.assertIsNotNone(slot_1)
        self.assertEqual(slot_1, slots[0])

        # 12-hour AM/PM format matching
        slot_time = self.connector.resolve_slot_choice("9:30 AM", slots)
        self.assertIsNotNone(slot_time)
        self.assertEqual(slot_time["time"], "09:30")

        # 24-hour format matching
        slot_24 = self.connector.resolve_slot_choice("09:30", slots)
        self.assertIsNotNone(slot_24)
        self.assertEqual(slot_24["time"], "09:30")

    def test_execute_booking_isolated(self):
        # Use temporary file to avoid modifying the real slots.json permanently
        test_slots = [
            {"slot_id": 9991, "doctor_id": 99, "date": "2026-03-01", "time": "10:00", "available": True},
            {"slot_id": 9992, "doctor_id": 99, "date": "2026-03-01", "time": "11:00", "available": False},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f_slots, \
             tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f_docs:
            json.dump(test_slots, f_slots)
            json.dump([{"doctor_id": 99, "name": "Dr. Test", "specialization": "Testology"}], f_docs)
            f_slots.flush()
            f_docs.flush()
            slots_path = f_slots.name
            docs_path = f_docs.name

        try:
            temp_conn = BookingConnector(doctors_path=docs_path, slots_path=slots_path)
            
            # Booking available slot succeeds
            success = temp_conn.execute_booking(9991, "Alice")
            self.assertTrue(success)

            # Re-booking same slot fails (already taken)
            failed = temp_conn.execute_booking(9991, "Bob")
            self.assertFalse(failed)

            # Booking already unavailable slot fails
            failed_taken = temp_conn.execute_booking(9992, "Charlie")
            self.assertFalse(failed_taken)

            # Nonexistent slot fails
            failed_nonexistent = temp_conn.execute_booking(99999, "Dave")
            self.assertFalse(failed_nonexistent)
        finally:
            os.remove(slots_path)
            os.remove(docs_path)

    def test_formatting_functions(self):
        depts_str = self.connector.format_department_list()
        self.assertIn("1. Cardiology", depts_str)

        docs = self.connector.get_doctors_for_department("Cardiology")
        docs_str = self.connector.format_doctor_list(docs)
        self.assertIn("Dr. Kiran Mehta", docs_str)

        slots = self.connector.get_slots_for_doctor(2)
        slots_str = self.connector.format_slot_list(slots)
        self.assertIn("2026-02-11 at", slots_str)


if __name__ == "__main__":
    unittest.main()
