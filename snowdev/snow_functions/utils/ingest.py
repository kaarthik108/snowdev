import os
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader
from typing import Any, Dict
from pydantic import BaseModel


class Secrets(BaseModel):
    OPENAI_API_KEY: str


class Config(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 0
    docs_dir: str = "snowdev/snow_functions/utils/knowledge"
    docs_glob: str = "**/*.py"


class DocumentProcessor:
    def __init__(self, secrets: Secrets, config: Config):
        self.loader = DirectoryLoader(config.docs_dir, glob=config.docs_glob)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=secrets.OPENAI_API_KEY)

    def process(self) -> Dict[str, Any]:
        data = self.loader.load()
        texts = self.text_splitter.split_documents(data)
        vector_store = Chroma.from_documents(
            texts, self.embeddings, persist_directory="chroma_db"
        )
        vector_store.persist()
        return vector_store


def run():
    secrets = Secrets(OPENAI_API_KEY=os.environ["OPENAI_API_KEY"])
    config = Config()
    doc_processor = DocumentProcessor(secrets, config)
    result = doc_processor.process()
    return result


if __name__ == "__main__":
    run()
