import datetime

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col


def handler(session: Session) -> str:

    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print(current_time)
    return current_time


# Local testing
if __name__ == "__main__":
    from snowdev import SnowflakeConnection

    session = SnowflakeConnection().get_session()
    handler(session)
