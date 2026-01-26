import vector_db.vector_memory
import llama_cpp
import prompts

def load_tinyllama():
  
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.3,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )

def generate_response(llm, user_input: str) -> str:
    """
    Generate chatbot response using SLM and vector memory.
    """
    past_info = vector_db.vector_memory.search_memory(user_input)

    memory_context = ""
    if past_info:
        memory_context = "Relevant past health information:\n"
        for info in past_info:
            memory_context += f"- {info}\n"

    messages = [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {"role": "system", "content": memory_context},
        {"role": "user", "content": user_input}
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]

    if len(user_input.split()) > 3:
        vector_db.vector_memory.add_to_memory(user_input)

    return reply

def main():
    vector_db.vector_memory.init_memory()
    llm = load_tinyllama()

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

        response = generate_response(llm, user_input)
        print("\nChatbot:", response, "\n")

if __name__ == "__main__":
    main()
