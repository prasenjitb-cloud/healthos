# Model Evaluation – Medical SLM Benchmark

---

## Project Structure
```bash
Model_Evaluation/
├── main.py
├── judge.py
├── models.py
├── testdata.json
└── README.md
```

---

## Project Overview

This module provides a **local evaluation framework for comparing Small Language Models (SLMs)** on **medical question answering tasks**.

Two models are evaluated:

- **BioMedLM (7B)**
- **TinyLlama (1.1B)**

A **judge model (Llama-3.1-8B via Groq API)** evaluates the responses produced by both models using several quality metrics.

The system:

1. Loads medical questions from a dataset.
2. Generates answers using both models.
3. Sends the results to a judge LLM.
4. Scores the responses.
5. Calculates average performance for each model.

---

## Dataset Format

### `testdata.json`

Each entry in the dataset contains:

```json
{
  "question": "What causes hypertension?",
  "answer": "Hypertension can be caused by genetics, high salt intake, obesity, stress, and underlying medical conditions."
}
```

Fields:

| Field | Description |
|------|-------------|
| `question` | Medical question to evaluate |
| `answer` | Reference answer used for judging |

---

## Evaluation Metrics

Each model response is scored from **1 to 5** on the following metrics:

### 1. Accuracy
Measures whether the medical information is correct.

### 2. Reasoning
Evaluates the logical explanation and understanding of the medical topic.

### 3. Completeness
Checks whether the answer fully addresses the question.

### 4. Safety
Ensures the response does not contain harmful or misleading medical advice.

Final score calculation:

```bash
score = (accuracy + reasoning + safety + completeness) / 4
```

---

## Available Functions

### 1. `run_models(question: str)`

Generates responses from both models.

```python
biomed_answer, tiny_answer = run_models(question)
```

---

### 2. `generate_answer(model, question)`

Creates an answer from a given model using a biomedical prompt.

```python
response = generate_answer(model, question)
```

---

### 3. `judge(question, reference, answer_a, answer_b)`

Evaluates the two answers using a **Groq LLM judge**.

```python
result = judge(question, reference, answer_a, answer_b)
```

Returns:

```json
{
  "model_a": {
    "accuracy": 4,
    "reasoning": 4,
    "completeness": 4,
    "safety": 5
  },
  "model_b": {
    "accuracy": 2,
    "reasoning": 2,
    "completeness": 3,
    "safety": 3
  },
  "winner": "A"
}
```

---

## Usage Example

Run the evaluation:

```bash
python main.py
```

Example output:

```bash
QUESTION: What causes hypertension?

BioMedLM: Hypertension can occur due to genetic factors, high sodium intake and obesity.
TinyLlama: High blood pressure happens when blood pushes too strongly against artery walls.

JUDGE RAW OUTPUT:
{
 "model_a": {...},
 "model_b": {...},
 "winner": "A"
}
```

Final results:

```bash
FINAL RESULTS

BioMedLM Average: 4.1
TinyLlama Average: 3.0

BioMedLM performs better in medical context
```

---

## Models Used

### BioMedLM
Biomedical specialized language model used for medical reasoning.

### TinyLlama
Lightweight general-purpose language model used for comparison.

### Judge Model
The evaluation uses **Groq Llama-3.1-8B** as an automated evaluator.

---

## Environment Setup

The judge model requires a **Groq API key**.

Create a `.env` file:

```bash
GROQ_API_KEY=your_api_key_here
```

Install dependencies:

```bash
pip install llama-cpp-python langchain langchain-groq python-dotenv
```

---

## Evaluation Workflow

```bash
testdata.json
      │
      ▼
run_models()
      │
      ▼
generate_answer()
      │
      ▼
judge()
      │
      ▼
compute_score()
      │
      ▼
final comparison
```
