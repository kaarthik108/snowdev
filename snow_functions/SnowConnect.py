import os
from typing import Any, Dict

import yaml
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
                """
                ░██████╗███╗░░██╗░█████╗░░██╗░░░░░░░██╗
                ██╔════╝████╗░██║██╔══██╗░██║░░██╗░░██║
                ╚█████╗░██╔██╗██║██║░░██║░╚██╗████╗██╔╝
                ░╚═══██╗██║╚████║██║░░██║░░████╔═████║░
                ██████╔╝██║░╚███║╚█████╔╝░░╚██╔╝░╚██╔╝░
                ╚═════╝░╚═╝░░╚══╝░╚════╝░░░░╚═╝░░░╚═╝░░
            """
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


import yaml


class SnowpipeRunner(SnowflakeConnection):
    """
    A class to handle running snowpipes in Snowflake.

    Attributes
    ----------
    session : snowflake.snowpark.Session
        a Snowflake session object
    pipe_name : str
        the name of the pipe to run
    yml_path : str
        the path to the snowpipe.yml file
    config : dict
        the configuration dictionary for the pipe
    sql_path : str
        the path to the SQL file to run
    pipe : dict
        the configuration dictionary for the pipe

    Methods
    -------
    _load_yml()
        Loads the snowpipe.yml file
    _get_pipe_info()
        Gets the pipe configuration from the snowpipe.yml file
    run_sql_with_yaml()
        Runs the SQL file with the YAML configuration
    """

    def __init__(self, pipe_name):
        super().__init__()
        self.session = self.get_session()
        self.yml_path = "src/snowpipe/snowpipe.yml"
        self.config = self._load_yml()
        self.pipe_name = pipe_name
        self.sql_path = f"src/snowpipe/{self.pipe_name}.sql"
        self.pipe = self._get_pipe_info()

    def _load_yml(self):
        with open(self.yml_path, "r") as file:
            return yaml.safe_load(file)

    def _get_pipe_info(self):
        for pipe in self.config["pipe"]:
            if pipe["name"] == self.pipe_name:
                return pipe
        raise ValueError(f"No pipe configuration found for '{self.pipe_name}'.")

    def handler_sql_with_yaml(self):
        with open(self.sql_path, "r") as sql_file:
            sql_template = sql_file.read()

        formatted_sql = sql_template.format(
            self.pipe["name"],
            self.pipe["database"],
            self.pipe["schema"],
            self.pipe["table"],
            self.pipe["stage"],
            self.pipe["stage_url"],
            self.pipe["file_format"],
            self.pipe["auto_ingest"],
        )

        self.session.sql(formatted_sql).collect()

    def handler_pipe(self):
        self.run_sql_with_yaml()
