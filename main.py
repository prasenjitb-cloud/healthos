import json
import llama_cpp
import prompts as local_prompts


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def load_slm(model_name):

    config = load_config()
    model_config = config[model_name]

    slm = llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"]
    )

    return slm, model_config


def generate_response(slm, model_config, user_input):

    messages = [
        {"role": "system", "content": local_prompts.SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    response = slm.create_chat_completion(
        messages=messages,
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        max_tokens=model_config["max_tokens"]
    )

    reply = response["choices"][0]["message"]["content"]

    return reply


def main():

    slm, model_config = load_slm("BioMedLM_CONFIG")

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

        response = generate_response(slm, model_config, user_input)

        print("\nChatbot:", response, "\n")


if __name__ == "__main__":
    main()
