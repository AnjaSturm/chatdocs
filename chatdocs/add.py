import os
import glob
from typing import List
from multiprocessing import Pool

from tqdm import tqdm
from langchain.document_loaders import (
    CSVLoader,
    EverNoteLoader,
    PDFMinerLoader,
    TextLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredODTLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from .vectorstores import get_collection



# helper functions
# Custom document loaders
class MyElmLoader(UnstructuredEmailLoader):
    """Wrapper to fallback to text/plain when default does not work"""

    def load(self) -> List[Document]:
        """Wrapper adding fallback for elm without html"""
        try:
            try:
                doc = UnstructuredEmailLoader.load(self)
            except ValueError as e:
                if "text/html content not found in email" in str(e):
                    # Try plain text
                    self.unstructured_kwargs["content_source"] = "text/plain"
                    doc = UnstructuredEmailLoader.load(self)
                else:
                    raise
        except Exception as e:
            # Add file_path to exception message
            raise type(e)(f"{self.file_path}: {e}") from e

        return doc


# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    ".csv": (CSVLoader, {"encoding": "utf8"}),
    # ".docx": (Docx2txtLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (MyElmLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PDFMinerLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
    # Add more mappings for other file extensions and loaders as needed
}


def load_single_document(file_path: str) -> List[Document]:
    ext = "." + file_path.rsplit(".", 1)[-1]
    if ext in LOADER_MAPPING:
        loader_class, loader_args = LOADER_MAPPING[ext]
        loader = loader_class(file_path, **loader_args)
        return loader.load()

    raise ValueError(f"Unsupported file extension '{ext}'")


def load_documents(source_dir: str, ignored_files: List[str] = []) -> List[Document]:
    """
    Loads all documents from the source documents directory, ignoring specified files
    """
    all_files = []
    for ext in LOADER_MAPPING:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)
        )
    filtered_files = [
        file_path for file_path in all_files if file_path not in ignored_files
    ]

    with Pool(processes=os.cpu_count()) as pool:
        results = []
        with tqdm(
            total=len(filtered_files), desc="Loading new documents", ncols=80
        ) as pbar:
            for i, docs in enumerate(
                pool.imap_unordered(load_single_document, filtered_files)
            ):
                results.extend(docs)
                pbar.update()

    return results


def process_documents(
    source_directory: str, ignored_files: List[str] = []
) -> List[Document]:
    """
    Load documents and split in chunks
    """
    print(f"Loading documents from {source_directory}")
    documents = load_documents(source_directory, ignored_files)
    if not documents:
        print("No new documents to load")
        return []
    print(f"Loaded {len(documents)} new documents from {source_directory}")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) #1000, 200?
    texts = text_splitter.split_documents(documents)
    return texts



# adds documents to collection
def add(source_directory: str, collection_name: str) -> None:
    collection = get_collection(collection_name)
    print("Count before add:", collection._client.get_collection(collection_name).count())
    metadatas = collection.get(include=["metadatas"])
    texts = process_documents(
        source_directory,
        [metadata["source"] for metadata in metadatas["metadatas"]],
    )
    if len(texts) != 0:
        print(f"Creating embeddings. May take a few minutes...")
        collection.add_documents(texts) 
    print("Count after add:", collection._client.get_collection(collection_name).count())
             
      
# delete complete collection        
def delete(collection_name: str) -> None:
    vectorstore = get_collection()
    collections = vectorstore._client.list_collections()
    collection_exists = any(collection.name == collection_name for collection in collections)

    # cannot happen bc of empty initialization after deletion, but just in case
    if not collection_exists:
        print("Collection", collection_name, "does not exist")
    else:
        print("Collections before delete of", collection_name)
        for collection in collections:
            print(collection.name)
        
        vectorstore._client.delete_collection(collection_name)
        
        print("Collections after delete of", collection_name)
        updated_collections = vectorstore._client.list_collections()
        for collection in updated_collections:
            print(collection.name)
            
# delete single file from collection            
def delete_file(collection_name: str, file_path: str) -> None:
    collection = get_collection(collection_name)
    
    ids = collection.get(where={"source": file_path})['ids']
    print("ids before delete of", file_path,":", ids)
    print(ids)
    print('REMOVE %s document(s) from %s collection' % (str(len(ids)), collection_name))
    if len(ids): collection.delete(ids)
    print("ids after delete of", file_path, ":", collection.get(where={"source": file_path})['ids'])
        