import os
import subprocess

import pkg_resources
import toml
from pydantic import BaseModel
from termcolor import colored


class SnowHelperConfig(BaseModel):
    udf: str = None
    sproc: str = None
    stream: str = None


class SnowHelper:
    SNOWFLAKE_ANACONDA_URL = "https://repo.anaconda.com/pkgs/snowflake/"
    BASE_PATHS = {
        "udf": "src/udf",
        "sproc": "src/stored_proc",
        "stream": "src/streamlit",
    }
    TEMPLATES = {
        "udf": {"py": "fillers/udf/fill.py", "toml": "fillers/udf/fill.toml"},
        "sproc": {"py": "fillers/stored_procs/fill.py", "toml": "fillers/stored_procs/fill.toml"},
        "stream": {"py": "fillers/streamlit/fill.py", "yml": "fillers/streamlit/fill.yml"},
    }

    @classmethod
    def read_file_lines(cls, path, filename):
        with open(os.path.join(path, filename), "r") as file:
            return file.read().splitlines()

    @classmethod
    def get_packages_from_requirements(cls, path):
        return cls.read_file_lines(path, "requirements.txt")

    @classmethod
    def get_imports(cls, path):
        return cls.read_file_lines(path, "imports.txt")

    @classmethod
    def get_packages_from_toml(cls, path):
        data = toml.load(os.path.join(path, "app.toml"))
        dependencies = data["tool"]["poetry"]["dependencies"]
        dependencies.pop("python", None)
        return [f"{pkg}=={version}" for pkg, version in dependencies.items()]

    @classmethod
    def search_package_in_snowflake_channel(cls, package_name):
        cmd = [
            "conda",
            "search",
            "-c",
            cls.SNOWFLAKE_ANACONDA_URL,
            "--override-channels",
            package_name,
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        if process.returncode != 0:
            return []

        # Parse the results
        lines = stdout.decode().split("\n")
        versions = []
        for line in lines:
            if package_name in line:
                versions.append(line.split()[1])  # Extract the version from the result

        # Return all versions
        return versions

    @classmethod
    def is_package_available_in_snowflake_channel(cls, package_name):
        versions = cls.search_package_in_snowflake_channel(package_name)
        return bool(versions)

    @classmethod
    def get_available_versions_from_snowflake_channel(cls, package_name):
        return cls.search_package_in_snowflake_channel(package_name)

    @classmethod
    def get_dependencies_of_package(cls, package_name):
        try:
            distribution = pkg_resources.get_distribution(package_name)
            return [requirement.name for requirement in distribution.requires()]
        except pkg_resources.DistributionNotFound:
            return []

    @classmethod
    def are_dependencies_available_in_snowflake_channel(cls, package_name):
        dependencies = cls.get_dependencies_of_package(package_name)
        return all(
            cls.is_package_available_in_snowflake_channel(dep) for dep in dependencies
        )

    @classmethod
    def is_specific_version_available_in_snowflake_channel(cls, package_name, version):
        available_versions = cls.get_available_versions_from_snowflake_channel(
            package_name
        )
        return version in available_versions

    @classmethod
    def create_new_component(cls, args_dict):
        config = SnowHelperConfig(**args_dict)
        item_type, item_name = next(
            ((key, value) for key, value in config.dict().items() if value),
            (None, None),
        )

        if not item_type:
            print(
                colored(
                    "Error: Please provide either --udf, --sproc, or --stream when using the 'new' command.",
                    "red",
                )
            )
            return

        base_path = cls.BASE_PATHS.get(item_type)
        if not base_path:
            print(colored(f"Unknown item type: {item_type}", "red"))
            return

        new_item_path = os.path.join(base_path, item_name)

        if os.path.exists(new_item_path):
            print(colored(f"{item_type} {item_name} already exists!", "yellow"))
            return

        os.makedirs(new_item_path, exist_ok=True)

        # Handling the streamlit templates specifically
        if item_type == "stream":
            for template_ext, output_name in [("py", "streamlit_app.py"), ("yml", "environment.yml")]:
                template_name = "fillers/streamlit/fill." + template_ext
                template_path = os.path.join("snowdev", template_name)

                if os.path.exists(template_path):
                    with open(template_path, "r") as template_file:
                        content = template_file.read()

                    with open(os.path.join(new_item_path, output_name), "w") as f:
                        f.write(content)
                else:
                    print(
                        colored(
                            f"No template found for {item_type} with extension {template_ext}. Creating an empty {output_name}...",
                            "yellow",
                        )
                    )
                    with open(os.path.join(new_item_path, output_name), "w") as f:
                        pass
        else:
            for ext, template_name in cls.TEMPLATES[item_type].items():
                template_path = os.path.join("snowdev", template_name)
                if os.path.exists(template_path):
                    with open(template_path, "r") as template_file:
                        content = template_file.read()

                    filename = "app.py" if ext == "py" else "app.toml"
                    with open(os.path.join(new_item_path, filename), "w") as f:
                        f.write(content)
                else:
                    print(
                        colored(
                            f"No template found for {item_type} with extension {ext}. Creating an empty {filename}...",
                            "yellow",
                        )
                    )
                    filename = "app.py" if ext == "py" else "app.toml"
                    with open(os.path.join(new_item_path, filename), "w") as f:
                        pass

        print(
            colored(f"{item_type} {item_name} has been successfully created!", "green")
        )