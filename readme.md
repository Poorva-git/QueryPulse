# ⚡ QueryPulse — Intelligent Conversational Data Engine for PostgreSQL

<p align="center">
  <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80" alt="QueryPulse Banner" width="100%" style="border-radius: 12px; max-height: 380px; object-fit: cover; border: 1px solid #1e293b;" />
</p>

<p align="center">
  <strong>Transform plain English & Hinglish questions into secure, production-grade PostgreSQL analytics, dynamic visual charts, and executive AI insights.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Security-AST_Guarded-emerald.svg?style=for-the-badge&logo=shield" />
  <img src="https://img.shields.io/badge/LLM-Groq_LPU-orange.svg?style=for-the-badge" />
</p>

---

## 📌 Executive Summary

In enterprise environments, non-technical stakeholders (Product Managers, Sales Leads, Operations) frequently need insights from relational databases but lack SQL proficiency. Traditional solutions force them to rely on data engineering backlogs or risky text-to-SQL wrappers that run unvetted AI queries directly on production databases.

**QueryPulse** solves this by providing a **zero-trust conversational BI platform**. It dynamically inspects PostgreSQL schemas, maps multi-table foreign key relationships, compiles user intent into SQL via Groq LPUs, subjects queries to a **multi-layer AST security sandbox**, executes them safely, and renders interactive Chart.js visualizations alongside 2-sentence executive summaries.

---

## 🆚 Why Not Just Use ChatGPT?

| Feature | Generic LLM (ChatGPT / Claude) | ⚡ QueryPulse |
| :--- | :--- | :--- |
| **Live Database Access** | ❌ No access to internal databases | ✅ Direct live connection to PostgreSQL |
| **Schema Awareness** | ❌ Requires manual copy-pasting of DDL | ✅ Dynamic schema & foreign-key auto-extraction |
| **Execution Safety** | ❌ Can hallucinate `DROP` or `DELETE` | ✅ **AST-level mathematical syntax validation** |
| **Data Privacy** | ❌ Full company data pasted into cloud | ✅ **Zero data leaves the server** (only schema metadata) |
| **End-to-End Workflow** | ❌ Copy SQL -> Open pgAdmin -> Make Excel | ✅ **Instant SQL + Live Table + Interactive Chart + Insight** |
| **Language Support** | ⚠️ Generic multilingual | ✅ Tuned for natural English and **Hinglish** business idioms |

---

## 🏗️ System Architecture & Data Pipeline

```
                     ┌────────────────────────────────────────┐
                     │    User Question (English / Hinglish)   │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │     Dynamic Schema Context Builder     │
                     │  (SQLAlchemy Inspector: Tables, FKs)   │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │           LLM Query Synthesis          │
                     │     (Groq LPU: Deterministic SQL)      │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │    🛡️ AST Security Sandbox (SQLGlot)   │
                     │  - Rejects Multi-Statements (;)        │
                     │  - Rejects DML (INSERT/UPDATE/DELETE)  │
                     │  - Rejects DDL (DROP/ALTER/TRUNCATE)   │
                     │  - Blocks Dangerous Functions          │
                     │  - Clamps to max LIMIT 1000            │
                     └───────────────────┬────────────────────┘
                                         │  (Sanitized SELECT Query)
                                         ▼
                     ┌────────────────────────────────────────┐
                     │         PostgreSQL Database Engine     │
                     │  - Read-Only User (analyst_readonly)   │
                     │  - Strict 5-Second Statement Timeout   │
                     └───────────────────┬────────────────────┘
                                         │
                     ┌───────────────────┴────────────────────┐
                     ▼                                        ▼
    ┌──────────────────────────────────┐    ┌──────────────────────────────────┐
    │     Visuals & Tabular Engine     │    │       Executive AI Insight       │
    │  - Smart Chart.js (Bar/Line/Pie) │    │  - 2-Sentence Punchy Synthesis   │
    │  - 1-Click CSV Data Export       │    │  - Highlights Core Metric/Trend  │
    └──────────────────────────────────┘    └──────────────────────────────────┘
```

---

## 🛡️ Security Architecture: Defense-in-Depth

Security is the core differentiator of QueryPulse. It operates under a **Defense-in-Depth** model across three isolated layers:

### 1. Application Layer: AST-Based SQL Parsing (sqlglot)
Naive implementations rely on regular expressions (`if 'drop' in sql.lower()`), which are easily bypassed using SQL comments (`/* DROP */`), column aliases, or nested Common Table Expressions (CTEs). 

QueryPulse parses every query into an **Abstract Syntax Tree (AST)**:
- **Root Node Validation:** Guarantees that the statement is strictly an `exp.Select`.
- **Deep Tree Traversal (`stmt.walk()`):** Recursively inspects every leaf node in subqueries to reject forbidden statements: `exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.Alter`, `exp.Command`, `exp.TruncateTable`.
- **Function Deny-Listing:** Prohibits destructive or information-disclosure functions such as `pg_sleep()` (DoS protection), `pg_read_file()`, and `pg_ls_dir()`.

