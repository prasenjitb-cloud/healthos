import os
import json

# Dynamically resolve paths relative to this file to work regardless of CWD
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RESOLVED_SLOTS = os.path.join(_BASE_DIR, "synthetic_data", "slots.json")
_RESOLVED_DOCTORS = os.path.join(_BASE_DIR, "synthetic_data", "doctors.json")

SLOTS_FILE = _RESOLVED_SLOTS if os.path.exists(_RESOLVED_SLOTS) else "slotbooking/ThirdPartyAPIs/synthetic_data/slots.json"
DOCTORS_FILE = _RESOLVED_DOCTORS if os.path.exists(_RESOLVED_DOCTORS) else "slotbooking/ThirdPartyAPIs/synthetic_data/doctors.json"

def get_doctors_by_specialization(specialization: str):
    with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    result = []

    for d in doctors:
        spec = d.get("specialization")
        if spec and spec.lower() == specialization.lower():
            result.append(d)

    return result

def specialization_exists(specialization: str) -> bool:
    with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    for d in doctors:
        spec = d.get("specialization")
        if spec and spec.lower() == specialization.lower():
            return True

    return False

def get_available_slots(doctor_id: int):
    with open(SLOTS_FILE, "r", encoding="utf-8") as f:
        slots = json.load(f)

    return [
        s for s in slots
        if s["doctor_id"] == doctor_id and s["available"]
    ]


def book_slot(slot_id: int, patient_name: str) -> bool:
    """
    Books a slot if available.
    Returns True if booking is successful, else False.
    """
    with open(SLOTS_FILE, "r", encoding="utf-8") as f:
        slots = json.load(f)

    for slot in slots:
        if slot["slot_id"] == slot_id and slot["available"]:
            slot["available"] = False
            slot["booked_by"] = patient_name

            with open(SLOTS_FILE, "w", encoding="utf-8") as f:
                json.dump(slots, f, indent=2)

            return True

    return False


def get_doctor_by_name(name: str):
    """Find a doctor by name (case-insensitive, partial match supported)."""
    with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    if not name or not isinstance(name, str):
        return None

    clean_target = name.lower().replace("dr.", "").replace("dr", "").replace("doctor", "").strip()
    target_tokens = set(clean_target.split())

    for d in doctors:
        doc_name = d.get("name", "").lower()
        clean_doc = doc_name.replace("dr.", "").replace("dr", "").replace("doctor", "").strip()
        doc_tokens = set(clean_doc.split())

        # Exact match or token subset match
        if clean_target == clean_doc or (target_tokens and target_tokens.issubset(doc_tokens)):
            return d

    # Also check if any single non-trivial token matches
    for d in doctors:
        doc_name = d.get("name", "").lower()
        clean_doc = doc_name.replace("dr.", "").replace("dr", "").replace("doctor", "").strip()
        doc_tokens = set(clean_doc.split())
        for token in target_tokens:
            if len(token) >= 3 and token in doc_tokens:
                return d

    return None
