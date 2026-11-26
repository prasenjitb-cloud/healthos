# HealthOS — Agentic Routing & Dynamic State System

---

## Project Structure

```bash
agents/
├── booking_connector.py        # Real doctor/slot lookups, name normalization & atomic booking
├── demo_scenarios.py           # Automated walkthroughs (Scenarios 1-5) & interactive terminal mode
├── dependency_engine.py        # Next-action workflow controller (ASK_USER / RUN_SYSTEM / COMPLETE)
├── greeter_agent.py            # Intent detection & LangGraph routing agent
├── guardrail_agent.py          # Safety guardrails (ToxicBERT & harmful intent interception)
├── observability.py            # LangSmith LLMOps tracing & clinical explainability bridge
├── response_generator_agent.py # Context-aware response generator & options formatter
├── run_custom_pipeline.py      # Multi-turn CLI tester & pure SLM decision execution pipeline
├── slm_engine.py               # Local SLM decision engine (intent, extraction, department & ambiguity)
├── state_schema.py             # DynamicSchema (TypedDict), safe merge & clinical audit cards
├── task_definitions.py         # Task enums, dependency chains & derived generators
├── task_resolver.py            # Intent + extracted entities → Task resolution
├── README.md                   # Agent module documentation
└── usecases/
    └── conversations.jsonl     # Benchmark conversation flows
```

---

## Overview

This module implements the **Dynamic Data Dependency & Agentic Workflow Engine** for HealthOS.

It drives chat-based appointment bookings bottom-up across core clinical workflows, backed by safety guardrails, emergency detection, real synthetic slot booking, and local Small Language Model (SLM) decision-making with zero hardcoded keyword heuristics.

### The Core Booking Scenarios

1. **Direct Doctor Booking**
   - *User Situation:* Knows the specific doctor they want to see (and optionally department).
   - *Workflow:* Extracts doctor name $\rightarrow$ collects date and time slot $\rightarrow$ executes slot booking.
2. **Department Booking**
   - *User Situation:* Knows the medical department/specialization, but not the specific doctor.
   - *Workflow:* Captures department $\rightarrow$ lists available doctors $\rightarrow$ collects doctor choice, date, and slot $\rightarrow$ completes booking.
3. **Symptom-Based Booking**
   - *User Situation:* Unaware of department or doctor, only knows symptoms.
   - *Workflow:* Collects symptoms $\rightarrow$ runs SLM `department_classifier` $\rightarrow$ suggests department & lists doctors $\rightarrow$ collects slot $\rightarrow$ completes booking.
4. **End-to-End Real Booking with Atomic Confirmation**
   - *User Situation:* Selects doctors and slots dynamically from real synthetic databases.
   - *Workflow:* Validates doctor availability $\rightarrow$ retrieves open slots $\rightarrow$ marks slot booked in `slots.json` $\rightarrow$ generates confirmation.
5. **Ambiguity Handling & General Medicine Indecision Fallback**
   - *User Situation:* Symptoms are multi-system or vague (e.g., general fatigue and body aches).
   - *Workflow:* SLM detects ambiguity $\rightarrow$ prompts user for preferred department $\rightarrow$ if user is undecided, safely routes to General Medicine.
6. **Emergency Override**
   - Immediate safety override for critical symptoms (e.g., severe chest pain, shortness of breath), routing to emergency guidance without booking delays.

---

## Architecture Flow

```
User Message
    │
    ▼
Guardrail Agent (ToxicBERT Safety & Harm Interception)
    │
    ▼
SLM Engine / Greeter Agent (Intent Classification & Entity Extraction)
    │
    ▼
Task Resolver (agents/task_resolver.py)
    │  - Evaluates extracted entities & greeter intent
    │  - Selects Task: DIRECT_BOOKING | DEPARTMENT_BOOKING | SYMPTOM_BASED_BOOKING | EMERGENCY
    ▼
Dynamic State Schema (agents/state_schema.py)
    │  - Maintains conversation state across multi-turn sessions
    │  - Non-destructive updates: None never overwrites existing clinical data
    │  - Tracks missing fields, task completeness & clinical audit trail
    ▼
Dependency Engine (agents/dependency_engine.py)
    │  - Walks TASK_DEPENDENCIES in order
    │  - Emits next action:
    │      • ASK_USER: User must provide next required field
    │      • RUN_SYSTEM: System generator triggered (e.g., DepartmentClassifier)
    │      • COMPLETE: All dependencies satisfied, ready for slot booking
    │      • EMERGENCY: Routes immediately to emergency protocol
    ▼
Booking Connector & Response Generator (agents/response_generator_agent.py)
    │  - In-memory indexed synthetic doctors & open slots
    │  - Formats options and generates empathetic, fact-verified responses
    ▼
Confirmed Booking / Output to User
```

---

## Core Modules

### 1. `task_definitions.py`
Defines supported tasks, ordered dependency sequences, and derived generator mappings:
- **`Task` Enum:** `DIRECT_BOOKING`, `DEPARTMENT_BOOKING`, `SYMPTOM_BASED_BOOKING`, `EMERGENCY`.
- **`TASK_DEPENDENCIES`:**
  - `direct_booking`: `["doctor_name", "date", "time_slot"]`
  - `department_booking`: `["department", "doctor_name", "date", "time_slot"]`
  - `symptom_based_booking`: `["symptoms", "department", "doctor_name", "date", "time_slot"]`
