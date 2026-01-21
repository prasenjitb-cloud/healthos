import core.chatbot
import vector_db.vector_memory
import llama_cpp

def load_tinyllama():
  
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.3,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )

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

        response = core.chatbot.generate_response(llm, user_input)
        print("\nChatbot:", response, "\n")

if __name__ == "__main__":
    main()
