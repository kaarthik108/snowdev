import json
import os
import re
import pkg_resources

import toml
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores import Chroma
from termcolor import colored
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
import yaml
from snowdev.functions.helper import SnowHelper

from snowdev.functions.utils.templates.sproc import TEMPLATE as SPROC_TEMPLATE
from snowdev.functions.utils.templates.streamlit import (
    TEMPLATE as STREAMLIT_TEMPLATE,
)
from snowdev.functions.utils.templates.udf import TEMPLATE as UDF_TEMPLATE
from snowdev.functions.utils.templates.task import TEMPLATE as TASK_TEMPLATE
from snowdev.functions.utils.ingest import DocumentProcessor, Secrets, Config
from snowdev.functions.utils.snowpark_methods import SnowparkMethods
import re

MODEL = os.environ.get("LLM_MODEL", "gpt-4")

python_schemas = [
    ResponseSchema(name="code", description="The full python code to run"),
    ResponseSchema(
        name="packages",
        description="The packages to install to run the code, ignore snowflake related packages, streamlit and snowdev packages",
    ),
]

task_schemas = [
    ResponseSchema(name="code", description="The sql code to run snowflake task"),
]


class SnowBot:

    TEMPLATES = {
        "udf": UDF_TEMPLATE,
        "sproc": SPROC_TEMPLATE,
        "streamlit": STREAMLIT_TEMPLATE,
        "task": TASK_TEMPLATE,
    }

    @staticmethod
    def ai_embed():
        """
        Embed all the documents in the knowledge folder.
        """
        secrets = Secrets(OPENAI_API_KEY=os.environ["OPENAI_API_KEY"])
        config = Config()
        doc_processor = DocumentProcessor(secrets, config)
        try:
            SnowparkMethods.generate_documentation()
            result = doc_processor.process()
            print(colored("✅ Documents have been successfully embedded!", "green"))
            return result
        except Exception as e:
            print(
                colored(f"❌ Error occurred while embedding documents: {str(e)}", "red")
            )
            return None

    @staticmethod
    def get_qa_prompt_for_type(template_type):
        output_parser = StructuredOutputParser.from_response_schemas(
            python_schemas if template_type != "task" else task_schemas
        )
        format_instructions = output_parser.get_format_instructions()
        if template_type not in SnowBot.TEMPLATES:
            raise ValueError(f"No template found for component type: {template_type}")
        return PromptTemplate(
            template=SnowBot.TEMPLATES[template_type],
            input_variables=["question", "context"],
            partial_variables={"format_instructions": format_instructions},
        )

    @staticmethod
    def component_exists(component_name, template_type):
        folder_path = os.path.join("src", template_type, component_name)
        return os.path.exists(folder_path)

    @staticmethod
    def get_chain_gpt(db):
        """
        Get a chain for chatting with a vector database.
        """
        llm = ChatOpenAI(
            model_name=MODEL,
            temperature=0,
            openai_api_key=os.environ["OPENAI_API_KEY"],
            max_tokens=500,
        )

        chain = RetrievalQA.from_chain_type(
            llm,
            chain_type="stuff",
            retriever=db.as_retriever(),
            chain_type_kwargs={"prompt": SnowBot.QA_PROMPT},
        )
        return chain

    @staticmethod
    def append_dependencies_to_toml(dependencies_dict, component_folder):
        """
        Append new dependencies to app.toml file.
        """
        toml_path = os.path.join(component_folder, "app.toml")
        if not os.path.exists(toml_path):
            print(colored(f"⚠️ {toml_path} does not exist!", "yellow"))
            return

        with open(toml_path, "r") as f:
            data = toml.load(f)
        for package_name, default_version in dependencies_dict.items():
            if not package_name.strip():
                continue
            print(f"\nSearching for package: {package_name}")
            available_versions = SnowHelper.search_package_in_snowflake_channel(
                package_name
            )
            if available_versions:
                # Set the found latest version to the TOML data
                data["tool"]["poetry"]["dependencies"][
                    package_name
                ] = available_versions
                print(
                    colored(
                        f"\nPackage {package_name} is available on the Snowflake anaconda channel. Latest version: {available_versions}\n",
                        "green",
                    )
                )
            else:
                print(
                    colored(
                        f"⚠️ Package {package_name} is not available on the Snowflake anaconda channel. Using default version: {default_version}",
                        "yellow",
                    )
                )
                data["tool"]["poetry"]["dependencies"][package_name] = default_version

        with open(toml_path, "w") as f:
            toml.dump(data, f)

    @staticmethod
    def append_packages_to_environment_file(component_folder, template_type, packages):
        if not isinstance(packages, list):
            packages = [packages]
        if template_type == "streamlit":
            env_file_path = os.path.join(component_folder, "environment.yml")

            if not os.path.exists(env_file_path):
                raise ValueError(f"The file '{env_file_path}' does not exist.")

            with open(env_file_path, "r") as env_file:
                data = yaml.safe_load(env_file) or {}

            # Capture old data
            old_channels = data.get("channels", [])
            old_dependencies = data.get("dependencies", [])

            # Ensure the packages are unique
            for package in packages:
                if package not in old_dependencies:
                    old_dependencies.append(package)

            # Construct new ordered dictionary
            new_data = {
                "name": os.path.basename(component_folder),
                "channels": old_channels,
                "dependencies": old_dependencies,
            }

            with open(env_file_path, "w") as env_file:
                yaml.safe_dump(
                    new_data, env_file, sort_keys=False, default_flow_style=False
                )

        else:
            # toml_file_path = os.path.join(component_folder, "app.toml")
            dependencies_dict = {package: "*" for package in packages}
            SnowBot.append_dependencies_to_toml(dependencies_dict, component_folder)

    @staticmethod
    def write_environment_file(component_folder, template_type):
        file_map = {"streamlit": "fill.yml", "udf": "fill.toml", "sproc": "fill.toml"}
        source_file_name = file_map.get(template_type)

        if not source_file_name:
            return

        content = pkg_resources.resource_string(
            f"snowdev.fillers.{template_type}", source_file_name
        ).decode("utf-8")

        target_file_name = (
            "environment.yml" if template_type == "streamlit" else "app.toml"
        )

        with open(os.path.join(component_folder, target_file_name), "w") as env_file:
            env_file.write(content)

    @staticmethod
    def create_new_ai_component(component_name, prompt, template_type):
        # Ensure that the template_type is valid
        if template_type not in SnowBot.TEMPLATES:
            print(
                colored(
                    f"⚠️ Template type {template_type} is not recognized.", "yellow"
                )
            )
            return

        SnowBot.QA_PROMPT = SnowBot.get_qa_prompt_for_type(template_type)

        if template_type == "task":
            prompt = f"{prompt}\nTask Name: {component_name}"
        # format_instructions = output_parser.get_format_instructions()
        # Check if the component already exists
        if SnowBot.component_exists(component_name, template_type):
            print(
                colored(
                    f"⚠️ {template_type.upper()} named {component_name} already exists!",
                    "yellow",
                )
            )
            return

        # Embedding and retrieving the content
        embeddings = OpenAIEmbeddings(
            openai_api_key=os.environ["OPENAI_API_KEY"], model="text-embedding-ada-002"
        )
        vectordb = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
        chain = SnowBot.get_chain_gpt(vectordb)
        res = chain(prompt)
        response_content = res["result"]

        match = re.search(r"```json\n(.*?)\n```", response_content, re.DOTALL)
        if match:
            json_string = match.group(1).strip()
        else:
            print(colored("JSON block not found in the response.\n", "red"))
            print(colored("Retry the command again.", "red"))
            return
        new = json.loads(json_string, strict=False)
        ai_generated_packages = new.get("packages", None)

        try:
            response_content = new.get("code", None)
        except:
            print(
                colored(
                    "Unexpected response content format. Expected code block not found. Please try again",
                    "red",
                )
            )

        component_folder = os.path.join("src", template_type, component_name)
        os.makedirs(component_folder, exist_ok=True)

        filename = "app.sql" if template_type == "task" else "app.py"
        if template_type == "streamlit":
            filename = "streamlit_app.py"

        with open(os.path.join(component_folder, filename), "w") as f:
            f.write(response_content)

        if template_type == "task":
            print(
                colored(
                    f"\n✅ TASK {component_name} SQL code generated successfully using AI!\n",
                    "green",
                )
            )
            return

        SnowBot.write_environment_file(component_folder, template_type)
        SnowBot.append_packages_to_environment_file(
            component_folder, template_type, ai_generated_packages
        )

        print(
            colored(
                f"\n✅ {template_type.upper()} {component_name} generated successfully using AI!\n",
                "green",
            )
        )


# if __name__ == "__main__":
#     # bot = SnowBot()
#     # bot.append_packages_to_environment_file("src/streamlit/test_new", "streamlit", "pandas")
#     SnowBot.create_new_ai_component(
#         "test_new_", "Fetch data from customer and return the top 1 row", template_type="sproc"
#     )
