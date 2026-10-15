from db import engine, check_db_connection
from schema_extractor import get_formatted_schema
from llm_sql import generate_sql_query

print("--- 1. Testing DB Connection ---")
if check_db_connection():
    print("Database connected successfully!")
else:
    print("Connection failed! Check .env password.")
    exit()

print("\n--- 2. Testing Schema Extraction (Deliverable 1) ---")
schema = get_formatted_schema(engine)
print(f"Extracted Schema (total {len(schema.splitlines())} lines of metadata)")
# Print first 20 lines to verify
print("\n".join(schema.splitlines()[:20]))

print("\n--- 3. Testing NL-to-SQL Generation (Deliverable 2) ---")
question = "Top 5 most rented movies kaunsi hain?"
print(f"Question: {question}")

sql = generate_sql_query(question, schema)
print("\nGenerated SQL by LLM:")
print(sql)