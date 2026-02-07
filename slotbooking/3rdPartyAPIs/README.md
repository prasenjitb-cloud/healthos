# Slot Booking – 3rd Party API (Synthetic Data)

This directory contains a lightweight slot booking utility that simulates a 3rd-party doctor appointment API using JSON-based synthetic data.
It is designed for local testing, backend logic validation, and API integration demos without relying on an external service or database.

---

## Project Structure
```bash

3rdPartyAPIs/
├── synthetic_data/
│   ├── doctors.json     
│   └── slots.json        
├── booking_system
│   ├── booking_service.py
└── README.md


```
---

## 🩺 Data Models

### `doctors.json`

```
{
  "doctor_id": 1,
  "name": "Dr. Ananya Rao",
  "specialization": "Cardiology"
}
```

### `slots.json`

```
{
  "slot_id": 101,
  "doctor_id": 1,
  "time": "10:30 AM",
  "available": true,
  "booked_by": null
}
```
---

## ⚙️ Available Functions

### 1. `get_doctors_by_specialization(specialization: str)`

Returns all doctors matching a given specialization (case-insensitive)

```bash
get_doctors_by_specialization("Cardiology")
```

### 2. `specialization_exists(specialization: str) -> bool`

Checks whether at least one doctor exists for the given specialization.

```bash
specialization_exists("Dermatology")
```

### 3. `get_available_slots(doctor_id: int)`

Returns all available slots for a specific doctor.

```bash
get_available_slots(1)
```

### 4. `book_slot(slot_id: int, patient_name: str) -> bool`

Books a slot if it is available.
- Marks slot as unavailable
- Stores patient name
- Persists changes to slots.json

```bash
success = book_slot(101, "Sujith")
```
---

## Usage Example
```bash
if specialization_exists("Cardiology"):
    doctors = get_doctors_by_specialization("Cardiology")
    slots = get_available_slots(doctors[0]["doctor_id"])

    if slots:
        book_slot(slots[0]["slot_id"], "John Doe")
```
---

