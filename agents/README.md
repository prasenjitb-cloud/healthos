# HealthOS – Agentic Routing System
---

## Project Structure
```bash

agents/
├── greeter_agent.py
└── guardrail_agent.py
```
---

## Overview

This module contains the core Agentic Workflow Engine for HealthOS.

It is responsible for:

Intent classification

- Emergency detection

- Medical triage routing

- Booking intent handling

- Agent graph execution using LangGraph

The system uses:

- Local LLM (TinyLLaMA via llama.cpp)

- Rule-based overrides for emergencies

- JSON-based doctor specialization mapping

- Conditional graph routing

---

## Agent Flow Architecture

```
User Input
    ↓
Gaurdrail Agent
    ↓
Greeter Agent (Intent Detection)
    ↓
 ┌──────────────┬──────────────┬──────────────┐
 │    Triage    │    Booking   │  Emergency   │
 └──────────────┴──────────────┴──────────────┘
    ↓
Final Response
```

---

## Agents
### 1. `greeter_agent(state)`
Responsible for:

- Detecting emergency keywords

- Detecting booking-related keywords

- Using LLM fallback classification for triage cases

- Routing to appropriate downstream agent

Supported Intents:

- `"emergency"`

- `"triage"`

- `"booking"`

---

### 2. `triage_agent(state)`

Responsible for:

- Uses LLM to predict ONE medical specialization

- Matches prediction with doctors.json

- Returns:

  - Specialist

  - Doctor Name

  - Hospital

  - Location

- Defaults to General Medicine if no match found.

---

### 3. `booking_agent(state)`

Handles booking requests.

```
"Booking: Please tell me which specialist you want to book."
```

Can be extended to connect with Slot Booking API.

---

### 4. `emergency_node(state)`

Triggered by rule-based emergency detection.

Returns:
```
"EMERGENCY: Please go to the nearest emergency room immediately."
```
Emergency intent overrides all other logic.

---

## Test Cases

```
"I have severe chest pain"
→ Emergency

"I have headaches and dizziness"
→ Triage → Neurology

"I want to book an appointment"
→ Booking

"My knees hurt and feel stiff"
→ Triage → Orthopedics
```


---

