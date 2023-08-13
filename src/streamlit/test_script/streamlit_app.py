import streamlit as st
from snowflake.snowpark import Session
import yaml


def get_snowflake_connection() -> Session:
    try:
        from snow_functions import SnowConnect

        snow_session = SnowConnect.SnowflakeConnection()
    except ModuleNotFoundError:
        from snowflake.snowpark.context import get_active_session

        snow_session = (
            get_active_session()
        )  # Get current Snowflake session from Snowsight
    return snow_session


session = get_snowflake_connection()
laybuy_colour_palette = ["#751DFF", "#E1CFFF"]

with open("query.yml") as fh:
    query = yaml.safe_load(fh)


st.set_page_config(
    layout="wide",
    page_title="Snowflake test",
    page_icon="❄️",
)

st.title("Testing")
st.caption("testing")
