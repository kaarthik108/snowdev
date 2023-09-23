from snowflake.snowpark import Session

def handler(session: Session, args) -> str:
    customer_data = session.sql("SELECT * FROM customer_table LIMIT 1")
    return customer_data.to_pandas()
 
# Local testing
# snowdev test --sproc sproc_name
if __name__ == "__main__":
    from snowdev import SnowflakeConnection
    session = SnowflakeConnection().get_session()

    print(handler(session,"test"))