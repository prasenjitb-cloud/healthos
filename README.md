# HealthKart 
---

## Getting Started

### Prerequisites


- **Python 3.12.1**  
- **pip** (or any Python package manager)

---

## Local SLM Setup
```bash
models/
└── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

core/
└── chatbot.py

vector_db/
└── vector_memory.py

main.py
prompts.py
requirements.txt
medical_chatbot.py   # test file
```
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
---

## Local SLM Setup

The project currently uses a Small Language Model (SLM) for offline inference.

Model Used

- TinyLLaMA (1.1B, quantized GGUF)

- Loaded via llama.cpp

- Runs entirely on CPU

### Step 1: Download the model from HuggingFace

🔗 **Model download link**: [Tinyllama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf)

---

### Step 2: Place the model in
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


