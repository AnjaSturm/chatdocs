from typing import Any, Callable, Dict, Optional

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from .llms import get_llm
from .vectorstores import get_vectorstore
import time

template = """
Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question (delimited by <qs></qs>). Answer based solely on the context. If you cannot answer solely based on the context, say that you don't know instead of making something up. Answer in German:
------
<ctx>
{context}
</ctx>
------
<hs>
{history}
</hs>
------
<qs>
{question}
</qs>
Answer:
"""
prompt = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=template,
)


def get_retrieval_qa(
    config: Dict[str, Any],
    *,
    callback: Optional[Callable[[str], None]] = None,
) -> RetrievalQA:
#[RetrievalQA, RetrievalQA]:
    tic = time.perf_counter()
    db = get_vectorstore(config)
    
    db1 = get_vectorstore(config)
    
    toc = time.perf_counter()
    print(f"Get vectorstore in {toc - tic:0.4f} seconds")
    tic2 = time.perf_counter()
    retriever = db.as_retriever(**config["retriever"])
    
    retriever1 = db1.as_retriever(**config["retriever"])
    
    toc2 = time.perf_counter()
    print(f"Get retriever in {toc2 - tic2:0.4f} seconds")
    tic3 = time.perf_counter()
    llm = get_llm(config, callback=callback)
    toc3 = time.perf_counter()
    print(f"Get llm in {toc3 - tic3:0.4f} seconds")
    print(f"Getting db, retriever, llm in summary: {toc3 - tic:0.4f} seconds")
    chain1 = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever1,
        return_source_documents=True,
        chain_type_kwargs={
            "verbose": True,
            "prompt": prompt,
            "memory": ConversationBufferMemory(
                memory_key="history",
                input_key="question"
            )
        }
    )
    
   
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

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
