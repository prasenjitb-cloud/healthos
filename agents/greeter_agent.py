import typing
import json
import argparse
import llama_cpp
import langgraph.graph
from state_schema import DynamicStateSchema


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
        n_gpu_layers=model_config["n_gpu_layers"],
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
        "../slotbooking/ThirdPartyAPIs/synthetic_data/doctors.json",
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
        triage_data: typing.Optional[dict]


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

        prompt = f""" You are the Greeter Agent of a medical application called HealthOS. Your task is to classify the user's message into EXACTLY ONE of these three classes: 1. Triage - The user is describing symptoms, pain, illness, discomfort, or a health concern. - The user wants to understand their condition or find the appropriate medical department/specialist. - The user is NOT explicitly requesting an appointment or booking. - Example: "I have severe joint pain and swelling in my knees." 2. Booking - The user explicitly wants to book, schedule, reserve, or check availability for a doctor/medical appointment. - Example: "I want to book an appointment with a cardiologist." 3. Emergency - The user describes a potentially life-threatening or urgent medical situation that requires immediate emergency attention. - Examples include severe chest pain, difficulty breathing, unconsciousness, severe bleeding, or symptoms suggesting a medical emergency. - Example: "I am having severe chest pain and I cannot breathe properly." IMPORTANT RULES: - Return ONLY one class name: Triage, Booking, or Emergency. - Do NOT provide explanations. - Do NOT provide medical advice. - Do NOT ask follow-up questions. - If the user describes symptoms without explicitly asking to book an appointment, classify as Triage. - If the user explicitly asks to book/schedule/reserve an appointment, classify as Booking, unless the message clearly describes an immediate emergency. - If the message indicates a possible life-threatening emergency, classify as Emergency. ### Examples Example 1: User: "I have been having severe pain in my knees for the past two weeks and they are swollen." Reasoning: The user is describing symptoms and has not requested an appointment. This should be handled through medical triage. Classification: Triage Example 2: User: "I want to schedule an appointment with a doctor for my back pain tomorrow." Reasoning: The user explicitly wants to schedule an appointment. Therefore, this is a booking request. Classification: Booking Example 3: User: "I suddenly have severe chest pain and I am having difficulty breathing." Reasoning: The symptoms indicate a potentially life-threatening emergency requiring immediate attention. Classification: Emergency Now classify the following user message: User: {user_msg} Classification: """

        intent = run_llm(slm, model_config, prompt).strip().lower()

        if intent not in ["emergency", "triage", "booking"]:
            intent = "triage"

        return {"intent": intent, "messages": state["messages"]}


    def triage_agent(state: AgentState):

        user_msg = state["user_input"]

        prompt = f""" You are the Triage Agent of a medical application called HealthOS. Your task is to identify the most appropriate medical specialization based on the user's symptoms. Choose EXACTLY ONE specialization from the following list: {', '.join(specializations)} IMPORTANT RULES: - Choose ONLY a specialization from the provided list. - Do NOT invent a new specialization. - Do NOT provide medical advice or diagnosis. - Do NOT explain your answer. - Return ONLY the specialization name. - Consider the symptoms described by the user and select the specialization that would normally handle those symptoms. - If the symptoms are unclear or do not strongly match any specialization, choose "General Medicine" if it is available in the list. ### Examples Example 1: Symptoms: "I have severe pain in my knees and I am having difficulty walking." Reasoning: The symptoms primarily involve the joints and musculoskeletal system. An orthopedic specialist would normally handle these symptoms. Classification: Orthopedics Example 2: Symptoms: "I have been experiencing chest discomfort and my heart feels like it is beating irregularly." Reasoning: The symptoms involve the heart and cardiovascular system. A cardiologist would normally handle these symptoms. Classification: Cardiology Example 3: Symptoms: "I have a persistent cough, fever, and difficulty breathing for the past few days." Reasoning: The symptoms primarily involve the respiratory system. A pulmonologist would normally handle these symptoms. Classification: Pulmonology ### Now classify the following symptoms: Symptoms: {user_msg} Specialization: """

        predicted = run_llm(
            slm,
            model_config,
            prompt
        ).strip()

        predicted = (
            predicted
            .replace(".", "")
            .replace("specialist", "")
            .strip()
        )

        # ------------------------------------------
        # Match LLM output with specialization
        # ------------------------------------------

        matched_specialization = None

        for spec in specializations:

            if spec.lower() in predicted.lower():
                matched_specialization = spec
                break

        if not matched_specialization:
            matched_specialization = "General Medicine"

        # ------------------------------------------
        # Find doctor
        # ------------------------------------------

        doctor = next(
            (
                doc for doc in doctors
                if doc["specialization"] == matched_specialization
            ),
            None
        )

        # ------------------------------------------
        # Create response
        # ------------------------------------------

        if doctor:

            message = (
                f"Triage Result:\n"
                f"Specialist: {matched_specialization}\n"
                f"Doctor: {doctor['name']}\n"
                f"Hospital: {doctor['hospital']}\n"
                f"Location: {doctor['location']}"
            )

            triage_data = {
                "symptoms": user_msg,
                "department": matched_specialization,
                "doctor_name": doctor["name"],
                "hospital": doctor["hospital"],
                "location": doctor["location"]
            }

        else:

            message = "No matching specialist found."

            triage_data = {
                "symptoms": user_msg,
                "department": matched_specialization,
                "doctor_name": None,
                "hospital": None,
                "location": None
            }

        return {
            "messages": state["messages"] + [message],
            "triage_data": triage_data
        }

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

    app = create_healthos_app(
        slm,
        model_config,
        doctors,
        specializations
    )

    state_schema = DynamicStateSchema()

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


        intent = result["intent"]

        if intent == "triage":

            triage_data = result.get("triage_data")

            if triage_data:

                state_schema.add_symptom_data(
                    symptoms=triage_data["symptoms"],
                    department=triage_data["department"],
                    doctor_name=triage_data["doctor_name"],
                    hospital=triage_data["hospital"],
                    location=triage_data["location"]
                )

        elif intent == "booking":

            state_schema.activate_sections(
                booking=True
            )

        elif intent == "emergency":

            state_schema.add_emergency_data(
                emergency_type=user_input,
                emergency_status=True
            )


        for msg in result["messages"]:
            print("\nHealthOS:", msg)


        state_schema.print_schema()


if __name__ == "__main__":
    main()
