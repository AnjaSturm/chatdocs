from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore, VectorStoreRetriever
from langchain.embeddings.base import Embeddings


from .embeddings import get_embeddings




def get_collection(config: Dict[str, Any], collection_name: str, embeddings: Embeddings) -> VectorStore:
    config = config["chroma"]
    return Chroma(
        collection_name=collection_name,
        persist_directory=config["persist_directory"],
        embedding_function=embeddings,
        client_settings=Settings(**config),
    )
    
def get_vectorstore(config: Dict[str, Any], embeddings: Embeddings) -> VectorStore:
    config = config["chroma"]
    return Chroma(
        persist_directory=config["persist_directory"],
        embedding_function=embeddings,
        client_settings=Settings(**config),
    )

def create_collection_from_documents(
    config: Dict[str, Any],
    documents: List[Document], collection_name: str,
    embeddings: Embeddings
) -> VectorStore:
    config = config["chroma"]
    return Chroma.from_documents(
        documents,
        embeddings,
        collection_name=collection_name,
        persist_directory=config["persist_directory"],
        client_settings=Settings(**config),
    )
