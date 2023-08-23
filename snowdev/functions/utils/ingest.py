from __future__ import annotations

from typing import Any, Dict

import pkg_resources
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from pydantic import BaseModel


class Secrets(BaseModel):
    OPENAI_API_KEY: str


class Config(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 0
    docs_dir: str = pkg_resources.resource_filename(
        "snowdev.functions.utils", "knowledge"
    )

class DocumentProcessor:
    def __init__(self, secrets: Secrets, config: Config):
        self.loader_py = DirectoryLoader(config.docs_dir, glob="**/*.py")
        self.loader_md = DirectoryLoader(config.docs_dir, glob="**/*.md")
        self.text_splitter = CharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=secrets.OPENAI_API_KEY)


    def process(self) -> Dict[str, Any]:
        data_py = self.loader_py.load()
        data_md = self.loader_md.load()
        data = data_py + data_md
        texts = self.text_splitter.split_documents(data)
        print(f"Found {len(texts)} documents")
        vector_store = Chroma.from_documents(
            texts, self.embeddings, persist_directory="chroma_db"
        )
        vector_store.persist()
        return vector_store
