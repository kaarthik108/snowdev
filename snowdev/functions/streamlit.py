from __future__ import annotations

import os

from termcolor import colored
import yaml


class StreamlitAppDeployer:
    def __init__(self, session, stage_name):
        self.session = session
        self.stage_name = stage_name
        self.warehouse = self.session.get_current_warehouse().replace('"', "")

    def create_stage_if_not_exists(self, stage_name):
        self.session.sql(
            f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE)"
        ).collect()

    def get_connection_details_from_yml(self, directory):
        """
        Parse the environment.yml file and extract the connection details.
        """
        yml_path = os.path.join(directory, "environment.yml")

        if not os.path.exists(yml_path):
            return {}

        with open(yml_path, "r") as file:
            content = yaml.safe_load(file)

        return content

    def _apply_connection_detail(self, directory, key, action, default_msg):
        """Apply a specific connection detail based on its key and the associated action."""
        connection_details = self.get_connection_details_from_yml(directory)
        detail = connection_details.get(key)
        if detail:
            try:
                action(detail)
                print(colored(f"Using {key}: {detail}", "green"))
            except Exception as e:
                print(colored(f"Error setting {key}: {e}", "red"))
        else:
            print(colored(default_msg, "yellow"))

    def apply_connection_details(self, directory):
        """Apply all the connection details."""
        self._apply_connection_detail(
            directory, "database", self.session.use_database, "Using default database"
        )
        self._apply_connection_detail(
            directory, "schema", self.session.use_schema, "Using default schema"
        )
        self._apply_connection_detail(
            directory, "role", self.session.use_role, "Using default role"
        )

    def upload_to_stage(self, file_path, stage_name, app_name):
        if os.path.isfile(file_path):
            # Uploading files can fail due to permissions, or network issues.
            # Check the response for any errors.
            put_result = self.session.file.put(
                file_path,
                f"@{stage_name}/streamlit/{app_name}",
                auto_compress=False,
                overwrite=True,
            )
            print(
                "\t\t-",
                colored(file_path, "yellow"),
                "...",
                colored(put_result[0].status.upper(), "green"),
            )

    def create_streamlit_app(self, func_name, stage_name, app_name):
        self.database = self.session.get_current_database().replace('"', "")
        streamlit_name = func_name.replace("_", " ").capitalize()
        
        self.session.sql(
            f"""
            CREATE OR REPLACE STREAMLIT "{streamlit_name}" 
            ROOT_LOCATION = '@{stage_name}/streamlit/{func_name}'
            MAIN_FILE = 'streamlit_app.py'
            QUERY_WAREHOUSE = '{self.warehouse}'
        """
        ).collect()

    def handler_streamlit(self, filepath):
        directory = os.path.dirname(filepath)

        if not os.path.exists(directory):
            print(colored(f"Error: The directory {directory} does not exist.", "red"))
            return

        self.connection_details = self.get_connection_details_from_yml(directory)

        self.apply_connection_details(directory)

        print(colored("Deploying STREAMLIT APP:", "cyan"))
        print("Directory:", colored(directory, "yellow"))

        directory_parts = os.path.normpath(directory).split(os.sep)
        func_name = directory_parts[-1]  # Using the directory name as function name
        streamlit_name = func_name.replace("_", " ").capitalize()

        print("\n\t", colored("Stage:", "magenta"), colored(self.stage_name, "yellow"))
        print("\t", colored("App Name:", "magenta"), colored(streamlit_name, "yellow"))
        print("\n\t", colored("Files:", "magenta"))

        # Loop through all files in the directory and upload them
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)

            # Check for file existence before attempting upload.
            if os.path.isfile(file_path):
                self.upload_to_stage(file_path, self.stage_name, func_name)

        try:
            self.create_streamlit_app(func_name, self.stage_name, func_name)
            print(
                "\n",
                colored(
                    f"Successfully Deployed Streamlit app: {streamlit_name}", "green"
                ),
            )
        except Exception as e:
            print(colored(f"Error: {e}", "red"))
            return
