"""
app_streamlit.py - Streamlit Frontend for AI SQL Analyst
"""
import streamlit as st
import pandas as pd
import requests
from chart_generator import generate_auto_chart

# Page Configuration
st.set_page_config(
    page_title="AI SQL Analyst",
    page_icon="📊",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"

st.title("📊 AI SQL Analyst")
st.caption("Ask questions in plain English or Hinglish to analyze your PostgreSQL database.")

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("🗄️ Database Explorer")
    try:
        tables_res = requests.get(f"{API_BASE_URL}/tables", timeout=3)
        if tables_res.status_code == 200:
            tables_data = tables_res.json()
            table_list = list(tables_data.keys())
            selected_table = st.selectbox("Select Table to Inspect:", table_list)
            
            if selected_table:
                cols = tables_data[selected_table]["columns"]
                st.write("**Columns:**")
                for c in cols:
                    pk = " 🔑" if c["primary_key"] else ""
                    st.text(f"• {c['name']} ({c['type']}){pk}")
        else:
            st.warning("Backend se tables load nahi ho paayi.")
    except Exception:
        st.error("FastAPI Backend running nahi hai!")

    st.divider()
    st.header("📜 Query History")
    try:
        hist_res = requests.get(f"{API_BASE_URL}/history", timeout=2)
        if hist_res.status_code == 200:
            history = hist_res.json()
            if history:
                for h in reversed(history[-5:]):
                    st.caption(f"❓ **{h['question']}**")
                    st.code(h["sql"], language="sql")
            else:
                st.caption("No queries yet.")
    except Exception:
        pass

# ----------------- MAIN AREA -----------------
user_question = st.text_input(
    "Apna sawal yahan likho (English ya Hinglish):",
    placeholder="e.g., Top 5 most rented films kaunsi hain? ya Which customer spent the most?"
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_btn = st.button("🚀 Analyze Data", type="primary")

if ask_btn and user_question:
    with st.spinner("AI is thinking, validating SQL, and executing..."):
        try:
            res = requests.post(f"{API_BASE_URL}/ask", json={"question": user_question}, timeout=30)
            
            if res.status_code == 200:
                result = res.json()
                
                # 1. AI Business Insight
                st.success(f"💡 **AI Insight:** {result['insight']}")
                
                # 2. Generated SQL Query
                with st.expander("🔍 View Generated & Validated SQL Query", expanded=True):
                    st.code(result["sql"], language="sql")
                    st.caption(f"⚡ Rows: {result['row_count']} | Time: {result['execution_time_sec']}s")

                # 3. Chart & Table Tabs
                data = result["data"]
                if data:
                    df = pd.DataFrame(data)
                    tab1, tab2 = st.tabs(["📈 Auto Chart", "📋 Data Table"])
                    
                    with tab1:
                        fig = generate_auto_chart(data)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Is data ke liye automatic chart draw nahi ho sakta. Data Table tab check karein.")

                    with tab2:
                        st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Query run ho gayi lekin koi data nahi mila (0 rows).")

            else:
                err_detail = res.json().get("detail", res.text)
                st.error(f"❌ Error: {err_detail}")

        except Exception as e:
            st.error(f"Backend se connect nahi ho paya: {e}")