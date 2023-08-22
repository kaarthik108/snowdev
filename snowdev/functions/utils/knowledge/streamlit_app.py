# This is example code for a streamlit app that runs in Snowflake. It's a simple dashboard that fetches data from Snowflake and visualizes it using streamlit.

import pandas as pd
from snowflake.snowpark import Session

import streamlit as st


def get_snowflake_session() -> Session:
    """
    Establish a connection to the Snowflake session.

    This function first attempts to use a custom connection (assuming the user might have their
    own connection script `snowdev`). If this method fails, it falls back to the default Snowflake
    connection.

    Returns:
        Session: Active Snowflake session.
    """
    try:
        # for local testing
        from snowdev import SnowflakeConnection

        snow_session = SnowflakeConnection().get_session()
    except ModuleNotFoundError:
        # for snowflake
        from snowflake.snowpark.context import get_active_session

        snow_session = get_active_session()
    return snow_session


def fetch_sales_data(session: Session) -> pd.DataFrame:
    """
    Fetch sales data from Snowflake.

    Args:
        session (Session): Active Snowflake session.

    Returns:
        pd.DataFrame: Sales data by category.
    """
    sales_data = session.sql(
        "SELECT category, SUM(sales) as total_sales FROM sales_table GROUP BY category"
    )
    return sales_data.to_pandas()


session = get_snowflake_session()

# Streamlit configuration
st.set_page_config(
    layout="wide",
    page_title="Sales Dashboard with Streamlit and Snowflake",
    page_icon="❄️",
)

st.title("Sales Dashboard")
st.caption("Visualizing sales data fetched directly from Snowflake!")

# Fetch data and visualize
df_sales = fetch_sales_data(session)
st.bar_chart(df_sales.set_index("category"))

st.sidebar.header("Settings")
st.sidebar.text(
    "Here, you can add controls related to data filters, date ranges, or any other parameter for the dashboard."
)
