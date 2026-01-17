from llama_cpp import Llama
from vector_memory import add_to_memory, search_memory

SYSTEM_PROMPT = """
You are a medical assistance chatbot.

Rules:
- Provide general medical information and health education only.
- Do NOT diagnose diseases.
- Do NOT prescribe medications or treatments.
- Do NOT handle emergencies.
- Always encourage consulting a qualified healthcare professional.
- You may use previously mentioned health information for context,
  but must not draw medical conclusions.
- Responses must be clear, cautious, and medically relevant.
"""

llm = Llama(
    model_path="models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_ctx=4096,
    temperature=0.2,
    top_p=0.9,
    n_threads=8,
    verbose=False
)

def chatbot(user_input):
    past_info = search_memory(user_input)

    memory_context = ""
    if past_info:
        memory_context = "Relevant past health information:\n"
        for info in past_info:
            memory_context += f"- {info}\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": memory_context},
        {"role": "user", "content": user_input}
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]

    if len(user_input.split()) > 3:
        add_to_memory(user_input)

    return reply

print("\n🩺 Offline Medical Assistance Chatbot")
print("Type your health-related question.")
print("Commands: 'exit', 'quit', 'reset'\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nChatbot: Take care! Always consult a healthcare professional when needed.")
        break

    if user_input.lower() == "reset":
        print("\nChatbot: Conversation reset. Memory is retained.\n")
        continue

    response = chatbot(user_input)
    print("\nChatbot:", response, "\n")
