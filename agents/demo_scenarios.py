"""
demo_scenarios.py

Demonstration of the 3 user appointment booking scenarios and emergency flow
using the Dynamic StateSchema, TaskResolver, and DependencyEngine.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_schema import (
    create_empty_schema,
    merge_schema_update,
    print_schema,
    is_schema_complete,
    get_missing_fields,
)
from task_resolver import TaskResolver
from dependency_engine import DependencyEngine
<<<<<<< HEAD
=======
from response_generator_agent import ResponseGeneratorAgent
from booking_connector import BookingConnector
from slm_engine import SLMEngine
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)


def simulate_scenario(title: str, steps: list):
    print("\n" + "#" * 70)
    print(f"  SCENARIO: {title}")
    print("#" * 70)

    resolver = TaskResolver()
    engine = DependencyEngine()
<<<<<<< HEAD
=======
    booking_connector = BookingConnector()
    response_agent = ResponseGeneratorAgent(booking_connector)
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    schema = create_empty_schema()

    for idx, user_input_update in enumerate(steps, 1):
        print(f"\n--- [Turn {idx}] Incoming Update: {user_input_update.get('_user_utterance', '')} ---")
        
        update_data = {k: v for k, v in user_input_update.items() if not k.startswith("_")}
        schema = merge_schema_update(schema, update_data)
        
        resolver.update_schema_task(schema)
        
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)
        
        print(f"  • Task Resolved   : {schema.get('task')}")
        print(f"  • Current Stage   : {schema.get('stage')}")
        print(f"  • Next Action     : {action_plan.get('action')}")
        print(f"  • Dependency Needed: {action_plan.get('dependency')}")
        print(f"  • Complete?       : {is_schema_complete(schema)}")
        if not is_schema_complete(schema):
            print(f"  • Missing Fields  : {get_missing_fields(schema)}")

<<<<<<< HEAD
=======
        # ----------------------------------------------------------
        # RESPONSE GENERATOR AGENT  (new section)
        # ----------------------------------------------------------
        print("\n" + "-" * 60)
        print("  RESPONSE GENERATOR AGENT")
        print("-" * 60)
        agent_response = response_agent.generate(schema, action_plan)
        if agent_response:
            print(f"  HealthOS:\n{agent_response}")
        else:
            print("  HealthOS: (No further input required)")
        print("-" * 60)

>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    print("\nFinal State:")
    print_schema(schema)


def run_all_scenarios():
    print("=" * 70)
    print("HealthOS Dynamic StateSchema & Dependency Engine Demonstration")
    print("=" * 70)

    simulate_scenario(
        "Scenario 1: Direct Doctor Booking (User knows doctor)",
        [
            {
<<<<<<< HEAD
                "_user_utterance": "I want an appointment with Dr. Sharma in Cardiology",
                "greeter_intent": "booking",
                "department_section": {"department": "Cardiology"},
                "booking_section": {"doctor_name": "Dr. Sharma"},
=======
                "_user_utterance": "I want an appointment with Dr. Kiran Mehta in Cardiology",
                "greeter_intent": "booking",
                "department_section": {"department": "Cardiology"},
                "booking_section": {"doctor_name": "Dr. Kiran Mehta"},
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
            },
            {
                "_user_utterance": "Tomorrow please",
                "booking_section": {"date": "tomorrow"},
            },
            {
                "_user_utterance": "10:00 AM works for me",
                "booking_section": {"time_slot": "10:00 AM"},
            },
        ],
    )

    simulate_scenario(
        "Scenario 2: Department Booking (User knows department)",
        [
            {
                "_user_utterance": "I need to see a dermatologist",
                "greeter_intent": "booking",
                "department_section": {"department": "Dermatology"},
            },
            {
<<<<<<< HEAD
                "_user_utterance": "Let's book Dr. Smith",
                "booking_section": {"doctor_name": "Dr. Smith"},
=======
                "_user_utterance": "Let's book Dr. Pooja Sharma",
                "booking_section": {"doctor_name": "Dr. Pooja Sharma"},
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
            },
            {
                "_user_utterance": "Next Monday",
                "booking_section": {"date": "Next Monday"},
            },
            {
                "_user_utterance": "2:30 PM",
                "booking_section": {"time_slot": "2:30 PM"},
            },
        ],
    )

    simulate_scenario(
        "Scenario 3: Symptom-Based Booking (System classifies department)",
        [
            {
                "_user_utterance": "I have severe chest tightness and shortness of breath",
                "greeter_intent": "triage",
                "symptom_section": {
                    "symptoms": ["chest tightness", "shortness of breath"],
                    "severity": "high",
                },
            },
            {
                "_user_utterance": "[System triggers Department Classifier -> Cardiology]",
                "department_section": {
                    "department": "Cardiology",
                    "source": "department_classifier",
                    "confidence": 0.96,
                },
            },
            {
<<<<<<< HEAD
                "_user_utterance": "I want to consult Dr. Mehta",
                "booking_section": {"doctor_name": "Dr. Mehta"},
=======
                "_user_utterance": "I want to consult Dr. Kiran Mehta",
                "booking_section": {"doctor_name": "Dr. Kiran Mehta"},
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
            },
            {
                "_user_utterance": "Friday at 4 PM",
                "booking_section": {"date": "Friday", "time_slot": "4:00 PM"},
            },
        ],
    )

<<<<<<< HEAD
=======
    simulate_scenario(
        "Scenario 4: End-to-End Real Booking Flow (Department -> Doctor Candidates -> Slot Selection -> Execution)",
        [
            {
                "_user_utterance": "I want to consult a cardiologist",
                "greeter_intent": "booking",
                "department_section": {"department": "Cardiology"},
            },
            {
                "_user_utterance": "1 (Dr. Kiran Mehta)",
                "booking_section": {
                    "doctor_name": "Dr. Kiran Mehta",
                    "doctor_valid": True,
                    "selected_doctor": {
                        "doctor_id": 2,
                        "name": "Dr. Kiran Mehta",
                        "specialization": "Cardiology",
                        "hospital": "Apollo Clinic",
                        "location": "Hyderabad",
                    },
                },
            },
            {
                "_user_utterance": "1 (Slot 201: 2026-02-11 at 09:30)",
                "booking_section": {
                    "date": "2026-02-11",
                    "time_slot": "09:30",
                    "selected_slot": {
                        "slot_id": 201,
                        "doctor_id": 2,
                        "date": "2026-02-11",
                        "time": "09:30",
                        "available": False,
                    },
                    "booking_slot_id": 201,
                    "patient_name": "Patient",
                    "booking_confirmed": True,
                },
            },
        ],
    )

    simulate_scenario(
        "Scenario 5: SLM Ambiguity & Fallback to General Medicine (User Undecided)",
        [
            {
                "_user_utterance": "I feel vaguely unwell, tired, and have slight body discomfort",
                "greeter_intent": "triage",
                "symptom_section": {
                    "symptoms": ["general malaise", "fatigue", "body discomfort"],
                },
            },
            {
                "_user_utterance": "[SLM Department Classifier detects ambiguity: is_ambiguous = True]",
                "department_section": {
                    "department": None,
                    "source": "slm_department_classifier",
                    "confidence": 0.45,
                    "is_ambiguous": True,
                },
            },
            {
                "_user_utterance": "I don't know which department, I'm not sure",
                "department_section": {
                    "department": "General Medicine",
                    "source": "general_medicine_fallback_due_to_indecision",
                    "routed_due_to_indecision": True,
                    "confidence": 1.0,
                    "is_ambiguous": False,
                },
            },
            {
                "_user_utterance": "Let's book Dr. Suresh Kumar",
                "booking_section": {"doctor_name": "Dr. Suresh Kumar"},
            },
        ],
    )

>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

def interactive_demo():
    print("\n" + "=" * 70)
    print("HealthOS Live Interactive Dynamic State Demo")
    print("Type your input at each step. Type 'reset' to start over, 'exit' to quit.")
    print("=" * 70)

    resolver = TaskResolver()
    engine = DependencyEngine()
<<<<<<< HEAD
    schema = create_empty_schema()
=======
    booking_connector = BookingConnector()
    slm_engine = SLMEngine()
    response_agent = ResponseGeneratorAgent(booking_connector)
    schema = create_empty_schema()
    available_depts = booking_connector.get_available_departments()
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

    print("\nInitial schema loaded. Try entering doctor name, department, or symptoms.")

    while True:
        curr_dep = schema.get("current_dependency")
        stage = schema.get("stage", "initial")
        prompt = f"\n[Stage: {stage}] (Needed: {curr_dep or 'Initial request'}) > "

        try:
            user_input = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            schema = create_empty_schema()
            print("State schema reset.")
            continue

        update = {}
<<<<<<< HEAD
        if curr_dep == "doctor_name":
            update["booking_section"] = {"doctor_name": user_input}
        elif curr_dep == "date":
            update["booking_section"] = {"date": user_input}
        elif curr_dep == "time_slot":
            update["booking_section"] = {"time_slot": user_input}
        elif curr_dep == "symptoms":
            update["symptom_section"] = {"symptoms": [user_input]}
        elif curr_dep == "department":
            update["department_section"] = {"department": user_input}
        else:
            low = user_input.lower()
            if "emergency" in low or "chest pain" in low:
                update["greeter_intent"] = "emergency"
            elif "dr." in low or "doctor" in low:
                update["greeter_intent"] = "booking"
                update["booking_section"] = {"doctor_name": user_input}
            elif any(d in low for d in ["cardiology", "dermatology", "neurology", "orthopedics"]):
                update["greeter_intent"] = "booking"
                update["department_section"] = {"department": user_input}
            else:
                update["greeter_intent"] = "triage"
                update["symptom_section"] = {"symptoms": [user_input]}
=======
        if curr_dep == "department":
            if schema.get("department_section", {}).get("is_ambiguous", False) and slm_engine.is_user_undecided(user_input):
                print("  ⚡ [SLM Decision] User undecided -> Routing to General Medicine.")
                update = {
                    "department_section": {
                        "department": "General Medicine",
                        "source": "general_medicine_fallback_due_to_indecision",
                        "routed_due_to_indecision": True,
                        "confidence": 1.0,
                        "is_ambiguous": False,
                    }
                }
            else:
                is_valid, clarification, patch = response_agent.handle_user_input(schema, user_input, "department")
                if not is_valid and clarification:
                    print(f"\n  HealthOS:\n{clarification}")
                    continue
                update = patch or {"department_section": {"department": user_input, "is_ambiguous": False}}

        elif curr_dep in ("doctor_name", "date", "time_slot"):
            is_valid, clarification, patch = response_agent.handle_user_input(schema, user_input, curr_dep)
            if not is_valid and clarification:
                print(f"\n  HealthOS:\n{clarification}")
                continue
            update = patch or {"booking_section": {curr_dep: user_input}}

        elif curr_dep == "symptoms":
            extracted = slm_engine.classify_intent_and_entities(user_input, available_depts)
            update = {"symptom_section": {"symptoms": extracted.get("symptoms") or [user_input]}}

        else:
            # Pure SLM Intent and Entity Extraction
            print("  ⚡ [SLM Decision] Analyzing intent & entities via SLM...")
            extracted = slm_engine.classify_intent_and_entities(user_input, available_depts)
            update["greeter_intent"] = extracted.get("intent", "triage")
            if extracted.get("symptoms"):
                update["symptom_section"] = {"symptoms": extracted["symptoms"]}
            if extracted.get("department"):
                update["department_section"] = {"department": extracted["department"]}
            b_patch = {}
            for f in ("doctor_name", "date", "time_slot", "patient_name"):
                if extracted.get(f):
                    b_patch[f] = extracted[f]
            if b_patch:
                update["booking_section"] = b_patch
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

        schema = merge_schema_update(schema, update)
        resolver.update_schema_task(schema)
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)

        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
<<<<<<< HEAD
            print("  ⚡ [System Auto-Trigger] Running department_classifier...")
            schema = merge_schema_update(schema, {
                "department_section": {
                    "department": "General Medicine",
                    "source": "department_classifier",
                    "confidence": 0.90,
                }
            })
            action_plan = engine.get_next_action(schema)
            engine.update_schema_state(schema)
=======
            symptoms = schema.get("symptom_section", {}).get("symptoms", [])
            print(f"  ⚡ [SLM Department Classifier] Inferring department for: {symptoms}...")
            classification = slm_engine.classify_department(symptoms, available_depts)
            if classification.get("is_ambiguous"):
                print("  ⚠️ [SLM Ambiguity Detected] Symptoms ambiguous. Prompting user to select a department...")
                schema["department_section"]["is_ambiguous"] = True
                schema["department_section"]["confidence"] = classification.get("confidence", 0.5)
                schema["department_section"]["source"] = "slm_department_classifier"
                action_plan = engine.get_next_action(schema)
                engine.update_schema_state(schema)
            else:
                schema = merge_schema_update(schema, {
                    "department_section": {
                        "department": classification.get("department"),
                        "source": "slm_department_classifier",
                        "confidence": classification.get("confidence", 0.95),
                        "is_ambiguous": False,
                    }
                })
                action_plan = engine.get_next_action(schema)
                engine.update_schema_state(schema)

        if action_plan.get("action") == "COMPLETE":
            selected_slot = schema.get("booking_section", {}).get("selected_slot")
            if selected_slot and not schema.get("booking_section", {}).get("booking_confirmed"):
                slot_id = selected_slot.get("slot_id")
                patient = schema.get("booking_section", {}).get("patient_name") or "Patient"
                success = booking_connector.execute_booking(slot_id, patient)
                schema["booking_section"]["booking_confirmed"] = success
                schema["booking_section"]["booking_slot_id"] = slot_id
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

        print_schema(schema)
        print(f"\nNext Action: {action_plan.get('action')} | Dependency: {action_plan.get('dependency')}")

<<<<<<< HEAD
=======
        print("\n" + "-" * 60)
        print("  RESPONSE GENERATOR AGENT")
        print("-" * 60)
        agent_response = response_agent.generate(schema, action_plan)
        if agent_response:
            print(f"  HealthOS:\n{agent_response}")
        print("-" * 60)

>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HealthOS Scenario & State Demo")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch live interactive terminal demo")
    args = parser.parse_args()

    if args.interactive:
        interactive_demo()
    else:
        run_all_scenarios()
