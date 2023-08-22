from __future__ import annotations

import os
from typing import Any, Dict
from termcolor import colored

from snowflake.snowpark.session import Session
from snowflake.snowpark.version import VERSION


class SnowflakeConnection:
    """
    This class is used to establish a connection to Snowflake.

    Attributes
    ----------
    connection_parameters : Dict[str, Any]
        A dictionary containing the connection parameters for Snowflake.
    session : snowflake.snowpark.Session
        A Snowflake session object.

    Methods
    -------
    get_session()
        Establishes and returns the Snowflake connection session.

    """

    def __init__(self):
        self.connection_parameters = self._get_connection_parameters_from_env()
        self.session = None

    @staticmethod
    def _get_connection_parameters_from_env() -> Dict[str, Any]:
        connection_parameters = {
            "account": os.environ["ACCOUNT"],
            "user": os.environ["USER_NAME"],
            "password": os.environ["PASSWORD"],
            "warehouse": os.environ["WAREHOUSE"],
            "database": os.environ["DATABASE"],
            "schema": os.environ["SCHEMA"],
            "role": os.environ["ROLE"],
        }
        return connection_parameters

    def get_session(self):
        """
        Establishes and returns the Snowflake connection session.
        Returns:
            session: Snowflake connection session.
        """
        if self.session is None:
            print(
                colored(
                    """
                                       _            
            ___ _ __   _____      ____| | _____   __
            / __| '_ \ / _ \ \ /\ / / _` |/ _ \ \ / /
            \__ \ | | | (_) \ V  V / (_| |  __/\ V / 
            |___/_| |_|\___/ \_/\_/ \__,_|\___| \_/  
                                                    
            """,
                    "cyan",
                )
            )
            self.session = Session.builder.configs(self.connection_parameters).create()
            self.session.sql_simplifier_enabled = True
        return self.session

    def _get_snowflake_environment_info(self):
        return self.session.sql(
            """
            SELECT 
                current_user(), 
                current_role(), 
                current_database(), 
                current_schema(), 
                current_version(), 
                current_warehouse()
            """
        ).collect()

    def __str__(self) -> str:
        snowflake_environment = self._get_snowflake_environment_info()
        snowpark_version = VERSION

        info = (
            f"User                        : {snowflake_environment[0][0]}\n"
            f"Role                        : {snowflake_environment[0][1]}\n"
            f"Database                    : {snowflake_environment[0][2]}\n"
            f"Schema                      : {snowflake_environment[0][3]}\n"
            f"Warehouse                   : {snowflake_environment[0][5]}\n"
            f"Snowflake version           : {snowflake_environment[0][4]}\n"
            f'Snowpark for Python version : {".".join(map(str, snowpark_version))}'
        )

        return info
