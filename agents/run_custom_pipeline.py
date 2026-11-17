"""
run_custom_pipeline.py

HealthOS Dynamic State & SLM Decision Pipeline Runner.

Operates on pure SLM decision making (no conditional keyword matching):
- SLM classifies intent (Emergency vs Booking vs Triage) and extracts entities.
- SLM classifies department from patient symptoms.
- If SLM department classification is ambiguous, the system asks the user to choose a department.
- If the user is unable to decide, the SLM detects indecision and directs the patient to General Medicine.

Usage:
  1. Pass turns directly via command line:
     python3 agents/run_custom_pipeline.py "I want to see a cardiologist" "1" "1"

  2. Or run interactively:
     python3 agents/run_custom_pipeline.py -i

  3. Or test ambiguous symptoms:
     python3 agents/run_custom_pipeline.py "I feel tired and have mild nausea with joint discomfort" "I am not sure" "1" "1"
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
from slm_engine import SLMEngine


def test_custom_inputs(turns: list, verbose: bool = True, slm_engine: SLMEngine = None):
    """
    Executes a list of string utterances through the SLM-driven HealthOS pipeline.
    """
    resolver = TaskResolver()
    engine = DependencyEngine()
    booking_connector = BookingConnector()
    slm = slm_engine or SLMEngine()
    response_agent = ResponseGeneratorAgent(booking_connector)
    schema = create_empty_schema()

    available_depts = booking_connector.get_available_departments()

    print("\n" + "=" * 70)
    print("  HEALTHOS SLM PIPELINE TEST (Zero Conditional Keyword Heuristics)")
    print(f"  Input Turns ({len(turns)}): {turns}")
    print(f"  SLM Engine Loaded: {slm.is_available()} (Model: {getattr(slm, 'model_path', 'None')})")
    print("=" * 70)

    for idx, user_utterance in enumerate(turns, 1):
        print(f"\n--- [Turn {idx}] User Input: \"{user_utterance}\" ---")

        curr_dep = schema.get("current_dependency")
        update = {}

        # -----------------------------------------------------------------
        # Step A: Process input according to current conversation dependency
        # -----------------------------------------------------------------
        if curr_dep == "department":
            is_ambiguous_flow = schema.get("department_section", {}).get("is_ambiguous", False)

            if is_ambiguous_flow:
                # Check if user is undecided or unable to pick a department
                is_undecided = slm.is_user_undecided(user_utterance)
                if is_undecided:
                    print("  ⚡ [SLM Decision] Detected user indecision -> Directing to General Medicine.")
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
                    # User picked a department (e.g. name or number)
                    is_valid, clarification, patch = response_agent.handle_user_input(
                        schema, user_utterance, "department"
                    )
                    if not is_valid and clarification:
                        print(f"\n  HealthOS Clarification:\n{clarification}")
                        continue
                    update = patch or {"department_section": {"department": user_utterance, "is_ambiguous": False}}
            else:
                is_valid, clarification, patch = response_agent.handle_user_input(
                    schema, user_utterance, "department"
                )
                if not is_valid and clarification:
                    print(f"\n  HealthOS Clarification:\n{clarification}")
                    continue
                update = patch or {"department_section": {"department": user_utterance}}

        elif curr_dep in ("doctor_name", "date", "time_slot"):
            is_valid, clarification, patch = response_agent.handle_user_input(
                schema, user_utterance, curr_dep
            )
            if not is_valid and clarification:
                print(f"\n  HealthOS Clarification:\n{clarification}")
                print(f"  • Status: Input not accepted, remaining on dependency '{curr_dep}'")
                continue
            update = patch or {"booking_section": {curr_dep: user_utterance}}

        elif curr_dep == "symptoms":
            extracted = slm.classify_intent_and_entities(user_utterance, available_depts)
            syms = extracted.get("symptoms") or [user_utterance]
            update = {"symptom_section": {"symptoms": syms}}

        else:
            # General initial turn: SLM performs Intent Classification and Entity Extraction
            print("  ⚡ [SLM Decision] Analyzing message intent and entities via SLM...")
            extracted = slm.classify_intent_and_entities(user_utterance, available_depts)
            print(f"  ⚡ [SLM Extraction] Extracted: {extracted}")

            intent = extracted.get("intent", "triage")
            update["greeter_intent"] = intent

            if extracted.get("symptoms"):
                update["symptom_section"] = {"symptoms": extracted["symptoms"]}

            if extracted.get("department"):
                update["department_section"] = {"department": extracted["department"]}

            booking_patch = {}
            for field in ("doctor_name", "date", "time_slot", "patient_name"):
                if extracted.get(field):
                    booking_patch[field] = extracted[field]
            if booking_patch:
                update["booking_section"] = booking_patch

        # -----------------------------------------------------------------
        # Step B: Non-destructive schema update & task resolution
        # -----------------------------------------------------------------
        schema = merge_schema_update(schema, update)
        resolver.update_schema_task(schema)
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)

        # -----------------------------------------------------------------
        # Step C: Handle System Generators via SLM (Department Classification)
        # -----------------------------------------------------------------
        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
            symptoms = schema.get("symptom_section", {}).get("symptoms", [])
            print(f"  ⚡ [SLM Department Classifier] Inferring department for symptoms: {symptoms}...")
            classification = slm.classify_department(symptoms, available_depts)
            print(f"  ⚡ [SLM Department Classifier] Output: {classification}")

            if classification.get("is_ambiguous"):
                print("  ⚠️ [SLM Ambiguity Detected] Symptoms could not be uniquely mapped. Prompting user to select a department...")
                schema["department_section"]["is_ambiguous"] = True
                schema["department_section"]["confidence"] = classification.get("confidence", 0.5)
                schema["department_section"]["source"] = "slm_department_classifier"
                # Recompute action so dependency engine solicits department from user
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

        # -----------------------------------------------------------------
        # Step D: Booking Confirmation Execution
        # -----------------------------------------------------------------
        if action_plan.get("action") == "COMPLETE":
            selected_slot = schema.get("booking_section", {}).get("selected_slot")
            if selected_slot and not schema.get("booking_section", {}).get("booking_confirmed"):
                slot_id = selected_slot.get("slot_id")
                patient = schema.get("booking_section", {}).get("patient_name") or "Patient"
                success = booking_connector.execute_booking(slot_id, patient)
                schema["booking_section"]["booking_confirmed"] = success
                schema["booking_section"]["booking_slot_id"] = slot_id

        # -----------------------------------------------------------------
        # Step E: Response Generation
        # -----------------------------------------------------------------
        agent_response = response_agent.generate(schema, action_plan, last_user_input=user_utterance)

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


def interactive_chat():
    """Live interactive chat session powered by SLM decision making."""
    resolver = TaskResolver()
    engine = DependencyEngine()
    booking_connector = BookingConnector()
    slm = SLMEngine()
    response_agent = ResponseGeneratorAgent(booking_connector)
    schema = create_empty_schema()
    available_depts = booking_connector.get_available_departments()

    print("\n" + "=" * 70)
    print("  HEALTHOS INTERACTIVE CHAT (SLM Decision Driven)")
    print("  Type your message. Commands: 'reset' to restart, 'exit' to quit.")
    print("=" * 70)

    turn = 1
    while True:
        try:
            user_input = input(f"\n[Turn {turn}] You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting session. Take care!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Chat ended. Goodbye!")
            break
        if user_input.lower() == "reset":
            schema = create_empty_schema()
            turn = 1
            print("Conversation state has been reset.")
            continue

        curr_dep = schema.get("current_dependency")
        update = {}

        if curr_dep == "department":
            if schema.get("department_section", {}).get("is_ambiguous", False):
                if slm.is_user_undecided(user_input):
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
                    is_valid, clarif, patch = response_agent.handle_user_input(schema, user_input, "department")
                    if not is_valid and clarif:
                        print(f"\nHealthOS: {clarif}")
                        continue
                    update = patch or {"department_section": {"department": user_input, "is_ambiguous": False}}
            else:
                is_valid, clarif, patch = response_agent.handle_user_input(schema, user_input, "department")
                if not is_valid and clarif:
                    print(f"\nHealthOS: {clarif}")
                    continue
                update = patch or {"department_section": {"department": user_input}}

        elif curr_dep in ("doctor_name", "date", "time_slot"):
            is_valid, clarif, patch = response_agent.handle_user_input(schema, user_input, curr_dep)
            if not is_valid and clarif:
                print(f"\nHealthOS: {clarif}")
                continue
            update = patch or {"booking_section": {curr_dep: user_input}}

        elif curr_dep == "symptoms":
            extracted = slm.classify_intent_and_entities(user_input, available_depts)
            syms = extracted.get("symptoms") or [user_input]
            update = {"symptom_section": {"symptoms": syms}}

        else:
            extracted = slm.classify_intent_and_entities(user_input, available_depts)
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

        schema = merge_schema_update(schema, update)
        resolver.update_schema_task(schema)
        action_plan = engine.get_next_action(schema)
        engine.update_schema_state(schema)

        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
            symptoms = schema.get("symptom_section", {}).get("symptoms", [])
            classification = slm.classify_department(symptoms, available_depts)
            if classification.get("is_ambiguous"):
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

        agent_response = response_agent.generate(schema, action_plan, last_user_input=user_input)
        if agent_response:
            print(f"\nHealthOS:\n{agent_response}")
        else:
            print("\nHealthOS: Request completed.")

        turn += 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ("-i", "--interactive", "-h", "--help"):
        user_turns = sys.argv[1:]
        test_custom_inputs(user_turns)
    elif len(sys.argv) > 1 and sys.argv[1] in ("-i", "--interactive"):
        interactive_chat()
    else:
        sample_turns = [
            "I want to see a cardiologist",
            "1",
            "1",
        ]
        test_custom_inputs(sample_turns)
