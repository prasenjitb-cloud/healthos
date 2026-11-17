"""
booking_connector.py

Integration layer between HealthOS agents / DynamicStateSchema and the
Synthetic Data & Booking System (doctors.json, slots.json, booking_service).

Provides:
- In-memory indexed data lookups for doctors and appointment slots.
- Name normalization and fuzzy/token-based doctor resolution.
- Flexible slot resolution (1-based index, 12h/24h time matching).
- Real booking execution with atomic updates.
"""

import os
import re
import json
from typing import List, Dict, Optional, Tuple, Any


class BookingConnector:
    """
    In-memory indexed interface to synthetic doctors and slots.
    """

    def __init__(
        self,
        doctors_path: Optional[str] = None,
        slots_path: Optional[str] = None,
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_data_dir = os.path.join(base_dir, "slotbooking", "ThirdPartyAPIs", "synthetic_data")

        self.doctors_file = doctors_path or os.path.join(default_data_dir, "doctors.json")
        self.slots_file = slots_path or os.path.join(default_data_dir, "slots.json")

        self.doctors: List[Dict[str, Any]] = []
        self.slots: List[Dict[str, Any]] = []

        self.doctors_by_id: Dict[int, Dict[str, Any]] = {}
        self.doctors_by_spec: Dict[str, List[Dict[str, Any]]] = {}
        self.slots_by_doctor_id: Dict[int, List[Dict[str, Any]]] = {}
        self.slots_by_id: Dict[int, Dict[str, Any]] = {}

        self.reload_data()

    def reload_data(self):
        """Loads and indexes doctors and slots from JSON files."""
        if not os.path.exists(self.doctors_file):
            raise FileNotFoundError(f"Doctors file not found: {self.doctors_file}")
        if not os.path.exists(self.slots_file):
            raise FileNotFoundError(f"Slots file not found: {self.slots_file}")

        try:
            with open(self.doctors_file, "r", encoding="utf-8") as f:
                self.doctors = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed doctors.json: {e}")

        try:
            with open(self.slots_file, "r", encoding="utf-8") as f:
                self.slots = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed slots.json: {e}")

        self._build_indexes()

    def _build_indexes(self):
        """Builds in-memory O(1) lookup tables."""
        self.doctors_by_id = {d["doctor_id"]: d for d in self.doctors if "doctor_id" in d}
        
        self.doctors_by_spec = {}
        for d in self.doctors:
            spec = d.get("specialization")
            if spec:
                spec_key = spec.strip().lower()
                self.doctors_by_spec.setdefault(spec_key, []).append(d)

        self.slots_by_doctor_id = {}
        self.slots_by_id = {}
        for s in self.slots:
            s_id = s.get("slot_id")
            if s_id is not None:
                self.slots_by_id[s_id] = s
            d_id = s.get("doctor_id")
            if d_id is not None:
                self.slots_by_doctor_id.setdefault(d_id, []).append(s)

    # ------------------------------------------------------------------
    # Doctor Methods
    # ------------------------------------------------------------------

    def get_all_doctors(self) -> List[Dict[str, Any]]:
        return list(self.doctors)

    def get_available_departments(self) -> List[str]:
        """Returns sorted list of unique department/specialization names."""
        departments = sorted({d.get("specialization") for d in self.doctors if d.get("specialization")})
        return departments

    DEPARTMENT_SYNONYMS = {
        "cardio": "Cardiology",
        "cardiologist": "Cardiology",
        "cardiology": "Cardiology",
        "heart": "Cardiology",
        "derma": "Dermatology",
        "dermatologist": "Dermatology",
        "dermatology": "Dermatology",
        "skin": "Dermatology",
        "neuro": "Neurology",
        "neurologist": "Neurology",
        "neurology": "Neurology",
        "brain": "Neurology",
        "ortho": "Orthopedics",
        "orthopedic": "Orthopedics",
        "orthopedics": "Orthopedics",
        "bone": "Orthopedics",
        "general": "General Medicine",
        "physician": "General Medicine",
        "medicine": "General Medicine",
        "gynec": "Gynecology",
        "gynecology": "Gynecology",
        "gynecologist": "Gynecology",
        "pediatric": "Pediatrics",
        "pediatrics": "Pediatrics",
        "pediatrician": "Pediatrics",
        "child": "Pediatrics",
    }

    def match_department(self, text: str) -> Optional[str]:
        """Resolves natural language text or synonym to a standard department."""
        if not text:
            return None
        t = text.strip().lower()
        
        # Check standard departments exact/substring
        for dept in self.get_available_departments():
            if dept.lower() == t or dept.lower() in t:
                return dept

        # Check synonyms
        words = re.findall(r"\b\w+\b", t)
        for w in words:
            if w in self.DEPARTMENT_SYNONYMS:
                return self.DEPARTMENT_SYNONYMS[w]

        for syn, target in self.DEPARTMENT_SYNONYMS.items():
            if syn in t:
                return target

        return None

    def format_department_list(self) -> str:
        """Returns 1-based numbered list of available departments."""
        depts = self.get_available_departments()
        lines = [f"  {idx}. {dept}" for idx, dept in enumerate(depts, 1)]
        return "\n".join(lines)

    def get_doctors_for_department(self, department: str) -> List[Dict[str, Any]]:
        """
        Finds doctors for a department.
        Supports exact match and partial/prefix match (e.g. 'cardio' -> Cardiology).
        """
        if not department or not isinstance(department, str):
            return []

        dep_clean = department.strip().lower()

        # 1. Exact match
        if dep_clean in self.doctors_by_spec:
            return list(self.doctors_by_spec[dep_clean])

        # 2. Check if user typed a number matching get_available_departments()
        if dep_clean.isdigit():
            idx = int(dep_clean)
            depts = self.get_available_departments()
            if 1 <= idx <= len(depts):
                chosen_dept = depts[idx - 1].lower()
                return list(self.doctors_by_spec.get(chosen_dept, []))

        # 3. Partial / substring match
        matched = []
        for spec_key, docs in self.doctors_by_spec.items():
            if dep_clean in spec_key or spec_key in dep_clean:
                matched.extend(docs)

        return matched

    def _normalize_name(self, name: str) -> str:
        """Strips titles and punctuation from doctor names for clean comparison."""
        if not name:
            return ""
        n = name.lower()
        n = re.sub(r"\b(dr\.|dr|doctor)\b", "", n)
        n = re.sub(r"[^\w\s]", "", n)
        return " ".join(n.split())

    def validate_doctor_name(self, name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks whether a doctor name exists in the database.
        Returns (True, doctor_dict) if valid, else (False, None).
        """
        if not name or not isinstance(name, str):
            return False, None

        clean_target = self._normalize_name(name)
        if not clean_target:
            return False, None

        target_tokens = set(clean_target.split())

        # Exact normalized match
        for d in self.doctors:
            doc_norm = self._normalize_name(d.get("name", ""))
            if clean_target == doc_norm:
                return True, d

        # Token subset match
        for d in self.doctors:
            doc_norm = self._normalize_name(d.get("name", ""))
            doc_tokens = set(doc_norm.split())
            if target_tokens and target_tokens.issubset(doc_tokens):
                return True, d

        # Single distinct token match (length >= 3)
        for d in self.doctors:
            doc_norm = self._normalize_name(d.get("name", ""))
            doc_tokens = set(doc_norm.split())
            for t in target_tokens:
                if len(t) >= 3 and t in doc_tokens:
                    return True, d

        return False, None

    def resolve_doctor_choice(
        self,
        user_input: str,
        candidates: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves user input to one of the candidate doctors.
        Supports 1-based index or name matching.
        """
        if not user_input or not candidates:
            return None

        clean_input = user_input.strip()

        # 1. Number index
        if clean_input.isdigit():
            idx = int(clean_input)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1]
            return None

        # 2. Match against candidate names
        input_norm = self._normalize_name(clean_input)
        if not input_norm:
            return None
        input_tokens = set(input_norm.split())

        for doc in candidates:
            doc_norm = self._normalize_name(doc.get("name", ""))
            if input_norm == doc_norm:
                return doc

        for doc in candidates:
            doc_norm = self._normalize_name(doc.get("name", ""))
            doc_tokens = set(doc_norm.split())
            if input_tokens and input_tokens.issubset(doc_tokens):
                return doc

        for doc in candidates:
            doc_norm = self._normalize_name(doc.get("name", ""))
            doc_tokens = set(doc_norm.split())
            for t in input_tokens:
                if len(t) >= 3 and t in doc_tokens:
                    return doc

        return None

    def format_doctor_list(self, candidates: List[Dict[str, Any]]) -> str:
        """Formats candidates into a numbered list."""
        if not candidates:
            return "  (No doctors found)"
        lines = []
        for idx, doc in enumerate(candidates, 1):
            name = doc.get("name", "Unknown")
            hosp = doc.get("hospital", "")
            loc = doc.get("location", "")
            details = f" — {hosp}, {loc}" if (hosp or loc) else ""
            lines.append(f"  {idx}. {name}{details}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Slot Methods
    # ------------------------------------------------------------------

    def get_slots_for_doctor(self, doctor_id: int, only_available: bool = True) -> List[Dict[str, Any]]:
        """Returns slots for a doctor, optionally filtering only available."""
        slots = self.slots_by_doctor_id.get(doctor_id, [])
        if only_available:
            return [s for s in slots if s.get("available") is True]
        return list(slots)

    def _normalize_time(self, time_str: str) -> Optional[str]:
        """
        Normalizes various user time representations into 'HH:MM' (24-hour format).
        Examples:
          '09:30'   -> '09:30'
          '9:30'    -> '09:30'
          '9:30 AM' -> '09:30'
          '9 AM'    -> '09:00'
          '2:30 PM' -> '14:30'
          '2 PM'    -> '14:00'
        """
        if not time_str or not isinstance(time_str, str):
            return None

        t = time_str.strip().lower()

        # Handle 12-hour AM/PM with optional minutes: e.g. "9 am", "9:30 am", "09:30 am"
        match_12h = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", t)
        if match_12h:
            hour = int(match_12h.group(1))
            minute = int(match_12h.group(2) or 0)
            meridiem = match_12h.group(3)
            if hour == 12:
                hour = 0 if meridiem == "am" else 12
            elif meridiem == "pm":
                hour += 12
            return f"{hour:02d}:{minute:02d}"

        # Handle 24-hour HH:MM or H:MM: e.g. "09:30", "9:30", "14:00"
        match_24h = re.match(r"^(\d{1,2}):(\d{2})$", t)
        if match_24h:
            hour = int(match_24h.group(1))
            minute = int(match_24h.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"

        return None

    def resolve_slot_choice(
        self,
        user_input: str,
        slots: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves user input to one of the provided slots.
        Supports 1-based index or time matching.
        """
        if not user_input or not slots:
            return None

        clean_input = user_input.strip()

        # 1. Number index
        if clean_input.isdigit():
            idx = int(clean_input)
            if 1 <= idx <= len(slots):
                return slots[idx - 1]
            return None

        # 2. Time matching
        norm_time = self._normalize_time(clean_input)
        if norm_time:
            for s in slots:
                if s.get("time") == norm_time:
                    return s

        # 3. Substring matching in slot representation
        for s in slots:
            slot_repr = f"{s.get('date')} {s.get('time')}".lower()
            if clean_input.lower() in slot_repr:
                return s

        return None

    def format_slot_list(self, slots: List[Dict[str, Any]]) -> str:
        """Formats slots into a numbered list."""
        if not slots:
            return "  (No available slots)"
        lines = []
        for idx, s in enumerate(slots, 1):
            date = s.get("date", "Unknown date")
            time = s.get("time", "Unknown time")
            lines.append(f"  {idx}. {date} at {time}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Booking Execution
    # ------------------------------------------------------------------

    def execute_booking(self, slot_id: int, patient_name: str = "Patient") -> bool:
        """
        Executes real booking on the specified slot.
        Updates both in-memory cache and slots.json.
        Returns True on success, False if already taken or not found.
        """
        # Re-read file to avoid race conditions with external updates
        if not os.path.exists(self.slots_file):
            return False

        try:
            with open(self.slots_file, "r", encoding="utf-8") as f:
                disk_slots = json.load(f)
        except Exception:
            disk_slots = self.slots

        booked = False
        for s in disk_slots:
            if s.get("slot_id") == slot_id and s.get("available") is True:
                s["available"] = False
                s["booked_by"] = patient_name or "Patient"
                booked = True
                break

        if booked:
            # Write back
            with open(self.slots_file, "w", encoding="utf-8") as f:
                json.dump(disk_slots, f, indent=2)

            self.slots = disk_slots
            self._build_indexes()
            return True

        return False
