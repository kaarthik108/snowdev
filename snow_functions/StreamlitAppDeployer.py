from snow_functions.SnowConnect import SnowflakeConnection
import os


class StreamlitAppDeployer(SnowflakeConnection):
    def __init__(self):
        super().__init__()
        self.session = self.get_session()
        self.stage_name = "snowdev"

    def create_stage_if_not_exists(self, stage_name):
        self.session.sql(
            f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE)"
        ).collect()

    def upload_to_stage(self, file_path, stage_name, app_name):
        if os.path.isfile(file_path):
            put_result = self.session.file.put(
                file_path,
                f"@{stage_name}/streamlit/{app_name}",
                auto_compress=False,
                overwrite=True,
            )
            print(f"App: {file_path} is {put_result[0].status}")

    def create_streamlit_app(self, streamlit_name, stage_name, app_name):
        self.database = self.session.get_current_database().replace('"', "")
        self.session.sql(
            f"""
            CREATE OR REPLACE STREAMLIT "{streamlit_name}" 
            ROOT_LOCATION = '@{stage_name}/streamlit/'
            MAIN_FILE = 'streamlit_app.py'
            QUERY_WAREHOUSE = 'COMPUTE_WH'
        """
        ).collect()

    def handler_streamlit(self, filepath):
        directory = os.path.dirname(filepath)

        if not os.path.exists(directory):
            print(f"Error: The directory {directory} does not exist.")
            return

        print(f"Deploying STREAMLIT APP from directory: {directory}")

        directory_parts = os.path.normpath(directory).split(os.sep)
        func_name = directory_parts[-1]  # Using the directory name as function name
        streamlit_name = func_name.replace("_", " ").capitalize()

        print(f"Uploading to Stage name: {self.stage_name}")
        print(f"func_name: {streamlit_name}")

        # Loop through all files in the directory and upload them
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            print(f"Uploading file: {file_path}")

            if os.path.isfile(file_path):
                self.upload_to_stage(file_path, self.stage_name, func_name)

        # Create a new streamlit app
        self.create_streamlit_app(streamlit_name, self.stage_name, func_name)
