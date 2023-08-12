import datetime
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

from snow_functions import SnowConnect


def run(session: Session) -> str:

    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print(current_time)
    return current_time

session = SnowConnect.SnowflakeConnection().get_session()

run(session)