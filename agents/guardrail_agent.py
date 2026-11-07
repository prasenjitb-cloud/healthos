<<<<<<< HEAD
import argparse
import json
import llama_cpp
import transformers


def load_config(config_file):
    with open(config_file, "r") as f:
        return json.load(f)


def load_slm(config_data, model_name):
=======
"""
guardrail_agent.py

Safety and toxicity guardrails for HealthOS.
Filters toxic, abusive, or harmful patient inputs and sanitized agent outputs.

Supports:
1. HuggingFace toxic-bert pipeline via transformers when available.
2. SLM safety evaluation via SLMEngine when transformers is not installed.
3. Safe fallback offline toxicity filtering.
"""

import os
import argparse
import json
from typing import Tuple, Optional, Any

try:
    import transformers
except ImportError:
    transformers = None


def load_config(config_file: str) -> dict:
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_slm(config_data: dict, model_name: str):
    import llama_cpp
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)

    if model_name not in config_data:
        raise ValueError(f"Config '{model_name}' not found")

    model_config = config_data[model_name]

    slm = llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
<<<<<<< HEAD
        verbose=model_config["verbose"]
=======
        verbose=model_config.get("verbose", False),
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    )

    return slm, model_config


<<<<<<< HEAD
def load_guard_model(config_data):

    guard_config = config_data["guard_model"]

    return transformers.pipeline(
        "text-classification",
        model=guard_config["model_name"]
    )


def generate_response(slm, model_config, prompt: str):

=======
def load_guard_model(config_data: dict):
    """
    Attempts to load the text-classification pipeline if transformers is installed.
    Returns None if transformers is not present.
    """
    if transformers is None:
        return None

    try:
        guard_config = config_data.get("guard_model", {})
        model_name = guard_config.get("model_name", "unitary/toxic-bert")
        try:
            return transformers.pipeline(
                "text-classification",
                model=model_name,
                local_files_only=True,
            )
        except Exception:
            return transformers.pipeline(
                "text-classification",
                model=model_name,
            )
    except Exception as e:
        print(f"[Guardrail] Warning: Could not initialize transformers pipeline: {e}")
        return None


def generate_response(slm, model_config, prompt: str):
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    output = slm(
        prompt,
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
<<<<<<< HEAD
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

=======
        stop=model_config.get("stop", ["</s>"]),
    )
    return output["choices"][0]["text"].strip()


def check_safety(guard_model, config_data: Any, text: str, slm_engine=None) -> Tuple[bool, float]:
    """
    Evaluates whether text is safe.
    Returns (is_safe: bool, toxicity_score: float).
    """
    if not text or not text.strip():
        return True, 0.0

    threshold = 0.6
    if isinstance(config_data, dict) and "guard_model" in config_data:
        threshold = config_data["guard_model"].get("threshold", 0.6)

    low = text.lower().strip()

    # 1. Fast-path deterministic safety & harm patterns (immediate zero-latency block)
    severe_patterns = [
        "kill someone",
        "how to kill",
        "kill people",
        "commit murder",
        "how to murder",
        "murder someone",
        "kill yourself",
        "commit suicide",
        "how to suicide",
        "how to make a bomb",
        "shoot someone",
        "poison someone",
        "die idiot",
        "stupid piece of shit",
        "fuck you",
        "hate you all",
        "go to hell",
    ]
    for pat in severe_patterns:
        if pat in low:
            return False, 0.98

    # 2. Transformers ToxicBERT pipeline if available (multi-head evaluation)
    if guard_model is not None:
        try:
            results = guard_model(text, top_k=None)
            items = results[0] if (results and isinstance(results[0], list)) else results
            for item in items:
                scr = float(item.get("score", 0.0))
                if scr > threshold:
                    return False, scr
            top_score = float(items[0].get("score", 0.0)) if items else 0.0
            return True, top_score
        except Exception:
            try:
                result = guard_model(text)[0]
                label = str(result.get("label", "")).lower()
                score = float(result.get("score", 0.0))
                if label == "toxic" and score > threshold:
                    return False, score
                return True, score
            except Exception:
                pass

    # 3. SLM evaluation if engine provided
    if slm_engine is not None and hasattr(slm_engine, "query_json"):
        try:
            system_prompt = (
                "You are HealthOS Safety Guardrail Classifier. "
                "Evaluate if the user message contains violence, threats, harm, hate speech, severe profanity, or abuse. "
                "Respond with strictly valid JSON only: {\"is_toxic\": bool, \"score\": float, \"reason\": string}."
            )
            user_prompt = (
                f"Evaluate if the following message contains severe profanity, hate speech, threats of violence, or abuse:\n"
                f"Message: \"{text}\"\n"
                f"Return JSON ONLY: {{\"is_toxic\": true or false, \"score\": float between 0.0 and 1.0}}"
            )

            # Check if model has raw LLM access for refusal detection
            if hasattr(slm_engine, "slm") and slm_engine.slm is not None:
                try:
                    res_raw = slm_engine.slm.create_chat_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=60,
                    )
                    content = res_raw["choices"][0]["message"]["content"].strip()

                    # Check for direct AI safety refusals (e.g., "violates ethical and moral standards")
                    refusal_markers = [
                        "violates ethical", "violates moral", "inappropriate", "illegal",
                        "harmful activities", "murder", "cannot provide information on illegal",
                        "violation of human rights"
                    ]
                    if any(marker in content.lower() for marker in refusal_markers):
                        return False, 0.99

                    parsed = slm_engine._parse_json_safe(content)
                    if parsed and "is_toxic" in parsed:
                        if parsed.get("is_toxic") and float(parsed.get("score", 0)) > threshold:
                            return False, float(parsed.get("score", 0.9))
                        return True, float(parsed.get("score", 0.0))
                except Exception:
                    pass

            res = slm_engine.query_json(user_prompt, system_prompt=system_prompt, max_tokens=50)
            if res and "is_toxic" in res:
                if res.get("is_toxic") and float(res.get("score", 0)) > threshold:
                    return False, float(res.get("score", 0.9))
                return True, float(res.get("score", 0.0))
        except Exception:
            pass

    return True, 0.0


