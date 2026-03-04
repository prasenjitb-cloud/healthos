# HealthKart 
---

## Project Structure
```bash

HEALTHOS/
│
├── models/
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
│
├── main.py
├── prompts.py
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

- Step 1: Download Model from Hugging Face 🔗 **Model download link**: [Tinyllama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf)


- Step 2: Place the model in 'models'
```bash
models/
└── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```
---

## How to RUN
```bash
python main.py
```

## Perfect get medical recommendation from bot ✅
---

