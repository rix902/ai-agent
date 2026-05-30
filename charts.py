import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def generate_chart(df: pd.DataFrame, plan: dict):

    chart_type = plan.get("chart_type", "none")

    if chart_type == "none":
        return None

    x_col = plan.get("chart_x", df.columns[0])
    y_col = plan.get("chart_y", df.columns[-1])

    if chart_type == "bar":
        return px.bar(df, x=x_col, y=y_col)

    if chart_type == "line":
        return px.line(df, x=x_col, y=y_col)

    if chart_type == "pie":
        return px.pie(df, names=x_col, values=y_col)

    if chart_type == "table":
        return go.Figure(
            data=[
                go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(
                        values=[df[c] for c in df.columns]
                    )
                )
            ]
        )

    return None
