import toml

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
            dependencies = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            
            # Exclude python from the packages
            if 'python' in dependencies:
                del dependencies['python']
            
            return list(dependencies.keys())