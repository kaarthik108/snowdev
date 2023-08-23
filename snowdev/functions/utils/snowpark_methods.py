import inspect
import os
import pkg_resources
from snowflake import snowpark, ml


class SnowparkMethods:
    @classmethod
    def _extract_methods_and_docs_from_session(cls, module):
        """
        Extract methods and their docstrings from the Session class of a module.
        """
        items = []

        # Check if the module has a Session class
        SessionClass = getattr(module, "Session", None)
        if SessionClass:
            for name, obj in inspect.getmembers(SessionClass):
                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    if obj.__doc__:
                        items.append((name, obj.__doc__))
        return items

    @classmethod
    def _write_to_markdown_file(cls, filename, data):
        """
        Write method names and docstrings to a markdown file.
        """
        with open(filename, "w") as f:
            f.write("# Snowflake Session Methods\n")
            f.write(
                "This document lists methods available in the Snowflake Session class, along with their documentation.\n\n"
            )
            for name, doc in data:
                f.write(f"## {name}\n\n")
                f.write(f"{doc}\n\n")

    @classmethod
    def generate_documentation(cls):
        snowpark_items = cls._extract_methods_and_docs_from_session(snowpark)
        ml_items = cls._extract_methods_and_docs_from_session(ml)

        all_items = snowpark_items + ml_items

        # Using pkg_resources to get the path inside the package
        knowledge_dir = pkg_resources.resource_filename(
            "snowdev.functions.utils", "knowledge"
        )
        filepath = os.path.join(knowledge_dir, "documentation.md")

        cls._write_to_markdown_file(filepath, all_items)

if __name__ == "__main__":
    SnowparkMethods.generate_documentation()
