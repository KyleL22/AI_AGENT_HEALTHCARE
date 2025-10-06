import os, pathlib, requests, re
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

def fetch_text_from_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        text = r.text
        # crude HTML strip
        text = re.sub("<[^<]+?>", " ", text)
        return re.sub("\s+", " ", text).strip()
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

def build_vectorstore(urls: List[str], vector_dir: str, embedding_deployment: str, api_key: str, endpoint: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = []
    for u in urls:
        raw = fetch_text_from_url(u)
        for chunk in splitter.split_text(raw):
            docs.append({"page_content": chunk, "metadata": {"source": u}})

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=embedding_deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01"
    )
    texts = [d["page_content"] for d in docs]
    metas = [d["metadata"] for d in docs]
    vs = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metas)
    pathlib.Path(vector_dir).mkdir(parents=True, exist_ok=True)
    vs.save_local(vector_dir)
    return True
