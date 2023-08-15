import os

from termcolor import colored


class StreamlitAppDeployer:
    def __init__(self, session, stage_name):
        self.session = session
        self.stage_name = stage_name
        self.warehouse = self.session.get_current_warehouse().replace('"', "")

    def create_stage_if_not_exists(self, stage_name):
        # Using SQL commands in string formats can be error-prone.
        # Ensure proper validations and avoid SQL injections.
        self.session.sql(
            f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE)"
        ).collect()

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

    def create_streamlit_app(self, streamlit_name, stage_name, app_name):
        self.database = self.session.get_current_database().replace('"', "")
        # Again, ensure SQL command safety.
        self.session.sql(
            f"""
            CREATE OR REPLACE STREAMLIT "{streamlit_name}" 
            ROOT_LOCATION = '@{stage_name}/streamlit/'
            MAIN_FILE = 'streamlit_app.py'
            QUERY_WAREHOUSE = '{self.warehouse}'
        """
        ).collect()

    def handler_streamlit(self, filepath):
        directory = os.path.dirname(filepath)

        # Check if the directory exists before proceeding.
        if not os.path.exists(directory):
            print(colored(f"Error: The directory {directory} does not exist.", "red"))
            return

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
            self.create_streamlit_app(streamlit_name, self.stage_name, func_name)
            print(
                "\n",
                colored(
                    f"Successfully Deployed Streamlit app: {streamlit_name}", "green"
                ),
            )
        except Exception as e:
            print(colored(f"Error: {e}", "red"))
            return
