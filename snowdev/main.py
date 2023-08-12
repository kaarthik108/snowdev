import argparse
import os
from dataclasses import dataclass
import subprocess
from typing import Optional

from pydantic import BaseModel, validator
from snow_functions import SnowConnect, SnowHelper, SnowRegister, StreamlitAppDeployer, TaskRunner

class DeploymentArguments(BaseModel):
    udf: Optional[str]
    sproc: Optional[str]
    stream: Optional[str]
    task: Optional[str]
    pipe: Optional[str]
    test: bool = False
    upload: Optional[str]

    @validator("udf", "sproc", "stream", "pipe")
    def validate_path(cls, v, field):
        if v is not None:
            path_map = {
                "udf": "src/udf/",
                "sproc": "src/stored_procs/",
                "stream": "src/streamlit/",
            }
            path_prefix = path_map.get(field.name, "")
            if not os.path.exists(path_prefix + v):
                raise ValueError(f"Provided path does not exist: {path_prefix + v}")
        return v


@dataclass
class DeploymentManager:
    args: DeploymentArguments

    def main(self):
        if self.args.test:
            self.test_locally()
            return
        if self.args.upload == "static":
            self.upload_static()

        if self.args.udf:
            self.deploy_udf("src/udf/" + self.args.udf + "/app.py")
        elif self.args.sproc:
            self.deploy_sproc("src/stored_procs/" + self.args.sproc + "/app.py")
        elif self.args.stream:
            self.deploy_streamlit(
                "src/streamlit/" + self.args.stream + "/streamlit_app.py"
            )
        elif self.args.task:
            self.deploy_task(self.args.task)
        elif self.args.pipe:
            self.deploy_pipe(self.args.pipe)

    def test_locally(self):
        if self.args.sproc:
            dir_path = f"src/stored_procs/{self.args.sproc}/"
            self.run_poetry_script(dir_path)

    def run_poetry_script(self, dir_path):
        os.chdir(dir_path)
        subprocess.call(["poetry", "install"])
        subprocess.call(["poetry", "run", "python", "app.py"])

    def deploy_udf(self, filepath):
        dir_path, filename = os.path.split(filepath)
        FUNCTION_NAME = os.path.basename(dir_path)

        STAGE_LOCATION = "snowdev_stage"
        PACKAGES = SnowHelper.get_packages_from_requirements(dir_path)
        IMPORTS = SnowHelper.get_imports(dir_path)

        print(f"packages: {PACKAGES}")
        SNOW_DEPLOY = SnowRegister.snowflakeregister()
        try:
            SNOW_DEPLOY.main(
                func=filepath,
                function_name=FUNCTION_NAME,
                stage_location=STAGE_LOCATION,
                packages=PACKAGES,
                imports=IMPORTS,
                is_sproc=False,
            )
            print(f"Deployed UDF {FUNCTION_NAME} successfully.")
        except Exception as e:
            raise Exception(f"Error deploying UDF: {e}")

    def deploy_sproc(self, filepath):
        dir_path, filename = os.path.split(filepath)
        STORED_PROC_NAME = os.path.basename(dir_path)
        STAGE_LOCATION = "snowdev_stage"
        PACKAGES = SnowHelper.get_packages_from_toml(dir_path)
        upload_dir = f"src/stored_procs/{STORED_PROC_NAME}/uploads"
        SNOW_DEPLOY = SnowRegister.snowflakeregister()

        if os.path.isdir(upload_dir) and len(os.listdir(upload_dir)) > 0:
            for root, dirs, files in os.walk(upload_dir):
                for file in files:
                    print(f"Uploading file {file} to stage {STAGE_LOCATION}")
                    file_path = os.path.join(root, file)
                    remote_path = f"@{STAGE_LOCATION}/{STORED_PROC_NAME}"
                    SNOW_DEPLOY.session.file.put(
                        file_path, remote_path, overwrite=True, auto_compress=False
                    )
        try:
            IMPORTS = SnowHelper.get_imports(dir_path)
        except Exception:
            print("No imports found.")
            IMPORTS = None

        try:
            SNOW_DEPLOY.main(
                func=filepath,
                function_name=STORED_PROC_NAME,
                stage_location=STAGE_LOCATION,
                packages=PACKAGES,
                is_sproc=True,
                imports=IMPORTS,
            )

            print(f"Deployed stored procedure {STORED_PROC_NAME} successfully.")
        except Exception as e:
            raise Exception(f"Error deploying stored procedure: {e}")

    def deploy_streamlit(self, filepath):
        dir_path, filename = os.path.split(filepath)
        STREAMLIT_NAME = os.path.basename(dir_path)
        STAGE_LOCATION = "STREAMLIT_APPS"
        deployer = StreamlitAppDeployer()
        session = SnowConnect.SnowflakeConnection().get_session()
        database = session.sql(
            """
            SELECT 
                 current_database()
            """
        ).collect()

        upload_dir = f"src/streamlit/{STREAMLIT_NAME}/uploads"

        if database[0][0] == "ANALYTICS":
            if os.path.isdir(upload_dir) and len(os.listdir(upload_dir)) > 0:
                for root, dirs, files in os.walk(upload_dir):
                    for file in files:
                        print(f"Uploading file {file} to stage {STAGE_LOCATION}")
                        file_path = os.path.join(root, file)
                        remote_path = f"@{STAGE_LOCATION}/{STREAMLIT_NAME}"
                        session.file.put(
                            file_path, remote_path, overwrite=True, auto_compress=False
                        )
            try:
                deployer.run_streamlit(directory=filepath)

                print(f"Deployed Streamlit app {filepath} successfully.")
            except Exception as e:
                raise Exception(f"Error deploying Streamlit app: {e}")  # noqa: B904
        else:
            print("You must be in the ANALYTICS database to deploy a Streamlit app.")

    def deploy_task(self, taskname):
        runner = TaskRunner(taskname)
        session = SnowConnect.SnowflakeConnection().get_session()
        database = session.sql(
            """
            SELECT 
                 current_database()
            """
        ).collect()

        if database[0][0] == "ANALYTICS":
            try:
                runner.run_task()
                print(f"Deployed task {taskname} successfully.")
            except Exception as e:
                raise Exception(f"Error deploying task: {e}")  # noqa: B904
        else:
            print("You must be in the ANALYTICS database to run/schedule a task.")

    def get_current_environment_info(self):
        snowConnect = SnowConnect.SnowflakeConnection()
        snowConnect.get_session()
        env_info = snowConnect._get_snowflake_environment_info()

        return {
            'user': env_info[0][0],
            'role': env_info[0][1],
            'database': env_info[0][2],
            'schema': env_info[0][3],
            'version': env_info[0][4],
            'warehouse': env_info[0][5]
        }

    def stage_exists(self, stage_name):
        try:
            # Assuming SnowflakeConnection's get_session() returns a Snowflake session
            session = SnowConnect.SnowflakeConnection().get_session()
            query = f"DESC STAGE {stage_name};"
            print(f"Query: {query}")
            session.sql(query).collect()
            return True
        except:
            return False
    
    def create_stage(self, stage_name):
        try:
            session = SnowConnect.SnowflakeConnection().get_session()
            query = f"CREATE STAGE {stage_name};"
            session.sql(query)
            print(f"Stage {stage_name} created successfully.")
        except Exception as e:
            print(f"Error creating stage {stage_name}: {e}")

        
    def upload_static(self):
        static_folder = "static"  # assuming the static folder is at the root level of your project
        
        env_info = self.get_current_environment_info()
        STAGE_LOCATION = f"{env_info['database']}.{env_info['schema']}.SNOWDEV_STAGE"
        SNOW_DEPLOY = SnowRegister.snowflakeregister()
        print(f"Current stage: {STAGE_LOCATION}")
        if not self.stage_exists(STAGE_LOCATION):
            print(f"Stage {STAGE_LOCATION} does not exist. Creating it...")
            self.create_stage(STAGE_LOCATION)

        if os.path.isdir(static_folder) and len(os.listdir(static_folder)) > 0:
            for root, dirs, files in os.walk(static_folder):
                for file in files:
                    print(f"Uploading file {file} to stage {STAGE_LOCATION}")
                    file_path = os.path.join(root, file)
                    remote_path = f"@{STAGE_LOCATION}/{file}"
                    SNOW_DEPLOY.session.file.put(
                        file_path, remote_path, overwrite=True, auto_compress=False
                    )


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Snowflake UDFs and Stored Procedures."
    )
    parser.add_argument(
        "--udf", type=str, help="The relative path to the UDF python file to deploy."
    )
    parser.add_argument(
        "--sproc",
        type=str,
        help="The relative path to the Stored Procedure python file to deploy.",
    )
    parser.add_argument(
        "--stream",
        type=str,
        help="The relative path to the Streamlit python file to deploy.",
    )
    parser.add_argument("--task", type=str, help="The task name to schedule.")
    parser.add_argument("--pipe", type=str, help="The pipe name to deploy.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the sproc locally using poetry.",
    )

    parser.add_argument(
        "--upload",
        type=str,
        choices=["static"],  # expand this list if you have other things to upload in the future
        help="Specify what to upload (e.g., static).",
    )

    args = parser.parse_args()
    deployment_args = DeploymentArguments(
        udf=args.udf,
        sproc=args.sproc,
        stream=args.stream,
        task=args.task,
        pipe=args.pipe,
        test=args.test,
        upload=args.upload,
    )
    deployment_manager = DeploymentManager(deployment_args)
    deployment_manager.main()
