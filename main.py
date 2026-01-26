import llama_cpp
import vector_db as local_vector_db
import prompts as local_prompts

def load_slm():
  
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.3,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )

def generate_response(slm, user_input: str) -> str:
    """
    Generate chatbot response using SLM and vector memory.
    """
    past_info = local_vector_db.search(user_input)

    memory_context = ""
    if past_info:
        memory_context = "Relevant past health information:\n"
        for info in past_info:
            memory_context += f"- {info}\n"

    messages = [
        {"role": "system", "content": local_prompts.SYSTEM_PROMPT},
        {"role": "system", "content": memory_context},
        {"role": "user", "content": user_input}
    ]

    response = slm.create_chat_completion(
        messages=messages,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]

    if len(user_input.split()) > 3:
        local_vector_db.add(user_input)

    return reply

def main():
    local_vector_db.init()
    slm = load_slm()

    print("\n🩺 Offline Medical Assistance Chatbot")
    print("Type your health-related question.")
    print("Commands: 'exit', 'quit', 'reset'\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            print("\nChatbot: Take care!")
            break

        if user_input.lower() == "reset":
            print("\nChatbot: Conversation reset. Memory is retained.\n")
            continue

        response = generate_response(slm, user_input)
        print("\nChatbot:", response, "\n")

if __name__ == "__main__":
    main()
