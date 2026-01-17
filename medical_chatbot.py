from llama_cpp import Llama

SYSTEM_PROMPT = """
You are a medical assistance chatbot designed strictly for academic use.

Rules:
- Provide general medical information and health education only.
- Do NOT diagnose diseases.
- Do NOT prescribe medications or treatments.
- Do NOT handle medical emergencies.
- Always encourage consulting a qualified healthcare professional.
- Ask relevant follow-up questions when helpful.
- Keep responses clear, cautious, and medically relevant.
"""

llm = Llama(
    model_path="models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_ctx=4096,
    temperature=0.2,
    top_p=0.9,
    n_threads=8,
    verbose=False
)

chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def chatbot(user_input):
    chat_history.append({"role": "user", "content": user_input})

    response = llm.create_chat_completion(
        messages=chat_history,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]
    chat_history.append({"role": "assistant", "content": reply})

    return reply

print("\n🩺 Medical Assistance Chatbot (Offline)")
print("Type your question below.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nChatbot: Take care! Always consult a healthcare professional if needed.")
        break

    response = chatbot(user_input)
    print("\nChatbot:", response, "\n")
