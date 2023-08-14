import toml
import requests
from bs4 import BeautifulSoup
import pkg_resources


class SnowHelper:
    SNOWFLAKE_ANACONDA_URL = "https://repo.anaconda.com/pkgs/snowflake/"

    @staticmethod
    def read_file_lines(path, filename):
        """Unified method to read files."""
        with open(f"{path}/{filename}", "r") as file:
            return file.read().splitlines()

    @staticmethod
    def get_packages_from_requirements(path):
        return SnowHelper.read_file_lines(path, "requirements.txt")

    @staticmethod
    def get_imports(path):
        return SnowHelper.read_file_lines(path, "imports.txt")

    @staticmethod
    def get_packages_from_toml(path):
        data = toml.load(f"{path}/app.toml")
        dependencies = data["tool"]["poetry"]["dependencies"]
        if "python" in dependencies:
            dependencies.pop("python")
        return [f"{pkg}=={version}" for pkg, version in dependencies.items()]

    @staticmethod
    def fetch_snowflake_packages():
        """Fetch and parse the Snowflake Anaconda URL."""
        response = requests.get(SnowHelper.SNOWFLAKE_ANACONDA_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [
            link.get("href")
            for link in soup.find_all("a")
            if link.get("href") is not None
        ]

    @staticmethod
    def is_package_available_in_snowflake_channel(package_name):
        package_links = SnowHelper.fetch_snowflake_packages()
        return any(package_name in link for link in package_links)

    @staticmethod
    def get_available_versions_from_snowflake_channel(package_name):
        package_links = SnowHelper.fetch_snowflake_packages()
        return [
            link.split("-")[1]
            for link in package_links
            if package_name in link and len(link.split("-")) > 1
        ]

    @staticmethod
    def get_dependencies_of_package(package_name):
        try:
            distribution = pkg_resources.get_distribution(package_name)
            return [requirement.name for requirement in distribution.requires()]
        except pkg_resources.DistributionNotFound:
            return []

    @staticmethod
    def are_dependencies_available_in_snowflake_channel(package_name):
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
