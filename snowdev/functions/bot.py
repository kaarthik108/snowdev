import os
import re
import pkg_resources

import toml
from langchain.chains import LLMChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores import Chroma
from termcolor import colored

from snowdev.functions.utils.templates.sproc import TEMPLATE as SPROC_TEMPLATE
from snowdev.functions.utils.templates.streamlit import (
    TEMPLATE as STREAMLIT_TEMPLATE,
)
from snowdev.functions.utils.templates.udf import TEMPLATE as UDF_TEMPLATE
from snowdev.functions.utils.ingest import DocumentProcessor, Secrets, Config
from snowdev.functions.utils.snowpark_methods import SnowparkMethods

MODEL = "gpt-4"


class SnowBot:

    TEMPLATES = {
        "udf": UDF_TEMPLATE,
        "sproc": SPROC_TEMPLATE,
        "streamlit": STREAMLIT_TEMPLATE,
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
        if template_type not in SnowBot.TEMPLATES:
            raise ValueError(f"No template found for component type: {template_type}")
        return PromptTemplate(
            template=SnowBot.TEMPLATES[template_type],
            input_variables=["question", "context"],
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
        chain = LLMChain(llm=llm, prompt=SnowBot.QA_PROMPT)
        chain = RetrievalQA.from_chain_type(
            llm,
            chain_type="stuff",
            retriever=db.as_retriever(),
            chain_type_kwargs={"prompt": SnowBot.QA_PROMPT},
        )
        return chain

    @staticmethod
    def append_dependencies_to_toml(dependencies_dict):
        """
        Append new dependencies to app.toml file.
        """
        toml_path = "app.toml"

        if not os.path.exists(toml_path):
            print(colored(f"⚠️ {toml_path} does not exist!", "yellow"))
            return

        with open(toml_path, "r") as f:
            data = toml.load(f)

        for key, value in dependencies_dict.items():
            data["tool.poetry.dependencies"][key] = value

        with open(toml_path, "w") as f:
            toml.dump(data, f)

    @staticmethod
    def write_environment_file(component_folder, template_type):
        """
        This is temporary, until we have a better way to auto create environment files through Langchain output parsers.
        """
        file_map = {"streamlit": "fill.yml", "udf": "fill.toml", "sproc": "fill.toml"}
        source_file_name = file_map.get(template_type)

        if not source_file_name:
            return

        content = pkg_resources.resource_string(
            f"snowdev.fillers.{template_type}", source_file_name
        ).decode("utf-8")

        target_file_name = (
            "environment.yml" if template_type == "streamlit" else source_file_name
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
        response_content = chain(prompt)["result"]

        matches = re.findall(r"```(?:python)?\n(.*?)\n```", response_content, re.DOTALL)

        if matches:
            # Take the first match, as there might be multiple code blocks
            response_content = matches[0].strip()
        else:
            print(
                colored(
                    "Unexpected response content format. Expected code block not found. Please try again",
                    "red",
                )
            )

        component_folder = os.path.join("src", template_type, component_name)
        os.makedirs(component_folder, exist_ok=True)
        SnowBot.write_environment_file(component_folder, template_type)

        filename = "app.py"
        if template_type == "streamlit":
            filename = "streamlit_app.py"

        with open(os.path.join(component_folder, filename), "w") as f:
            f.write(response_content)

        print(
            colored(
                f"✅ {template_type.upper()} {component_name} generated successfully using AI!",
                "green",
            )
        )
