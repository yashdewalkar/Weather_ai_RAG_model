
import os
import hashlib
import tempfile
import inspect
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# Load .env (keys, config)
load_dotenv(find_dotenv(filename=".env"), override=True)

# Import 
from ai_pipeline import answer_query
try:
    
    from ai_pipeline import compute_doc_id as _pipeline_compute_doc_id
except Exception:
    _pipeline_compute_doc_id = None

# ----- Helpers -----
def _compute_doc_id_local(path: str) -> str:
    """Stable SHA1 of file bytes (used if pipeline doesn't provide one)."""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _save_uploaded_pdf(uploaded) -> str:
    """Persist uploaded PDF to a temp file and return its absolute path."""
    data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    sha8 = hashlib.sha1(data).hexdigest()[:8]
    safe_name = os.path.basename(uploaded.name).replace(" ", "_")
    tmp_path = os.path.join(tempfile.gettempdir(), f"{sha8}_{safe_name}")
    with open(tmp_path, "wb") as f:
        f.write(data)
    return tmp_path

def _call_answer_query(query: str, pdf_path: str | None, doc_id: str | None):
    """Call answer_query, passing doc_id only if the function supports it."""
    sig = inspect.signature(answer_query)
    kwargs = {"pdf_path": pdf_path}
    if "doc_id" in sig.parameters:
        kwargs["doc_id"] = doc_id
    out = answer_query(query, **kwargs)
    if isinstance(out, dict):
        return out.get("answer") or out.get("output") or str(out)
    return str(out)

# ----- Streamlit UI -----
st.set_page_config(page_title="AI Weather & PDF Q&A Chatbot", page_icon="⛅", layout="centered")
st.title("⛅ AI Weather & PDF Q&A Chatbot")

# Session state
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None

# Sidebar: Upload & controls
st.sidebar.header("Upload PDF for RAG")
pdf_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
if pdf_file is not None:
    try:
        tmp_path = _save_uploaded_pdf(pdf_file)
        st.session_state.pdf_path = tmp_path
        # Prefer pipeline's compute_doc_id if available; else local SHA1
        if _pipeline_compute_doc_id is not None:
            st.session_state.doc_id = _pipeline_compute_doc_id(tmp_path)
        else:
            st.session_state.doc_id = _compute_doc_id_local(tmp_path)
        st.sidebar.success(f"PDF uploaded: {os.path.basename(tmp_path)}")
        st.sidebar.caption(f"doc_id: {st.session_state.doc_id[:12]}… (retrieval filtered to this file)")
    except Exception as e:
        st.sidebar.error(f"Failed to save PDF: {e}")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🧹 Clear PDF"):
        st.session_state.pdf_path = None
        st.session_state.doc_id = None
        st.sidebar.info("PDF cleared. Upload a new one for RAG.")
with col2:
    if st.button("🔑 Keys OK?"):
        st.sidebar.write("OPENAI_API_KEY:", "✅" if os.getenv("OPENAI_API_KEY") else "❌")
        st.sidebar.write("OPENWEATHER_API_KEY:", "✅" if os.getenv("OPENWEATHER_API_KEY") else "❌")

# Main input
query = st.text_input("Ask me anything (weather or PDF-based):")

if st.button("Ask"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        try:
            answer = _call_answer_query(query, st.session_state.pdf_path, st.session_state.doc_id)
            st.markdown("**Answer:**")
            st.write(answer)
        except Exception as e:
            st.error(f"Error while answering: {e}")
