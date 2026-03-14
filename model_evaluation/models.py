import llama_cpp

print("Loading models...")

biomed_model = llama_cpp.Llama(
        model_path="../models/BioMedLM-7B.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.2,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )

tiny_model = llama_cpp.Llama(
        model_path="../models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.2,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )


def generate_answer(model, question):

    prompt = f"""
### System
You are a biomedical expert assistant.

Your task:
- Answer medical questions accurately.
- Use biomedical knowledge.
- Respond in 1 sentences.
- Do NOT repeat the question.

### Question
{question}

### Answer
"""

    result = model(
        prompt,
        max_tokens=120,
        temperature=0.2,
        top_p=0.9,
        stop=["###"]
    )

    text = result["choices"][0]["text"].strip()

    if text == "":
        text = "No response generated"

    return text

def run_models(question):

    biomed = generate_answer(biomed_model, question)
    tiny = generate_answer(tiny_model, question)

    return biomed, tiny