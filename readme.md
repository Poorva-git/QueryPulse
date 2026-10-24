# ⚡ QueryPulse — Intelligent Conversational Data Engine for PostgreSQL

<p align="center">
  <strong>Transform plain English & Hinglish questions into secure, production-grade PostgreSQL analytics, dynamic visual charts, and executive AI insights.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Security-AST_Guarded-emerald.svg?style=for-the-badge&logo=shield" />
  <img src="https://img.shields.io/badge/LLM-Groq_LPU-orange.svg?style=for-the-badge" />
  <a href="https://querypulse-sok8.onrender.com/"><img src="https://img.shields.io/badge/Live_Demo-Render-success?style=for-the-badge&logo=render" /></a>
</p>

<p align="center">
  <a href="https://querypulse-sok8.onrender.com/"><strong>🚀 Click Here to Try the Live Interactive Demo</strong></a>
</p>

---

## 📌 Executive Summary

In enterprise environments, non-technical stakeholders (Product Managers, Sales Leads, Operations) frequently need insights from relational databases but lack SQL proficiency. Traditional solutions force them to rely on data engineering backlogs or risky text-to-SQL wrappers that run unvetted AI queries directly on production databases.

**QueryPulse** solves this by providing a **zero-trust conversational analytics platform**. It dynamically inspects PostgreSQL schemas, maps multi-table foreign key relationships, compiles user intent into SQL via Groq LPUs, subjects queries to a **multi-layer AST security sandbox**, executes them safely with PostgreSQL cost evaluation, and renders interactive Chart.js visualizations alongside 2-sentence executive summaries.

---

## 🆚 Why Not Just Use ChatGPT?

| Feature | Generic LLM (ChatGPT / Claude) | ⚡ QueryPulse |
| :--- | :--- | :--- |
| **Live Database Access** | ❌ No access to internal databases | ✅ Direct live connection to PostgreSQL |
| **Schema Awareness** | ❌ Requires manual copy-pasting of DDL | ✅ Dynamic schema & foreign-key auto-extraction |
| **Execution Safety** | ❌ Can hallucinate `DROP` or `DELETE` | ✅ **AST-level mathematical syntax validation** |
| **Data Privacy** | ❌ Full company data pasted into cloud | ✅ **Zero data leaves the server** (only schema metadata) |
| **Performance Visibility** | ❌ Cannot measure database load | ✅ **PostgreSQL EXPLAIN cost & scan type analysis** |
| **Custom Database Support**| ❌ Manual configuration | ✅ **BYODB: Connect any Postgres via session isolation** |
| **End-to-End Workflow** | ❌ Copy SQL -> Open pgAdmin -> Make Excel | ✅ **Instant SQL + Live Table + Interactive Chart + AI Insight** |
| **Language Support** | ⚠️ Generic multilingual | ✅ Tuned for natural English and **Hinglish** business idioms |

---

## 🌟 Key Features

* **Natural Language to SQL:** Ask in plain English or Hinglish (e.g. *"Top 5 most rented films kaunsi hain?"*). Groq LPU (`GPT-o-120B`) generates deterministic, syntax-checked PostgreSQL queries in milliseconds.
* **Zero-Trust AST Security Guard:** Replaces brittle Regex with **SQLGlot AST validation**. Rejects `DROP`, `DELETE`, `UPDATE`, `ALTER`, `pg_sleep`, `pg_read_file`, and multi-statement injection attempts.
* **PostgreSQL EXPLAIN Cost Analyzer:** Runs `EXPLAIN (FORMAT JSON)` on every query before execution. Calculates internal execution cost and identifies scan types (`Index Scan`, `Hash Join`, `Seq Scan`).
* **Interactive BI Visualizations:** Automatically renders Bar, Line, or Doughnut charts via Chart.js. Includes interactive raw data table and one-click CSV export.
* **🔌 Bring Your Own Database (BYODB):** Connect any external Supabase, Neon, AWS RDS, or local PostgreSQL database. Connections are session-isolated in memory and never saved to disk.
* **Executive AI Insights:** Translates raw database rows into concise, 2-sentence executive business takeaways.

---

## 🏗️ System Architecture & Data Pipeline

```
[ User Prompt: English / Hinglish ]
                │
                ▼
   [ FastAPI Backend Endpoint: /ask ]
                │
                ├─► 1. Schema Extractor: Reads tables, columns & foreign keys from pg_catalog
                │
                ├─► 2. Groq LPU (GPT-o-120B): Generates deterministic, schema-aware SQL
                │
                ├─► 3. SQLGlot AST Sandbox: Verifies syntax tree (Blocks DDL/DML/DoS/Injections)
                │
                ├─► 4. Query Executor: Computes EXPLAIN plan cost + 5s statement_timeout
                │
                ├─► 5. Insight Generator: Produces 2-sentence executive business takeaways
                │
                ▼
   [ Single Page Dashboard: Chart.js + Tailwind CSS ]
   (Interactive Charts · Data Tables · SQL Display with Cost Badge · CSV Export)
```

---

## 🛡️ Security Architecture & Defense Matrix

