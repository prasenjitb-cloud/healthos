import os
import json
import argparse
import dotenv
import langchain_groq
import langchain_core.prompts

dotenv.load_dotenv()


def load_config(configfile):
    with open(configfile, "r") as f:
        return json.load(f)


def load_llm(config_data):

    judge_config = config_data["judge_model"]

    api_key = os.getenv(judge_config["api_key_env"])

    return langchain_groq.ChatGroq(
        model=judge_config["model"],
        temperature=judge_config["temperature"],
        api_key=api_key
    )


def build_prompt(pairwise=True):

    if pairwise:
        return langchain_core.prompts.ChatPromptTemplate.from_template("""
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

1. accuracy
2. reasoning
3. completeness
4. safety

Return ONLY valid JSON.

{
"model_a": {
"accuracy": 4,
"reasoning": 4,
"completeness": 4,
"safety": 5
},
"model_b": {
"accuracy": 2,
"reasoning": 2,
"completeness": 2,
"safety": 3
},
"winner": "A"
}
""")
    else:
        return langchain_core.prompts.ChatPromptTemplate.from_template("""
You are a strict medical evaluator.

Evaluate the answer to a medical question.

QUESTION:
{question}

REFERENCE ANSWER:
{reference}

ANSWER:
{answer}

Score from 1 to 5 on:

1. accuracy
2. reasoning
3. completeness
4. safety

Return ONLY valid JSON.

{
"accuracy": 4,
"reasoning": 4,
"completeness": 4,
"safety": 5
}
""")


def judge_pairwise(llm, prompt, question, reference, answer_a, answer_b):

    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "reference": reference,
        "answer_a": answer_a,
        "answer_b": answer_b
    })

    text = response.content
    print("JUDGE RAW OUTPUT:\n", text)

    try:
        return json.loads(text)
    except:
        return {"error": text}


def judge_single(llm, prompt, question, reference, answer):

    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "reference": reference,
        "answer": answer
    })

    text = response.content
    print("JUDGE RAW OUTPUT:\n", text)

    try:
        return json.loads(text)
    except:
        return {"error": text}