- **`DERIVED_DEPENDENCIES`:** Identifies system-computed fields (e.g., `department` in symptom flow generated by `department_classifier`).

### 2. `state_schema.py`
Central dictionary-based conversation state (`DynamicSchema` using `TypedDict`):
- **Sections:**
  - `symptom_section`: `symptoms` (list of strings), `severity`.
  - `department_section`: `department`, `source`, `confidence`, `is_ambiguous`.
  - `booking_section`: `doctor_name`, `date`, `time_slot`, `hospital`, `doctor_valid`, `doctor_candidates`, `selected_slot`, `booking_confirmed`.
- **Key Functions:**
  - `create_empty_schema()`: Initializes blank state.
  - `merge_schema_update(current, update)`: Merges new extractions without overwriting existing data with `None`. Automatically normalizes and deduplicates symptoms.
  - `format_clinical_audit(schema)`: Formats a structured explainability audit card for medical reviewers.
  - `is_schema_complete(schema)`: Returns `True` when all required fields for the task are satisfied.
  - `get_missing_fields(schema)`: Returns ordered list of remaining required fields.

### 3. `task_resolver.py`
Determines which workflow task should handle the session:
- **Resolution Priority:**
  1. `emergency` (Intent or emergency condition detected)
  2. `direct_booking` (`doctor_name` present)
  3. `department_booking` (`department` present)
  4. `symptom_based_booking` (`symptoms` present)
  5. Fallback from greeter intent (`"triage"` / `"symptom_guidance"` $\rightarrow$ symptom booking; `"booking"` $\rightarrow$ direct booking)

### 4. `dependency_engine.py`
Evaluates the current state against task dependencies to determine the exact next action:
- `ASK_USER`: When user-supplied information is needed (e.g., date, doctor choice).
- `RUN_SYSTEM`: When a system generator is required (e.g., department classification).
- `COMPLETE`: When all dependencies for the selected task are satisfied.
- `EMERGENCY`: When an emergency state is active.
- `update_schema_state(schema)`: Automatically updates `schema["current_dependency"]` and `schema["stage"]`.

### 5. `booking_connector.py`
Integration layer with synthetic clinical databases (`doctors.json` and `slots.json`):
- In-memory indexed data lookups for doctors and appointment slots.
- Name normalization and fuzzy/token-based doctor resolution.
- Flexible slot resolution (1-based index or 12h/24h time matching).
- Real atomic booking execution.

### 6. `response_generator_agent.py`
Generates human-like, context-aware responses when schema sections are missing:
- Presents numbered doctor and slot choices from real synthetic data.
- Handles invalid input clarification and reprompting.
- Confirms bookings upon dependency satisfaction.

### 7. `slm_engine.py`
Pure SLM decision engine eliminating keyword heuristics:
- Semantic intent classification (Emergency vs Booking vs Triage).
- Entity extraction (`symptoms`, `doctor_name`, `department`, `date`, `time_slot`).
- Symptom-to-department classification with ambiguity detection.
- Indecision detection (routes to General Medicine when patient cannot choose).

### 8. `guardrail_agent.py`
Safety guardrail powered by `unitary/toxic-bert` with pattern fallback:
- Evaluates incoming patient utterances for toxicity, harassment, and severe harm requests.
- Halts execution and displays safe emergency rejection message if toxicity threshold is breached.

### 9. `greeter_agent.py`
Intent detection and initial conversational routing agent powered by LangGraph and local SLM (`llama.cpp`).

### 10. `observability.py`
LangSmith clinical observability and LLMOps tracing bridge:
- Transparent execution tracing for guardrail confidence, SLM extraction, triage ambiguity, and dependency transitions.
- Exports structured Clinical Triage Audit Cards (`format_clinical_audit`) as run metadata for physician inspection.
- Zero-latency offline fallback when unconfigured.

---

## Verification & Testing

### Running the Live Demos & Testing Custom Inputs

There are three ways to test and run the HealthOS Agent Pipeline:

#### 1. Test with Your Own Custom Inputs (CLI Arguments)
Pass any sequence of user turns as command-line arguments to test how the pipeline handles them:

```bash
# Example 1: Direct department booking with slot selection
python agents/run_custom_pipeline.py "I want to see a cardiologist" "1" "1"

# Example 2: Ambiguity detection & indecision fallback to General Medicine
python agents/run_custom_pipeline.py "I feel tired and have mild nausea with joint discomfort" "I am not sure" "1" "1"

# Example 3: Symptom triage flow
python agents/run_custom_pipeline.py "I have severe chest pain"
```

#### 2. Live Interactive Terminal Demo (Chat Mode)
Launch an interactive terminal session where you can chat turn-by-turn with the agent, test edge cases, pick doctors, and confirm real slots:

```bash
python agents/demo_scenarios.py -i
# or
python agents/run_custom_pipeline.py -i
```
*(Special commands during chat: type `reset` to clear schema and restart, `exit` to quit)*

#### 3. Automated Walkthrough (Scenarios 1–5)
Runs a turn-by-turn simulation of all five clinical booking and fallback scenarios (including real booking execution):

```bash
python agents/demo_scenarios.py
```

---

### Running the LangGraph Chat Agent (`greeter_agent.py`)
To run the interactive LangGraph greeter agent with the local SLM:

```bash
# From repository root
python agents/greeter_agent.py -configfile config.json -config BioMedLM_CONFIG

# Or with TinyLlama:
python agents/greeter_agent.py -configfile config.json -config TinyLlama_CONFIG
```
