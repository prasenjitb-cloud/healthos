from prompts import SYSTEM_PROMPT
import vector_db.vector_memory

def generate_response(llm, user_input: str) -> str:
    """
    Generate chatbot response using SLM and vector memory.
    """
    past_info = vector_db.vector_memory.search_memory(user_input)

    memory_context = ""
    if past_info:
        memory_context = "Relevant past health information:\n"
        for info in past_info:
            memory_context += f"- {info}\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": memory_context},
        {"role": "user", "content": user_input}
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=300
    )

    reply = response["choices"][0]["message"]["content"]

    if len(user_input.split()) > 3:
        add_to_memory(user_input)

    return reply
