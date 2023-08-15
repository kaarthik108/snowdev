import os
import subprocess
import tempfile
import zipfile

from termcolor import colored

from . import SnowHelper


class SnowPackageZip:
    def __init__(self, session, stage_name):
        self.session = session
        self.current_database = self.session.get_current_database().replace('"', "")
        self.current_schema = self.session.get_current_schema().replace('"', "")
        self.stage_name = stage_name

    def _print_success(self, message):
        print(colored(message, "green"))

    def _print_error(self, message):
        print(colored(message, "red"))

    def _print_info(self, message):
        print(colored(message, "blue"))

    def zip_and_upload_package(self, package_name, upload):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                venv_path = os.path.join(temp_dir, "venv")
                package_path = os.path.join(
                    venv_path, "lib", "python3.9", "site-packages"
                )

                # Create a virtual environment
                subprocess.check_call(["python3", "-m", "venv", venv_path])

                # Install the package in the virtual environment
                subprocess.check_call(
                    [os.path.join(venv_path, "bin", "pip"), "install", package_name]
                )
                zip_path = f"static/packages/{package_name}.zip"

                # Zip the package
                with zipfile.ZipFile(
                    f"static/packages/{package_name}.zip", "w"
                ) as zipf:
                    for foldername, subfolders, filenames in os.walk(package_path):
                        for filename in filenames:
                            absolute_path = os.path.join(foldername, filename)
                            relative_path = os.path.relpath(absolute_path, package_path)
                            zipf.write(absolute_path, relative_path)

                if upload:
                    self.upload_to_snowflake(zip_path, package_name)
                    self._print_success(
                        f"\nPackage {package_name} has been zipped and uploaded to Snowflake stage."
                    )
                else:
                    self._print_success(
                        f"\nPackage {package_name} has been zipped."
                    )

        except Exception as e:
            self._print_error(f"Error encountered: {e}")

    def zip_and_upload_package_with_dependencies(
        self, package_name, dependencies, upload
    ):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                venv_path = os.path.join(temp_dir, "venv")
                package_path = os.path.join(
                    venv_path, "lib", "python3.9", "site-packages"
                )

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

                if upload:
                    self.upload_to_snowflake(zip_path, package_name)
                    self._print_success(
                        f"\nPackage {package_name} along with its dependencies has been zipped and uploaded to Snowflake stage."
                    )
                else:
                    self._print_success(
                        f"\nPackage {package_name} along with its dependencies has been zipped."
                    )

        except Exception as e:
            self._print_error(f"Error encountered: {e}")

    def deploy_package(self, package_name, upload):
        try:
            available_versions = SnowHelper.get_available_versions_from_snowflake_channel(package_name)
            
            if available_versions:
                print(colored(
                    f"\nPackage {package_name} is available on the Snowflake anaconda channel. Latest version: {available_versions[0]}\n", "green"
                ))
                print(colored(
                    "No need to create a package. Just include in your `app.toml` declaration.", "green"
                ))
                return

            dependencies = SnowHelper.get_dependencies_of_package(package_name)
            if dependencies:
                available_dependencies = [
                    dep
                    for dep in dependencies
                    if SnowHelper.is_package_available_in_snowflake_channel(dep)
                ]
                if len(available_dependencies) != len(dependencies):
                    missing_dependencies = set(dependencies) - set(
                        available_dependencies
                    )
                    print(
                        f"Dependencies {', '.join(missing_dependencies)} are not available in Snowflake Anaconda channel."
                    )
                    print(f"Zipping and uploading only the {package_name} package.")
                    self.zip_and_upload_package(package_name, upload)
                else:
                    print(
                        f"Dependencies for {package_name} are available in Snowflake Anaconda channel."
                    )
                    print(
                        f"Zipping and uploading the {package_name} package along with its dependencies."
                    )
                    self.zip_and_upload_package_with_dependencies(
                        package_name, dependencies, upload
                    )
            else:
                # print(f"Zipping and uploading only the {package_name} package.")
                self.zip_and_upload_package(package_name, upload)

        except Exception as e:
            self._print_error(f"Error encountered: {e}")

    def upload_to_snowflake(self, zip_path, package_name):
        try:
            stage_location = (
                f"{self.current_database}.{self.current_schema}.{self.stage_name}"
            )
            remote_path = f"@{stage_location}/static/packages"
            self.session.file.put(
                zip_path, remote_path, overwrite=True, auto_compress=False
            )
        except Exception as e:
            self._print_error(f"Failed to upload {package_name}. Error: {e}")
