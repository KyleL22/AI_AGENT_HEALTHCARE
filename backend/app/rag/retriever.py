import os
from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings

def load_vectorstore(vector_dir: str, embedding_deployment: str, api_key: str, endpoint: str):
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=embedding_deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01"
    )
    return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True)

def retrieve(query: str, k: int, vector_dir: str, embedding_deployment: str, api_key: str, endpoint: str) -> List[Tuple[str, dict]]:
    vs = load_vectorstore(vector_dir, embedding_deployment, api_key, endpoint)
    docs = vs.similarity_search(query, k=k)
    return [(d.page_content, d.metadata) for d in docs]
