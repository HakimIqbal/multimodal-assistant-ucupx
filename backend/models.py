import os
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from src.vector_db import process_and_store_text
from supabase import create_client, Client
from pydantic import SecretStr

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": "mps" if torch.backends.mps.is_available() else "cpu"}
)

INDEX_NAME = "rag-index"
_vector_store = None

def get_vector_store():
    """Lazy initialization of vector store"""
    global _vector_store
    if _vector_store is None:
        try:
            _vector_store = PineconeVectorStore(
                index_name=INDEX_NAME,
                embedding=embedding_model,
                pinecone_api_key=PINECONE_API_KEY
            )
            print("[VectorStore] Berhasil memuat Pinecone vector store.")
        except Exception as e:
            print(f"[VectorStore] Gagal memuat Pinecone vector store: {str(e)}. Membuat indeks baru.")
            try:
                from pinecone import Pinecone, ServerlessSpec
                pc = Pinecone(api_key=PINECONE_API_KEY)
                pc.create_index(
                    name=INDEX_NAME,
                    dimension=1536,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                print("[VectorStore] Indeks baru Pinecone berhasil dibuat.")
                _vector_store = PineconeVectorStore(
                    index_name=INDEX_NAME,
                    embedding=embedding_model,
                    pinecone_api_key=PINECONE_API_KEY
                )
            except Exception as e2:
                print(f"[VectorStore] Gagal membuat indeks Pinecone baru: {str(e2)}")
                _vector_store = None
    return _vector_store

# Model support configuration:
# - SUPPORTED_GROQ_DEFAULT_MODELS: Model Groq (wajib tampil di semua fitur, pakai GROQ_API_KEY dari config)
# - SUPPORTED_GEMINI_DEFAULT_MODELS: Model Gemini (wajib tampil di semua fitur, pakai GEMINI_API_KEY dari config)
# - SUPPORTED_GENERAL_CHAT_MODELS: Model OpenRouter khusus General Chat (pakai OPENROUTER_API_KEY dari config)
# - SUPPORTED_CODER_CHAT_MODELS: Model OpenRouter khusus Coder Chat (pakai OPENROUTER_API_KEY dari config)
# - SUPPORTED_PDF_CHAT_MODELS: Model OpenRouter khusus PDF Chat (pakai OPENROUTER_API_KEY dari config)
SUPPORTED_GROQ_DEFAULT_MODELS = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "llama-3.3-70b-versatile"
]
SUPPORTED_GEMINI_DEFAULT_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro"
]
SUPPORTED_GENERAL_CHAT_MODELS = [
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "moonshotai/kimi-dev-72b:free",
    "opengvlab/internvl3-14b:free",
    "qwen/qwen3-14b:free",
    "qwen/qwen3-32b:free",
    "thudm/glm-z1-32b:free",
    "shisa-ai/shisa-v2-llama3.3-70b:free",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    "qwen/qwen2.5-vl-32b-instruct:free",
    "featherless/qwerky-72b:free"
]
SUPPORTED_CODER_CHAT_MODELS = [
    "agentica-org/deepcoder-14b-preview:free",
    "nvidia/llama-3.3-nemotron-super-49b-v1:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "deepseek/deepseek-r1-distill-qwen-14b:free"
]
SUPPORTED_PDF_CHAT_MODELS = [
    "qwen/qwen3-235b-a22b:free",
    "thudm/glm-4-32b:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free"
]

def get_groq_model(model_name: str = "llama3-70b-8192"):
    if model_name not in SUPPORTED_GROQ_DEFAULT_MODELS:
        print(f"System: Model '{model_name}' tidak didukung. Menggunakan default 'llama3-70b-8192'.")
        model_name = "llama3-70b-8192"
    try:
        return ChatGroq(
            api_key=SecretStr(GROQ_API_KEY),
            model=model_name,
            temperature=0.0,
            max_tokens=4096
        )
    except Exception as e:
        print(f"System: Gagal memuat model '{model_name}': {str(e)}. Menggunakan default 'llama3-70b-8192'.")
        return ChatGroq(
            api_key=SecretStr(GROQ_API_KEY),
            model="llama3-70b-8192",
            temperature=0.0,
            max_tokens=4096
        )

llm = get_groq_model()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_from_supabase():
    try:
        res = supabase.table("documents").select("filename, text_content").execute()
        print(f"System: Data dari Supabase: {res.data}")
        return res.data
    except Exception as e:
        print(f"System: Gagal load data dari Supabase: {str(e)}")
        return []

if LANGSMITH_TRACING:
    from langsmith import Client
    langsmith_client = Client()
    print(f"System: Terhubung ke LangSmith project: {os.environ['LANGSMITH_PROJECT']}")