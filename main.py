import json
import llama_cpp
import prompts as local_prompts


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def load_slm(model_name="BioMedLM_CONFIG"):
    config = load_config()
    model_config = config[model_name]

    return llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"],
        temperature=0.3,
        top_p=0.9
    )


def generate_response(slm, user_input: str) -> str:

    messages = [
        {"role": "system", "content": local_prompts.SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    response = slm.create_chat_completion(
        messages=messages,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]

    return reply


def main():

    slm = load_slm("BioMedLM_CONFIG")

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
