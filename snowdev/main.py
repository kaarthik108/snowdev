import argparse
import os
import subprocess
from typing import Optional
from termcolor import colored

from pydantic import BaseModel
from snow_functions.SnowConnect import SnowflakeConnection
from snow_functions.SnowRegister import snowflakeregister
from snow_functions.SnowPackageZip import SnowPackageZip
from snow_functions.SnowHelper import SnowHelper
from snow_functions.StreamlitAppDeployer import StreamlitAppDeployer
from snow_functions.TaskRunner import TaskRunner
import toml


class DeploymentArguments(BaseModel):
    udf: Optional[str]
    sproc: Optional[str]
    stream: Optional[str]
    task: Optional[str]
    pipe: Optional[str]
    test: bool = False
    upload: Optional[str]
    package: Optional[str]


class DeploymentManager:
    UDF_PATH = "src/udf/"
    SPROC_PATH = "src/stored_procs/"
    STREAM_PATH = "src/streamlit/"

    def __init__(self, args):
        self.args = args
        self.stage_name = "SNOWDEV"
        self.session = SnowflakeConnection().get_session()
        self.current_database = self.session.sql("SELECT current_database()").collect()[
            0
        ][0]
        self.current_schema = self.session.sql("SELECT current_schema()").collect()[0][
            0
        ]

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

        if self.args.package:
            # self.deploy_package(self.args.package)
            SnowPackageZip(
                self.session,
                self.current_database,
                self.current_schema,
                self.stage_name,
            ).deploy_package(self.args.package)
            return

        deployment_path_map = {
            "udf": self.UDF_PATH,
            "sproc": self.SPROC_PATH,
            "stream": self.STREAM_PATH,
        }

        for arg_key, path in deployment_path_map.items():
            arg_value = getattr(self.args, arg_key, None)
            if arg_value:
                # Adjust the filename based on the arg_key
                filename = "streamlit_app.py" if arg_key == "stream" else "app.py"
                self.deploy(arg_key, f"{path}{arg_value}/{filename}")
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
        print("dir path is ------", dir_path)
        packages = self.get_packages_from_toml(dir_path)
        imports = self.get_imports(dir_path)
        # Extract just the package names without versions
        package_names = [pkg.split("==")[0] for pkg in packages]

        packages_to_check = [
            package
            for package in package_names
            if package != "snowflake-snowpark-python"
        ]
        unavailable_packages = [
            package
            for package in packages_to_check
            if not SnowHelper.is_package_available_in_snowflake_channel(package)
        ]

        if unavailable_packages:
            print(
                colored(
                    f"Error: These packages are not available in Snowflake's Anaconda channel: {', '.join(unavailable_packages)}",
                    "red",
                )
            )
            print(
                colored(
                    "Consider using the command 'snowdev --package <package_name>' to zip and then use in imports.txt.",
                    "yellow",
                )
            )
            return

        print("packages are----", packages)
        try:
            self.snow_deploy = snowflakeregister(session=self.session)
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
                "green",
            )
            print(success_msg)
        except Exception as e:
            self.handle_deployment_error(e, "stored procedure" if is_sproc else "UDF")

    def deploy_streamlit(self, filepath):
        deployer = StreamlitAppDeployer(
            session=self.session, stage_name=self.stage_name
        )
        try:
            deployer.handler_streamlit(filepath=filepath)
        except Exception as e:
            self.handle_deployment_error(e, "Streamlit app")

    def deploy_task(self, taskname):
        runner = TaskRunner(taskname)
        try:
            runner.run_task()
            success_msg = colored(f"Deployed task {taskname} successfully.", "green")
            print(success_msg)
        except Exception as e:
            self.handle_deployment_error(e, "task")

    def get_packages_from_toml(self, dir_path):
        return SnowHelper.get_packages_from_toml(dir_path)

    def get_imports(self, dir_path):
        try:
            return SnowHelper.get_imports(dir_path)
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

        # Create a new poetry environment
        subprocess.call(["poetry", "env", "use", "python3"])

        # Activate the virtual environment
        venv_path = (
            subprocess.check_output(["poetry", "env", "info", "-p"]).decode().strip()
        )
        pip_path = os.path.join(venv_path, "bin", "pip")

        # Install dependencies directly using pip from app.toml
        with open("app.toml", "r") as file:
            data = file.readlines()
            for line in data:
                if "=" in line and not line.startswith("["):
                    package = line.split("=")[0].strip()
                    subprocess.call([pip_path, "install", package])

        # Run app.py
        subprocess.call(["poetry", "run", "python", "app.py"])

    def install_external_dependencies(self, dir_path):
        # Parse the pyproject.toml file for external dependencies
        toml_content = toml.load("app.toml")
        external_deps = (
            toml_content.get("tool", {})
            .get("poetry", {})
            .get("external_dependencies", {})
        )

        for package, version in external_deps.items():
            # Use poetry add to install the external dependencies
            subprocess.call(["poetry", "add", f"{package}=={version}"])

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
        stage_location = (
            f"{self.current_database}.{self.current_schema}.{self.stage_name}"
        )

        if not self.stage_exists(stage_location):
            warning = colored(
                f"Stage {stage_location} does not exist. Creating it...", "yellow"
            )
            print(warning)
            self.create_stage(stage_location)

        if os.path.isdir(static_folder) and len(os.listdir(static_folder)) > 0:
            for root, dirs, files in os.walk(static_folder):
                for file in files:
                    info_msg = colored(
                        f"Uploading file {file} to stage {stage_location}", "blue"
                    )
                    print(info_msg)
                    file_path = os.path.join(root, file)
                    remote_path = f"@{stage_location}/static/"
                    self.session.file.put(
                        file_path, remote_path, overwrite=True, auto_compress=False
                    )

    def deploy_pipe(self, pipe_name):
        pass

    def get_packages(self, dir_path):
        package_file = os.path.join(dir_path, "app.toml")

        # Assuming app.toml has a structure like: [dependencies] \n package_name = "version"
        toml_data = toml.load(package_file)
        dependencies = toml_data.get("dependencies", {})
        print("zipping")
        # List of packages that need to be zipped and uploaded
        packages_to_upload = []

        for package in dependencies:
            if not SnowHelper.SnowHelper.is_package_available_in_snowflake_channel(
                package
            ):
                self.zip_and_upload_package(package, dir_path)
                packages_to_upload.append(package)

        return packages_to_upload

    def get_poetry_venv_path(self):
        try:
            # Use Poetry to get the path to the virtual environment
            venv_path = subprocess.check_output(
                ["poetry", "env", "info", "--path"], text=True
            ).strip()
            return venv_path
        except subprocess.CalledProcessError:
            print(
                colored(
                    "Error: Couldn't determine Poetry virtual environment path.", "red"
                )
            )
            return None


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
    parser.add_argument(
        "--package",
        type=str,
        help="Name of the package to zip and upload to the static folder.",
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
        package=args.package,
    )
    deployment_manager = DeploymentManager(deployment_args)
    deployment_manager.main()
