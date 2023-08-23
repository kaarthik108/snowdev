import os
import subprocess
from typing import Optional

import toml
from pydantic import BaseModel, validator
from termcolor import colored

from snowdev import (
    SnowflakeConnection,
    SnowflakeRegister,
    SnowHelper,
    SnowPackageZip,
    StreamlitAppDeployer,
)


class DeploymentArguments(BaseModel):
    udf: Optional[str]
    sproc: Optional[str]
    streamlit: Optional[str]
    test: bool = False
    upload: Optional[str]
    package: Optional[str]

    @validator("udf", "sproc", "streamlit", pre=True, always=True)
    def path_exists(cls, value, values, field, **kwargs):
        if value:
            path = ""
            if "udf" in field.name:
                path = os.path.join(DeploymentManager.UDF_PATH, value)
            elif "sproc" in field.name:
                path = os.path.join(DeploymentManager.SPROC_PATH, value)
            elif "streamlit" in field.name:
                path = os.path.join(DeploymentManager.STREAMLIT_PATH, value)

            if not os.path.exists(path):
                error_message = colored(
                    f"\n❌ ERROR: The specified path '{path}' does not exist. Please ensure the path is correct and try again.\n",
                    "red",
                )
                raise ValueError(error_message)
        return value


class DeploymentManager:
    UDF_PATH = "src/udf/"
    SPROC_PATH = "src/sproc/"
    STREAMLIT_PATH = "src/streamlit/"

    def __init__(self, args=None):
        self.args = args
        self.stage_name = "SNOWDEV"
        self.session = SnowflakeConnection().get_session()
        self.current_database = self.session.get_current_database().replace('"', "")
        self.current_schema = self.session.get_current_schema().replace('"', "")

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
            self.deploy_package()
            return

        deployment_path_map = {
            "udf": self.UDF_PATH,
            "sproc": self.SPROC_PATH,
            "streamlit": self.STREAMLIT_PATH,
        }

        for arg_key, path in deployment_path_map.items():
            arg_value = getattr(self.args, arg_key, None)
            if arg_value:
                # Adjust the filename based on the arg_key
                filename = "streamlit_app.py" if arg_key == "streamlit" else "app.py"
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
        elif deployment_type == "streamlit":
            self.deploy_streamlit(filepath)

    def deploy_function(self, filepath, is_sproc):
        dir_path, filename = os.path.split(filepath)
        function_name = os.path.basename(dir_path)
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

        # print("packages are----", packages)
        try:
            self.snow_deploy = SnowflakeRegister(session=self.session)
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

    def deploy_package(self, package_name, upload):
        try:
            SnowPackageZip(
                self.session,
                self.stage_name,
            ).deploy_package(package_name, upload)
        except Exception as e:
            self.handle_deployment_error(e, "package")

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
        if not self.args:
            print("No arguments provided!")
            return
        if self.args.sproc:
            dir_path = f"{self.SPROC_PATH}{self.args.sproc}/"
            self.run_poetry_script(dir_path)
        elif self.args.udf:
            dir_path = f"{self.UDF_PATH}{self.args.udf}/"
            self.run_poetry_script(dir_path)

    def run_poetry_script(self, dir_path):
        os.chdir(dir_path)

        subprocess.call(["poetry", "env", "use", "python3"])

        venv_path = (
            subprocess.check_output(["poetry", "env", "info", "-p"]).decode().strip()
        )
        pip_path = os.path.join(venv_path, "bin", "pip")

        with open("app.toml", "r") as file:
            data = file.readlines()
            for line in data:
                if "=" in line and not line.startswith("["):
                    package = line.split("=")[0].strip()
                    subprocess.call([pip_path, "install", package])

        subprocess.call(["poetry", "run", "python", "app.py"])

    def install_external_dependencies(self, dir_path):
        toml_content = toml.load("app.toml")
        external_deps = (
            toml_content.get("tool", {})
            .get("poetry", {})
            .get("external_dependencies", {})
        )

        for package, version in external_deps.items():
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

    def deploy_task(self, taskname):
        pass

    def deploy_pipe(self, pipe_name):
        pass

    @staticmethod
    def create_directory_structure():
        dirs_to_create = {
            "src": ["sproc", "streamlit", "udf"],
            "static": ["packages"],
        }

        # Initialize a flag to check if the structure already exists
        structure_already_exists = True

        for root_dir, sub_dirs in dirs_to_create.items():
            if not os.path.exists(root_dir):
                structure_already_exists = False
                os.mkdir(root_dir)
                for sub_dir in sub_dirs:
                    os.mkdir(os.path.join(root_dir, sub_dir))

        files_to_create = [".env", ".gitignore", "pyproject.toml"]

        if not os.path.exists(".env"):
            structure_already_exists = False
            with open(".env", "w") as f:
                f.write("")

        if not os.path.exists(".gitignore"):
            structure_already_exists = False
            with open(".gitignore", "w") as f:
                f.write("*.pyc\n__pycache__/\n.env")

        if not os.path.exists("pyproject.toml"):
            structure_already_exists = False
            template_path = SnowHelper.get_template_path("fillers/pyproject.toml")
            try:
                with open(template_path, "r") as template_file:
                    content = template_file.read()

                with open("pyproject.toml", "w") as f:
                    f.write(content)
            except FileNotFoundError:
                print(colored(f"Error: Template {template_path} not found!", "red"))

        if structure_already_exists:
            print(colored("Project structure is already initialized!", "yellow"))
        else:
            print(colored("Project structure initialized!", "green"))
