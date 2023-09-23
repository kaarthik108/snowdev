from snowflake.snowpark import Session

def get_snowflake_session() -> Session:
    try:
        from snowdev import SnowflakeConnection
        snow_session = SnowflakeConnection().get_session()
    except ModuleNotFoundError:
        from snowflake.snowpark.context import get_active_session
        snow_session = get_active_session()
    return snow_session

def fetch_customer_data(session: Session):
    customer_data = session.sql("SELECT * FROM customer_table LIMIT 1")
    return customer_data.to_pandas()

session = get_snowflake_session()
df_customer = fetch_customer_data(session)
