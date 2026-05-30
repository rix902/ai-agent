import json
import re

import streamlit as st
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama3-8b-8192",
    api_key=st.secrets["GROQ_API_KEY"]
)


class DataMetricsAgent:

    def __init__(
        self,
        sql_engine,
        excel_files,
        csv_files
    ):
        self.sql_engine = sql_engine
        self.excel_files = excel_files
        self.csv_files = csv_files

    def ask(self, question):

        prompt = f"""
        Analyze this question:

        {question}

        Return JSON only.
        """

        raw = llm.invoke(prompt)

        match = re.search(r"\{.*\}", raw, re.S)

        plan = json.loads(match.group())

        source = plan["source_type"]

        if source == "sql":
            df = run_sql_query(
                self.sql_engine,
                plan["query"]
            )

        elif source == "excel":
            df = query_file(
                self.excel_files,
                plan["file_key"],
                plan["query"],
                "excel"
            )

        else:
            df = query_file(
                self.csv_files,
                plan["file_key"],
                plan["query"],
                "csv"
            )

        answer = llm.invoke(
            f"Explain:\n{df.head(20).to_string()}"
        )

        return {
            "success": True,
            "answer": answer,
            "data": df,
            "plan": plan
        }