def safe_chat_flow(slm, guard_model, config_data, model_config, user_query: str):
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    max_retries = 2

    input_safe, input_score = check_safety(guard_model, config_data, user_query)

    if not input_safe:
        print(f"BLOCKED | User input toxicity: {input_score:.2f}")
        return "I cannot assist with harmful or abusive requests."

    print(f"Input PASS | Score: {input_score:.2f}")

    current_prompt = user_query

    for attempt in range(max_retries + 1):
<<<<<<< HEAD

        print(f"\n--- Attempt {attempt + 1}: Generating Response ---")

        response = generate_response(slm, model_config, current_prompt)

=======
        print(f"\n--- Attempt {attempt + 1}: Generating Response ---")
        response = generate_response(slm, model_config, current_prompt)
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
        print("Generated:", response)

        is_safe, score = check_safety(guard_model, config_data, response)

        if is_safe:
            print(f"PASS | Output Toxicity Score: {score:.2f}")
            return response
<<<<<<< HEAD

        else:

            print(f"FAIL | Toxicity Detected ({score:.2f})")

=======
        else:
            print(f"FAIL | Toxicity Detected ({score:.2f})")
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
            if attempt < max_retries:
                current_prompt = (
                    "Rewrite the following text in a professional and safe manner:\n\n"
                    f"{response}"
                )
            else:
                return "I'm sorry, I cannot provide a safe answer after multiple attempts."


def parse_args():
<<<<<<< HEAD

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

=======
    parser = argparse.ArgumentParser(description="Safe Local Chatbot")
    parser.add_argument("-configfile", required=True, help="Path to config JSON file")
    parser.add_argument("-config", required=True, help="Model configuration name")
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
    return parser.parse_args()


def main():
<<<<<<< HEAD

    args = parse_args()

    config_data = load_config(args.configfile)

    slm, model_config = load_slm(config_data, args.config)

    guard_model = load_guard_model(config_data)

    print("\n🛡️ Safe Local Chatbot")
    print("Type your question.")
    print("Commands: 'exit', 'quit'\n")

    while True:

        user_input = input("You: ")

=======
    args = parse_args()
    config_data = load_config(args.configfile)
    slm, model_config = load_slm(config_data, args.config)
    guard_model = load_guard_model(config_data)

    print("\n🛡️ Safe Local Chatbot")
    print("Type your question. Commands: 'exit', 'quit'\n")

    while True:
        user_input = input("You: ")
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
        if user_input.lower() in ("exit", "quit"):
            print("\nChatbot: Stay safe!")
            break

<<<<<<< HEAD
        final_output = safe_chat_flow(
            slm,
            guard_model,
            config_data,
            model_config,
            user_input
        )

=======
        final_output = safe_chat_flow(slm, guard_model, config_data, model_config, user_input)
>>>>>>> d10637a (Backup: Complete local HealthOS implementation)
        print("\nChatbot:", final_output, "\n")


if __name__ == "__main__":
    main()
