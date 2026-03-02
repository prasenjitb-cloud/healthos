import llama_cpp
import transformers

def load_slm():
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        n_threads=4,
        verbose=False
    )


def load_guard_model():
    return transformers.pipeline(
        "text-classification",
        model="unitary/toxic-bert"
    )

def generate_response(slm, prompt: str) -> str:
    output = slm(
        prompt,
        max_tokens=256,
        temperature=0.7,
        top_p=0.9,
        stop=["</s>"]
    )

    return output["choices"][0]["text"].strip()


def check_safety(guard_model, text: str, threshold: float = 0.6):
    result = guard_model(text)[0]

    if result["label"] == "toxic" and result["score"] > threshold:
        return False, result["score"]

    return True, result["score"]


def safe_chat_flow(slm, guard_model, user_query: str, max_retries: int = 2):

    # ----- Input Safety -----
    input_safe, input_score = check_safety(guard_model, user_query)

    if not input_safe:
        print(f"BLOCKED | User input toxicity: {input_score:.2f}")
        return "I cannot assist with harmful or abusive requests."

    print(f"Input PASS | Score: {input_score:.2f}")

    current_prompt = user_query

    for attempt in range(max_retries + 1):

        print(f"\n--- Attempt {attempt + 1}: Generating Response ---")

        response = generate_response(slm, current_prompt)
        print("Generated:", response)

        is_safe, score = check_safety(guard_model, response)

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


def main():

    slm = load_slm()
    guard_model = load_guard_model()

    print("\n🛡️ Safe Local Chatbot")
    print("Type your question.")
    print("Commands: 'exit', 'quit'\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            print("\nChatbot: Stay safe!)
            break

        final_output = safe_chat_flow(slm, guard_model, user_input)

        print("\nChatbot:", final_output, "\n")


if __name__ == "__main__":
    main()
