import streamlit as st

from sqlalchemy import create_engine

from config import *
from agent import DataMetricsAgent
from charts import generate_chart

st.set_page_config(
    page_title="AI Data Metrics Agent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI Data Metrics Agent")

sql_engine = create_engine(
    f"sqlite:///{DEFAULT_SQL_PATH}"
)

agent = DataMetricsAgent(
    sql_engine,
    DEFAULT_EXCEL_FILES,
    DEFAULT_CSV_FILES
)

question = st.chat_input(
    "Ask about your data..."
)

if question:

    result = agent.ask(question)

    st.write(result["answer"])

    st.dataframe(result["data"])

    fig = generate_chart(
        result["data"],
        result["plan"]
    )

    if fig:
        st.plotly_chart(
            fig,
            use_container_width=True
        )
