# HealthOS
---

## Project Structure
```bash

HEALTHOS/
│
├── .streamlit/
│     └── config.toml
│
├── models/
│     ├── BioMedLM-7B.Q4_K_M.gguf
│     └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
│
├── vector_db/
│     ├── __init__.py
│     └── vector_memory.py
│
├── slotbooking/
│     └── ThirdPartyAPIs/
│              ├── README.md
│              ├── synthetic_data/
│              │       ├── doctors.json
│              │       └── slots.json
│              │
│              └── booking_system/
│                       └── booking_service.py
│
├── model_evaluation/
│     ├── results/
│     │      ├── BioMedLM_CONFIG_*.json
│     │      └── TinyLlama_CONFIG_*.json
│     ├── judge.py
│     ├── main.py
│     ├── models.py
│     ├── testdata.json
│     └── README.md
│
├── agents/
│     ├── booking_connector.py
│     ├── demo_scenarios.py
│     ├── dependency_engine.py
│     ├── greeter_agent.py
│     ├── guardrail_agent.py
│     ├── response_generator_agent.py
│     ├── run_custom_pipeline.py
│     ├── slm_engine.py
│     ├── state_schema.py
│     ├── task_definitions.py
│     ├── task_resolver.py
│     ├── README.md
│     └── usecases/
│            └── conversations.jsonl
│
├── tests/
│     └── medical_chatbot.py
│
├── app.py
├── demo.py
├── main.py
├── prompts.py
├── config.json
├── requirements.txt
└── README.md

```
---

## Getting Started

### Prerequisites

- **Python 3.12.1**  
- **pip** (or any Python package manager)

---

## Installation and ENV Setup

### 1. Clone the repository
```bash
git clone https://github.com/prasenjitb-cloud/healthos.git
```

### 2. Navigate to the project directory
```bash
cd healthos
```

### 3. Environment Creation and activation
```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux / macOS
python3 -m venv env
source env/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Model Setup

- Step 1: Download Models from Hugging Face 🔗 **Model download link**: [BioMedLM](https://huggingface.co/mradermacher/BioMedLM-7B-GGUF/resolve/main/BioMedLM-7B.Q4_K_M.gguf) and [Tinyllama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf)

- Step 2: Place the model in 'models'
```bash
models/
    ├── BioMedLM-7B.Q4_K_M.gguf
    └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```
---

## How to Run

### 1. Master Demonstration Suite (Recommended)
Run the all-in-one terminal menu to launch the web portal, interactive terminal chat, automated clinical scenario simulations, or guardrail tests:
```bash
python demo.py
```

### 2. Streamlit Web Consultation Portal
Launch the visual web application featuring real-time conversational triage, live dynamic state schema tracking, and clinical audit cards:
```bash
streamlit run app.py
```

### 3. Terminal Interactive Consultation (Master Pipeline)
Run the conversational medical triage and booking system directly via `main.py`:

```bash
python main.py -configfile config.json -config BioMedLM_CONFIG
```

#### Parameters

- **-configfile** → Path to the JSON configuration file containing model settings (defaults to `config.json`).
- **-config** → The specific model configuration key inside the config file (`BioMedLM_CONFIG` or `TinyLlama_CONFIG`).

#### Example

Run the chatbot using the lightweight TinyLlama configuration:

```bash
python main.py -configfile config.json -config TinyLlama_CONFIG
```

### 4. Agentic Workflow Simulations & Custom Pipeline Testing

```bash
# Interactive multi-turn CLI agent demo
python agents/demo_scenarios.py -i

# Automated walkthrough of core booking scenarios (1 to 4)
python agents/demo_scenarios.py

# Custom multi-turn input evaluation via CLI
python agents/run_custom_pipeline.py "I want to see a cardiologist" "1" "1"
```

## Perfect get medical recommendation from bot ✅
---
