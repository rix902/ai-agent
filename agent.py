def ask(self, question):

    q = question.lower()

    # SALES QUESTIONS
    if "revenue by region" in q:

        plan = {
            "source_type": "sql",
            "query": """
                SELECT region,
                       SUM(revenue) AS revenue
                FROM sales
                GROUP BY region
            """,
            "chart_type": "bar"
        }

    elif "profit by quarter" in q:

        plan = {
            "source_type": "sql",
            "query": """
                SELECT quarter,
                       SUM(profit) AS profit
                FROM sales
                GROUP BY quarter
            """,
            "chart_type": "line"
        }

    # EMPLOYEE QUESTIONS
    elif "highest average salary" in q or "average salary" in q:

        import pandas as pd

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

        plan = {
            "source_type": "excel",
            "chart_type": "bar"
        }

        response = llm.invoke(
            f"""
            Answer the question:

            {question}

            Data:
            {df.to_string()}
            """
        )

        return {
            "success": True,
            "answer": response.content,
            "data": df,
            "plan": plan
        }

    # WEBSITE QUESTIONS
    elif "traffic" in q or "visitor" in q:

        import pandas as pd

        df = pd.read_csv(
            self.csv_files["web_analytics"]
        )

        df = (
            df.groupby("date")["page_views"]
            .sum()
            .reset_index()
        )

        plan = {
            "source_type": "csv",
            "chart_type": "line"
        }

        response = llm.invoke(
            f"""
            Answer the question:

            {question}

            Data:
            {df.head(50).to_string()}
            """
        )

        return {
            "success": True,
            "answer": response.content,
            "data": df,
            "plan": plan
        }

    else:

        plan = {
            "source_type": "sql",
            "query": "SELECT * FROM sales LIMIT 20",
            "chart_type": "table"
        }

    df = run_sql_query(
        self.sql_engine,
        plan["query"]
    )

    response = llm.invoke(
        f"""
        Answer the question:

        {question}

        Data:
        {df.to_string()}
        """
    )

    return {
        "success": True,
        "answer": response.content,
        "data": df,
        "plan": plan
    }
