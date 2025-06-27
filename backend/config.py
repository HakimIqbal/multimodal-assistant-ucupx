import os
from dotenv import load_dotenv

load_dotenv()

# ===================== MODEL API KEYS =====================
# Groq API untuk model bahasa
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "multimodal-assistant")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY tidak ditemukan di .env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan di .env")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY tidak ditemukan di .env")

if LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = str(LANGSMITH_API_KEY)
    else:
        print("Warning: LANGSMITH_API_KEY tidak ditemukan, tracing mungkin tidak berfungsi dengan baik.")
    os.environ["LANGCHAIN_ENDPOINT"] = str(LANGSMITH_ENDPOINT or "https://api.smith.langchain.com")
    os.environ["LANGCHAIN_PROJECT"] = str(LANGSMITH_PROJECT or "multimodal-assistant")
    print("System: LangSmith tracing diaktifkan.")
else:
    print("System: LangSmith tracing tidak diaktifkan.")