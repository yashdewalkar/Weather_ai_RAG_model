
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from langchain_qdrant import Qdrant         
from langchain_openai import OpenAIEmbeddings

def _embedding_size() -> int:
    
    model = (os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small") or "").lower()
    return 3072 if "3-large" in model else 1536

def _ensure_collection(client: QdrantClient, name: str, size: int) -> None:
   
    exists = False
    try:
        if hasattr(client, "collection_exists"):
            exists = bool(client.collection_exists(name))
        else:
            client.get_collection(name)  
            exists = True
    except Exception:
        exists = False

    if not exists:
       
        client.create_collection(
            collection_name=name,
            vectors_config=rest.VectorParams(
                size=size,
                distance=rest.Distance.COSINE,
            ),
        )

def get_qdrant_collection():
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    )

    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "pdf_chunks")
    size = _embedding_size()

    if url:  
        client = QdrantClient(url=url, api_key=api_key, timeout=30.0, prefer_grpc=False)
    else:   
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            timeout=30.0,
            prefer_grpc=False,
        )

    _ensure_collection(client, collection, size)

   
    return Qdrant(client=client, collection_name=collection, embeddings=embeddings)
