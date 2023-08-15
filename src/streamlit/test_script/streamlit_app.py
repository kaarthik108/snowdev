import streamlit as st
from snowflake.snowpark import Session
import yaml


def get_snowflake_connection() -> Session:
    try:
        from snowdev import SnowflakeConnection

        snow_session = SnowflakeConnection().get_session()
    except ModuleNotFoundError:
        from snowflake.snowpark.context import get_active_session

        snow_session = get_active_session()
    return snow_session


session = get_snowflake_connection()
laybuy_colour_palette = ["#751DFF", "#E1CFFF"]

with open("external.yml") as fh:
    query = yaml.safe_load(fh)


st.set_page_config(
    layout="wide",
    page_title="Snowflake test",
    page_icon="❄️",
)

st.title("Testing")
st.caption("testing")
