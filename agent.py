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

        q = question.lower()

        # SALES
        if "revenue" in q and "region" in q:

            df = run_sql_query(
                self.sql_engine,
                """
                SELECT region,
                       SUM(revenue) AS revenue
                FROM sales
                GROUP BY region
                """
            )

            plan = {"chart_type": "bar"}

        elif "profit" in q and "quarter" in q:

            df = run_sql_query(
                self.sql_engine,
                """
                SELECT quarter,
                       SUM(profit) AS profit
                FROM sales
                GROUP BY quarter
                """
            )

            plan = {"chart_type": "line"}

        elif "product" in q and "revenue" in q:

            df = run_sql_query(
                self.sql_engine,
                """
                SELECT product,
                       SUM(revenue) AS revenue
                FROM sales
                GROUP BY product
                ORDER BY revenue DESC
                """
            )

            plan = {"chart_type": "bar"}

        # EMPLOYEE

        elif "salary" in q:

            df = pd.read_excel(
                self.excel_files["employees"]
            )

            df = (
                df.groupby("department")["salary"]
                .mean()
                .reset_index()
                .sort_values(
                    "salary",
                    ascending=False
                )
            )

            plan = {"chart_type": "bar"}

        elif "employee count" in q or "employees" in q:

            df = pd.read_excel(
                self.excel_files["employees"]
            )

            df = (
                df.groupby("department")
                .size()
                .reset_index(name="employees")
            )

            plan = {"chart_type": "bar"}

        # WEB ANALYTICS

        elif "traffic" in q or "page views" in q:

            df = pd.read_csv(
                self.csv_files["web_analytics"]
            )

            df = (
                df.groupby("date")["page_views"]
                .sum()
                .reset_index()
            )

            plan = {"chart_type": "line"}

        elif "conversion" in q or "channel" in q:

            df = pd.read_csv(
                self.csv_files["web_analytics"]
            )

            df = (
                df.groupby("channel")["conversions"]
                .sum()
                .reset_index()
                .sort_values(
                    "conversions",
                    ascending=False
                )
            )

            plan = {"chart_type": "bar"}

        elif "bounce rate" in q:

            df = pd.read_csv(
                self.csv_files["web_analytics"]
            )

            df = (
                df.groupby("channel")["bounce_rate"]
                .mean()
                .reset_index()
            )

            plan = {"chart_type": "bar"}

        else:

            df = run_sql_query(
                self.sql_engine,
                "SELECT * FROM sales LIMIT 20"
            )

            plan = {"chart_type": "table"}

        response = llm.invoke(
            f"""
            Answer the user's question based on the data.

            Question:
            {question}

            Data:
            {df.head(50).to_string(index=False)}

            Give a concise business-style explanation.
            """
        )

        return {
            "success": True,
            "answer": response.content,
            "data": df,
            "plan": plan
        }
