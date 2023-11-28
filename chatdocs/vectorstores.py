from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore

from .config import get_config
from .embeddings import get_embeddings


def get_collection(collection_name: str = "straightlabs") -> VectorStore:
    config = get_config()
    embeddings = get_embeddings(config)
    return Chroma(
        collection_name=collection_name,
        persist_directory=config["chroma"]["persist_directory"],
        embedding_function=embeddings,
        client_settings=Settings(**config["chroma"]),
    )
    
