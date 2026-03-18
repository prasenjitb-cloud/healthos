import json
import llama_cpp


def load_config(configfile):
    with open(configfile, "r") as f:
        return json.load(f)


def load_model(configfile, config_name):

    config = load_config(configfile)

    if config_name not in config:
        raise ValueError(f"Config '{config_name}' not found")

    model_config = config[config_name]

    model = llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"]
    )

    return model, model_config


def generate_answer(model, model_config, question):

    prompt = f"""
### System
You are a biomedical expert assistant.

Your task:
- Answer medical questions accurately.
- Use biomedical knowledge.
- Respond in 1 sentence.
- Do NOT repeat the question.

### Question
{question}

### Answer
"""

    result = model(
        prompt,
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"],
        top_p=model_config["top_p"],
        stop=model_config.get("stop", ["###"])
    )

    text = result["choices"][0]["text"].strip()

    if text == "":
        text = "No response generated"

    return text


def run_model(question, configfile, config_name,model,model_config):

    response = generate_answer(model, model_config, question)

    return response
