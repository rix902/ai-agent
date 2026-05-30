import pandas as pd
import streamlit as st
from langchain_groq import ChatGroq

from data_loader import run_sql_query

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=st.secrets["GROQ_API_KEY"]
)

class DataMetricsAgent:

    def __init__(self, sql_engine, excel_files, csv_files):
        self.sql_engine = sql_engine
        self.excel_files = excel_files
        self.csv_files = csv_files

    def ask(self, question):

        df = run_sql_query(
            self.sql_engine,
            "SELECT * FROM sales LIMIT 20"
        )

        response = llm.invoke(
            f"Explain this data:\n{df.to_string()}"
        )

        return {
            "success": True,
            "answer": response.content,
            "data": df,
            "plan": {"chart_type": "table"}
        }
