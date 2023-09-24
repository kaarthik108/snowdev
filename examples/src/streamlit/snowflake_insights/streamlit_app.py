from snowflake.snowpark import Session

import streamlit as st
import altair as alt


def get_snowflake_session() -> Session:
    try:
        from snowdev import SnowflakeConnection

        snow_session = SnowflakeConnection().get_session()
    except ModuleNotFoundError:
        from snowflake.snowpark.context import get_active_session

        snow_session = get_active_session()
    return snow_session


session = get_snowflake_session()

# Set up Streamlit config
st.set_page_config(layout="wide", page_title="Snowflake Insights", page_icon="❄️")

# Title
st.title("Snowflake Insights Dashboard")
st.caption("Visualizing and Analyzing Data from Snowflake")

# Fetch Customer Data
customer_query = "SELECT * FROM STREAM_HACKATHON.STREAMLIT.CUSTOMER_DETAILS"
customer_df = session.sql(customer_query).to_pandas()

# Display Customer Insights
st.subheader("Customer Insights")
st.dataframe(customer_df.head())
st.write(f"Total Unique Customers: {customer_df['CUSTOMER_ID'].nunique()}")

# Fetch Order Data
order_query = "SELECT * FROM STREAM_HACKATHON.STREAMLIT.ORDER_DETAILS"
order_df = session.sql(order_query).to_pandas()

# Display Order Insights
st.subheader("Order Insights")
st.dataframe(order_df.head())

# Time-Series chart for Total Orders Over Time using Altair
order_chart = (
    alt.Chart(order_df)
    .mark_line()
    .encode(
        x="ORDER_DATE:T", y="TOTAL_AMOUNT:Q", tooltip=["ORDER_DATE", "TOTAL_AMOUNT"]
    )
    .properties(width=600, height=300, title="Total Orders Over Time")
)

st.altair_chart(order_chart, use_container_width=True)

# Fetch Product Data
product_query = "SELECT * FROM STREAM_HACKATHON.STREAMLIT.PRODUCTS"
product_df = session.sql(product_query).to_pandas()

# Display Product Insights
st.subheader("Product Insights")
st.dataframe(product_df.head())

# Bar chart for Products by Category using Altair
product_chart = (
    alt.Chart(product_df)
    .mark_bar()
    .encode(
        x="CATEGORY:N",
        y="count():Q",
        color="CATEGORY:N",
        tooltip=["CATEGORY", "count()"],
    )
    .properties(width=600, height=300, title="Number of Products by Category")
)

st.altair_chart(product_chart, use_container_width=True)
