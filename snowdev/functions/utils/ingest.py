from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, NamedTuple

import pkg_resources
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


class DocumentProcessor:
    def __init__(
        self, secrets: Secrets, config: Config, checksum_file: str = "checksums.json"
    ):
        """
        Initialize the DocumentProcessor with the provided secrets and configuration.
        """
        self._initialize_loaders(config.docs_dir)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=secrets.OPENAI_API_KEY)
        self.checksum_file = checksum_file
        self.checksum_dict = self._load_checksums()

    def _initialize_loaders(self, docs_dir: str):
        """
        Initialize data loaders.
        """
        self.loader_py = DirectoryLoader(docs_dir, glob="**/*.py")
        self.loader_md = DirectoryLoader(docs_dir, glob="**/*.md")
        self.loader_src_py = DirectoryLoader("src/", glob="**/*.py")

    def _load_checksums(self) -> Dict[str, str]:
        """
        Load checksums from a checksum file.
        """
        if os.path.exists(self.checksum_file):
            with open(self.checksum_file, "r") as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    print("Checksum file is empty. Creating a new checksum dictionary.")
                    return {}
        else:
            return {}

    def _save_checksums(self) -> None:
        """
        Save checksums to the checksum file.
        """
        with open(self.checksum_file, "w") as f:
            json.dump(self.checksum_dict, f)

    @staticmethod
    def _create_checksum(content: str) -> str:
        """
        Create a checksum for the provided content.
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_prompt_from_path(self, path: str) -> str:
        """
        Generate a prompt based on the file path.
        """
        folder_name = os.path.basename(os.path.dirname(path))
        mappings = {
            "src/sproc/": f"This is the stored procedure written in snowflake snowpark named {folder_name}.",
            "src/udf/": f"This is the user-defined function written in snowflake snowpark named {folder_name}.",
            "src/streamlit/": f"This is the Streamlit app written in snowflake snowpark named {folder_name}.",
        }
        return mappings.get(path, "")

    def process(self) -> Dict[str, Any]:
        """
        Process the documents: load, filter, split, embed, and persist.
        """
        data = self._load_and_filter_documents()

        if not data:
            print(colored("No new documents found to embed.\n", "yellow"))
            return {}

        texts = self.text_splitter.split_documents(data)

        if not texts:
            print(colored("No new text segments found to embed.\n", "yellow"))
            return {}

        print(colored(f"\n Found {len(texts)} documents \n", "cyan"))

        vector_store = Chroma.from_documents(
            texts, self.embeddings, persist_directory="chroma_db"
        )
        vector_store.persist()

        self._save_checksums()
        return vector_store

    def _load_and_filter_documents(self) -> List[str]:
        """
        Load documents and filter out previously embedded ones.
        """
        data_py = self.loader_py.load()
        data_md = self.loader_md.load()
        data_src_py = self.loader_src_py.load()

        # Filter out previously embedded files using checksums
        data = []
        for record in data_py + data_md + data_src_py:
            content = self._extract_content_from_record(record)
            checksum = self._create_checksum(content)
            filename = self._extract_filename_from_record(record)

            if checksum != self.checksum_dict.get(filename, None):
                self.checksum_dict[filename] = checksum
                prompt = self._generate_prompt_from_path(filename)
                self._update_record_metadata(record, filename, prompt)
                if not filename.startswith("src/"):
                    print(
                        colored(f"Embedding {filename} with Prompt: {prompt}", "green")
                    )
                data.append(record)
            else:
                if not filename.startswith("src/"):
                    print(colored(f"Skipped {filename}", "yellow"))

        return data

    @staticmethod
    def _extract_content_from_record(record: Any) -> str:
        """
        Extract content from a record.
        """
        if isinstance(record, str):
            return record
        return record.content if hasattr(record, "content") else str(record)

    @staticmethod
    def _extract_filename_from_record(record: Any) -> str:
        """
        Extract filename from a record.
        """
        return record.metadata["source"] if hasattr(record, "metadata") else ""

    @staticmethod
    def _update_record_metadata(record: Any, filename: str, prompt: str) -> None:
        """
        Update metadata for a record.
        """
        if hasattr(record, "metadata"):
            record.metadata["prompt"] = prompt
        else:
            record.metadata = {"prompt": prompt, "source": filename}
