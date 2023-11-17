from typing import Any, Callable, Dict, Optional

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler  # for streaming response
from langchain.callbacks.manager import CallbackManager
from langchain.llms.base import LLM
from langchain.vectorstores.base import VectorStore

from .add import as_retriever




from .llms import get_llm
from .vectorstores import get_collection, get_vectorstore


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
    llm: LLM,
    collection: VectorStore,
) -> RetrievalQA:
    # retriever = collection.as_retriever(**config["retriever"])
    retriever = as_retriever(collection)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        verbose = True,
        callbacks=callback_manager,
        chain_type_kwargs={
            "verbose": True,
            "prompt": prompt,
            "memory": memory
        } 
    )
    
    return qa
