# HealthKart 
---

## Project Structure
```bash

HEALTHOS/
│
├── models/
│     ├── BioMedLM-7B.Q4_K_M.gguf
│     └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
│
├── vector_db/
│     ├──__init__.py
│     └── vector_memory.py
│
├── tests
│     └── medical_chatbot.py
│
├── agents
│     ├── guardrail_agent.py
│     ├── greeter_agent.py
│     ├── README.md
│     └── usecases
│            └── conversation.jsonl
│
├── slotbooking
│     └── ThirdPartyAPIs
│              ├── synthetic_data
│              │       ├──doctors.json
│              │       └── slots.json
│              │
│              └── booking_system
│                       └── booking_service.py
├── model_evaluation
│     ├── results
│     │      ├── BioMedLM_CONFIG_20260318_111418.json
│     │      └── TinyLlama_CONFIG_20260318_111708.json
│     ├── judge.py
│     ├── main.py
│     ├── questions.py
│     ├── models.py
│     └── README.md
│
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
git clone https://github.com/sujithvaishnav/healthos.git
```

### 2. Navigate to the project directory
```bash
cd healthos
```

### 3. Environment Creation and activation
```bash
python -m venv env
env\Scripts\activate
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

Run the chatbot by specifying the configuration file and the model configuration name.

```bash
python main.py -configfile config.json -config BioMedLM_CONFIG
```

### Parameters

- **-configfile** → Path to the JSON configuration file containing model settings.
- **-config** → The specific model configuration key inside the config file.

### Example

Run the chatbot using the TinyLlama configuration:

```bash
python main.py -configfile config.json -config TinyLlama_CONFIG
```

## Perfect get medical recommendation from bot ✅
---

