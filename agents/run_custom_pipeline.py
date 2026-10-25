"""
run_custom_pipeline.py

A simple runner allowing you to test the HealthOS Dynamic State &
Response Generator Pipeline with your own custom utterances.

Usage:
  1. Pass turns directly via command line:
     python3 agents/run_custom_pipeline.py "I want to see a cardiologist" "1" "1"

  2. Or run interactively:
     python3 agents/run_custom_pipeline.py --interactive

  3. Or import in Python:
     from run_custom_pipeline import test_custom_inputs
     test_custom_inputs(["I have a headache", "1", "1"])
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
from booking_connector import BookingConnector
from response_generator_agent import ResponseGeneratorAgent


def test_custom_inputs(turns: list, verbose: bool = True):
    """
    Executes a list of string utterances through the full HealthOS pipeline.
    """
    resolver = TaskResolver()
    engine = DependencyEngine()
    booking_connector = BookingConnector()
    response_agent = ResponseGeneratorAgent(booking_connector)
    schema = create_empty_schema()

    print("\n" + "=" * 70)
    print("  HEALTHOS CUSTOM PIPELINE TEST")
    print(f"  Input Turns ({len(turns)}): {turns}")
    print("=" * 70)

    for idx, user_utterance in enumerate(turns, 1):
        print(f"\n--- [Turn {idx}] User Input: \"{user_utterance}\" ---")

        curr_dep = schema.get("current_dependency")
        update = {}

        if curr_dep in ("doctor_name", "date", "time_slot", "department"):
            is_valid, clarification, patch = response_agent.handle_user_input(
                schema, user_utterance, curr_dep
            )
            if not is_valid and clarification:
                print(f"\n  HealthOS Response (Clarification):\n{clarification}")
                print(f"  • Status: Input not accepted, remaining on dependency '{curr_dep}'")
                continue
            if patch:
                update = patch
            else:
                if curr_dep == "doctor_name":
                    update["booking_section"] = {"doctor_name": user_utterance}
                elif curr_dep == "date":
                    update["booking_section"] = {"date": user_utterance}
                elif curr_dep == "time_slot":
                    update["booking_section"] = {"time_slot": user_utterance}
                elif curr_dep == "department":
                    update["department_section"] = {"department": user_utterance}
        elif curr_dep == "symptoms":
            update["symptom_section"] = {"symptoms": [user_utterance]}
        else:
            low = user_utterance.lower()
            if "emergency" in low or "chest pain" in low:
                update["greeter_intent"] = "emergency"
            elif "dr." in low or "doctor" in low:
                update["greeter_intent"] = "booking"
                is_valid, clarif, patch = response_agent.handle_user_input(schema, user_utterance, "doctor_name")
                if patch:
                    update = patch
                else:
                    update["booking_section"] = {"doctor_name": user_utterance}
            elif booking_connector.match_department(user_utterance):
                matched_dept = booking_connector.match_department(user_utterance)
                update["greeter_intent"] = "booking"
                update["department_section"] = {"department": matched_dept}
            else:
                update["greeter_intent"] = "triage"
                update["symptom_section"] = {"symptoms": [user_utterance]}

        # 1. Update Schema
        schema = merge_schema_update(schema, update)

        # 2. Resolve Task
        resolver.update_schema_task(schema)

        # 3. Determine Next Action
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)

        # 4. Handle System Generators (e.g. classifier)
        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
            print("  ⚡ [System Auto-Trigger] Running department_classifier -> General Medicine...")
            schema = merge_schema_update(schema, {
                "department_section": {
                    "department": "General Medicine",
                    "source": "department_classifier",
                    "confidence": 0.90,
                }
            })
            action_plan = engine.get_next_action(schema)
            engine.update_schema_state(schema)

        # 5. Handle Booking Confirmation
        if action_plan.get("action") == "COMPLETE":
            selected_slot = schema.get("booking_section", {}).get("selected_slot")
            if selected_slot and not schema.get("booking_section", {}).get("booking_confirmed"):
                slot_id = selected_slot.get("slot_id")
                patient = schema.get("booking_section", {}).get("patient_name") or "Patient"
                success = booking_connector.execute_booking(slot_id, patient)
                schema["booking_section"]["booking_confirmed"] = success
                schema["booking_section"]["booking_slot_id"] = slot_id

        # 6. Generate Conversational Agent Response
        agent_response = response_agent.generate(schema, action_plan)

        if verbose:
            print(f"  • Task Resolved   : {schema.get('task')}")
            print(f"  • Current Stage   : {schema.get('stage')}")
            print(f"  • Next Action     : {action_plan.get('action')}")
            print(f"  • Needed Dep      : {action_plan.get('dependency')}")
            print(f"  • Is Complete?    : {is_schema_complete(schema)}")

        print("\n" + "-" * 60)
        print("  HEALTHOS AGENT RESPONSE")
        print("-" * 60)
        if agent_response:
            print(f"  {agent_response}")
        else:
            print("  (Workflow complete)")
        print("-" * 60)

    print("\nFinal State Schema:")
    print_schema(schema)
    return schema


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ("-i", "--interactive", "-h", "--help"):
        # Custom inputs provided on CLI
        user_turns = sys.argv[1:]
        test_custom_inputs(user_turns)
    elif len(sys.argv) > 1 and sys.argv[1] in ("-i", "--interactive"):
        from demo_scenarios import interactive_demo
        interactive_demo()
    else:
        # Default sample run
        sample_turns = [
            "I want to see a cardiologist",
            "1",
            "1",
        ]
        print("No custom arguments provided. Running default example turns:")
        test_custom_inputs(sample_turns)