| Attack Vector | Attacker Payload Example | Defense Mechanism | Result |
| :--- | :--- | :--- | :--- |
| **Multi-Statement Injection** | `SELECT 1; DROP TABLE customer;` | AST parses statement list length | ❌ **BLOCKED** |
| **Destructive DDL** | `DROP TABLE film CASCADE;` | Rejects `exp.Drop` nodes | ❌ **BLOCKED** |
| **Unauthorized DML** | `DELETE FROM rental WHERE id = 1;` | Enforces root `exp.Select` | ❌ **BLOCKED** |
| **DoS Resource Exhaustion** | `SELECT pg_sleep(10);` | Blocks sleep/benchmark functions | ❌ **BLOCKED** |
| **Filesystem Inspection** | `SELECT pg_read_file('/etc/passwd');` | Rejects server filesystem calls | ❌ **BLOCKED** |
| **Runaway Result Set** | `SELECT * FROM payment;` | Enforces `LIMIT 1000` clamping | ⚠️ **CLAMPED** |
| **Query Deadlocks** | Long-running blocking locks | `SET statement_timeout = 5000` | ⏱️ **KILLED (5s)** |

---

## 💻 Tech Stack

* **Language:** Python 3.11+
* **Backend:** FastAPI, SQLAlchemy, Psycopg2-binary, Uvicorn
* **Security & Validation:** SQLGlot (Abstract Syntax Tree Parser), Pydantic
* **AI & LLM Inference:** Groq LPU Cloud API (`openai/gpt-oss-120b`)
* **Database:** PostgreSQL (Neon Cloud Serverless PostgreSQL in Singapore + Local PostgreSQL 18)
* **Frontend:** Vanilla JavaScript, Tailwind CSS (CDN), Chart.js, Lucide Icons
* **DevOps & Testing:** Pytest, Docker, Docker Compose, Git/GitHub, Render.com

---

## 📁 Project Structure

```
AI-SQL-ANALYST/
├── main.py                 # FastAPI backend with CORS, /ask, and BYODB session endpoints
├── db.py                   # Multi-database SQLAlchemy engine with session isolation
├── schema_extractor.py     # Live PostgreSQL schema & foreign-key relationship extractor
├── llm_sql.py              # Groq LPU text-to-SQL engine with deterministic prompts
├── sql_validator.py        # Zero-trust AST-based security sandbox using SQLGlot
├── query_executor.py       # Safe execution with EXPLAIN cost analysis & statement_timeout
├── insight_generator.py    # AI executive business summary generator
├── static/
│   └── index.html          # Clean, modern single-page dashboard with Chart.js & Tailwind
├── tests/
│   └── test_security.py    # 8 automated adversarial pytest security test cases
├── Dockerfile              # Production Python 3.11-slim container definition
├── docker-compose.yml      # 1-command deployment configuration
├── requirements.txt        # Python dependency manifest
└── README.md               # Complete project documentation
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
* Python 3.11 or higher
* PostgreSQL installed locally or a free [Neon.tech](https://neon.tech) / [Supabase](https://supabase.com) account
* Free API key from [Groq Console](https://console.groq.com)

### 2. Clone the Repository
```bash
git clone https://github.com/Poorva-git/QueryPulse.git
cd QueryPulse
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dvdrental
GROQ_API_KEY=your_groq_api_key_here
```

### 6. Run the Application
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 🧪 Running Security Test Suite

Run the automated adversarial test suite to verify that SQL injections and malicious mutations are blocked:

```bash
pytest tests/test_security.py -v
```

Expected output:
```text
tests/test_security.py::test_legitimate_select_query PASSED
tests/test_security.py::test_row_limit_clamping PASSED
tests/test_security.py::test_block_multistatement_injection PASSED
tests/test_security.py::test_block_delete_dml PASSED
tests/test_security.py::test_block_drop_ddl PASSED
tests/test_security.py::test_block_update_dml PASSED
tests/test_security.py::test_block_pg_sleep_dos PASSED
tests/test_security.py::test_block_file_read PASSED
======================== 8 passed in 0.45s =========================
```

---

## 🐳 Docker Deployment

To run QueryPulse in an isolated Docker container with one command:

```bash
docker-compose up --build -d
```
The application will be live at `http://localhost:8000`.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive dashboard (`index.html`) |
| `GET` | `/databases` | Lists all available PostgreSQL databases in the engine pool |
| `POST` | `/switch-db` | Switches the active database for the current context |
| `POST` | `/connect-custom-db` | Connects a custom database to the active session via BYODB |
| `POST` | `/disconnect-custom-db` | Disconnects the custom database and reverts to sandbox demo |
| `GET` | `/tables` | Retrieves tables, column definitions, and primary keys |
| `POST` | `/ask` | Primary pipeline: NL to SQL -> AST Guard -> EXPLAIN -> Exec -> Chart/Insight |
| `GET` | `/history` | Returns the recent query execution history |

---

## 👤 Author

* **Developer:** Poorva Soni
* **Degree:** Final Year B.Tech Computer Science & Engineering
* **GitHub:** [@Poorva-git](https://github.com/Poorva-git)
* **Live Project:** [QueryPulse on Render](https://querypulse-sok8.onrender.com/)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
