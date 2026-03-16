import argparse
import json
import llama_cpp
import transformers


def load_config(config_file):
    with open(config_file, "r") as f:
        return json.load(f)


def load_slm(config_data, model_name):

    if model_name not in config_data:
        raise ValueError(f"Config '{model_name}' not found")

    model_config = config_data[model_name]

    slm = llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"]
    )

    return slm, model_config


def load_guard_model(config_data):

    guard_config = config_data["guard_model"]

    return transformers.pipeline(
        "text-classification",
        model=guard_config["model_name"]
    )


def generate_response(slm, model_config, prompt: str):

    output = slm(
        prompt,
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        stop=model_config.get("stop", ["</s>"])
    )

    return output["choices"][0]["text"].strip()


def check_safety(guard_model, config_data, text: str):

    threshold = config_data["guard_model"]["threshold"]

    result = guard_model(text)[0]

    if result["label"] == "toxic" and result["score"] > threshold:
        return False, result["score"]

    return True, result["score"]


def safe_chat_flow(slm, guard_model, config_data, model_config, user_query: str):

    max_retries = config_data["safety"]["max_retries"]

    input_safe, input_score = check_safety(guard_model, config_data, user_query)

    if not input_safe:
        print(f"BLOCKED | User input toxicity: {input_score:.2f}")
        return "I cannot assist with harmful or abusive requests."

    print(f"Input PASS | Score: {input_score:.2f}")

    current_prompt = user_query

    for attempt in range(max_retries + 1):

        print(f"\n--- Attempt {attempt + 1}: Generating Response ---")

        response = generate_response(slm, model_config, current_prompt)

        print("Generated:", response)

        is_safe, score = check_safety(guard_model, config_data, response)

        if is_safe:
            print(f"PASS | Output Toxicity Score: {score:.2f}")
            return response

        else:

            print(f"FAIL | Toxicity Detected ({score:.2f})")

            if attempt < max_retries:
                current_prompt = (
                    "Rewrite the following text in a professional and safe manner:\n\n"
                    f"{response}"
                )
            else:
                return "I'm sorry, I cannot provide a safe answer after multiple attempts."


def parse_args():

    parser = argparse.ArgumentParser(description="Safe Local Chatbot")

    parser.add_argument(
        "-configfile",
        required=True,
        help="Path to config JSON file"
    )

    parser.add_argument(
        "-config",
        required=True,
        help="Model configuration name"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    config_data = load_config(args.configfile)

    slm, model_config = load_slm(config_data, args.config)

    guard_model = load_guard_model(config_data)

    print("\n🛡️ Safe Local Chatbot")
    print("Type your question.")
    print("Commands: 'exit', 'quit'\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            print("\nChatbot: Stay safe!")
            break

        final_output = safe_chat_flow(
            slm,
            guard_model,
            config_data,
            model_config,
            user_input
        )

        print("\nChatbot:", final_output, "\n")


if __name__ == "__main__":
    main()
