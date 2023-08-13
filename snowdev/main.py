import argparse
import os
import subprocess
from typing import Optional
from termcolor import colored

from pydantic import BaseModel
from snow_functions import (
    SnowHelper,
    SnowRegister,
    StreamlitAppDeployer,
    TaskRunner,
)


class DeploymentArguments(BaseModel):
    udf: Optional[str]
    sproc: Optional[str]
    stream: Optional[str]
    task: Optional[str]
    pipe: Optional[str]
    test: bool = False
    upload: Optional[str]


class DeploymentManager:
    UDF_PATH = "src/udf/"
    SPROC_PATH = "src/stored_procs/"
    STREAM_PATH = "src/streamlit/"

    def __init__(self, args):
        self.args = args
        self.stage_name = "SNOWDEV"
        self.snow_deploy = SnowRegister.snowflakeregister()
        self.session = self.snow_deploy.session
        self.current_database = self.session.sql("SELECT current_database()").collect()[0][0]
        self.current_schema = self.session.sql("SELECT current_schema()").collect()[0][0]

    def handle_deployment_error(self, e, deployment_type):
        error_msg = colored(f"Error deploying {deployment_type}: {e}", "red")
        raise Exception(error_msg)

    def main(self):
        if self.args.test:
            self.test_locally()
            return

        if self.args.upload == "static":
            self.upload_static()
            return

        deployment_path_map = {
            "udf": self.UDF_PATH,
            "sproc": self.SPROC_PATH,
            "stream": self.STREAM_PATH,
        }

        for arg_key, path in deployment_path_map.items():
            arg_value = getattr(self.args, arg_key, None)
            if arg_value:
                self.deploy(arg_key, f"{path}{arg_value}/app.py")
                break
        else:
            if self.args.task:
                self.deploy_task(self.args.task)
            elif self.args.pipe:
                self.deploy_pipe(self.args.pipe)

    def deploy(self, deployment_type, filepath):
        if deployment_type in ["udf", "sproc"]:
            is_sproc = deployment_type == "sproc"
            self.deploy_function(filepath, is_sproc)
        elif deployment_type == "stream":
            self.deploy_streamlit(filepath)

    def deploy_function(self, filepath, is_sproc):
        dir_path, filename = os.path.split(filepath)
        function_name = os.path.basename(dir_path)

        packages = self.get_packages(dir_path)
        imports = self.get_imports(dir_path)

        try:
            self.snow_deploy.main(
                func=filepath,
                function_name=function_name,
                stage_location=self.stage_name,
                packages=packages,
                imports=imports,
                is_sproc=is_sproc,
            )
            success_msg = colored(
                f"Deployed {'stored procedure' if is_sproc else 'UDF'} {function_name} successfully.",
                "green"
            )
            print(success_msg)
        except Exception as e:
            self.handle_deployment_error(e, 'stored procedure' if is_sproc else 'UDF')


    def deploy_streamlit(self, filepath):
        if not self.is_current_database_analytics():
            warning = colored("You must be in the ANALYTICS database to deploy a Streamlit app.", "yellow")
            print(warning)
            return

        deployer = StreamlitAppDeployer()
        try:
            deployer.run_streamlit(directory=filepath)
            success_msg = colored(f"Deployed Streamlit app {filepath} successfully.", "green")
            print(success_msg)
        except Exception as e:
            self.handle_deployment_error(e, "Streamlit app")

    def deploy_task(self, taskname):
        if not self.is_current_database_analytics():
            warning = colored("You must be in the ANALYTICS database to run/schedule a task.", "yellow")
            print(warning)
            return

        runner = TaskRunner(taskname)
        try:
            runner.run_task()
            success_msg = colored(f"Deployed task {taskname} successfully.", "green")
            print(success_msg)
        except Exception as e:
            self.handle_deployment_error(e, "task")

    def is_current_database_analytics(self):
        database = self.session.sql("SELECT current_database()").collect()
        return database[0][0] == "ANALYTICS"

    def get_packages(self, dir_path):
        return SnowHelper.SnowHelper.get_packages_from_toml(dir_path)

    def get_imports(self, dir_path):
        try:
            return SnowHelper.SnowHelper.get_imports(dir_path)
        except Exception:
            warning = colored("No imports found.", "yellow")
            print(warning)
            return None

    def test_locally(self):
        if self.args.sproc:
            dir_path = f"{self.SPROC_PATH}{self.args.sproc}/"
            self.run_poetry_script(dir_path)
        elif self.args.udf:
            dir_path = f"{self.UDF_PATH}{self.args.udf}/"
            self.run_poetry_script(dir_path)

    def run_poetry_script(self, dir_path):
        os.chdir(dir_path)
        subprocess.call(["poetry", "install"])
        subprocess.call(["poetry", "run", "python", "app.py"])

    def stage_exists(self, stage_name):
        try:
            query = f"DESC STAGE {stage_name};"
            self.session.sql(query).collect()
            return True
        except:
            return False

    def create_stage(self, stage_name):
        try:
            query = f"CREATE STAGE {stage_name};"
            self.session.sql(query).collect()
            success_msg = colored(f"Stage {stage_name} created successfully.", "green")
            print(success_msg)
        except Exception as e:
            error_msg = colored(f"Error creating stage {stage_name}: {e}", "red")
            raise Exception(error_msg)

    def upload_static(self):
        static_folder = "static"
        stage_location = f"{self.current_database}.{self.current_schema}.{self.stage_name}"

        if not self.stage_exists(stage_location):
            warning = colored(f"Stage {stage_location} does not exist. Creating it...", "yellow")
            print(warning)
            self.create_stage(stage_location)

        if os.path.isdir(static_folder) and len(os.listdir(static_folder)) > 0:
            for root, dirs, files in os.walk(static_folder):
                for file in files:
                    info_msg = colored(f"Uploading file {file} to stage {stage_location}", "blue")
                    print(info_msg)
                    file_path = os.path.join(root, file)
                    remote_path = f"@{stage_location}/static/"
                    self.session.file.put(
                        file_path, remote_path, overwrite=True, auto_compress=False
                    )

    def deploy_pipe(self, pipe_name):
        pass


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
        choices=[
            "static"
        ],  # expand this list if you have other things to upload in the future
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
