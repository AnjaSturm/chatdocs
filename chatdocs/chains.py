from typing import Any, Callable, Dict, Optional

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler  # for streaming response
from langchain.callbacks.manager import CallbackManager
from chromadb.config import Settings


from .llms import get_llm
from .vectorstores import get_collection
import time
import chromadb


callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

template_llama = """
[INST]
You are a helpful assistant, you will use the provided context (delimited by <ctx></ctx>) to answer user questions (delimited by <qs></qs>).
Read the given context before answering questions and think step by step. If you can not answer a user question based on 
the provided context, inform the user. Do not use any other information for answering user. Provide a detailed answer to the question. Answer in German.
------
<ctx>
{history} \n
{context}
</ctx>
------
<qs>
{question}
</qs>
------
Answer:
[/INST]
"""


template_mistral = """
<s>[INST]
You are a helpful assistant, you will use the provided context (delimited by <ctx></ctx>) to answer user questions (delimited by <qs></qs>).
Read the given context before answering questions and think step by step. If you can not answer a user question based on 
the provided context, inform the user. Do not use any other information for answering user. Provide a detailed answer to the question. Answer in German.
------
<ctx>
{history} \n
{context}
</ctx>
------
<qs>
{question}
</qs>
------
Answer:
[/INST]
"""

prompt = PromptTemplate(input_variables=["history", "context", "question"], template=template_llama)
memory = ConversationBufferMemory(input_key="question", memory_key="history")

def get_retrieval_qa(
    config: Dict[str, Any],
    collection_name: str = "cats",
    *,
    callback: Optional[Callable[[str], None]] = None,
) -> RetrievalQA:
#[RetrievalQA, RetrievalQA]:
    # tic = time.perf_counter()
    db = get_collection(config, collection_name)
    collection = db.get()
    print(db._collection.name, "COLLECTION_NAME")
    print(db._collection.count(), "COLLECTION_NAME")
    
    print(db._client, "CLIENTCOUNT")
    print(db.embeddings, "EMBEDDINGS")
    
    
    # print(collection.count(), "COLLECTION_NAME") greht nicht    
    # print(collection["metadatas"][0], "COLLECTIONFULL")
    
    
    # list = []
    # # list.append(metadata["source"] for metadata in collection["metadatas"])
    # source = collection["metadatas"][0]["source"]
    # document = collection["documents"][0]
    # document1 = collection["documents"][1]
    
    # # data = db._collection.get(include=['documents'])
    # print(source, "SOURCE")
    # print(document, "DOCUMENT")
    # print(document1, "DOCUMENT1")
    
    
    
    # collection = db.get()
    # client = chromadb.Client(Settings(persist_directory="db"))
    # col = db._collection.name
    # print(db._collection, "COLLECTION")
    # print(collection['metadata'], "COLLECTION")
    
        
    
    # db1 = get_vectorstore(config)
    
    # toc = time.perf_counter()
    # print(f"Get vectorstore in {toc - tic:0.4f} seconds")
    # tic2 = time.perf_counter()
    retriever = db.as_retriever(**config["retriever"]) # config übergibt anzahl an documenten -> 4
    
    # retriever1 = db1.as_retriever(**config["retriever"])
    
    # toc2 = time.perf_counter()
    # print(f"Get retriever in {toc2 - tic2:0.4f} seconds")
    # tic3 = time.perf_counter()
    llm = get_llm(config, callback=callback)
    #llm = get_llm(config)
    
    # toc3 = time.perf_counter()
    # print(f"Get llm in {toc3 - tic3:0.4f} seconds")
    # print(f"Getting db, retriever, llm in summary: {toc3 - tic:0.4f} seconds")
    
   
    # return [RetrievalQA.from_chain_type(
    #     llm=llm,
    #     retriever=retriever,
    #     return_source_documents=True,
    #     chain_type_kwargs={
    #         "verbose": True,
    #         "prompt": prompt,
    #         "memory": ConversationBufferMemory(
    #             memory_key="history",
    #             input_key="question"
    #         )
    #     }
    # ), chain1]

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        verbose = True, #what does this do?
        callbacks=callback_manager, # same here
        chain_type_kwargs={
            "verbose": True,
            "prompt": prompt,
            "memory": memory
        } 
    )
    
    return qa
