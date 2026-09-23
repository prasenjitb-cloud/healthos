"""
task_definitions.py

Defines all supported HealthOS tasks and their
data dependencies.

IMPORTANT:
This module does not contain any LLM logic.

It only defines:
- Available tasks
- Required data for each task
- Dependency order
"""

from enum import Enum


class Task(str, Enum):

    DIRECT_BOOKING = "direct_booking"

    DEPARTMENT_BOOKING = "department_booking"

    SYMPTOM_BASED_BOOKING = "symptom_based_booking"

    EMERGENCY = "emergency"


TASK_DEPENDENCIES = {

    Task.DIRECT_BOOKING.value: [
        "doctor_name",
        "date",
        "time_slot",
    ],

    Task.DEPARTMENT_BOOKING.value: [
        "department",
        "doctor_name",
        "date",
        "time_slot",
    ],

    Task.SYMPTOM_BASED_BOOKING.value: [
        "symptoms",
        "department",
        "doctor_name",
        "date",
        "time_slot",
    ],

    Task.EMERGENCY.value: [],
}


DEPENDENCY_SOURCE = {

    "symptoms": "user",

    "department": "user_or_system",

    "doctor_name": "user",

    "date": "user",

    "time_slot": "user",
}


DERIVED_DEPENDENCIES = {

    Task.SYMPTOM_BASED_BOOKING.value: {

        "department": {
            "depends_on": ["symptoms"],
            "generated_by": "department_classifier",
        }

    }

}


TASK_DESCRIPTIONS = {

    Task.DIRECT_BOOKING.value:
        "Direct appointment booking",

    Task.DEPARTMENT_BOOKING.value:
        "Department-based appointment booking",

    Task.SYMPTOM_BASED_BOOKING.value:
        "Symptom-based consultation and appointment booking",

    Task.EMERGENCY.value:
        "Emergency assistance",

}
