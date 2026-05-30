streamlit_code = r'''
import os
import re
import json
import time
import traceback

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from langchain_ollama import OllamaLLM
from sqlalchemy import create_engine, text


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama2:latest"

# Default data source paths (can be changed in sidebar)
DEFAULT_SQL_PATH = "./data/sales.db"
DEFAULT_EXCEL_FILES = {"employees": "./data/employees.xlsx"}
DEFAULT_CSV_FILES = {"web_analytics": "./data/web_analytics.csv"}

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Data Metrics Agent", page_icon="📊", layout="wide")
st.title("📊 AI Data Metrics Agent")
st.caption("Ask questions about your data in plain English — powered by local Ollama")


# ══════════════════════════════════════════════════════════════
#  CACHED RESOURCES
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def get_llm():
    return OllamaLLM(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.1)


# ══════════════════════════════════════════════════════════════
#  DATA SOURCE FUNCTIONS
# ══════════════════════════════════════════════════════════════
def get_sql_schema(engine) -> str:
    with engine.connect() as conn:
        tables = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).fetchall()
        parts = []
        for (table_name,) in tables:
            cols = conn.execute(text(f"PRAGMA table_info('{table_name}')")).fetchall()
            col_defs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
            sample = conn.execute(text(f"SELECT * FROM '{table_name}' LIMIT 2")).fetchall()
            parts.append(
                f"Table: {table_name}\n  Columns: {col_defs}\n  Sample: {sample}"
            )
        return "\n\n".join(parts)
def run_sql_query(engine, query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_file_info(files: dict, file_type: str) -> str:
    parts = []
    for name, path in files.items():
        reader = pd.read_excel if file_type == "excel" else pd.read_csv
        df = reader(path, nrows=3)
        full_shape = reader(path).shape
        cols = ", ".join([f"{c} ({df[c].dtype})" for c in df.columns])
        parts.append(
            f"{file_type.title()} file: {name} ({path})\n"
            f"  Columns: {cols}\n  Shape: {full_shape}\n"
            f"  Sample:\n{df.head(2).to_string()}"
        )
    return "\n\n".join(parts)


def query_file(files: dict, file_key: str, pandas_code: str, file_type: str) -> pd.DataFrame:
    if file_key not in files:
        raise ValueError(f"Unknown {file_type} file: {file_key}. Available: {list(files.keys())}")
    reader = pd.read_excel if file_type == "excel" else pd.read_csv
    df = reader(files[file_key])
    local_vars = {"df": df, "pd": pd, "np": np}
    exec(f"result = {pandas_code}", {}, local_vars)
    result = local_vars["result"]
    if isinstance(result, pd.Series):
        result = result.to_frame()
    elif not isinstance(result, pd.DataFrame):
        result = pd.DataFrame({"result": [result]})
    return result
# ══════════════════════════════════════════════════════════════
#  CHART GENERATION
# ══════════════════════════════════════════════════════════════
def generate_chart(df: pd.DataFrame, plan: dict):
    chart_type = plan.get("chart_type", "none")
    if chart_type == "none" or df.empty:
        return None

    if df.index.name or isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    x_col = plan.get("chart_x", df.columns[0])
    y_col = plan.get("chart_y", df.columns[-1] if len(df.columns) > 1 else df.columns[0])
    title = plan.get("chart_title", "Query Result")

    if x_col not in df.columns:
        x_col = df.columns[0]
    if y_col not in df.columns:
        y_col = df.columns[-1] if len(df.columns) > 1 else df.columns[0]

    try:
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, title=title, text_auto=True)
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title)
        elif chart_type == "table":
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns), fill_color="#3b82f6", font=dict(color="white")),
                cells=dict(values=[df[c] for c in df.columns], fill_color="#f1f5f9"),
            )])
            fig.update_layout(title=title)
        else:
return None

        fig.update_layout(template="plotly_white", height=400, margin=dict(l=40, r=40, t=60, b=40))
        return fig
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════
#  AGENT LOGIC
# ══════════════════════════════════════════════════════════════
def build_schema_context(sql_engine, excel_files, csv_files) -> str:
    parts = ["=== AVAILABLE DATA SOURCES ==="]
    if sql_engine:
        parts.append("\n--- SQL DATABASE (source_type: sql) ---")
        parts.append(get_sql_schema(sql_engine))
    if excel_files:
        parts.append("\n--- EXCEL FILES (source_type: excel) ---")
        parts.append(get_file_info(excel_files, "excel"))
    if csv_files:
        parts.append("\n--- CSV FILES (source_type: csv) ---")
        parts.append(get_file_info(csv_files, "csv"))
    return "\n".join(parts)


def get_routing_prompt(question: str, schema_context: str, history: list) -> str:
    history_text = ""
    if history:
        recent = history[-6:]
        history_text = "\n--- Recent conversation ---\n"
        for h in recent:
            history_text += f"{h['role'].upper()}: {h['content']}\n"
 return f"""You are a data analytics agent. Given the user's question and the
available data sources below, do the following:

1. Determine which data source to query (sql, excel, or csv).
2. Write the exact query to answer the question.
3. Specify what chart type would best visualize the result.

{schema_context}
{history_text}

USER QUESTION: {question}

Respond in EXACTLY this JSON format (no extra text, no markdown):
{{
  "source_type": "sql" | "excel" | "csv",
  "file_key": "<file key for excel/csv, or empty for sql>",
  "query": "<SQL query for sql, or pandas expression for excel/csv>",
  "chart_type": "bar" | "line" | "pie" | "table" | "none",
  "chart_x": "<column for x-axis>",
  "chart_y": "<column for y-axis>",
  "chart_title": "<chart title>"
}}

RULES:
- For sql: write valid SQLite SQL.
- For excel/csv: write a valid pandas expression using 'df'. Must return DataFrame or Series.
- Pick the best chart type for the result shape.
- Use "table" for multi-column detail, "none" for single numbers.

JSON response:"""


def parse_llm_response(response: str) -> dict:
    response = response.strip()
response = re.sub(r"```json\s*", "", response)
    response = re.sub(r"```\s*", "", response)
    match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not parse LLM response as JSON.")


def process_question(question, llm, sql_engine, excel_files, csv_files, schema_context, history):
    # Step 1: Route
    prompt = get_routing_prompt(question, schema_context, history)
    raw = llm.invoke(prompt)
    plan = parse_llm_response(raw)

    # Step 2: Execute
    source = plan["source_type"]
    if source == "sql":
        result_df = run_sql_query(sql_engine, plan["query"])
    elif source == "excel":
        result_df = query_file(excel_files, plan["file_key"], plan["query"], "excel")
    elif source == "csv":
        result_df = query_file(csv_files, plan["file_key"], plan["query"], "csv")
    else:
        raise ValueError(f"Unknown source: {source}")

    # Step 3: Explain
    explain_prompt = f"""Based on this data result, answer the user's question clearly.
Include key numbers. Be concise (2-4 sentences).

Question: {question}
Source: {source}
Result:
{result_df.to_string(max_rows=20)}
Answer:"""
    explanation = llm.invoke(explain_prompt)

    return plan, result_df, explanation


# ══════════════════════════════════════════════════════════════
#  SIDEBAR — Data Source Configuration
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔗 Data Sources")

    # SQL
    st.subheader("SQL Database")
    sql_path = st.text_input("SQLite DB path", value=DEFAULT_SQL_PATH)
    sql_engine = None
    if sql_path and os.path.exists(sql_path):
        sql_engine = create_engine(f"sqlite:///{sql_path}")
        st.success(f"Connected: {sql_path}")
    elif sql_path:
        st.warning("DB file not found")

    # Excel
    st.subheader("Excel Files")
    excel_input = st.text_area(
        "Name=Path (one per line)",
        value="\n".join([f"{k}={v}" for k, v in DEFAULT_EXCEL_FILES.items()]),
        height=68,
    )
    excel_files = {}
    for line in excel_input.strip().split("\n"):
        if "=" in line:
            k, v = line.split("=", 1)
if os.path.exists(v.strip()):
                excel_files[k.strip()] = v.strip()
    if excel_files:
        st.success(f"{len(excel_files)} Excel file(s)")

    # CSV
    st.subheader("CSV Files")
    csv_input = st.text_area(
        "Name=Path (one per line)",
        value="\n".join([f"{k}={v}" for k, v in DEFAULT_CSV_FILES.items()]),
        height=68,
    )
    csv_files = {}
    for line in csv_input.strip().split("\n"):
        if "=" in line:
            k, v = line.split("=", 1)
            if os.path.exists(v.strip()):
                csv_files[k.strip()] = v.strip()
    if csv_files:
        st.success(f"{len(csv_files)} CSV file(s)")

    st.divider()
    st.caption(f"**Model:** {LLM_MODEL}")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["agent_history"] = []
        st.rerun()
# ══════════════════════════════════════════════════════════════
#  BUILD SCHEMA CONTEXT
# ══════════════════════════════════════════════════════════════
schema_context = build_schema_context(sql_engine, excel_files, csv_files)


# ══════════════════════════════════════════════════════════════
#  CHAT INTERFACE
# ══════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "agent_history" not in st.session_state:
    st.session_state["agent_history"] = []

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart"):
            st.plotly_chart(msg["chart"], use_container_width=True)
        if msg.get("data") is not None:
            with st.expander("📋 Raw Data"):
                st.dataframe(msg["data"], use_container_width=True)
        if msg.get("plan"):
            with st.expander("🔍 Query Details"):
                st.json(msg["plan"])

# Chat input
if prompt := st.chat_input("Ask about your data... (e.g., 'What is total revenue by region?')"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["agent_history"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your data..."):
            try:
                start = time.time()
                plan, result_df, explanation = process_question(
                    prompt, get_llm(), sql_engine, excel_files, csv_files,
                    schema_context, st.session_state["agent_history"]
                )
                elapsed = time.time() - start

                # Display explanation
                st.markdown(explanation)

                # Display chart
                fig = generate_chart(result_df, plan)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

                # Raw data expander
                with st.expander("📋 Raw Data"):
                    st.dataframe(result_df, use_container_width=True)
 # Query details expander
                with st.expander("🔍 Query Details"):
                    st.json(plan)

                st.caption(f"⏱️ {elapsed:.2f}s | Source: {plan['source_type']}")

                # Save to history
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": explanation,
                    "chart": fig,
                    "data": result_df,
                    "plan": plan,
                })
                st.session_state["agent_history"].append(
                    {"role": "assistant", "content": explanation}
                )

            except Exception as e:
                error_msg = f"Sorry, I ran into an error: {str(e)}"
                st.error(error_msg)
                with st.expander("Traceback"):
                    st.code(traceback.format_exc())
                st.session_state["messages"].append(
                    {"role": "assistant", "content": error_msg}
                )
'''

with open("app.py", "w") as f:
    f.write(streamlit_code.strip())

print("✅ Streamlit app written to 'app.py'")
print("\n🚀 To launch:")
print("   streamlit run app.py")