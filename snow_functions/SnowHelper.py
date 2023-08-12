import toml

class SnowHelper:
    """
    A helper class containing utility functions for Snowflake operations.

    Methods
    -------
    get_packages_from_requirements()
        Returns a list of packages from a requirements.txt file
    get_imports()
        Returns a list of imports from an imports.txt file
    """

    @staticmethod
    def get_packages_from_requirements(path):
        """
        Reads the requirements.txt file and returns a list of packages.

        Parameters
        ----------
        path : str
            the path to the requirements.txt file

        Returns
        ----------
        list
            a list of strings, each string being a package and its version.
        """
        with open(f"{path}/requirements.txt", "r") as file:
            # read lines in the file and strip off the newline character
            lines = file.read().splitlines()
        return lines

    @staticmethod
    def get_imports(path):
        """
        Reads the imports.txt file and returns a list of imports.

        Parameters
        ----------
        path : str
            the path to the imports.txt file

        Returns
        ----------
        list
            a list of strings, each string being an import statement.
        """

        with open(f"{path}/imports.txt", "r") as file:
            # read lines in the file and strip off the newline character
            lines = file.read().splitlines()
        return lines

    @staticmethod
    def get_packages_from_toml(path):
        with open(f"{path}/pyproject.toml", "r") as file:
            data = toml.load(file)
            dependencies = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            
            # Exclude python from the packages
            if 'python' in dependencies:
                del dependencies['python']
            
            return list(dependencies.keys())