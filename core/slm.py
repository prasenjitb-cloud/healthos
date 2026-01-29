import llama_cpp
import prompts
import json

def load_slm():
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.2,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )


def analyze_symptoms(llm, symptoms: str) -> dict:
    prompt = prompts.SYSTEM_PROMPT.format(symptoms=symptoms)

    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    content = response["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except Exception:
        return {
            "description": "Symptoms may be related to a general medical condition.",
            "specialization": "General Medicine"
        }

