"""
task_resolver.py

Determines which HealthOS task/workflow should be used.

IMPORTANT:

This component does NOT modify the Greeter Agent.

The Greeter Agent provides the initial intent.

TaskResolver uses:
- Greeter intent
- Extracted information

to select the appropriate workflow.
"""

try:
    from task_definitions import Task
except ImportError:
    from agents.task_definitions import Task


class TaskResolver:

    def resolve(
        self,
        schema,
    ):
        """
        Resolve the workflow task.

        Priority:

        1. Emergency
        2. Direct Booking   (doctor_name present)
        3. Department Booking (department present)
        4. Symptom Based Booking (symptoms present)
        5. Fallback from greeter intent
        """

        greeter_intent = schema.get(
            "greeter_intent"
        )

        # ====================================================
        # EMERGENCY
        # ====================================================

        if greeter_intent == "emergency":

            return Task.EMERGENCY.value

        booking = schema.get(
            "booking_section",
            {}
        )

        department_section = schema.get(
            "department_section",
            {}
        )

        symptom_section = schema.get(
            "symptom_section",
            {}
        )

        doctor_name = booking.get(
            "doctor_name"
        )

        department = department_section.get(
            "department"
        )

        symptoms = symptom_section.get(
            "symptoms",
            []
        )

        # ====================================================
        # TASK 1
        #
        # DIRECT BOOKING
        #
        # User knows which doctor they want.
        # ====================================================

        if doctor_name:

            return Task.DIRECT_BOOKING.value

        # ====================================================
        # TASK 2
        #
        # DEPARTMENT BOOKING
        #
        # User knows the department but not the doctor.
        # ====================================================

        if department:

            return Task.DEPARTMENT_BOOKING.value

        # ====================================================
        # TASK 3
        #
        # SYMPTOM BASED BOOKING
        #
        # User describes symptoms. System classifies
        # department and suggests doctors.
        # ====================================================

        if symptoms:

            return Task.SYMPTOM_BASED_BOOKING.value

        # ====================================================
        # FALLBACK BASED ON GREETER
        # ====================================================

        if greeter_intent in ("triage", "symptom_guidance"):

            return Task.SYMPTOM_BASED_BOOKING.value

        if greeter_intent == "booking":

            # Booking intent but no doctor/department yet.
            #
            # We do NOT assume symptoms are required.
            #
            # The dependency engine will ask what the user
            # wants (starting with doctor_name).

            return Task.DIRECT_BOOKING.value

        # ====================================================
        # DEFAULT
        # ====================================================

        return None


    def update_schema_task(
        self,
        schema,
    ):
        """
        Resolve task and store it in schema.
        """

        task = self.resolve(schema)

        if task:

            schema["task"] = task

        return schema
