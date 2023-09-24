import os

import pandas as pd
from snowflake.snowpark import Session


def handler(df: str) -> str:
    """
    Handler function for the UDF.
    """
    print("Hello World!")

    return df


# Local testing
# snowdev test --udf udf_name
if __name__ == "__main__":
    print(handler("test"))
