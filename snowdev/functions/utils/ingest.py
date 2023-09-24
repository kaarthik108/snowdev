from __future__ import annotations

import hashlib
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, NamedTuple

import pkg_resources
import sqlparse
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from pydantic import BaseModel
from termcolor import colored


class Secrets(BaseModel):
    OPENAI_API_KEY: str


class Document(NamedTuple):
    content: str
    metadata: dict


class Config(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 0
    docs_dir: str = pkg_resources.resource_filename(
        "snowdev.functions.utils", "knowledge"
    )


class PathType(Enum):
    SPROC = ("src/sproc", "stored procedure")
    UDF = ("src/udf", "user-defined function")
    STREAMLIT = ("src/streamlit", "Streamlit app")
    TASK = ("src/task", "snowflake task")

    def __init__(self, path: str, desc: str):
        self.path = path
        self.desc = desc


class DocumentProcessor:
    def __init__(
        self, secrets: Secrets, config: Config, checksum_file: str = "checksums.json"
    ):
        self._initialize_loaders(config.docs_dir)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=secrets.OPENAI_API_KEY)
        self.checksum_file = checksum_file
        self.checksum_dict = self._load_checksums()
        self._convert_sql_to_md_if_changed()

    def _initialize_loaders(self, docs_dir: str):
        self.loader_py = DirectoryLoader(docs_dir, glob="**/*.py")
        self.loader_md = DirectoryLoader(docs_dir, glob="**/*.md")
        self.loader_src_py = DirectoryLoader("src/", glob="**/*.py")
        self.loader_src_sql = DirectoryLoader("src/", glob="**/*.md")

    def _load_checksums(self) -> Dict[str, str]:
        if os.path.exists(self.checksum_file):
            with open(self.checksum_file, "r") as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    print(
                        colored(
                            "Checksum file is empty. Creating a new checksum dictionary.",
                            "yellow",
                        )
                    )
                    return {}
        else:
            return {}

    def _save_checksums(self) -> None:
        with open(self.checksum_file, "w") as f:
            json.dump(self.checksum_dict, f)

    @staticmethod
    def _create_checksum(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_prompt_from_path(self, path: str) -> str:
        folder_name = os.path.basename(os.path.dirname(path))
        for path_type in PathType:
            if path_type.path in path:
                return f"This is the {path_type.desc} written in snowflake snowpark named {folder_name}."
        return ""

    def process(self) -> Dict[str, Any]:
        data = self._load_and_filter_documents()
        if not data:
            print(colored("No new documents found to embed.", "yellow"))
            return {}

        texts = self.text_splitter.split_documents(data)
        if not texts:
            print(colored("No new text segments found to embed.", "yellow"))
            return {}

        print(colored(f"Found {len(texts)} documents.", "cyan"))
        vector_store = Chroma.from_documents(
            texts, self.embeddings, persist_directory="chroma_db"
        )
        vector_store.persist()
        self._save_checksums()
        return vector_store

    def _convert_sql_to_md_if_changed(self):
        src_dir = Path("src/task")
        target_dir = Path("compiled/task")

        target_dir.mkdir(parents=True, exist_ok=True)

        for sql_file in src_dir.glob("**/*.sql"):
            with sql_file.open("r") as file:
                content = file.read()

            checksum = self._create_checksum(content)

            if checksum != self.checksum_dict.get(str(sql_file)):
                self.checksum_dict[str(sql_file)] = checksum

                # Convert SQL content to Markdown
                formatted_sql = sqlparse.format(content, reindent=True)
                md_content = f"```sql\n{formatted_sql}\n```"

                # Define the target Markdown file path
                relative_path = sql_file.relative_to(src_dir)
                target_md_file = target_dir / relative_path.with_suffix(".md")

                target_md_file.parent.mkdir(parents=True, exist_ok=True)

                with target_md_file.open("w") as file:
                    file.write(md_content)

                self._save_checksums()

    def _load_and_filter_documents(self) -> List[str]:
        data = []
        for record in (
            self.loader_py.load()
            + self.loader_md.load()
            + self.loader_src_py.load()
            + self.loader_src_sql.load()
        ):
            content = self._extract_content_from_record(record)
            checksum = self._create_checksum(content)
            filename = self._extract_filename_from_record(record)

            # Check if the content is SQL
            if filename.endswith(".sql"):
                # Convert SQL to Markdown
                formatted_sql = sqlparse.format(content, reindent=True)
                content = f"```sql\n{formatted_sql}\n```"

            if checksum != self.checksum_dict.get(filename):
                self.checksum_dict[filename] = checksum
                prompt = self._generate_prompt_from_path(filename)
                self._update_record_metadata(record, filename, prompt)
                log_msg = (
                    colored(f"Embedding {filename} with Prompt: {prompt}", "green")
                    if filename.startswith("src/")
                    else colored(f"Skipped {filename}", "yellow")
                )
                print(log_msg)
                data.append(record)

        return data

    @staticmethod
    def _extract_content_from_record(record: Any) -> str:
        return getattr(record, "content", str(record))

    @staticmethod
    def _extract_filename_from_record(record: Any) -> str:
        return getattr(record, "metadata", {}).get("source", "")

    @staticmethod
    def _update_record_metadata(record: Any, filename: str, prompt: str) -> None:
        if hasattr(record, "metadata"):
            record.metadata["prompt"] = prompt
        else:
            record.metadata = {"prompt": prompt, "source": filename}
