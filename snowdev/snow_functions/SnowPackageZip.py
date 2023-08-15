import os
import subprocess
import tempfile
import zipfile

from . import SnowHelper


class SnowPackageZip:
    def __init__(self, session, current_database, current_schema, stage_name):
        self.session = session
        self.current_database = current_database
        self.current_schema = current_schema
        self.stage_name = stage_name

    def zip_and_upload_package(self, package_name):
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = os.path.join(temp_dir, "venv")
            package_path = os.path.join(venv_path, "lib", "python3.9", "site-packages")

            # Create a virtual environment
            subprocess.check_call(["python3", "-m", "venv", venv_path])

            # Install the package in the virtual environment
            subprocess.check_call(
                [os.path.join(venv_path, "bin", "pip"), "install", package_name]
            )
            zip_path = f"static/packages/{package_name}.zip"

            # Zip the package
            with zipfile.ZipFile(f"static/packages/{package_name}.zip", "w") as zipf:
                for foldername, subfolders, filenames in os.walk(package_path):
                    for filename in filenames:
                        absolute_path = os.path.join(foldername, filename)
                        relative_path = os.path.relpath(absolute_path, package_path)
                        zipf.write(absolute_path, relative_path)

            self.upload_to_snowflake(zip_path, package_name)
            print(
                f"Package {package_name} has been zipped and uploaded to Snowflake stage."
            )

    def zip_and_upload_package_with_dependencies(self, package_name, dependencies):
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = os.path.join(temp_dir, "venv")
            package_path = os.path.join(venv_path, "lib", "python3.9", "site-packages")

            # Create a virtual environment
            subprocess.check_call(["python3", "-m", "venv", venv_path])

            # Install the package and its dependencies in the virtual environment
            subprocess.check_call(
                [os.path.join(venv_path, "bin", "pip"), "install", package_name]
                + dependencies
            )
            zip_path = f"static/packages/{package_name}_with_dependencies.zip"

            # Zip the package and its dependencies
            with zipfile.ZipFile(
                f"static/packages/{package_name}_with_dependencies.zip", "w"
            ) as zipf:
                for foldername, subfolders, filenames in os.walk(package_path):
                    for filename in filenames:
                        absolute_path = os.path.join(foldername, filename)
                        relative_path = os.path.relpath(absolute_path, package_path)
                        zipf.write(absolute_path, relative_path)
            # Upload to Snowflake
            self.upload_to_snowflake(zip_path, package_name)
            print(
                f"Package {package_name} along with its dependencies has been zipped and uploaded to Snowflake stage."
            )

    def deploy_package(self, package_name):
        if SnowHelper.SnowHelper().is_package_available_in_snowflake_channel(
            package_name
        ):
            print(
                f"Package {package_name} is available on the Snowflake anaconda channel."
            )
            print(
                "No need to create a package. Just include in your `packages` declaration."
            )
            return

        dependencies = SnowHelper.SnowHelper().get_dependencies_of_package(package_name)
        if dependencies:
            available_dependencies = [
                dep
                for dep in dependencies
                if SnowHelper.SnowHelper().is_package_available_in_snowflake_channel(
                    dep
                )
            ]
            if len(available_dependencies) != len(dependencies):
                missing_dependencies = set(dependencies) - set(available_dependencies)
                print(
                    f"Dependencies {', '.join(missing_dependencies)} are not available in Snowflake Anaconda channel."
                )
                print(f"Zipping and uploading only the {package_name} package.")
                self.zip_and_upload_package(package_name)
            else:
                print(
                    f"Dependencies for {package_name} are available in Snowflake Anaconda channel."
                )
                print(
                    f"Zipping and uploading the {package_name} package along with its dependencies."
                )
                self.zip_and_upload_package_with_dependencies(
                    package_name, dependencies
                )
        else:
            print(f"Zipping and uploading only the {package_name} package.")
            self.zip_and_upload_package(package_name)

    def upload_to_snowflake(self, zip_path, package_name):
        stage_location = (
            f"{self.current_database}.{self.current_schema}.{self.stage_name}"
        )
        remote_path = f"@{stage_location}/static/packages"
        self.session.file.put(
            zip_path, remote_path, overwrite=True, auto_compress=False
        )
