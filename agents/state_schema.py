"""
state_schema.py

Central conversation state for HealthOS.

The schema stores data.

It DOES NOT decide:
- Which task should be selected
- What field should be collected next
- How departments are classified

Those responsibilities belong to:
- TaskResolver
- DependencyEngine
- DepartmentClassifier
"""

import copy
import typing

try:
    from task_definitions import (
        TASK_DEPENDENCIES,
    )
except ImportError:
    from agents.task_definitions import (
        TASK_DEPENDENCIES,
    )

class SymptomSection(typing.TypedDict, total=False):

    symptoms: typing.List[str]

    severity: typing.Optional[str]


class DepartmentSection(typing.TypedDict, total=False):

    department: typing.Optional[str]

    source: typing.Optional[str]

    confidence: typing.Optional[float]


class BookingSection(typing.TypedDict, total=False):

    doctor_name: typing.Optional[str]

    date: typing.Optional[str]

    time_slot: typing.Optional[str]

    hospital: typing.Optional[str]

    doctor_valid: typing.Optional[bool]

    doctor_candidates: typing.List[dict]


class DynamicSchema(typing.TypedDict, total=False):

    greeter_intent: typing.Optional[str]

    task: typing.Optional[str]

    stage: typing.Optional[str]

    current_dependency: typing.Optional[str]

    symptom_section: SymptomSection

    department_section: DepartmentSection

    booking_section: BookingSection



def create_empty_schema() -> DynamicSchema:

    return {

        "greeter_intent": None,

        "task": None,

        "stage": "initial",

        "current_dependency": None,

        "symptom_section": {

            "symptoms": [],

            "severity": None,

        },

        "department_section": {

            "department": None,

            "source": None,

            "confidence": None,

        },

        "booking_section": {

            "doctor_name": None,

            "date": None,

            "time_slot": None,

            "hospital": None,

            "doctor_valid": None,

            "doctor_candidates": [],

        },

    }



def clean_string(
    value,
) -> typing.Optional[str]:

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    return value



def normalize_symptoms(
    symptoms,
) -> typing.List[str]:

    if not isinstance(symptoms, list):
        return []

    cleaned = []

    seen = set()

    for symptom in symptoms:

        if not isinstance(symptom, str):
            continue

        symptom = symptom.strip()

        if not symptom:
            continue

        normalized = symptom.lower()

        if normalized in seen:
            continue

        seen.add(normalized)

        cleaned.append(symptom)

    return cleaned



def merge_schema_update(
    current: DynamicSchema,
    update: dict,
) -> DynamicSchema:
    """
    Safely merge newly extracted data into the conversation state.

    IMPORTANT RULE:

    None means:
        "No information extracted this turn."

    Therefore:

    None must NEVER overwrite existing information.
    """

    schema = copy.deepcopy(current)

    if not isinstance(update, dict):
        return schema


    if update.get("greeter_intent"):

        schema["greeter_intent"] = (
            update["greeter_intent"]
        )


    if update.get("task"):

        schema["task"] = update["task"]


    if update.get("stage"):

        schema["stage"] = update["stage"]


    if "current_dependency" in update:

        schema["current_dependency"] = (
            update["current_dependency"]
        )


    symptom_update = update.get(
        "symptom_section"
    )

    if isinstance(symptom_update, dict):

        symptoms = symptom_update.get(
            "symptoms"
        )

        if symptoms is not None:

            cleaned_symptoms = (
                normalize_symptoms(symptoms)
            )

            if cleaned_symptoms:

                existing = schema["symptom_section"].get(
                    "symptoms", []
                )

                existing_normalized = {
                    s.lower() for s in existing
                }

                for symptom in cleaned_symptoms:

                    if symptom.lower() not in existing_normalized:

                        existing.append(symptom)

                        existing_normalized.add(
                            symptom.lower()
                        )

                schema["symptom_section"][
                    "symptoms"
                ] = existing

        severity = clean_string(
            symptom_update.get("severity")
        )

        if severity is not None:

            schema["symptom_section"][
                "severity"
            ] = severity


    department_update = update.get(
        "department_section"
    )

    if isinstance(department_update, dict):

        department = clean_string(
            department_update.get(
                "department"
            )
        )

        if department is not None:

            schema["department_section"][
                "department"
            ] = department

        source = clean_string(
            department_update.get(
                "source"
            )
        )

        if source is not None:

            schema["department_section"][
                "source"
            ] = source

        confidence = department_update.get(
            "confidence"
        )

        if isinstance(
            confidence,
            (float, int),
        ):

            schema["department_section"][
                "confidence"
            ] = float(confidence)


    booking_update = update.get(
        "booking_section"
    )

    if isinstance(booking_update, dict):

        string_fields = [

            "doctor_name",

            "date",

            "time_slot",

            "hospital",

        ]

        for field in string_fields:

            value = clean_string(
                booking_update.get(field)
            )

            if value is not None:

                schema["booking_section"][
                    field
                ] = value

        if (
            "doctor_valid"
            in booking_update
        ):

            doctor_valid = booking_update[
                "doctor_valid"
            ]

            if (
                doctor_valid is None
                or isinstance(
                    doctor_valid,
                    bool,
                )
            ):

                schema["booking_section"][
                    "doctor_valid"
                ] = doctor_valid

        candidates = booking_update.get(
            "doctor_candidates"
        )

        if isinstance(candidates, list):

            schema["booking_section"][
                "doctor_candidates"
            ] = candidates

    return schema



