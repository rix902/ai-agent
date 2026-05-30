import pandas as pd
import numpy as np
from sqlalchemy import text


def get_sql_schema(engine):
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()

        parts = []

        for (table_name,) in tables:
            cols = conn.execute(
                text(f"PRAGMA table_info('{table_name}')")
            ).fetchall()

            col_defs = ", ".join(
                [f"{c[1]} ({c[2]})" for c in cols]
            )

            parts.append(
                f"Table: {table_name}\nColumns: {col_defs}"
            )

        return "\n\n".join(parts)


def run_sql_query(engine, query):
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def query_file(files, file_key, pandas_code, file_type):

    reader = pd.read_excel if file_type == "excel" else pd.read_csv

    df = reader(files[file_key])

    local_vars = {
        "df": df,
        "pd": pd,
        "np": np
    }

    exec(f"result = {pandas_code}", {}, local_vars)

    result = local_vars["result"]

    if isinstance(result, pd.Series):
        result = result.to_frame()

    return result
