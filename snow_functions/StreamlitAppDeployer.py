from snow_functions.SnowConnect import SnowflakeConnection
import os

class StreamlitAppDeployer(SnowflakeConnection):

    def __init__(self):
        super().__init__()
        self.session = self.get_session()
        self.warehouse_name = "STREAMLIT_APPS"
        self.stage_name = "STREAMLIT_APPS"

    def create_stage_if_not_exists(self, stage_name):
        self.session.sql(
            f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE)"
        ).collect()

    def upload_to_stage(self, file_path, stage_name, app_name):
        if os.path.isfile(file_path):
            put_result = self.session.file.put(
                file_path,
                f"@{stage_name}/{app_name}",
                auto_compress=False,
                overwrite=True,
            )
            print(f"App: {file_path} is {put_result[0].status}")

    def create_streamlit_app(
        self, streamlit_name, stage_name, app_name, warehouse_name
    ):
        self.database = self.session.get_current_database().replace('"', "")
        if self.database == "ANALYTICS":
            self.session.sql(
                f"""
                CREATE OR REPLACE STREAMLIT "{streamlit_name}" 
                ROOT_LOCATION = '@{stage_name}/{app_name}'
                MAIN_FILE = 'streamlit_app.py'
                QUERY_WAREHOUSE = '{warehouse_name}'
            """
            ).collect()
        else:
            print(
                f" You are not authorized to create streamlit apps in {self.database} database"
            )

    def grant_usage(self, streamlit_name):
        try:
            self.session.sql(
                f"""
                GRANT USAGE ON STREAMLIT "ANALYTICS"."PUBLIC"."{streamlit_name}" TO ROLE "ANALYST"
            """
            ).collect()
        except Exception:
            print(
                f" You are not authorized to grant usage on {streamlit_name} to role ANALYST {Exception}"
            )

    def run_streamlit(self, directory):
        directory_parts = os.path.normpath(directory).split(os.sep)
        func_name = directory_parts[-2]
        streamlit_name = func_name.replace("_", " ").capitalize()

        print(f"Deploying STREAMLIT APP: {func_name}")
        print(f"Uploading to Stage name: {self.stage_name}")

        print(f"func_name: {streamlit_name}")
        self.create_stage_if_not_exists(self.stage_name)

        # Define file paths based on the input directory
        streamlit_app_path = os.path.join(
            os.path.dirname(directory), "streamlit_app.py"
        )
        env_path = os.path.join(os.path.dirname(directory), "environment.yml")

        # UPLOAD streamlit_app.py
        self.upload_to_stage(streamlit_app_path, self.stage_name, func_name)

        # UPLOAD environment.yml
        self.upload_to_stage(env_path, self.stage_name, func_name)

        # create a new streamlit app
        self.create_streamlit_app(
            streamlit_name, self.stage_name, func_name, self.warehouse_name
        )

        # Grant usage
        self.grant_usage(streamlit_name)