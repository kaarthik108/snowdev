import toml
import requests
from bs4 import BeautifulSoup
import pkg_resources


class SnowHelper:
    @staticmethod
    def get_packages_from_requirements(path):
        with open(f"{path}/requirements.txt", "r") as file:
            # read lines in the file and strip off the newline character
            lines = file.read().splitlines()
        return lines

    @staticmethod
    def get_imports(path):

        with open(f"{path}/imports.txt", "r") as file:
            # read lines in the file and strip off the newline character
            lines = file.read().splitlines()
        return lines

    @staticmethod
    def get_packages_from_toml(path):
        with open(f"{path}/app.toml", "r") as file:
            data = toml.load(file)
            dependencies = data["tool"]["poetry"]["dependencies"]

            # Exclude python from the packages
            if "python" in dependencies:
                dependencies.pop("python", None)
            # Return the packages with their versions
            return [f"{pkg}=={version}" for pkg, version in dependencies.items()]

    @staticmethod
    def is_package_available_in_snowflake_channel(package_name):
        SNOWFLAKE_ANACONDA_URL = "https://repo.anaconda.com/pkgs/snowflake/"

        response = requests.get(SNOWFLAKE_ANACONDA_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        package_links = [
            link.get("href")
            for link in soup.find_all("a")
            if link.get("href") is not None
        ]

        # Check if the package name exists in the links
        return any(package_name in link for link in package_links)

    @staticmethod
    def get_available_versions_from_snowflake_channel(package_name):
        SNOWFLAKE_ANACONDA_URL = "https://repo.anaconda.com/pkgs/snowflake/"

        response = requests.get(SNOWFLAKE_ANACONDA_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        package_links = [
            link.get("href")
            for link in soup.find_all("a")
            if link.get("href") is not None
        ]

        versions = [
            link.split("-")[1]
            for link in package_links
            if package_name in link and len(link.split("-")) > 1
        ]

        return versions

    @staticmethod
    def get_dependencies_of_package(package_name):
        """Fetch dependencies of a given package using pkg_resources."""
        try:
            distribution = pkg_resources.get_distribution(package_name)
            print(distribution.requires())
            return [requirement.name for requirement in distribution.requires()]
        except pkg_resources.DistributionNotFound:
            return []  # Return an empty list if the package isn't found

    @staticmethod
    def are_dependencies_available_in_snowflake_channel(package_name):
        """Check if all dependencies of a package are available in Snowflake's Anaconda channel."""
        dependencies = SnowHelper.get_dependencies_of_package(package_name)
        return all(
            SnowHelper.is_package_available_in_snowflake_channel(dep)
            for dep in dependencies
        )

    @staticmethod
    def is_specific_version_available_in_snowflake_channel(package_name, version):
        available_versions = SnowHelper.get_available_versions_from_snowflake_channel(
            package_name
        )
        return version in available_versions
