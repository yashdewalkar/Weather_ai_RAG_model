
from dotenv import load_dotenv
load_dotenv(override=True)
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Qdrant as QdrantVS

from db_utils import get_qdrant_collection
from weather_utils import fetch_weather

from langsmith import traceable
from langchain.chains import RetrievalQA

llm = ChatOpenAI(
    temperature=0,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
)

embeddings = OpenAIEmbeddings(
    model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
)

def is_weather_query(query):
    keywords = ["weather", "temperature", "humidity", "forecast", "rain", "sunny", "climate"]
    return any(word in query.lower() for word in keywords)

@traceable  # This sends trace info to LangSmith if enabled
def answer_query(query, pdf_path=None):
    if is_weather_query(query):
        # Try to extract city from the query
        for word in query.split():
            if word[0].isupper():  # crude city detection, can be improved
                return fetch_weather(word)
        return "Please specify a city for the weather."
    else:
        if pdf_path:
            # Load, split, embed, store & retrieve from PDF
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_documents(docs)
            vector_store = get_qdrant_collection()
            vector_store.add_documents(chunks)
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
            qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
            return qa_chain.run(query)
        else:
            return "Please upload a PDF first for RAG-based QA."
import re

def extract_city(query: str) -> str | None:
    m = re.search(r"(?:\bin|\bat|\bfor)\s+([A-Za-z][A-Za-z\s\-\.,]+)", query or "", flags=re.IGNORECASE)
    if not m:
        return None
    city = m.group(1)
    city = re.sub(r"[^\w\s\-.]", "", city).strip(" .,-?")
    city = re.sub(r"\s{2,}", " ", city)
    return city