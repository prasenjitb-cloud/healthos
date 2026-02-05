import json

SLOTS_FILE = "3rdPartyAPIs/synthetic_data/slots.json"
DOCTORS_FILE = "3rdPartyAPIs/synthetic_data/doctors.json"

def get_doctors_by_specialization(specialization: str):
    with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    return [
        d for d in doctors
        if d["specialization"].lower() == specialization.lower()
    ]

def specialization_exists(specialization: str) -> bool:
    with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    return any(
        d["specialization"].lower() == specialization.lower()
        for d in doctors
    )

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
