<<<<<<< HEAD
import json
import argparse
import llama_cpp
import prompts as local_prompts


def load_config(config_file):
    with open(config_file, "r") as f:
        return json.load(f)


def load_slm(config_data, model_name):

    if model_name not in config_data:
        raise ValueError(f"Config '{model_name}' not found in config file")

    model_config = config_data[model_name]

    slm = llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"]
    )

    return slm, model_config


def generate_response(slm, model_config, user_input):

    messages = [
        {"role": "system", "content": local_prompts.SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    response = slm.create_chat_completion(
        messages=messages,
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        max_tokens=model_config["max_tokens"]
    )

    reply = response["choices"][0]["message"]["content"]

    return reply


def parse_args():

    parser = argparse.ArgumentParser(description="Offline Medical Chatbot")

    parser.add_argument(
        "-configfile",
        required=True,
        help="Path to config JSON file"
    )

    parser.add_argument(
        "-config",
        required=True,
        help="Model configuration name inside config file"
    )

=======
"""
main.py

Unified Master Application Entry Point for HealthOS.

Integrates the full 4-tier pipeline:
1. Safety Guardrails (Toxic-BERT / SLM Safety filter)
2. Vector Memory (Patient History & Encounter recall via vector_db)
3. Dynamic State Schema (Non-destructive multi-turn state tracking)
4. Task Resolver & Dependency Engine (Autonomous next-action controller)
5. SLM Decision Engine (Zero conditional keyword heuristics, clinical triage, ambiguity handling)
6. Booking Connector (Synthetic doctor/slot indexing and atomic booking)
7. Response Generator Agent (Context-aware conversational generation & fact verification)

Usage:
  python main.py -configfile config.json -config BioMedLM_CONFIG
  or simply:
  python main.py
"""

import os
import sys
import argparse
import json

# Add agents and vector_db directories to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
sys.path.insert(0, os.path.join(BASE_DIR, "vector_db"))

from typing import Tuple, Dict, Any, Optional
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
from guardrail_agent import load_guard_model, check_safety
import vector_memory


def load_config(config_file: str) -> dict:
    if not os.path.isabs(config_file):
        config_file = os.path.join(BASE_DIR, config_file)
    if not os.path.exists(config_file):
        return {}
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


class HealthOSPipeline:
    """
    Unified Orchestrator for the HealthOS Agentic Medical System.
    """

    def __init__(self, config_data: dict, model_name: str = "BioMedLM_CONFIG", slm_engine: Optional[SLMEngine] = None):
        self.config_data = config_data
        self.model_name = model_name

        print("Initializing HealthOS Unified Pipeline...")

        # 1. Initialize Memory
        print("  • Initializing Vector Memory...")
        vector_memory.init_memory()

        # 2. Initialize SLM Engine
        print("  • Loading SLM Decision Engine...")
        self.slm_engine = slm_engine or SLMEngine(config_path=os.path.join(BASE_DIR, "config.json"))

        # 3. Initialize Guardrails
        print("  • Initializing Guardrails...")
        self.guard_model = load_guard_model(config_data)

        # 4. Initialize Booking Backend & Agents
        print("  • Initializing Booking Connector & State Engine...")
        self.booking_connector = BookingConnector()
        self.resolver = TaskResolver()
        self.dependency_engine = DependencyEngine()
        self.response_agent = ResponseGeneratorAgent(self.booking_connector)
        self.available_departments = self.booking_connector.get_available_departments()

        print("HealthOS Pipeline ready.\n")

    def process_turn(self, user_input: str, schema: dict) -> Tuple[str, dict]:
        """
        Executes a single conversational turn through the end-to-end pipeline.
        Returns: (agent_response: str, updated_schema: dict)
        """
        user_input_clean = user_input.strip()

        # -------------------------------------------------------------
        # 1. INPUT GUARDRAIL FILTER
        # -------------------------------------------------------------
        is_safe, toxicity_score = check_safety(
            self.guard_model,
            self.config_data,
            user_input_clean,
            slm_engine=self.slm_engine,
        )
        if not is_safe:
            return (
                "⚠️ I cannot assist with abusive, harmful, or inappropriate requests. "
                "Please describe your medical question or appointment request politely.",
                schema,
            )

        # -------------------------------------------------------------
        # 2. PATIENT MEMORY RECALL (Vector DB)
        # -------------------------------------------------------------
        # Check if user mentioned an existing patient or past medical history
        relevant_memories = vector_memory.search_memory(user_input_clean, k=2)

        curr_dep = schema.get("current_dependency")
        update = {}

        # -------------------------------------------------------------
        # 3. SLM NLU & CONVERSATION STATE PROCESSING
        # -------------------------------------------------------------
        if curr_dep == "department":
            is_ambiguous = schema.get("department_section", {}).get("is_ambiguous", False)
            if is_ambiguous and self.slm_engine.is_user_undecided(user_input_clean):
                # User expressed indecision -> route to General Medicine
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
                is_valid, clarification, patch = self.response_agent.handle_user_input(
                    schema, user_input_clean, "department"
                )
                if not is_valid and clarification:
                    return clarification, schema
                update = patch or {"department_section": {"department": user_input_clean, "is_ambiguous": False}}

        elif curr_dep in ("doctor_name", "date", "time_slot"):
            is_valid, clarification, patch = self.response_agent.handle_user_input(
                schema, user_input_clean, curr_dep
            )
            if not is_valid and clarification:
                return clarification, schema
            update = patch or {"booking_section": {curr_dep: user_input_clean}}

        elif curr_dep == "symptoms":
            extracted = self.slm_engine.classify_intent_and_entities(user_input_clean, self.available_departments)
            syms = extracted.get("symptoms") or [user_input_clean]
            update = {"symptom_section": {"symptoms": syms}}
            if extracted.get("intent"):
                update["greeter_intent"] = extracted["intent"]
            if extracted.get("department"):
                update["department_section"] = {"department": extracted["department"]}
            b_patch = {}
            for field in ("doctor_name", "date", "time_slot", "patient_name"):
                if extracted.get(field):
                    b_patch[field] = extracted[field]
            if b_patch:
                update["booking_section"] = b_patch

        else:
            # Free-form initial utterance: Pure SLM Decision Making
            extracted = self.slm_engine.classify_intent_and_entities(user_input_clean, self.available_departments)
            update["greeter_intent"] = extracted.get("intent", "triage")

            if extracted.get("symptoms"):
                update["symptom_section"] = {"symptoms": extracted["symptoms"]}
            if extracted.get("department"):
                update["department_section"] = {"department": extracted["department"]}

            b_patch = {}
            for field in ("doctor_name", "date", "time_slot", "patient_name"):
                if extracted.get(field):
                    b_patch[field] = extracted[field]
            if b_patch:
                update["booking_section"] = b_patch

        # -------------------------------------------------------------
        # 4. STATE MERGE & TASK ROUTING
        # -------------------------------------------------------------
        schema = merge_schema_update(schema, update)
        self.resolver.update_schema_task(schema)
        action_plan = self.dependency_engine.get_next_action(schema)
        self.dependency_engine.update_schema_state(schema)

        # -------------------------------------------------------------
        # 5. SYSTEM GENERATORS (SLM Clinical Triage)
        # -------------------------------------------------------------
        if action_plan.get("action") == "RUN_SYSTEM" and action_plan.get("dependency") == "department":
            symptoms = schema.get("symptom_section", {}).get("symptoms", [])
            classification = self.slm_engine.classify_department(symptoms, self.available_departments)

            if classification.get("is_ambiguous"):
                schema["department_section"]["is_ambiguous"] = True
                schema["department_section"]["confidence"] = classification.get("confidence", 0.5)
                schema["department_section"]["source"] = "slm_department_classifier"
                action_plan = self.dependency_engine.get_next_action(schema)
                self.dependency_engine.update_schema_state(schema)
            else:
                schema = merge_schema_update(schema, {
                    "department_section": {
                        "department": classification.get("department"),
                        "source": "slm_department_classifier",
                        "confidence": classification.get("confidence", 0.95),
                        "is_ambiguous": False,
                    }
                })
                action_plan = self.dependency_engine.get_next_action(schema)
                self.dependency_engine.update_schema_state(schema)

        # -------------------------------------------------------------
        # 6. ATOMIC SLOT BOOKING & VECTOR MEMORY RECORDING
        # -------------------------------------------------------------
        if action_plan.get("action") == "COMPLETE":
            selected_slot = schema.get("booking_section", {}).get("selected_slot")
            if selected_slot and not schema.get("booking_section", {}).get("booking_confirmed"):
                slot_id = selected_slot.get("slot_id")
                patient = schema.get("booking_section", {}).get("patient_name") or "Patient"
                success = self.booking_connector.execute_booking(slot_id, patient)
                schema["booking_section"]["booking_confirmed"] = success
                schema["booking_section"]["booking_slot_id"] = slot_id

                # Save encounter into Vector Memory for future reference
                doc_name = schema.get("booking_section", {}).get("doctor_name", "Doctor")
                dept = schema.get("department_section", {}).get("department", "General")
                date_val = schema.get("booking_section", {}).get("date", "")
                time_val = schema.get("booking_section", {}).get("time_slot", "")
                encounter_summary = (
                    f"Patient {patient} confirmed appointment with {doc_name} ({dept}) "
                    f"on {date_val} at {time_val}. Slot ID: {slot_id}."
                )
                vector_memory.add_to_memory(encounter_summary, metadata={
                    "patient_name": patient,
                    "doctor_name": doc_name,
                    "slot_id": slot_id,
                    "department": dept,
                })

        # -------------------------------------------------------------
        # 7. CONVERSATIONAL RESPONSE GENERATION
        # -------------------------------------------------------------
        response = self.response_agent.generate(schema, action_plan, last_user_input=user_input_clean)
        if not response:
            response = "Your request has been processed. Is there anything else I can help you with?"

        # -------------------------------------------------------------
        # 8. OUTPUT GUARDRAIL FILTER
        # -------------------------------------------------------------
        out_safe, _ = check_safety(self.guard_model, self.config_data, response, slm_engine=self.slm_engine)
        if not out_safe:
            response = "I apologize, but I must provide safe health assistance. Please consult a licensed physician."

        return response, schema


def parse_args():
    parser = argparse.ArgumentParser(description="HealthOS Master Medical System")
    parser.add_argument("-configfile", default="config.json", help="Path to config JSON file")
    parser.add_argument("-config", default="BioMedLM_CONFIG", help="Model configuration name")
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    return parser.parse_args()


def main():
<<<<<<< HEAD

    args = parse_args()

    config_data = load_config(args.configfile)

    slm, model_config = load_slm(config_data, args.config)

    print("\n🩺 Offline Medical Assistance Chatbot")
    print("Type your health-related question.")
    print("Commands: 'exit', 'quit', 'reset'\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            print("\nChatbot: Take care!")
            break

        if user_input.lower() == "reset":
            print("\nChatbot: Conversation reset. Memory is retained.\n")
            continue

        response = generate_response(slm, model_config, user_input)

        print("\nChatbot:", response, "\n")
=======
    args = parse_args()
    config_data = load_config(args.configfile)

    pipeline = HealthOSPipeline(config_data, model_name=args.config)
    schema = create_empty_schema()

    print("=" * 70)
    print("🩺 HealthOS: Agentic Medical Appointment & Triage System")
    print("Type your symptoms, medical concerns, or booking request.")
    print("Commands: 'reset' to start over, 'schema' to view state, 'exit' to quit.")
    print("=" * 70 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nHealthOS: Take care! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("\nHealthOS: Take care! 👋")
            break
        if user_input.lower() == "reset":
            schema = create_empty_schema()
            print("\nHealthOS: Conversation state reset. Medical memory is retained.\n")
            continue
        if user_input.lower() == "schema":
            print_schema(schema)
            continue

        response, schema = pipeline.process_turn(user_input, schema)
        print(f"\nHealthOS:\n{response}\n")
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)


if __name__ == "__main__":
    main()