def get_dependency_value(
    schema: DynamicSchema,
    dependency: str,
):
    """
    Returns the current value of a dependency.

    Maps dependency names to their location in the schema.
    """

    if dependency == "symptoms":

        return schema.get(
            "symptom_section",
            {},
        ).get(
            "symptoms"
        )

    if dependency == "severity":

        return schema.get(
            "symptom_section",
            {},
        ).get(
            "severity"
        )

    if dependency == "department":

        return schema.get(
            "department_section",
            {},
        ).get(
            "department"
        )

    if dependency == "doctor_name":

        return schema.get(
            "booking_section",
            {},
        ).get(
            "doctor_name"
        )

    if dependency == "date":

        return schema.get(
            "booking_section",
            {},
        ).get(
            "date"
        )

    if dependency == "time_slot":

        return schema.get(
            "booking_section",
            {},
        ).get(
            "time_slot"
        )

    return None



def is_dependency_satisfied(
    schema: DynamicSchema,
    dependency: str,
) -> bool:

    value = get_dependency_value(
        schema,
        dependency,
    )

    # Lists such as symptoms.
    if isinstance(value, list):

        return len(value) > 0

    return value is not None



def is_schema_complete(
    schema: DynamicSchema,
) -> bool:
    """
    Returns True if all dependencies for the current
    task have been satisfied.

    Returns False if:
    - No task is set
    - Any required dependency is missing
    """

    task = schema.get("task")

    if not task:
        return False

    dependencies = TASK_DEPENDENCIES.get(
        task,
        [],
    )

    for dependency in dependencies:

        if not is_dependency_satisfied(
            schema,
            dependency,
        ):

            return False

    return True



def get_missing_fields(
    schema: DynamicSchema,
) -> typing.List[str]:
    """
    Returns a list of all unsatisfied dependencies
    for the current task.

    Returns an empty list if:
    - No task is set
    - All dependencies are satisfied
    """

    task = schema.get("task")

    if not task:
        return []

    dependencies = TASK_DEPENDENCIES.get(
        task,
        [],
    )

    missing = []

    for dependency in dependencies:

        if not is_dependency_satisfied(
            schema,
            dependency,
        ):

            missing.append(dependency)

    return missing



def print_schema(
    schema: DynamicSchema,
):

    print("\n" + "=" * 60)
    print("              DYNAMIC STATE SCHEMA")
    print("=" * 60)

    print(f"\n  Greeter Intent : {schema.get('greeter_intent')}")
    print(f"  Task           : {schema.get('task')}")
    print(f"  Stage          : {schema.get('stage')}")
    print(f"  Current Dep    : {schema.get('current_dependency')}")

    symptom = schema.get("symptom_section", {})
    print("\n  Symptom Section:")
    print(f"    Symptoms     : {symptom.get('symptoms', [])}")
    print(f"    Severity     : {symptom.get('severity')}")

    department = schema.get("department_section", {})
    print("\n  Department Section:")
    print(f"    Department   : {department.get('department')}")
    print(f"    Source       : {department.get('source')}")
    print(f"    Confidence   : {department.get('confidence')}")

    booking = schema.get("booking_section", {})
    print("\n  Booking Section:")
    print(f"    Doctor Name  : {booking.get('doctor_name')}")
    print(f"    Date         : {booking.get('date')}")
    print(f"    Time Slot    : {booking.get('time_slot')}")
    print(f"    Hospital     : {booking.get('hospital')}")
    print(f"    Doctor Valid  : {booking.get('doctor_valid')}")
    print(f"    Candidates   : {booking.get('doctor_candidates', [])}")

    task = schema.get("task")
    if task:
        missing = get_missing_fields(schema)
        complete = is_schema_complete(schema)
        print(f"\n  Complete       : {complete}")
        print(f"  Missing Fields : {missing}")

    print("\n" + "=" * 60)



class DynamicStateSchema:
    """
    Backward-compatibility class wrapping DynamicSchema.
    Allows existing code referencing DynamicStateSchema() to work seamlessly.
    """

    def __init__(self, data: typing.Optional[dict] = None):
        self.data: DynamicSchema = create_empty_schema()
        if data:
            self.data = merge_schema_update(self.data, data)

    def to_dict(self) -> DynamicSchema:
        return self.data

    def add_symptom_data(
        self,
        symptoms: typing.Optional[typing.List[str]] = None,
        department: typing.Optional[str] = None,
        doctor_name: typing.Optional[str] = None,
        hospital: typing.Optional[str] = None,
        location: typing.Optional[str] = None,
        severity: typing.Optional[str] = None,
    ):
        update = {
            "symptom_section": {
                "symptoms": symptoms or [],
                "severity": severity,
            },
            "department_section": {
                "department": department,
            },
            "booking_section": {
                "doctor_name": doctor_name,
                "hospital": hospital,
            },
        }
        self.data = merge_schema_update(self.data, update)

    def activate_sections(
        self,
        symptoms: bool = False,
        department: bool = False,
        booking: bool = False,
    ):
        pass

    def add_emergency_data(
        self,
        emergency_type: typing.Optional[str] = None,
        emergency_status: bool = True,
    ):
        self.data["task"] = "emergency"
        self.data["stage"] = "emergency"

    def print_schema(self):
        print_schema(self.data)