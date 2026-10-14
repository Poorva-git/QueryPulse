"""
llm_sql.py
----------
Translates English/Hinglish questions into PostgreSQL queries via Groq LLM.
"""

import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
DEFAULT_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are an expert PostgreSQL Data Analyst.
Your sole job is to translate a user's natural language question into a single, syntactically correct PostgreSQL SELECT query.

DATABASE SCHEMA:
{schema_context}

RULES YOU MUST STRICTLY FOLLOW:
1. ONLY return a single valid PostgreSQL SELECT query.
2. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, or multi-statement queries.
3. Understand questions in plain English or Hinglish (e.g., "sabse zyada" -> ORDER BY ... DESC LIMIT 1, "iss mahine" -> date filter, "kaunsa" -> SELECT identifier).
4. Use ILIKE for text matching where case-insensitive search makes sense.
5. Use proper JOIN conditions based strictly on the Foreign Keys provided in the schema.
6. Do NOT return markdown fences like ```sql or ```.
7. Do NOT include any explanations, greetings, or conversational text. Return ONLY the raw SQL query string.
"""


def clean_llm_sql_response(raw_response: str) -> str:
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip().rstrip(";")
    return cleaned


def generate_sql_query(question: str, schema_context: str, model: str = DEFAULT_MODEL) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not set in environment or .env file.")

    formatted_system_prompt = SYSTEM_PROMPT.format(schema_context=schema_context)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": f"User Question: {question}\nSQL Query:"}
        ],
        temperature=0.0,
        max_tokens=600,
    )

    raw_sql = response.choices[0].message.content.strip()
    return clean_llm_sql_response(raw_sql)