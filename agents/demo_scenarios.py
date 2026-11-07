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
from response_generator_agent import ResponseGeneratorAgent
from booking_connector import BookingConnector


def simulate_scenario(title: str, steps: list):
    print("\n" + "#" * 70)
    print(f"  SCENARIO: {title}")
    print("#" * 70)

    resolver = TaskResolver()
    engine = DependencyEngine()
    booking_connector = BookingConnector()
    response_agent = ResponseGeneratorAgent(booking_connector)
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
                "_user_utterance": "I want an appointment with Dr. Kiran Mehta in Cardiology",
                "greeter_intent": "booking",
                "department_section": {"department": "Cardiology"},
                "booking_section": {"doctor_name": "Dr. Kiran Mehta"},
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
                "_user_utterance": "Let's book Dr. Pooja Sharma",
                "booking_section": {"doctor_name": "Dr. Pooja Sharma"},
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
                "_user_utterance": "I want to consult Dr. Kiran Mehta",
                "booking_section": {"doctor_name": "Dr. Kiran Mehta"},
            },
            {
                "_user_utterance": "Friday at 4 PM",
                "booking_section": {"date": "Friday", "time_slot": "4:00 PM"},
            },
        ],
    )

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


def interactive_demo():
    print("\n" + "=" * 70)
    print("HealthOS Live Interactive Dynamic State Demo")
    print("Type your input at each step. Type 'reset' to start over, 'exit' to quit.")
    print("=" * 70)

    resolver = TaskResolver()
    engine = DependencyEngine()
    booking_connector = BookingConnector()
    response_agent = ResponseGeneratorAgent(booking_connector)
    schema = create_empty_schema()

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
        if curr_dep in ("doctor_name", "date", "time_slot", "department"):
            is_valid, clarification, patch = response_agent.handle_user_input(schema, user_input, curr_dep)
            if not is_valid and clarification:
                print(f"\n  HealthOS:\n{clarification}")
                continue
            if patch:
                update = patch
            else:
                if curr_dep == "doctor_name":
                    update["booking_section"] = {"doctor_name": user_input}
                elif curr_dep == "date":
                    update["booking_section"] = {"date": user_input}
                elif curr_dep == "time_slot":
                    update["booking_section"] = {"time_slot": user_input}
                elif curr_dep == "department":
                    update["department_section"] = {"department": user_input}
        elif curr_dep == "symptoms":
            update["symptom_section"] = {"symptoms": [user_input]}
        else:
            low = user_input.lower()
            if "emergency" in low or "chest pain" in low:
                update["greeter_intent"] = "emergency"
            elif "dr." in low or "doctor" in low:
                update["greeter_intent"] = "booking"
                is_valid, clarif, patch = response_agent.handle_user_input(schema, user_input, "doctor_name")
                if patch:
                    update = patch
                else:
                    update["booking_section"] = {"doctor_name": user_input}
            elif booking_connector.match_department(user_input):
                matched_dept = booking_connector.match_department(user_input)
                update["greeter_intent"] = "booking"
                update["department_section"] = {"department": matched_dept}
            else:
                update["greeter_intent"] = "triage"
                update["symptom_section"] = {"symptoms": [user_input]}

        schema = merge_schema_update(schema, update)
        resolver.update_schema_task(schema)
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)

        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
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

        if action_plan.get("action") == "COMPLETE":
            selected_slot = schema.get("booking_section", {}).get("selected_slot")
            if selected_slot and not schema.get("booking_section", {}).get("booking_confirmed"):
                slot_id = selected_slot.get("slot_id")
                patient = schema.get("booking_section", {}).get("patient_name") or "Patient"
                success = booking_connector.execute_booking(slot_id, patient)
                schema["booking_section"]["booking_confirmed"] = success
                schema["booking_section"]["booking_slot_id"] = slot_id

        print_schema(schema)
        print(f"\nNext Action: {action_plan.get('action')} | Dependency: {action_plan.get('dependency')}")

        print("\n" + "-" * 60)
        print("  RESPONSE GENERATOR AGENT")
        print("-" * 60)
        agent_response = response_agent.generate(schema, action_plan)
        if agent_response:
            print(f"  HealthOS:\n{agent_response}")
        print("-" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HealthOS Scenario & State Demo")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch live interactive terminal demo")
    args = parser.parse_args()

    if args.interactive:
        interactive_demo()
    else:
        run_all_scenarios()
