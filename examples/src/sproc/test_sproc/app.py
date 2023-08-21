import datetime
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

# comment how the function should be executed choose from: caller, owner

# execute as caller


def handler(session: Session) -> str:

    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print(current_time)
    return current_time


# Local testing
if __name__ == "__main__":
    from snowdev import SnowflakeConnection

    session = SnowflakeConnection().get_session()
    handler(session)
