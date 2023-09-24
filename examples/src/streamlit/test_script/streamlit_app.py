import streamlit as st
from snowflake.snowpark import Session


def get_snowflake_session() -> Session:
    try:
        from snowdev import SnowflakeConnection

        snow_session = SnowflakeConnection().get_session()
    except ModuleNotFoundError:
        from snowflake.snowpark.context import get_active_session

        snow_session = get_active_session()
    return snow_session


session = get_snowflake_session()

st.set_page_config(
    layout="wide",
    page_title="Snowflake test",
    page_icon="❄️",
)

st.title("Testing")
st.caption("testing")
