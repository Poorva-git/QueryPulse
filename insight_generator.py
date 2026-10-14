"""
insight_generator.py - Generates 2-3 line plain business insights from query results
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_business_insight(question: str, sql: str, data: list) -> str:
    if not data or len(data) == 0:
        return "Query ran successfully, but no matching records were found."

    sample_data = data[:5]  # first 5 rows for context

    prompt = f"""You are a helpful business data analyst.
Question: "{question}"
Executed SQL: {sql}
Result Sample (first few rows): {sample_data}

Provide a short, punchy 2-line business insight answering the question in plain, clear English/Hinglish.
Keep it strictly under 3 sentences. Highlight the top finding directly. Do NOT explain SQL.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Key findings generated from {len(data)} returned rows."