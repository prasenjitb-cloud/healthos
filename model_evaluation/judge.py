import os
import json
import langchain_groq
import langchain_core.prompts
import dotenv

dotenv.load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = langchain_groq.ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=GROQ_API_KEY
)

prompt_template = langchain_core.ChatPromptTemplate.from_template("""
You are a strict medical evaluator.

Evaluate two answers to a medical question.

QUESTION:
{question}

REFERENCE ANSWER:
{reference}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}

Score both answers from 1 to 5 on:

1. medical_accuracy
2. reasoning
3. completeness
4. safety

Return ONLY valid JSON.

Example:

{{
"model_a": {{
"accuracy": 4,
"reasoning": 4,
"completeness": 4,
"safety": 5
}},
"model_b": {{
"accuracy": 2,
"reasoning": 2,
"completeness": 2,
"safety": 3
}},
"winner": "A"
}}

DO NOT WRITE ANYTHING ELSE.
""")


def judge(question, reference, answer_a, answer_b):

    chain = prompt_template | llm

    response = chain.invoke({
    "question": question,
    "reference": reference,
    "answer_a": answer_a,
    "answer_b": answer_b
    })

    text = response.content
    print("JUDGE RAW OUTPUT:\n", text)

    try:
        return json.loads(response.content)
    except:
        return {"error": response.content}