### 2. Database Layer: Role-Based Access Control (RBAC)
Queries execute under a dedicated PostgreSQL role with strictly read-only grants:
```sql
CREATE ROLE analyst_readonly WITH LOGIN PASSWORD 'readonly_secret_pass';
GRANT CONNECT ON DATABASE dvdrental TO analyst_readonly;
GRANT USAGE ON SCHEMA public TO analyst_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analyst_readonly;
```
Even if an application-level parser zero-day occurred, the PostgreSQL engine will directly reject any write or schema-alteration command.

### 3. Resource Exhaustion & DoS Guardrails
- **Statement Timeout:** Every session executes with `SET statement_timeout = '5000';` (5-second hard cap).
- **Automatic Row Clamping:** If the query does not contain a `LIMIT` clause, or if the user requests more than 1,000 rows, QueryPulse automatically injects/clamps the AST to `LIMIT 1000`.

---

## 🚀 Key Features

* **Multi-Database Dynamic Switching:** Seamlessly toggle between multiple connected databases (e.g., `dvdrental`, `onlinebookstore`) in real time from the sidebar dropdown without restarting the server.
* **Bilingual English & Hinglish Translation:** Zero-shot prompt engineering maps business vernacular (e.g., *"sabse zyada"* -> `ORDER BY ... DESC LIMIT 1`, *"iss mahine"* -> date filtering) directly to SQL syntax.
* **Interactive Charting:** Automatically detects data patterns (time-series, categorical comparisons) to render Bar, Line, or Doughnut charts with Chart.js.
* **Query History & Schema Inspector:** Inspect database tables, primary keys, and foreign keys visually in the sidebar without writing code.

---

## 📂 Repository File Structure

```text
QueryPulse/
│
├── .gitignore                # Protects secrets (.env) and environment folders
├── requirements.txt          # Python dependencies
├── README.md                 # Complete system documentation
│
├── db.py                     # Multi-database SQLAlchemy connection pool
├── schema_extractor.py       # Inspects tables, types, and Foreign Key constraints
├── llm_sql.py                # Groq LPU prompt orchestration & SQL generation
├── sql_validator.py          # AST-based syntax security validator (SQLGlot)
├── query_executor.py         # Safe query execution, timeouts, and JSON serialization
├── insight_generator.py      # Executive AI business insight generation
├── main.py                   # FastAPI REST API & static server orchestrator
│
├── static/
│   └── index.html            # Luxury dark-mode dashboard (Tailwind, Lucide, Chart.js)
│
├── tests/
│   └── test_security.py      # Pytest adversarial test suite (SQL injection tests)
│
├── Dockerfile                # Containerized deployment specification
└── docker-compose.yml        # Multi-container orchestration
```

---

## ⚡ Quickstart Guide

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/Poorva-git/QueryPulse.git
cd QueryPulse

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# PostgreSQL connection string
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/dvdrental

# Groq API Key (Free tier from https://console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Run Application
```bash
uvicorn main:app --reload
```
Open your browser at `http://127.0.0.1:8000` to access the interactive QueryPulse canvas.

---

## 🧪 Running Security Test Suite

Run the automated adversarial security test suite to verify AST validation:
```bash
pytest tests/test_security.py -v
```

**Expected output:**
```text
tests/test_security.py::test_valid_select_query PASSED           [ 12%]
tests/test_security.py::test_custom_limit_clamping PASSED        [ 25%]
tests/test_security.py::test_block_multistatement_injection PASSED [ 37%]
tests/test_security.py::test_block_delete_dml PASSED             [ 50%]
tests/test_security.py::test_block_drop_ddl PASSED               [ 62%]
tests/test_security.py::test_block_update_dml PASSED             [ 75%]
tests/test_security.py::test_block_time_based_dos PASSED         [ 87%]
tests/test_security.py::test_block_file_read_exposure PASSED     [100%]

============================== 8 passed in 0.35s ==============================
```

---

## 💡 Sample Questions to Try

### 🎬 dvdrental (Movies & Stores)
- *"Top 5 most rented films kaunsi hain?"*
- *"Which customer has paid the highest total rental amount?"*
- *"Total films count grouped by rating"*
- *"Top 10 actors who have acted in the most films"*

### 📚 onlinebookstore (Books & Orders)
- *"Sabse zyada bikne wali top 5 books kaunsi hain?"*
- *"Which author generated the highest total book sales?"*
- *"Total count of books grouped by genre"*
- *"Top 5 most expensive books in the inventory"*

---

## 👤 Author

* **Poorva** — Final Year B.Tech Computer Science & Engineering
* **GitHub:** [@Poorva-git](https://github.com/Poorva-git)