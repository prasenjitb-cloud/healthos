import typing
import json
import argparse
import llama_cpp
import langgraph.graph


def load_config(config_file):
    with open(config_file, "r") as f:
        return json.load(f)


def load_slm(config_data, model_name):

    if model_name not in config_data:
        raise ValueError(f"Config '{model_name}' not found in config file")

    model_config = config_data[model_name]

    return llama_cpp.Llama(
        model_path=model_config["model_path"],
        n_ctx=model_config["n_ctx"],
        n_threads=model_config["n_threads"],
        verbose=model_config["verbose"]
    ), model_config


def run_llm(slm, model_config, prompt: str) -> str:

    output = slm(
        prompt,
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"],
        top_k=model_config.get("top_k", 1),
        top_p=model_config["top_p"],
        stop=model_config.get("stop", ["</s>"])
    )

    return output["choices"][0]["text"].strip()


def load_doctors():

    with open(
        "slotbooking/ThirdPartyAPIs/synthetic_data/doctors.json",
        "r",
        encoding="utf-8"
    ) as f:
        doctors = json.load(f)

    specializations = list(set(doc["specialization"] for doc in doctors))

    return doctors, specializations


def create_healthos_app(slm, model_config, doctors, specializations):

    class AgentState(typing.TypedDict):
        messages: typing.Annotated[typing.List[str], "Chat history"]
        user_input: str
        intent: str


    def greeter_agent(state: AgentState):

        user_msg = state["user_input"].lower()

        emergency_keywords = [
            "chest pain",
            "difficulty breathing",
            "bleeding",
            "unconscious",
            "heart attack"
        ]

        for word in emergency_keywords:
            if word in user_msg:
                return {"intent": "emergency", "messages": state["messages"]}

        booking_keywords = [
            "book",
            "appointment",
            "schedule",
            "availability",
            "reserve"
        ]

        for word in booking_keywords:
            if word in user_msg:
                return {"intent": "booking", "messages": state["messages"]}

        prompt = f"""
Classify this medical message into one word:
emergency, triage, booking

Message: {user_msg}

Answer with one word only.
"""

        intent = run_llm(slm, model_config, prompt).strip().lower()

        if intent not in ["emergency", "triage", "booking"]:
            intent = "triage"

        return {"intent": intent, "messages": state["messages"]}


    def triage_agent(state: AgentState):

        user_msg = state["user_input"]

        prompt = f"""
You are a medical triage assistant.

Choose ONLY ONE specialization from:
{', '.join(specializations)}

Symptoms: {user_msg}

Answer with only the specialization name.
"""

        predicted = run_llm(slm, model_config, prompt).strip()
        predicted = predicted.replace(".", "").replace("specialist", "").strip()

        matched_specialization = None

        for spec in specializations:
            if spec.lower() in predicted.lower():
                matched_specialization = spec
                break

        if not matched_specialization:
            matched_specialization = "General Medicine"

        doctor = next(
            (doc for doc in doctors if doc["specialization"] == matched_specialization),
            None
        )

        if doctor:
            message = (
                f"Triage Result:\n"
                f"Specialist: {matched_specialization}\n"
                f"Doctor: {doctor['name']}\n"
                f"Hospital: {doctor['hospital']}\n"
                f"Location: {doctor['location']}"
            )
        else:
            message = "No matching specialist found."

        return {"messages": state["messages"] + [message]}


    def booking_agent(state: AgentState):

        return {
            "messages": state["messages"] + [
                "Booking: Please tell me which specialist you want to book."
            ]
        }


    def emergency_node(state: AgentState):

        return {
            "messages": state["messages"] + [
                "EMERGENCY: Please go to the nearest emergency room immediately."
            ]
        }


    workflow = langgraph.graph.StateGraph(AgentState)

    workflow.add_node("greeter", greeter_agent)
    workflow.add_node("triage", triage_agent)
    workflow.add_node("booking", booking_agent)
    workflow.add_node("emergency", emergency_node)


    def route(state: AgentState) -> typing.Literal["triage", "booking", "emergency"]:
        return state["intent"]


    workflow.add_conditional_edges(
        "greeter",
        route,
        {
            "triage": "triage",
            "booking": "booking",
            "emergency": "emergency"
        }
    )

    workflow.add_edge("triage", langgraph.graph.END)
    workflow.add_edge("booking", langgraph.graph.END)
    workflow.add_edge("emergency", langgraph.graph.END)

    workflow.set_entry_point("greeter")

    return workflow.compile()


def parse_args():

    parser = argparse.ArgumentParser(description="HealthOS Agentic Medical System")

    parser.add_argument(
        "-configfile",
        required=True,
        help="Path to configuration JSON file"
    )

    parser.add_argument(
        "-config",
        required=True,
        help="Model configuration name in the config file"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    config_data = load_config(args.configfile)

    slm, model_config = load_slm(config_data, args.config)

    doctors, specializations = load_doctors()

    app = create_healthos_app(slm, model_config, doctors, specializations)

    print("\n🩺 HealthOS Agentic Medical System")
    print("Type your symptoms or booking request.")
    print("Commands: 'exit', 'quit'\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            print("\nHealthOS: Take care! 👋")
            break

        result = app.invoke({
            "user_input": user_input,
            "messages": [],
            "intent": ""
        })

        for msg in result["messages"]:
            print("\nHealthOS:", msg)


if __name__ == "__main__":
    main()
