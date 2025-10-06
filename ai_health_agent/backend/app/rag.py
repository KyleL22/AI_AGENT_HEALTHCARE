import os, time, hashlib
from dotenv import load_dotenv
from typing import List, Dict
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import chromadb

load_dotenv()
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR","./data/vectorstore")

_client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
_collection = _client.get_or_create_collection(name="health_rag")

def _emb():
    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AOAI_DEPLOY_EMBED_3_SMALL","text-embedding-3-small"),
        openai_api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        openai_api_version="2024-02-01"
    )

def chunk_and_ingest_text(user_id: str, raw_text: str) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    docs = [Document(page_content=raw_text, metadata={"user_id": user_id})]
    chunks = splitter.split_documents(docs)
    emb = _emb()

    ids, metadatas, contents = [], [], []
    for i, ch in enumerate(chunks):
        cid = hashlib.md5((user_id + ch.page_content + str(time.time()) + str(i)).encode()).hexdigest()
        ids.append(cid)
        metadatas.append({"user_id": user_id})
        contents.append(ch.page_content)

    vectors = emb.embed_documents(contents)
    _collection.add(ids=ids, metadatas=metadatas, documents=contents, embeddings=vectors)
    return len(ids)

def query_rag(user_id: str, q: str, k: int = 5) -> List[Dict]:
    emb = _emb()
    qv = emb.embed_query(q)
    res = _collection.query(query_embeddings=[qv], n_results=k, where={"user_id": user_id})
    out = []
    for i in range(len(res.get("ids",[[]])[0])):
        out.append({
            "doc": res["documents"][0][i],
            "score": float(res["distances"][0][i]) if "distances" in res else 0.0,
        })
    return out
