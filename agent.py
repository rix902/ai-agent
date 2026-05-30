import json
import re

import streamlit as st
from langchain_groq import ChatGroq

from data_loader import run_sql_query, query_file


llm = ChatGroq(
    model="llama-3.1-8b-instant",
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

        # Temporary test plan
        plan = {
            "source_type": "sql",
            "query": "SELECT * FROM sales LIMIT 10",
            "chart_type": "table"
        }

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

        response = llm.invoke(
            f"""
            Explain this data in simple language.

            User Question:
            {question}

            Data:
            {df.head(20).to_string()}
            """
        )

        answer = response.content

        return {
            "success": True,
            "answer": answer,
            "data": df,
            "plan": plan
        }
