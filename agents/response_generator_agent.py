"""
response_generator_agent.py

Response Generator Agent for HealthOS.

Generates human-like, context-aware responses when schema sections are missing,
presents structured options (departments, doctors, slots) from real synthetic data,
detects and handles invalid or irrelevant inputs, and confirms bookings upon completion.

Design principle: Deterministic generation runs first. SLM is optionally used
for tone enhancement while strictly verifying fact preservation.
"""

import re
from typing import Optional, Dict, Any, List, Tuple

try:
    from booking_connector import BookingConnector
    from state_schema import (
        DynamicSchema,
        is_schema_complete,
        get_missing_fields,
    )
except ImportError:
    from agents.booking_connector import BookingConnector
    from agents.state_schema import (
        DynamicSchema,
        is_schema_complete,
        get_missing_fields,
    )


class ResponseGeneratorAgent:
    """
    Generates human-like, professional conversational responses
    for HealthOS schema collection and booking workflows.
    """

    QUESTIONS = {
        "symptoms": (
            "What symptoms are you experiencing?\n"
            "Please describe your discomfort in a few words."
        ),
        "department": (
            "Which medical department or specialist would you like to consult?"
        ),
        "doctor_name": (
            "Which doctor would you like to book an appointment with?"
        ),
        "date": (
            "What date would you prefer for the appointment?"
        ),
        "time_slot": (
            "What time would you prefer for the appointment?"
        ),
        "hospital": (
            "Which hospital would you prefer?"
        ),
    }

    def __init__(
        self,
        booking_connector: Optional[BookingConnector] = None,
        slm=None,
        model_config=None,
        run_llm_fn=None,
    ):
        self.booking_connector = booking_connector or BookingConnector()
        self.slm = slm
        self.model_config = model_config
        self.run_llm_fn = run_llm_fn

    # ============================================================
    # PUBLIC ENTRY POINTS
    # ============================================================

    def generate(
        self,
        schema: DynamicSchema,
        action_plan: Optional[Dict[str, Any]] = None,
        last_user_input: Optional[str] = None,
    ) -> Optional[str]:
        """
        Main response generation entry point.
        Takes schema and action_plan (from DependencyEngine), returns conversational response.
        """
        # 1. Generate deterministic base response
        base_response = self._build_deterministic_response(schema, action_plan, last_user_input)

        if not base_response:
            return None

        # 2. Optionally rephrase using SLM
        if self.slm and self.run_llm_fn:
            try:
                enhanced = self._rephrase_with_slm(base_response)
                if self._verify_facts_preserved(base_response, enhanced):
                    return enhanced
            except Exception:
                pass  # Fall back safely on deterministic base

        return base_response

    def generate_response(self, schema: DynamicSchema) -> Optional[str]:
        """
        Backward compatibility entry point for callers passing only schema.
        """
        action_plan = self._infer_action_plan(schema)
        return self.generate(schema, action_plan)

    # ============================================================
    # DETERMINISTIC RESPONSE BUILDER
    # ============================================================

    def _build_deterministic_response(
        self,
        schema: DynamicSchema,
        action_plan: Optional[Dict[str, Any]] = None,
        last_user_input: Optional[str] = None,
    ) -> Optional[str]:
        if action_plan is None:
            action_plan = self._infer_action_plan(schema)

        action = action_plan.get("action")
        dependency = action_plan.get("dependency")

        # Case G: Emergency
        if action == "EMERGENCY" or schema.get("task") == "emergency":
            return (
                "🚨 This sounds like a medical emergency.\n"
                "Please call emergency services immediately (108 / 112) "
                "or go to the nearest emergency room right away.\n"
                "Do not wait for an appointment — please seek immediate help."
            )

        # Case H: Run System (e.g. classifier working)
        if action == "RUN_SYSTEM":
            return (
                "Analyzing your symptoms to find the right specialist for you...\n"
                "Please wait a moment."
            )

        # Case F: Complete
        if action == "COMPLETE" or is_schema_complete(schema):
            return self._build_confirmation_response(schema)

        # Case A - E: ASK_USER
        if action == "ASK_USER":
            return self._build_ask_user_response(schema, dependency, last_user_input)

        if action == "WAIT":
            return "Please provide more details about your symptoms or medical concern."

        return "Could you please provide the required information to continue?"

    def _build_ask_user_response(
        self,
        schema: DynamicSchema,
        dependency: Optional[str],
        last_user_input: Optional[str] = None,
    ) -> str:
        booking = schema.get("booking_section", {})
        dept_section = schema.get("department_section", {})
        department = dept_section.get("department")

        # ----------------------------------------------------
        # Case A: Symptoms
        # ----------------------------------------------------
        if dependency == "symptoms":
            return self.QUESTIONS["symptoms"]

        # ----------------------------------------------------
        # Case B: Department
        # ----------------------------------------------------
        if dependency == "department":
            dept_list = self.booking_connector.format_department_list()
            return (
                "Which medical department or specialist would you like to consult?\n\n"
                "Available departments:\n"
                f"{dept_list}\n\n"
                "(Type the department name or its number)"
            )

        # ----------------------------------------------------
        # Case C & E: Doctor Name
        # ----------------------------------------------------
        if dependency == "doctor_name":
            # Check if doctor name was already supplied but invalid
            if booking.get("doctor_name") and booking.get("doctor_valid") is False:
                doc_name = booking.get("doctor_name")
                candidates = booking.get("doctor_candidates") or self.booking_connector.get_all_doctors()
                formatted = self.booking_connector.format_doctor_list(candidates)
                return (
                    f"I couldn't find '{doc_name}' in our available doctor list.\n"
                    "Please select from our available doctors:\n\n"
                    f"{formatted}\n\n"
                    "(Type the number or the doctor's full name)"
                )

            # If department is known, present doctors from that department
            if department:
                candidates = self.booking_connector.get_doctors_for_department(department)
                if candidates:
                    booking["doctor_candidates"] = candidates
                    formatted = self.booking_connector.format_doctor_list(candidates)
                    return (
                        f"I found the following doctors in {department}:\n\n"
                        f"{formatted}\n\n"
                        "Which doctor would you like to book an appointment with?\n"
                        "(Type the number or the doctor's name)"
                    )
                else:
                    return (
                        f"I'm sorry, there are currently no available doctors in {department}.\n"
                        "Would you like to choose a different department?"
                    )

            # Direct booking without department: prompt for doctor
            return self.QUESTIONS["doctor_name"]

        # ----------------------------------------------------
        # Case D: Date / Time Slot (Unified Slot Selection)
        # ----------------------------------------------------
        if dependency in ("date", "time_slot"):
            selected_doc = booking.get("selected_doctor")
            doc_id = None
            doc_name = booking.get("doctor_name") or "the doctor"

            if selected_doc and "doctor_id" in selected_doc:
                doc_id = selected_doc["doctor_id"]
                doc_name = selected_doc.get("name", doc_name)
            elif booking.get("doctor_name"):
                is_valid, doc_rec = self.booking_connector.validate_doctor_name(booking["doctor_name"])
                if is_valid and doc_rec:
                    doc_id = doc_rec["doctor_id"]
                    doc_name = doc_rec.get("name", doc_name)
                    booking["selected_doctor"] = doc_rec

            if doc_id is not None:
                slots = self.booking_connector.get_slots_for_doctor(doc_id, only_available=True)
                booking["slot_candidates"] = slots

                if not slots:
                    return (
                        f"I'm sorry, {doc_name} has no available slots at this time.\n"
                        "Would you like to choose a different doctor?"
                    )

                formatted_slots = self.booking_connector.format_slot_list(slots)
                return (
                    f"{doc_name} has the following available appointment slots:\n\n"
                    f"{formatted_slots}\n\n"
                    "Which slot would you prefer?\n"
                    "(Type the number, e.g. '1', or the time, e.g. '09:30')"
                )

            return self.QUESTIONS.get(dependency, "Could you please provide your preferred date/time?")

        return self.QUESTIONS.get(dependency, "Could you please provide more information?")

    # ============================================================
    # CONFIRMATION RESPONSE (Case F)
    # ============================================================

    def _build_confirmation_response(self, schema: DynamicSchema) -> str:
        booking = schema.get("booking_section", {})
        dept = schema.get("department_section", {}).get("department", "")

        selected_doc = booking.get("selected_doctor") or {}
        selected_slot = booking.get("selected_slot") or {}

        doc_name = selected_doc.get("name") or booking.get("doctor_name") or "Doctor"
        spec = selected_doc.get("specialization") or dept
        spec_text = f" ({spec})" if spec else ""

        hosp = selected_doc.get("hospital") or booking.get("hospital") or "HealthOS Partner Clinic"
        loc = selected_doc.get("location")
        hosp_text = f"{hosp}, {loc}" if loc else hosp

        date = selected_slot.get("date") or booking.get("date") or "Scheduled Date"
        time = selected_slot.get("time") or booking.get("time_slot") or "Scheduled Time"
        slot_id = selected_slot.get("slot_id") or booking.get("booking_slot_id")
        slot_text = f"\n  Slot ID  : {slot_id}" if slot_id else ""

        return (
            "✅ Your appointment has been confirmed!\n\n"
            f"  Doctor   : {doc_name}{spec_text}\n"
            f"  Hospital : {hosp_text}\n"
            f"  Date     : {date}\n"
            f"  Time     : {time}"
            f"{slot_text}\n\n"
            "Is there anything else I can help you with?"
        )

    # ============================================================
    # INPUT VALIDATION & IRRELEVANCE HANDLING
    # ============================================================

    def handle_user_input(
        self,
        schema: DynamicSchema,
        user_input: str,
        current_dependency: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validates user input against current dependency.
        Returns:
          (is_valid: bool, clarification_message_if_invalid: Optional[str], schema_patch: Optional[dict])
        """
        dep = current_dependency or schema.get("current_dependency")
        booking = schema.get("booking_section", {})
        clean_input = user_input.strip()

        # Doctor selection validation
        if dep == "doctor_name":
            candidates = booking.get("doctor_candidates")
            if candidates:
                resolved = self.booking_connector.resolve_doctor_choice(clean_input, candidates)
                if resolved:
                    patch = {
                        "booking_section": {
                            "doctor_name": resolved["name"],
                            "selected_doctor": resolved,
                            "doctor_valid": True,
                            "hospital": resolved.get("hospital"),
                        }
                    }
                    return True, None, patch
                else:
                    # Input is invalid for candidate list
                    formatted = self.booking_connector.format_doctor_list(candidates)
                    dept = schema.get("department_section", {}).get("department", "this")
                    clarification = (
                        f"I couldn't find '{user_input}' in our {dept} department.\n"
                        "Please select from the available options:\n\n"
                        f"{formatted}\n\n"
                        "(Type the number or the doctor's full name)"
                    )
                    return False, clarification, None
            else:
                # Direct validation
                is_valid, doc = self.booking_connector.validate_doctor_name(clean_input)
                if is_valid and doc:
                    patch = {
                        "booking_section": {
                            "doctor_name": doc["name"],
                            "selected_doctor": doc,
                            "doctor_valid": True,
                            "hospital": doc.get("hospital"),
                        }
                    }
                    return True, None, patch
                else:
                    all_docs = self.booking_connector.get_all_doctors()
                    formatted = self.booking_connector.format_doctor_list(all_docs)
                    clarification = (
                        f"I couldn't find a doctor named '{user_input}' in our system.\n"
                        "Please provide the full name or choose from our available doctors:\n\n"
                        f"{formatted}\n\n"
                        "(Type a name or number)"
                    )
                    return False, clarification, {"booking_section": {"doctor_valid": False}}

        # Slot selection validation (date or time_slot)
        if dep in ("date", "time_slot"):
            slots = booking.get("slot_candidates")
            if slots:
                resolved_slot = self.booking_connector.resolve_slot_choice(clean_input, slots)
                if resolved_slot:
                    patch = {
                        "booking_section": {
                            "selected_slot": resolved_slot,
                            "date": resolved_slot.get("date"),
                            "time_slot": resolved_slot.get("time"),
                            "booking_slot_id": resolved_slot.get("slot_id"),
                        }
                    }
                    return True, None, patch
                else:
                    formatted_slots = self.booking_connector.format_slot_list(slots)
                    doc_name = booking.get("doctor_name", "the doctor")
                    clarification = (
                        f"I couldn't find a slot matching '{user_input}' for {doc_name}.\n"
                        "Please choose from the available slots:\n\n"
                        f"{formatted_slots}\n\n"
                        "Which slot would you prefer?"
                    )
                    return False, clarification, None

        # Department selection validation
        if dep == "department":
            depts = self.booking_connector.get_available_departments()
            matched_dept = None
            if clean_input.isdigit():
                idx = int(clean_input)
                if 1 <= idx <= len(depts):
                    matched_dept = depts[idx - 1]
            else:
                for d in depts:
                    if clean_input.lower() in d.lower() or d.lower() in clean_input.lower():
                        matched_dept = d
                        break

            if matched_dept:
                patch = {"department_section": {"department": matched_dept}}
                return True, None, patch
            else:
                formatted_depts = self.booking_connector.format_department_list()
                clarification = (
                    f"I couldn't find department '{user_input}'.\n"
                    "Please choose from the available departments:\n\n"
                    f"{formatted_depts}\n\n"
                    "(Type the department name or its number)"
                )
                return False, clarification, None

        return True, None, None

    # ============================================================
    # SLM REPHRASING & FACT PRESERVATION
    # ============================================================

    def _rephrase_with_slm(self, base_response: str) -> str:
        prompt = (
            "You are a friendly medical appointment assistant.\n"
            "Rephrase the following message to sound warm, natural, and conversational.\n"
            "CRITICAL: Keep all names, numbers, dates, times, and slot IDs EXACTLY as given.\n"
            "Do NOT add or remove any factual information.\n\n"
            f"Message:\n{base_response}\n\n"
            "Rephrased:"
        )
        return self.run_llm_fn(prompt, self.slm, self.model_config)

    def _verify_facts_preserved(self, base: str, enhanced: str) -> bool:
        if not enhanced or len(enhanced.strip()) < 10:
            return False

        # Verify all numbers/IDs are preserved
        base_numbers = re.findall(r"\b\d+\b", base)
        for num in base_numbers:
            if num not in enhanced:
                return False

        # Verify all time patterns (e.g. 09:30) are preserved
        base_times = re.findall(r"\b\d{1,2}:\d{2}\b", base)
        for tm in base_times:
            if tm not in enhanced:
                return False

        return True

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    def _infer_action_plan(self, schema: DynamicSchema) -> Dict[str, Any]:
        task = schema.get("task")
        if not task:
            return {"action": "WAIT", "dependency": None}
        if task == "emergency":
            return {"action": "EMERGENCY", "dependency": None}
        if is_schema_complete(schema):
            return {"action": "COMPLETE", "dependency": None}

        missing = get_missing_fields(schema)
        if missing:
            return {"action": "ASK_USER", "dependency": missing[0]}

        return {"action": "COMPLETE", "dependency": None}
