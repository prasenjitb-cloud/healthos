import time
from llama_cpp import Llama

SYSTEM_PROMPT = """
You are a medical assistance chatbot designed strictly for academic evaluation.

Your role:
- Explain symptoms in a general, educational manner.
- Provide possible health-related explanations using common medical knowledge.
- Do NOT provide diagnoses.
- Do NOT prescribe medications or treatments.
- Do NOT suggest doctors or appointments.

Style:
- Calm, empathetic, structured
- Do NOT repeat rules or policies
"""

MODELS = {
    "tinyllama": {
        "path": "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "n_ctx": 2048
    },
    "llama31": {
        "path": "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "n_ctx": 4096
    }
}

MODEL_NAME = "tinyllama"   

model_cfg = MODELS[MODEL_NAME]

llm = Llama(
    model_path=model_cfg["path"],
    n_ctx=model_cfg["n_ctx"],
    temperature=0.3,
    top_p=0.9,
    n_threads=8,
    verbose=False
)

chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def chatbot(user_input):
    chat_history.append({"role": "user", "content": user_input})

    start_time = time.time()

    response = llm.create_chat_completion(
        messages=chat_history,
        max_tokens=300
    )

    end_time = time.time()

    reply = response["choices"][0]["message"]["content"]
    chat_history.append({"role": "assistant", "content": reply})

    # Metrics
    latency = round(end_time - start_time, 2)
    tokens_used = response["usage"]["total_tokens"]
    response_length = len(reply.split())

    return reply, latency, tokens_used, response_length


print(f"\n🩺 Offline Medical Chatbot — Model: {MODEL_NAME}")
print("Type your health-related question.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nChatbot: Session ended.\n")
        break

    reply, latency, tokens, length = chatbot(user_input)

    print("\nChatbot:", reply)
    print(f"\n[Metrics] Latency: {latency}s | Tokens: {tokens} | Words: {length}\n")
