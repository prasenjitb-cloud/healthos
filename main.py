from core.model_loader import load_tinyllama
from core.chatbot import generate_response

def main():
    init_memory()
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
